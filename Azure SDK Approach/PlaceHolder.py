## Sales Recommendation Advisor using Azure OpenAI and Azure Cognitive Search
## UploadBatchData.py was used to create embedding data and then upload to Azure Search Index.
## So, before running this code, run UploadBatchData.py to create the index with data.
## You can use this program as base version and create a new program to suit your needs.

import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from datetime import datetime
from pathlib import Path


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

# Create a log file to log key operations
script_dir = Path(__file__).parent  # Get the directory of the script
file_name = "LLM Recommendation Output.txt"
log_file_path = script_dir / file_name

# Function to write messages to the user log file
def write_to_file(text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] : {text}\n")


def embed_text(text):
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding

def get_top_matches(prompt, stage_filter, top_k=10):

    write_to_file(f"Searching for top {top_k} matches for stage '{stage_filter}' with prompt: {prompt}")
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
        f"Deal Value Ratio: {doc.get('deal_value_ratio')}"
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
    write_to_file("\n\n=== New Session Started ===")
    write_to_file(f"****  Using Azure OpenAI Model: {CHAT_MODEL}  ****")

    while True:
        # Start fresh conversation history
        conversation = [
            {
                "role": "system",
                "content": (
                    "You are a sales strategy expert. You will help users improve their sales opportunity based on similar won/lost deals from the database. Use all prior context for reasoning."
                )
            }
        ]

        write_to_file(f"The persona for this session:\n Role: {conversation[0]['role']} \n Content: {conversation[0]['content']}")

        # Get user's sales opportunity description
        prompt = input("\nDescribe new sales opportunity (or 'quit' to exit): ")
        if prompt.strip().lower() == "quit":
            break

        write_to_file(f"User Sales Opportunity Prompt: {prompt}")
        
        # Retrieve similar opportunities
        print("\n🔎 Retrieving top matches from index...")
        write_to_file("Retrieving top 10 won and lost matches from Azure Cognitive Search...")
        won_docs = get_top_matches(prompt, stage_filter="won", top_k=10)
        lost_docs = get_top_matches(prompt, stage_filter="lost", top_k=10)
        print(f"=== Top 10 Successful Matches ===\n{format_docs(won_docs)}")
        print(f"\n=== Top 10 Failed Matches ===\n{format_docs(lost_docs)}")
        
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
        write_to_file(f"LLM Recommendation:\n{recommendation}")

        # Add the LLM recommendation to the conversation
        conversation.append({
            "role": "assistant",
            "content": recommendation
        })

        # Allow follow-up questions
        while True:
            follow_up = input("\nAsk any follow-up question on this sales scenario (or 'quit' to start over): ")
            write_to_file(f"\n\nUser Follow-up Question:{follow_up}")
            if follow_up.strip().lower() == "quit":
                break
            conversation.append({
                "role": "user",
                "content": follow_up
            })
            answer = llm_chat(conversation)
            print("\n🔄 GPT Response:\n", answer)
            write_to_file(f"LLM Follow-up Response:\n{answer}")
            # Add the answer to conversation for stateful context
            conversation.append({
                "role": "assistant",
                "content": answer
            })

if __name__ == "__main__":
    main()
