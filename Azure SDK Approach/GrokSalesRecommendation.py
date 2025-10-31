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
import json


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

# Load historical statistics
script_dir = Path(__file__).parent  # Get the directory of the script
stats_path = script_dir / "Cline_stats.json"
with open(stats_path, "r", encoding="utf-8") as f:
    stats = json.load(f)

# Create a log file to log key operations
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
        f"Price: {doc.get('sales_price')} | Revenue: {doc.get('revenue_from_deal')} | Sales Cycle Duration: {doc.get('sales_cycle_duration')} days | "
        f"Deal Value Ratio: {doc.get('deal_value_ratio')}"
        for doc in docs
    ])


def extract_attributes(prompt):
    """Use LLM to extract key attributes from the user prompt."""
    extraction_prompt = [
        {
            "role": "system",
            "content": "You are an attribute extractor. Parse the user prompt and extract: product (str or None), sector (str or None), region (str or None), sales_price (float or None), expected_revenue (float or None), current_rep (str or None). Return as JSON dict."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=extraction_prompt,
        temperature=0.1,
        max_tokens=200
    )
    try:
        extracted = json.loads(response.choices[0].message.content)
        write_to_file(f"Extracted attributes: {json.dumps(extracted)}")
        return extracted
    except json.JSONDecodeError:
        write_to_file("Extraction failed; using defaults.")
        return {}


def get_relevant_stats(extracted_attrs):
    """Filter and summarize relevant stats from JSON based on extracted attributes."""
    relevant = {
        "overall_win_rate": stats["overall_win_rate"],
        "avg_cycle_days": stats["avg_cycle_days"],
        "correlations": stats["correlations"]
    }
    
    # Product-specific: If product extracted, include it and top 3 alternatives by lift
    product = extracted_attrs.get("product")
    if product and product in stats["product"]["win_rate"]:
        prod_stats = stats["product"]
        relevant["products"] = {product: prod_stats["win_rate"][product]}
        # Top alternatives (exclude current)
        alts = sorted(
            [(k, prod_stats["lift"][k]) for k in prod_stats["lift"] if k != product],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        for alt_prod, _ in alts:
            relevant["products"][alt_prod] = prod_stats["win_rate"][alt_prod]
        relevant["avg_revenue_by_product"] = {k: stats["avg_revenue_by_product"][k] for k in relevant["products"]}
    
    # Sector-specific
    sector = extracted_attrs.get("sector")
    if sector and sector in stats["account_sector"]["win_rate"]:
        sec_stats = stats["account_sector"]
        relevant["sector"] = {
            sector: {
                "win_rate": sec_stats["win_rate"][sector],
                "lift": sec_stats["lift"][sector]
            }
        }
        # Top 3 alternative sectors by lift
        alts = sorted(
            [(k, sec_stats["lift"][k]) for k in sec_stats["lift"] if k != sector],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        for alt_sec, _ in alts:
            relevant["sector"][alt_sec] = {
                "win_rate": sec_stats["win_rate"][alt_sec],
                "lift": sec_stats["lift"][alt_sec]
            }
        
        # Product-sector combos if product also extracted
        if product:
            prod_sec_key = f"{product}_{sector}"
            if prod_sec_key in stats["product_sector_win_rates"]:
                relevant["product_sector"] = {prod_sec_key: stats["product_sector_win_rates"][prod_sec_key]}
            # Top 3 alternative products in this sector
            sec_combos = [(k.split("_")[0], v) for k, v in stats["product_sector_win_rates"].items() if k.endswith(f"_{sector}")]
            alts = sorted(sec_combos, key=lambda x: x[1], reverse=True)[:3]
            for alt_prod, wr in alts:
                if alt_prod != product:
                    relevant["product_sector"][f"{alt_prod}_{sector}"] = wr
    
    # Region-specific
    region = extracted_attrs.get("region")
    if region and region in stats["account_region"]["win_rate"]:
        reg_stats = stats["account_region"]
        relevant["region"] = {
            region: {
                "win_rate": reg_stats["win_rate"][region],
                "lift": reg_stats["lift"][region]
            }
        }
    
    # Sales Rep stats: Always include top 5 by lift, and current if extracted
    rep_stats = stats["sales_rep"]
    current_rep = extracted_attrs.get("current_rep")
    if current_rep and current_rep in rep_stats["win_rate"]:
        relevant["current_rep"] = {
            "name": current_rep,
            "win_rate": rep_stats["win_rate"][current_rep],
            "lift": rep_stats["lift"][current_rep],
            "sample_size": rep_stats["sample_size"][current_rep]
        }
    # Top 5 reps by lift
    top_reps = sorted(
        [(k, rep_stats["lift"][k], rep_stats["win_rate"][k], rep_stats["sample_size"][k]) for k in rep_stats["lift"]],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    relevant["top_reps"] = [{"name": name, "win_rate": wr, "lift": lift, "sample_size": ss} for name, lift, wr, ss in top_reps]
    
    # Simulations: Simple Python-based estimates
    simulations = []
    baseline_wr = relevant["overall_win_rate"]
    if "sector" in relevant and sector:
        sec_lift = relevant["sector"][sector]["lift"]
        simulations.append({
            "description": f"Baseline adjusted for {sector} sector",
            "estimated_win_rate": baseline_wr * sec_lift,
            "uplift_percent": (sec_lift - 1) * 100
        })
    if "products" in relevant:
        for prod, wr in relevant["products"].items():
            lift = stats["product"]["lift"][prod]
            simulations.append({
                "description": f"Switch to {prod}",
                "estimated_win_rate": baseline_wr * lift,
                "uplift_percent": (lift - 1) * 100,
                "revenue_estimate": stats["avg_revenue_by_product"].get(prod, 0)
            })
    if "top_reps" in relevant:
        for rep in relevant["top_reps"]:
            simulations.append({
                "description": f"Assign to {rep['name']}",
                "estimated_win_rate": baseline_wr * rep["lift"],
                "uplift_percent": (rep["lift"] - 1) * 100,
                "confidence": "High" if rep["sample_size"] > 200 else "Medium"
            })
    relevant["simulations"] = simulations
    
    # Price/Revenue checks
    price = extracted_attrs.get("sales_price")
    if price:
        corr_price = stats["correlations"]["sales_price"]
        relevant["price_insight"] = f"Current price {price}: Correlation with win rate {corr_price:.4f} (negative suggests lower price may help)."
    rev = extracted_attrs.get("expected_revenue")
    if rev:
        relevant["revenue_insight"] = f"Expected revenue {rev}: Compare to product avgs for uplift potential."
    
    write_to_file(f"Relevant stats summary: {json.dumps(relevant, indent=2)}")
    return relevant


def llm_chat(messages):
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.6,
        max_tokens=1000  # Increased for more detailed responses
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
                    "You are a sales strategy expert specializing in opportunity optimization. Analyze the user's sales opportunity by comparing"
                     "it to similar won and lost deals from the database, focusing on key factors such as product, account sector, region,"
                     "sales rep, pricing, revenue potential, sales cycle duration, and deal value ratio.\n" 
                    
                    "Use the provided top 10 won deals as positive examples (what worked) and top 10 lost deals as cautionary examples (what failed)."
                     "Draw patterns from these matches to provide actionable, evidence-based advice, leveraging the filtered RELEVANT_STATS.\n\n"
                    
                    "RELEVANT_STATS is tailored to extracted attributes (e.g., sector, product); use it for precise suggestions. "
                    "Incorporate SIMULATIONS for estimated impacts (e.g., 'Switch to top rep for +4.7% win rate based on simulation').\n"
                    "For reps: Suggest changes if top_reps show >5% lift over current_rep.\n"
                    "Ground all in data; cite simulations/relevant metrics.\n\n"

                    "Structure your responses as follows:\n"
                    "- **Additions/Improvements for Success:** List 3-5 prioritized suggestions (e.g., product/rep changes), referencing won examples and quantifying with RELEVANT_STATS/SIMULATIONS (e.g., '+3% win rate, $X revenue').\n"
                    "- **Removals/Risks to Avoid:** List 3-5 suggestions to mitigate risks (e.g., pricing adjustments), referencing lost examples and quantifying downsides.\n"
                    "- **Overall Strategy:** Summarize plan, estimated win probability improvement (from simulations), revenue/cycle impact, and next steps.\n"

                    "Be concise, actionable, and professional."
                )
            }
        ]

        write_to_file(f"The persona for this session:\n Role: {conversation[0]['role']} \n Content: {conversation[0]['content']}")

        # Get user's sales opportunity description
        prompt = input("\nDescribe new sales opportunity (or 'quit' to exit): ")
        if prompt.strip().lower() == "quit":
            break

        write_to_file(f"User Sales Opportunity Prompt: {prompt}")
        
        # Extract attributes
        print("\n🔍 Extracting attributes from prompt...")
        extracted_attrs = extract_attributes(prompt)
        
        # Get relevant stats
        print("\n📊 Filtering relevant stats...")
        relevant_stats = get_relevant_stats(extracted_attrs)
        
        # Retrieve similar opportunities
        print("\n🔎 Retrieving top matches from index...")
        write_to_file("Retrieving top 10 won and lost matches from Azure Cognitive Search...")
        won_docs = get_top_matches(prompt, stage_filter="won", top_k=10)
        lost_docs = get_top_matches(prompt, stage_filter="lost", top_k=10)
        print(f"=== Top 10 Successful Matches ===\n{format_docs(won_docs)}")
        print(f"\n=== Top 10 Failed Matches ===\n{format_docs(lost_docs)}")
        
        context_msg = (
            f"User Opportunity:\n{prompt}\n"
            f"Extracted Attributes: {json.dumps(extracted_attrs)}\n\n"
            f"=== Top 10 Successful Matches ===\n{format_docs(won_docs)}\n\n"
            f"=== Top 10 Failed Matches ===\n{format_docs(lost_docs)}\n"
        )
        print("\n 🧠 Context for LLM:\n", context_msg)
        write_to_file(f"Context for LLM:\n{context_msg}")

        # Add initial user/context message with relevant stats
        conversation.append({
            "role": "user",
            "content": (
                f"Based on the following details:\n"
                f"{context_msg}\n\n"
                f"RELEVANT_STATS (filtered for this opportunity):\n{json.dumps(relevant_stats, indent=2)}\n\n"

                "Provide tailored recommendations, using RELEVANT_STATS and SIMULATIONS to quantify impacts:\n"
                "1. What 3-5 key additions/improvements (e.g., product/rep changes) to boost win chances? Prioritize, reference won examples, quantify (e.g., '+2% win rate via simulation, $X revenue').\n"
                "2. What 3-5 elements to remove/mitigate (e.g., pricing risks)? Reference lost examples, quantify risks.\n"
                "3. Overall: Estimated win probability improvement (e.g., +5-10% from baseline), revenue/cycle impact, next steps."
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
            write_to_file(f"User Follow-up Question: {follow_up}")
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