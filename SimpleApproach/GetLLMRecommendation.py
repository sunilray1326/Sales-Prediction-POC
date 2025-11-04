## This script retrieves similar successful and failed sales opportunities
## from an Azure AI Search index based on a user query, and then uses   
## LLM gpt-4o LLM to provide recommendations on improving the sales opportunity.
## Prerequisites: It uses "salespredictionindex" Azure AI Search index avaialble and upploaded with sales opportunity data.
## The program DataEmbedUpload.py was used to create and upload the index with sample data for this program.
## For this program the Index is defined as "salespredictionindex" with fields
## id, content, stage, metadata, content_vector (vector field for embeddings)

import os
import json
import pandas as pd
from pathlib import Path
from openai import AzureOpenAI
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from datetime import datetime

# Load environment variables
load_dotenv()

# Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("OPEN_AI_KEY"),
    azure_endpoint=os.getenv("OPEN_AI_ENDPOINT"),
    api_version="2024-12-01-preview"
)

# Azure AI Search settings
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("SEARCH_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")
CHAT_MODEL = os.getenv("CHAT_MODEL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

# Create a log file to log key operations
script_dir = Path(__file__).parent  # Get the directory of the script
file_name = "LLM Prediction Output.txt"
log_file_path = script_dir / file_name

# Function to write messages to the log file
def write_to_file(text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] : {text}\n")


# ---------- STEP 1: Prepare Data & Create Embeddings ----------
def create_embeddings(text):
    resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return resp.data[0].embedding


# ---------- STEP 2: Perform Vector Search ----------
def semantic_search(query, stage_filter=None, top_k=10):
    embedding = create_embeddings(query)
    print("\nSemantic Search - Query embedding length:", len(embedding))
    write_to_file(f"Performing semantic search for query: {query} with stage filter: {stage_filter}...")

    credential = AzureKeyCredential(SEARCH_KEY)
    search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=credential)

    search_options = {
        "vector_queries": [{
            "kind": "vector",
            "vector": embedding,
            "fields": "content_vector",
            "k": top_k,
            "exhaustive": False
        }],
        "select": "content, stage",
        "top": top_k
    }

    # Optional: Filter by deal stage (“won” or “lost”)
    if stage_filter:
        print("\n Stage filter applied:", stage_filter)
        search_options["filter"] = f"stage eq '{stage_filter}'"

    try:
        results = search_client.search(search_text=None, **search_options)
        return [doc for doc in results]
    except Exception as e:
        print(f"Search failed: {e}")
        return []

# ---------- STEP 3: GPT Reasoning ----------
def llm_recommendation(user_query, won_context, lost_context):
    print("🔹 Asking GPT for recommendations...")
    write_to_file(f"Generating GPT recommendations for: '{user_query}'")

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
                    f"1. What to REMOVE from the current opportunity to reduce likelihood of failure.\n"
                    f"2. What to ADD or IMPROVE to boost chances of success.\n"}
    ]

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        max_tokens=750,
        temperature=0.6
    )

    print("\n--- GPT Sales Recommendations ---\n")
    print(response.choices[0].message.content)
    write_to_file(f"GPT Sales Recommendations:\n{response.choices[0].message.content}")
    
 

# ---------- STEP 5: Run Workflow ----------
if __name__ == "__main__":
    
    # ---- Interactive query loop ----
    while True:
        query = input("\nEnter new opportunity description (or 'quit' to exit): ")
        if query.lower() == "quit":
            break

        write_to_file(f"New Opportunity query received: {query}...")
        # Retrieve top 10 successful & failed opportunities
        successful = semantic_search(query, stage_filter="won", top_k=10)
        failed = semantic_search(query, stage_filter="lost", top_k=10)

        print(f"\n✅ Retrieved {len(successful)} successful and {len(failed)} failed opportunities.")
        write_to_file(f"Retrieved {len(successful)} successful and {len(failed)} failed opportunities...")

        won_context = "\n".join([doc["content"] for doc in successful])
        write_to_file(f"Successful matching opportunities:\n{won_context}...")

        lost_context = "\n".join([doc["content"] for doc in failed])
        write_to_file(f"Failed matching opportunities:\n{lost_context}...")
        
        # Analyze via GPT
        llm_recommendation(query, won_context, lost_context)
