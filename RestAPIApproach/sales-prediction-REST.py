import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Azure AI Search settings
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("SEARCH_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")

# Azure OpenAI settings (REST)
OPENAI_ENDPOINT = os.getenv("OPEN_AI_ENDPOINT")
OPENAI_KEY = os.getenv("OPEN_AI_KEY")
EMBEDDING_DEPLOYMENT = os.getenv("EMBEDDING_DEPLOYMENT")  # e.g., "text-embedding-ada-002-deployment"
CHAT_DEPLOYMENT = os.getenv("CHAT_DEPLOYMENT")  # e.g., "gpt-35-turbo-deployment"
CHAT_MODEL = os.getenv("CHAT_MODEL")  # Optional, if needed in body
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")  # Optional
OPENAI_API_VERSION = "2023-05-15"
SEARCH_API_VERSION = "2024-07-01"

# Embedding Model End Point from Azure Portal ai.azure.com
# https://sunilaifoundry.cognitiveservices.azure.com/openai/deployments/text-embedding-ada-002/embeddings?api-version=2023-05-15
# Chat Model End Point from Azure Portal ai.azure.com
# https://sunilaifoundry.cognitiveservices.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview

# ---------- STEP 1: Prepare Data & Create Embeddings ----------
def create_embeddings(text):
    url = f"{OPENAI_ENDPOINT}/openai/deployments/{EMBEDDING_DEPLOYMENT}/embeddings?api-version={OPENAI_API_VERSION}"
    headers = {
        "api-key": OPENAI_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "input": text
    }
    resp = requests.post(url, headers=headers, json=body)
    if resp.status_code == 200:
        return resp.json()["data"][0]["embedding"]
    else:
        print(f"Embedding error: {resp.status_code} - {resp.text}")
        raise ValueError("Embedding failed")

# ---------- STEP 1: Prepare Data & Create Embeddings ----------
def prepare_data(file_path):
    print("🔹 Reading CSV file...")
    df = pd.read_csv(file_path)

    # Ensure consistent stage labels
    df["Deal Stage"] = df["deal_stage"].str.strip().str.lower()

    # Create textual representation for embeddings
    df["content"] = df.apply(
        lambda x: f"Opportunity for product {x['product']} in the {x['account_sector']} sector, "
                  f"region {x['account_region']}, "
                  f"stage {x['deal_stage']}, "
                  f"price {x['sales_price']}, revenue {x['revenue_from_deal']}.",
        axis=1
    )

    print("🔹 Generating embeddings (may take a few minutes)...")
    docs = []
    for i, row in tqdm(df.iterrows(), total=len(df), desc="Generating embeddings"):
        emb = create_embeddings(row["content"])
        docs.append({
            "opportunity_id": str(i),
            "content": row["content"],
            "stage": row["Deal Stage"],
            "metadata": json.dumps({
                "product": row["product"],
                "sector": row["account_sector"],
                "region": row["account_region"],
                "stage": row["deal_stage"]
            }),
            "content_vector": emb
        })
    return docs

# ---------- STEP 2: Upload Data to Azure AI Search ----------
def upload_to_search(docs):
    print("🔹 Uploading documents to Azure Search...")
    headers = {
        "Content-Type": "application/json",
        "api-key": SEARCH_KEY
    }
    
    url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}/docs/index?api-version=2024-07-01"
    resp = requests.post(url, headers=headers, json={"value": docs})
    if resp.status_code < 300:
        print("✅ Successfully uploaded all records to Azure Search.")
        print("\n Resp Status Code:", resp.status_code) # Deug print
        print("\n Resp Text:", resp.text[:2000])  # Debug print first 2000 chars of response
    else:
        print(resp.status_code, resp.text)

# ---------- STEP 3: Perform Vector Search ----------
def semantic_search(query, stage_filter=None, top_k=10):
    embedding = create_embeddings(query)

    # debug print
    print("\n Inside Semantic Search - Query embedding length:", len(embedding))

    headers = {
        "Content-Type": "application/json",
        "api-key": SEARCH_KEY
    }

    body = {
        "vectorQueries": [
            {
                "kind": "vector",
                "vector": embedding,
                "fields": "content_vector",
                "k": top_k,
                "exhaustive": False
            }    
        ],
        "select": "content,stage",
        "top": top_k
    }

    # Optional: Filter by deal stage (“won” or “lost”)
    if stage_filter:
        print("\n Stage filter applied:", stage_filter)
        body["filter"] = f"stage eq '{stage_filter}'"
    
    url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}/docs/search?api-version={SEARCH_API_VERSION}"
    resp = requests.post(url, headers=headers, json=body)
    
    # Start of debug prints
    print("\n Search HTTP status:", resp.status_code)
    if resp.status_code == 200:
        results = resp.json()
        print("\n Number of results returned:", len(results.get("value", [])))
        return results.get("value", [])
    else:
        print(f"\n Search error: {resp.status_code} - {resp.text[:500]}")
        return []
    

# ---------- STEP 4: GPT Reasoning ----------
def llm_recommendation(user_query, won_context, lost_context):
    print("🔹 Asking GPT for recommendations...")

    # Combine contexts
    context_text = (
        f"=== Successful Deals ===\n"
        f"{won_context}\n\n"
        f"=== Failed Deals ===\n"
        f"{lost_context}\n"
    )

    messages = [
        {"role": "system",
         "content": "You are a sales strategy advisor. Use given examples of successful and failed opportunities to analyze what to add or remove from the current opportunity to increase success rate."},
        {"role": "user",
         "content": f"Current Opportunity:\n{user_query}\n\n{context_text}\n\n"
                    f"Please provide clear insights:\n"
                    f"1️⃣ What to REMOVE from the current opportunity to reduce likelihood of failure.\n"
                    f"2️⃣ What to ADD or IMPROVE to boost chances of success.\n"}
    ]

    url = f"{OPENAI_ENDPOINT}/openai/deployments/{CHAT_DEPLOYMENT}/chat/completions?api-version={OPENAI_API_VERSION}"
    headers = {
        "api-key": OPENAI_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "messages": messages,
        "max_tokens": 750,
        "temperature": 0.6
    }
    resp = requests.post(url, headers=headers, json=body)
    if resp.status_code == 200:
        response_content = resp.json()["choices"][0]["message"]["content"]
        print("\n--- GPT Sales Recommendations ---\n")
        print(response_content)
    else:
        print(f"Chat error: {resp.status_code} - {resp.text}")


# ---------- STEP 5: Run Workflow ----------
if __name__ == "__main__":
    csv_path = "Test_Sales_Data.csv"

    # ---- Data preparation & upload (run once) ----
    docs = prepare_data(csv_path)
    upload_to_search(docs)

    # ---- Interactive query loop ----
    while True:
        query = input("\nEnter new opportunity description (or 'quit' to exit): ")
        if query.lower() == "quit":
            break

        # Retrieve top 10 successful & failed opportunities
        successful = semantic_search(query, stage_filter="won", top_k=10)
        failed = semantic_search(query, stage_filter="lost", top_k=10)

        print(f"\n✅ Retrieved {len(successful)} successful and {len(failed)} failed opportunities.")

        won_context = "\n".join([doc["content"] for doc in successful])
        print(f"Successful matching opportunities:\n{won_context}...")
        lost_context = "\n".join([doc["content"] for doc in failed])
        print(f"Failed matching opportunities:\n{lost_context}...")

        # Analyze via GPT
        llm_recommendation(query, won_context, lost_context)
