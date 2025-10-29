## This script reads sales pipeline data from an Excel file, generates vector embeddings using Azure OpenAI,
## and uploads the data along with embeddings to an Azure AI Search index for enhanced search capabilities.
## Prerequisites: The Azure AI search index must be created with a vector field to store embeddings.
## Required Libraries: openai, pandas, azure-search-documents, python-dotenv, tqdm
## tqdm - to show progress bar during embedding generation
## After running this script, the data will be available in the Azure AI Search index for vector-based search queries.
## USe GetLLMRecommendations.py to query the uploaded data.


import os
import json
import pandas as pd
from openai import AzureOpenAI
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from tqdm import tqdm

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
        
    df = pd.read_excel(file_path, sheet_name="sales_pipeline")

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
    

# ---------- STEP 3: Upload Data to Azure AI Search Index ----------
def upload_to_search(docs):
    print("🔹 Uploading documents to Azure Search...")

    credential = AzureKeyCredential(SEARCH_KEY)
    search_client = SearchClient(endpoint=SEARCH_ENDPOINT, index_name=INDEX_NAME, credential=credential)
    
    try:
        result = search_client.upload_documents(documents=docs)
        print("✅ Successfully uploaded all records to Azure Search.")
        print(f"Uploaded {len(result)} documents.")

    except Exception as e:
        print(f"Upload failed: {e}")


# Debug function to fetch a document by ID when debugging to check whether data is correctly uploaded
# and can be retrieved using Index in Azure AI Search
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
    print("🔹 Data preparation and upload completed.")

    # Debug print statements to search 2 documents to verify data upload
    print("\n Total docs prepared:", len(docs))
    print("\n Sample doc keys:", docs[0].keys())
    print("\n Sample doc content:", docs[0]['content'][:2000])
    print("\n Sample doc vector length:", len(docs[0]['content_vector']))
    fetch_doc_by_id("0")    # Debug fetch first document
    fetch_doc_by_id("200")  # Debug fetch 200th document
    