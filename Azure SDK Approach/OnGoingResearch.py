import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Load environment variables
load_dotenv()
OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")
OPEN_AI_ENDPOINT = os.getenv("OPEN_AI_ENDPOINT")
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("SEARCH_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
CHAT_MODEL = os.getenv("CHAT_MODEL")

openai_client = AzureOpenAI(
    api_key=OPEN_AI_KEY,
    azure_endpoint=OPEN_AI_ENDPOINT,
    api_version="2024-12-01-preview"
)
search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(SEARCH_KEY)
)

def embed_text(text):
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding

def get_top_matches(prompt, stage_filter, top_k=10):
    embedding = embed_text(prompt)
    filter_expr = f"deal_stage eq '{stage_filter}'"
    results = search_client.search(
        search_text=None,
        vector_queries=[
            {
                "kind": "vector",
                "fields": "text_vector",
                "vector": embedding,
                "k": top_k,
                "exhaustive": False
            }
        ],
        filter=filter_expr,
        select=[
            "opportunity_id", "content", "deal_stage", "product", "account_sector", "sales_rep", "account_region", 
            "sales_price", "revenue_from_deal", "sales_cycle_duration", "deal_value_ratio"
        ],
        top=top_k
    )
    return [doc for doc in results]


def format_docs(docs):
    return "\n".join([
        f"{doc.get('opportunity_id')} | Stage: {doc.get('deal_stage').capitalize()} | Rep: {doc.get('sales_rep')} | "
        f"Product: {doc.get('product')} | Sector: {doc.get('account_sector')} | Region: {doc.get('account_region')} | "
        f"Price: {doc.get('sales_price')}, | Revenue: {doc.get('revenue_from_deal')} | Sales Cycle Duration: {doc.get('sales_cycle_duration')} days | "
        f"Deal Value Ratio: {doc.get('deal_value_ratio')} | {doc.get('content')[:80]}..."
        for doc in docs
    ])


def llm_chat(messages):
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.6,
        max_tokens=700
    )
    return response.choices[0].message.content

def main():
    print("💡 Sales Opportunity RAG Advisor (Type 'quit' at any prompt to exit)")

    while True:
        # Start fresh conversation history
        conversation = [
            {
                "role": "system",
                "content": (
                    "You are a sales strategy advisor. You will help users improve their sales opportunity based on similar won/lost deals from the database. Use all prior context for reasoning."
                )
            }
        ]

        # Get user's sales opportunity description
        prompt = input("\nDescribe new sales opportunity (or 'quit' to exit): ")
        if prompt.strip().lower() == "quit":
            break

        # Retrieve similar opportunities
        print("\n🔎 Retrieving top matches from index...")
        won_docs = get_top_matches(prompt, stage_filter="won", top_k=10)
        lost_docs = get_top_matches(prompt, stage_filter="lost", top_k=10)

        context_msg = (
            f"User Opportunity:\n{prompt}\n\n"
            f"=== Top 10 Successful Matches ===\n{format_docs(won_docs)}\n\n"
            f"=== Top 10 Failed Matches ===\n{format_docs(lost_docs)}\n"
        )

        print("\n 🧠 Context for LLM:\n", context_msg)

        # Add initial user/context message
        conversation.append({
            "role": "user",
            "content": (
                f"{context_msg}\n"
                "Recommend:\n"
                "1. What should be added/improved to increase sale chances?\n"
                "2. What should be removed to reduce failure risk?"
            )
        })

        # Get LLM recommendation
        recommendation = llm_chat(conversation)
        print("\n🧠 GPT Recommendation:\n", recommendation)

        # Add the LLM recommendation to the conversation
        conversation.append({
            "role": "assistant",
            "content": recommendation
        })

        # Allow follow-up questions
        while True:
            follow_up = input("\nAsk any follow-up question on this sales scenario (or 'quit' to start over): ")
            if follow_up.strip().lower() == "quit":
                break
            conversation.append({
                "role": "user",
                "content": follow_up
            })
            answer = llm_chat(conversation)
            print("\n🔄 GPT Response:\n", answer)
            # Add the answer to conversation for stateful context
            conversation.append({
                "role": "assistant",
                "content": answer
            })

if __name__ == "__main__":
    main()
