## This script uploads sales opportunity data to an Azure AI Search index in batches.
## It reads data from a CSV file, generates embeddings using Azure OpenAI,
## and uploads the data along with embeddings to the search index.
## After running this script, the Azure AI Search index will be populated with the sales opportunity data.
## The you can run SalesRecommenderApp.py to search the index for simlar sales opportunities and send to LLM to generate recommendations.

import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
import os
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Load env variables
load_dotenv()
OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")
OPEN_AI_ENDPOINT = os.getenv("OPEN_AI_ENDPOINT")
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("SEARCH_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

# OpenAI client
openai_client = AzureOpenAI(
    api_key=OPEN_AI_KEY,
    azure_endpoint=OPEN_AI_ENDPOINT,
    api_version="2024-12-01-preview"
)

# Azure Search client
search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(SEARCH_KEY)
)

def embed_text(text):
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding

def upload_data_in_batches(df, batch_size=400):
    
    total = len(df)
    
    # Upload in batches
    for i in tqdm(range(0, total, batch_size), desc="Uploading batches..."):
        batch = df.iloc[i : i + batch_size]
        docs = []
        for idx, row in batch.iterrows():
            # Calculated fields
            try:
                sales_cycle_duration = None
                deal_value_ratio = None
                if pd.notnull(row['deal_close_date']) and pd.notnull(row['deal_engage_date']):
                    sales_cycle_duration = (
                        pd.to_datetime(row['deal_close_date']) - pd.to_datetime(row['deal_engage_date'])
                    ).days
                if pd.notnull(row['revenue_from_deal']) and pd.notnull(row['sales_price']) and row['sales_price'] != 0:
                    deal_value_ratio = float(row['revenue_from_deal']) / float(row['sales_price'])
            except Exception:
                pass

            # Content for embedding
            content = (
                f"Product: {row['product']}, Sector: {row['account_sector']}, Region: {row['account_region']}, "
                f"Stage: {row['deal_stage']}, Sales Rep: {row['sales_rep']}, Price: {row['sales_price']}, "
                f"Revenue: {row['revenue_from_deal']}, Account Size: {row['account_size']}, "
                f"Account Revenue: {row['account_revenue']}, Engage Date: {row['deal_engage_date']}, "
                f"Close Date: {row['deal_close_date']}"
            )

            try:
                embedding = embed_text(content)
                doc = {
                    "opportunity_id": str(row['opportunity_id']),
                    "sales_rep": str(row['sales_rep']),
                    "product": str(row['product']),
                    "product_series": str(row['product_series']),
                    "sales_price": float(row['sales_price']),
                    "account_name": str(row['account_name']),
                    "account_sector": str(row['account_sector']),
                    "account_region": str(row['account_region']),
                    "account_size": float(row['account_size']),
                    "account_revenue": float(row['account_revenue']),
                    "deal_stage": str(row['deal_stage']).strip().lower(),
                    "deal_engage_date": str(row['deal_engage_date']) if pd.notnull(row['deal_engage_date']) else None,
                    "deal_close_date": str(row['deal_close_date']) if pd.notnull(row['deal_close_date']) else None,
                    "revenue_from_deal": float(row['revenue_from_deal']),
                    "sales_cycle_duration": float(sales_cycle_duration) if sales_cycle_duration is not None else None,
                    "deal_value_ratio": float(deal_value_ratio) if deal_value_ratio is not None else None,
                    "content": content,
                    "text_vector": embedding
                }
                docs.append(doc)
            except Exception as ex:
                print(f"Row skipped due to error: {ex}")
        if docs:
            result = search_client.upload_documents(documents=docs)
            print(f"Batch {i // batch_size + 1}: Uploaded {len(docs)} records.")

if __name__ == "__main__":

    df = pd.read_csv("Sales-Opportunity-Data.csv", parse_dates=["deal_engage_date", "deal_close_date"], dayfirst=True)
    df['deal_engage_date'] = pd.to_datetime(df['deal_engage_date'], errors='coerce').dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    df['deal_close_date'] = pd.to_datetime(df['deal_close_date'], errors='coerce').dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    upload_data_in_batches(df)
    print("✅ All records uploaded to Azure AI Search index.")
