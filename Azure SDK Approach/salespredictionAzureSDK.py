####################################################################################################################################################
####################################################################################################################################################
## This program build embeddings for sales opportunity data from an Excel file and then uploads to Azure AI Search Index.
## It then allows user to input a new sales opportunity description, performs semantic search to find similar successful and failed opportunities,
## and uses GPT to provide recommendations on improving the chances of success for the new opportunity based on retrieved contexts.   
## Please note that you need to have the required Azure services set up and the necessary environment variables configured for this code to work.
## Like Setting up Azure AI Search Service, creating an index in Azure Search with vector search capabilities.
## Creatiing data emdedding and uploading to Azure AI Search Index shold be done only once unless the data changes.
## Once, the data is uploaded, you only need to run the interactive query loop to get recommendations for new opportunities.
## So, essentially, data embedding and upload is a one-time setup step.
## For this reason, this program should be split into two parts - one for data embedding and upload, and another for interactive querying and 
## recommendation. However, for simplicity, both parts are included in this single script here.
## I have created two other files - DataEmbedUpload.py to upload data once and then we can run SalesRecommendation.py to get recommendations.
## This file combines both functionalities for ease of use in a single script. But in production, it's better to separate them. 
## DO NOT USE THIS CODE AS IS IN PRODUCTION. IT IS FOR DEMONSTRATION PURPOSES ONLY.
#####################################################################################################################################################
#####################################################################################################################################################

import os
import json
import pandas as pd
from pathlib import Path
from openai import AzureOpenAI
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from tqdm import tqdm
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

# Function to write messages to the user log file
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

# Step 2 Prepare data from Excel and create vector embedding
def prepare_data(file_path):
    print("🔹 Reading Excel file...")
    write_to_file(f"Reading Excel file {file_path} for data preparation...")
        
    df = pd.read_excel(file_path, sheet_name="sales_pipeline")

    # Ensure consistent stage labels
    df["Deal Stage"] = df["Deal Stage"].str.strip().str.lower()

    # Create textual representation for embeddings
    df["content"] = df.apply(
        lambda x: f"Opportunity for product {x['product']} in the {x['account_sector']} sector, "
                  f"region {x['account_region']}, "
                  f"stage {x['deal_stage']}, "
                  f"price {x['sales_price']}, revenue {x['revenue_from_deal']}.",
        axis=1
    )

    print("🔹 Generating embeddings (may take a few minutes)...")
    write_to_file(f"Generating embeddings for the dataset(may take a few minutes)...")

    docs = []
    for i, row in tqdm(df.iterrows(), total=len(df), desc="Generating embeddings"):
        emb = create_embeddings(row["content"])
        docs.append({
            "opportunity_id": str(i),
            "content": row["content"],
            "stage": row["deal_stage"],
            "metadata": json.dumps({
                "product": row["product"],
                "sector": row["account_sector"],
                "region": row["account_region"],
                "stage": row["deal_stage"]
            }),
            "content_vector": emb
        })
    write_to_file(f"Generated embeddings for {len(docs)} documents.")  # Add at end 
    return docs
    

# ---------- STEP 3: Upload Data to Azure AI Search ----------
def upload_to_search(docs):
    print("🔹 Uploading documents to Azure Search...")
    write_to_file(f"Uploading {len(docs)} documents to Azure Search...")

    credential = AzureKeyCredential(SEARCH_KEY)
    search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=credential)
    
    try:
        result = search_client.upload_documents(documents=docs)
        print("✅ Successfully uploaded all records to Azure Search.")
        print(f"Uploaded {len(result)} documents.")
        write_to_file(f"Upload successful: {len(result)} documents indexed.")

    except Exception as e:
        print(f"Upload failed: {e}")
        write_to_file(f"Upload failed: {str(e)}")

# ---------- STEP 4: Perform Vector Search ----------
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

# ---------- STEP 5: GPT Reasoning ----------
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
    

# Debug function to fetch a document by ID when debugging to check whether data is correctly uploaded
# and can be retrieved using Index created in Azure AI Search
def fetch_doc_by_id(doc_id):
    print("🔹 Inside Fetch by document ID - Fetching document by ID from Azure Search... ")
    
    # Create a SearchClient
    credential = AzureKeyCredential(SEARCH_KEY)
    search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=credential)

    try:
        # Fetch the document by its ID
        document = search_client.get_document(key=doc_id)
        # Print the fetched document
        print(f"Fetched document with ID '{doc_id}':")
        for field_name, field_value in document.items():
            print(f"  {field_name}: {field_value[:200]}")  # Print first 200 chars of each field

    except Exception as ex:
        print(f"Failed to fetch document with ID '{doc_id}': {ex}")
    

# ---------- STEP 5: Run Workflow ----------
if __name__ == "__main__":
    excel_path = "Test Sales Data.xlsx"

    # ---- Data preparation & upload (run once) ----
    docs = prepare_data(excel_path)
    upload_to_search(docs)

    ###################################################################################
    # Debug print statements                                                          # 
    # print("\n Total docs prepared:", len(docs))                                     #
    # print("\n Sample doc keys:", docs[0].keys())                                    #
    # print("\n Sample doc content:", docs[0]['content'][:2000])                      #
    # print("\n Sample doc vector length:", len(docs[0]['content_vector']))           #
    # fetch_doc_by_id("0")    # Debug fetch first document                            #
    # fetch_doc_by_id("200")  # Debug fetch 200th document                            #
    ###################################################################################
    
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
