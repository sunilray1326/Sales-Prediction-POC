# REST API Version Guide

## Overview
Created a REST API version of `SalesAdvisorEngine` that uses direct HTTP calls instead of Azure SDK libraries.

## Files Created

### 1. `sales_advisor_engine_rest.py` (443 lines)
**Purpose**: Business logic engine using REST API calls only

**Key Differences from SDK Version**:
- ✅ Uses `requests` library instead of `openai` and `azure-search-documents`
- ✅ Direct HTTP calls to Azure OpenAI and Azure Cognitive Search
- ✅ No dependency on Azure SDK libraries
- ✅ Same functionality and API interface
- ✅ Same return structure and error handling

### 2. `requirements_rest.txt`
**Purpose**: Minimal dependencies for REST API version

**Dependencies**:
```
streamlit==1.51.0
python-dotenv==1.1.1
requests==2.31.0
```

**Removed Dependencies**:
- ❌ `openai==2.3.0` (replaced with REST API calls)
- ❌ `azure-search-documents==11.6.0` (replaced with REST API calls)
- ❌ `azure-core==1.35.1` (no longer needed)

## Comparison: SDK vs REST API

### SDK Version (`sales_advisor_engine.py`)

**Imports**:
```python
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
```

**Initialization**:
```python
self.openai_client = AzureOpenAI(
    api_key=self.config['OPEN_AI_KEY'],
    azure_endpoint=self.config['OPEN_AI_ENDPOINT'],
    api_version="2024-12-01-preview"
)

self.search_client = SearchClient(
    endpoint=self.config['SEARCH_ENDPOINT'],
    index_name=self.config['INDEX_NAME'],
    credential=AzureKeyCredential(self.config['SEARCH_KEY'])
)
```

**Embeddings Call**:
```python
response = self.openai_client.embeddings.create(
    model=self.config['EMBEDDING_MODEL'],
    input=text
)
return response.data[0].embedding
```

**Chat Completion Call**:
```python
response = self.openai_client.chat.completions.create(
    model=self.config['CHAT_MODEL'],
    messages=messages,
    temperature=temperature,
    max_tokens=4000,
    seed=seed
)
return response.choices[0].message.content
```

**Vector Search Call**:
```python
results = self.search_client.search(
    search_text=None,
    vector_queries=[{
        "kind": "vector",
        "fields": "text_vector",
        "vector": embedding,
        "k": top_k,
        "exhaustive": False
    }],
    filter=filter_expr,
    select=[...],
    top=top_k
)
return [doc for doc in results]
```

---

### REST API Version (`sales_advisor_engine_rest.py`)

**Imports**:
```python
import requests
# No Azure SDK imports needed
```

**Initialization**:
```python
# API versions
self.openai_api_version = "2024-12-01-preview"
self.search_api_version = "2023-11-01"

# Build base URLs
self.openai_base_url = self.config['OPEN_AI_ENDPOINT'].rstrip('/')
self.search_base_url = self.config['SEARCH_ENDPOINT'].rstrip('/')
```

**Embeddings Call (REST API)**:
```python
url = f"{self.openai_base_url}/openai/deployments/{self.config['EMBEDDING_MODEL']}/embeddings?api-version={self.openai_api_version}"

headers = {
    "Content-Type": "application/json",
    "api-key": self.config['OPEN_AI_KEY']
}

payload = {
    "input": text
}

response = requests.post(url, headers=headers, json=payload)
response.raise_for_status()

result = response.json()
return result['data'][0]['embedding']
```

**Chat Completion Call (REST API)**:
```python
url = f"{self.openai_base_url}/openai/deployments/{self.config['CHAT_MODEL']}/chat/completions?api-version={self.openai_api_version}"

headers = {
    "Content-Type": "application/json",
    "api-key": self.config['OPEN_AI_KEY']
}

payload = {
    "messages": messages,
    "temperature": temperature,
    "max_tokens": 4000
}

if seed is not None:
    payload["seed"] = seed

response = requests.post(url, headers=headers, json=payload)
response.raise_for_status()

result = response.json()
return result['choices'][0]['message']['content']
```

**Vector Search Call (REST API)**:
```python
url = f"{self.search_base_url}/indexes/{self.config['INDEX_NAME']}/docs/search?api-version={self.search_api_version}"

headers = {
    "Content-Type": "application/json",
    "api-key": self.config['SEARCH_KEY']
}

payload = {
    "search": None,
    "vectorQueries": [{
        "kind": "vector",
        "fields": "text_vector",
        "vector": embedding,
        "k": top_k,
        "exhaustive": False
    }],
    "filter": f"deal_stage eq '{stage_filter}'",
    "select": "opportunity_id,content,deal_stage,...",
    "top": top_k
}

response = requests.post(url, headers=headers, json=payload)
response.raise_for_status()

result = response.json()
return result.get('value', [])
```

## How to Use REST API Version

### Option 1: Modify app.py to use REST version

**Change this line in `app.py`**:
```python
# FROM:
from sales_advisor_engine import SalesAdvisorEngine

# TO:
from sales_advisor_engine_rest import SalesAdvisorEngine
```

### Option 2: Rename files

```bash
# Backup SDK version
mv sales_advisor_engine.py sales_advisor_engine_sdk.py

# Use REST version as default
mv sales_advisor_engine_rest.py sales_advisor_engine.py
```

### Option 3: Install minimal dependencies

```bash
# Uninstall Azure SDK packages
pip uninstall openai azure-search-documents azure-core

# Install only required packages
pip install -r requirements_rest.txt
```

## Benefits of REST API Version

### ✅ Fewer Dependencies
- Only 3 packages instead of 5
- Smaller installation footprint
- Faster deployment

### ✅ More Control
- Direct HTTP calls give you full control
- Easier to debug network issues
- Can add custom retry logic, timeouts, etc.

### ✅ Better Understanding
- See exactly what's being sent to Azure
- Easier to troubleshoot API issues
- Can log requests/responses for debugging

### ✅ Version Flexibility
- Not tied to SDK version updates
- Can use any API version by changing the version string
- More control over API features

### ✅ Lighter Weight
- No heavy SDK libraries
- Smaller Docker images
- Faster cold starts in serverless environments

## Drawbacks of REST API Version

### ❌ More Verbose Code
- More lines of code for each API call
- Manual URL construction
- Manual error handling

### ❌ No Type Hints
- SDK provides type hints and IntelliSense
- REST version uses plain dictionaries

### ❌ Manual Updates
- Need to update API versions manually
- SDK handles some API changes automatically

### ❌ Less Validation
- SDK validates parameters before sending
- REST version relies on server-side validation

## API Endpoints Used - Detailed Guide for Postman

This section explains each REST API call in simple terms, showing you exactly what to send and what you'll get back.

---

### 1️⃣ Azure OpenAI - Embeddings API

**What it does**: Converts your text into a list of numbers (called a "vector") that represents the meaning of the text. This is used to find similar opportunities.

#### **URL to Call**
```
POST https://your-resource-name.openai.azure.com/openai/deployments/text-embedding-ada-002/embeddings?api-version=2024-12-01-preview
```

#### **URL Parts Explained**
- `your-resource-name` = Your Azure OpenAI resource name (e.g., "mycompany-openai")
- `text-embedding-ada-002` = The name of your embedding model deployment
- `2024-12-01-preview` = The API version (use this exact value)

#### **Headers to Send**
You need to send 2 headers with your request:

| Header Name | Value | What it means |
|-------------|-------|---------------|
| `Content-Type` | `application/json` | Tells Azure you're sending JSON data |
| `api-key` | Your Azure OpenAI key | Your secret password to access the service |

**Example in Postman**:
- Click "Headers" tab
- Add header: `Content-Type` = `application/json`
- Add header: `api-key` = `abc123xyz456...` (your actual key from Azure portal)

#### **Body Parameters**
Send this in the "Body" tab (select "raw" and "JSON"):

| Parameter | Type | Required? | What it means | Example |
|-----------|------|-----------|---------------|---------|
| `input` | Text | ✅ Yes | The text you want to convert to a vector | `"We're pursuing a healthcare deal"` |

**Example Body**:
```json
{
  "input": "We're pursuing a $50,000 deal with a healthcare company"
}
```

#### **Response You'll Get Back**
Azure will send you back a JSON response like this:

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [0.0023, -0.0091, 0.0045, ... 1536 numbers total]
    }
  ],
  "model": "text-embedding-ada-002",
  "usage": {
    "prompt_tokens": 12,
    "total_tokens": 12
  }
}
```

#### **How to Parse the Response**
1. Look for `data` → this is a list
2. Get the first item: `data[0]`
3. Get the `embedding` field: `data[0].embedding`
4. This gives you a list of 1536 numbers representing your text

**In simple terms**: You'll get back an array of 1536 decimal numbers. Save this array - you'll need it for the search API.

---

### 2️⃣ Azure OpenAI - Chat Completions API

**What it does**: Sends a conversation to the AI and gets back a smart response. This is used to extract information from text or generate recommendations.

#### **URL to Call**
```
POST https://your-resource-name.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2024-12-01-preview
```

#### **URL Parts Explained**
- `your-resource-name` = Your Azure OpenAI resource name
- `gpt-4` = The name of your chat model deployment (could be "gpt-4", "gpt-35-turbo", etc.)
- `2024-12-01-preview` = The API version

#### **Headers to Send**

| Header Name | Value | What it means |
|-------------|-------|---------------|
| `Content-Type` | `application/json` | Tells Azure you're sending JSON data |
| `api-key` | Your Azure OpenAI key | Your secret password |

#### **Body Parameters**

| Parameter | Type | Required? | What it means | Example |
|-----------|------|-----------|---------------|---------|
| `messages` | List of message objects | ✅ Yes | The conversation history | See below |
| `temperature` | Number (0.0 to 2.0) | ❌ No | How creative the AI should be. 0 = very focused, 2 = very creative | `0.1` for extraction, `0.8` for creative writing |
| `max_tokens` | Number | ❌ No | Maximum length of the response (in tokens, roughly 4 characters = 1 token) | `4000` |
| `seed` | Number | ❌ No | Makes responses more consistent/repeatable | `12345` |

**About Messages**: Each message has 2 parts:
- `role` = Who is speaking: `"system"` (instructions), `"user"` (you), or `"assistant"` (AI)
- `content` = What they're saying (the actual text)

**Example Body**:
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant that extracts information from sales opportunities."
    },
    {
      "role": "user",
      "content": "Extract the product, sector, and region from this: We're pursuing a $50,000 deal with a healthcare company in the Northeast for our GTX-2000 product."
    }
  ],
  "temperature": 0.0,
  "max_tokens": 4000,
  "seed": 12345
}
```

#### **Response You'll Get Back**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "{\"product\": \"GTX-2000\", \"sector\": \"Healthcare\", \"region\": \"Northeast\", \"sales_price\": 50000}"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 28,
    "total_tokens": 73
  }
}
```

#### **How to Parse the Response**
1. Look for `choices` → this is a list
2. Get the first item: `choices[0]`
3. Get the message: `choices[0].message`
4. Get the content: `choices[0].message.content`
5. This is the AI's response (the text you need)

**In simple terms**: The AI's answer is in `choices[0].message.content`. That's the text response you're looking for.

---

### 3️⃣ Azure Cognitive Search - Vector Search API

**What it does**: Searches through your database of past sales opportunities to find the ones most similar to your current opportunity.

#### **URL to Call**
```
POST https://your-search-service.search.windows.net/indexes/your-index-name/docs/search?api-version=2023-11-01
```

#### **URL Parts Explained**
- `your-search-service` = Your Azure Search service name (e.g., "mycompany-search")
- `your-index-name` = The name of your search index (e.g., "sales-opportunities")
- `2023-11-01` = The API version

#### **Headers to Send**

| Header Name | Value | What it means |
|-------------|-------|---------------|
| `Content-Type` | `application/json` | Tells Azure you're sending JSON data |
| `api-key` | Your Azure Search admin key | Your secret password for the search service |

#### **Body Parameters**

| Parameter | Type | Required? | What it means | Example |
|-----------|------|-----------|---------------|---------|
| `search` | Text or null | ❌ No | Text to search for (use `null` for vector-only search) | `null` |
| `vectorQueries` | List of vector query objects | ✅ Yes (for vector search) | Tells Azure to search using vectors | See below |
| `filter` | Text | ❌ No | Filter results (like SQL WHERE clause) | `"deal_stage eq 'won'"` |
| `select` | Text (comma-separated) | ❌ No | Which fields to return | `"opportunity_id,product,sector"` |
| `top` | Number | ❌ No | How many results to return | `10` |

**About vectorQueries**: Each vector query has these parts:

| Sub-Parameter | Type | Required? | What it means | Example |
|---------------|------|-----------|---------------|---------|
| `kind` | Text | ✅ Yes | Type of query (always use `"vector"`) | `"vector"` |
| `fields` | Text | ✅ Yes | Which field in your index contains vectors | `"text_vector"` |
| `vector` | List of numbers | ✅ Yes | The embedding vector from step 1 (1536 numbers) | `[0.0023, -0.0091, ...]` |
| `k` | Number | ✅ Yes | How many similar items to find | `10` |
| `exhaustive` | true/false | ❌ No | Search all items (slower) or use approximate search (faster) | `false` |

**About filter**: Uses OData syntax (like SQL):
- `eq` = equals
- `ne` = not equals
- `gt` = greater than
- `lt` = less than
- `and` / `or` = combine conditions

Examples:
- `"deal_stage eq 'won'"` = Only won deals
- `"deal_stage eq 'lost'"` = Only lost deals
- `"sales_price gt 10000"` = Deals over $10,000
- `"product eq 'GTX-2000' and deal_stage eq 'won'"` = Won deals for GTX-2000

**Example Body**:
```json
{
  "search": null,
  "vectorQueries": [
    {
      "kind": "vector",
      "fields": "text_vector",
      "vector": [0.0023, -0.0091, 0.0045, ... put all 1536 numbers here],
      "k": 10,
      "exhaustive": false
    }
  ],
  "filter": "deal_stage eq 'won'",
  "select": "opportunity_id,content,deal_stage,product,account_sector,sales_rep,account_region,sales_price,revenue_from_deal,sales_cycle_duration,deal_value_ratio,Notes",
  "top": 10
}
```

#### **Response You'll Get Back**

```json
{
  "@odata.context": "https://your-search-service.search.windows.net/indexes('your-index-name')/$metadata#docs(*)",
  "value": [
    {
      "@search.score": 0.95,
      "opportunity_id": "OPP-12345",
      "content": "Healthcare deal in Northeast region...",
      "deal_stage": "won",
      "product": "GTX-2000",
      "account_sector": "Healthcare",
      "sales_rep": "John Smith",
      "account_region": "Northeast",
      "sales_price": 48000,
      "revenue_from_deal": 52000,
      "sales_cycle_duration": 45,
      "deal_value_ratio": 1.08,
      "Notes": "Customer was very interested in the advanced features"
    },
    {
      "@search.score": 0.92,
      "opportunity_id": "OPP-67890",
      "content": "Another similar deal...",
      "deal_stage": "won",
      "product": "GTX-2000",
      "account_sector": "Healthcare",
      "sales_rep": "Jane Doe",
      "account_region": "Northeast",
      "sales_price": 55000,
      "revenue_from_deal": 58000,
      "sales_cycle_duration": 60,
      "deal_value_ratio": 1.05,
      "Notes": "Long sales cycle but successful"
    }
  ]
}
```

#### **How to Parse the Response**
1. Look for `value` → this is a list of matching documents
2. Each item in the list is one matching opportunity
3. `@search.score` = How similar it is (higher = more similar, max is 1.0)
4. All the fields you requested in `select` will be included

**In simple terms**: You get back a list of similar opportunities. Each one has a score showing how similar it is. The list is sorted by score (most similar first).

---

## 📋 Complete Workflow Example

Here's how all 3 APIs work together:

### **Step 1: Get Embedding for Your Opportunity**
```
POST to Embeddings API
Send: "We're pursuing a $50,000 healthcare deal in Northeast for GTX-2000"
Get back: [0.0023, -0.0091, 0.0045, ... 1536 numbers]
```

### **Step 2: Search for Similar Won Deals**
```
POST to Vector Search API
Send: The 1536 numbers + filter "deal_stage eq 'won'"
Get back: List of 10 most similar won deals
```

### **Step 3: Search for Similar Lost Deals**
```
POST to Vector Search API
Send: The same 1536 numbers + filter "deal_stage eq 'lost'"
Get back: List of 10 most similar lost deals
```

### **Step 4: Extract Attributes**
```
POST to Chat Completions API
Send: "Extract product, sector, region from: [your opportunity text]"
Get back: {"product": "GTX-2000", "sector": "Healthcare", "region": "Northeast"}
```

### **Step 5: Generate Recommendation**
```
POST to Chat Completions API
Send: System prompt + User opportunity + Won deals + Lost deals + Statistics
Get back: AI-generated recommendation text
```

---

## 🔧 Postman Setup Guide

### **Setting Up Environment Variables in Postman**

Instead of typing the same values over and over, create variables:

1. Click "Environments" in Postman
2. Create new environment called "Azure Sales Advisor"
3. Add these variables:

| Variable Name | Value | What it's for |
|---------------|-------|---------------|
| `openai_endpoint` | `https://your-resource.openai.azure.com` | Your OpenAI base URL |
| `openai_key` | `abc123...` | Your OpenAI API key |
| `search_endpoint` | `https://your-search.search.windows.net` | Your Search base URL |
| `search_key` | `xyz789...` | Your Search API key |
| `embedding_model` | `text-embedding-ada-002` | Your embedding deployment name |
| `chat_model` | `gpt-4` | Your chat deployment name |
| `index_name` | `sales-opportunities` | Your search index name |

4. Now use them in URLs like: `{{openai_endpoint}}/openai/deployments/{{embedding_model}}/embeddings?api-version=2024-12-01-preview`

### **Creating a Postman Collection**

1. Create new collection: "Azure Sales Advisor APIs"
2. Add 3 requests:
   - "1. Get Embedding"
   - "2. Search Similar Deals"
   - "3. Chat with AI"
3. Set up each request with the examples above
4. Save and reuse!

---

## ❓ Common Questions

### **Q: Where do I find my API keys?**
- **OpenAI Key**: Azure Portal → Your OpenAI resource → "Keys and Endpoint" → Copy "Key 1"
- **Search Key**: Azure Portal → Your Search service → "Keys" → Copy "Primary admin key"

### **Q: What if I get an error "401 Unauthorized"?**
- Check your `api-key` header is correct
- Make sure you're using the right key (OpenAI key for OpenAI APIs, Search key for Search API)

### **Q: What if I get "404 Not Found"?**
- Check your deployment names are correct
- Check your index name is correct
- Check your endpoint URLs are correct

### **Q: How do I know if it's working?**
- Embeddings API: You should get back 1536 numbers
- Chat API: You should get back text in `choices[0].message.content`
- Search API: You should get back a list in `value`

### **Q: Can I test this without code?**
- Yes! Use Postman to test all APIs
- Copy the examples above
- Replace the placeholder values with your actual values
- Click "Send" and see the results

### **Q: What does "temperature" do in Chat API?**
- It controls randomness/creativity
- `0.0` = Very focused, deterministic, same answer every time
- `0.5` = Balanced
- `1.0` = More creative and varied
- `2.0` = Very creative, unpredictable
- Use low values (0.0-0.1) for data extraction
- Use higher values (0.7-1.0) for creative writing

### **Q: What is a "token" in max_tokens?**
- A token is roughly 4 characters or 0.75 words
- Example: "Hello world" = 2 tokens
- `max_tokens: 4000` means about 3000 words maximum response
- If response is cut off, increase this number

### **Q: Why do I need the embedding vector?**
- The vector represents the "meaning" of your text as numbers
- Azure Search uses these numbers to find similar opportunities
- Similar opportunities have similar vectors (mathematically close)

### **Q: Can I search without vectors (just text)?**
- Yes, but you won't get semantic similarity
- Set `"search": "your search text"` instead of `null`
- Remove or empty the `vectorQueries` parameter
- This does keyword matching, not meaning matching

### **Q: How do I combine text search and vector search?**
```json
{
  "search": "healthcare",
  "vectorQueries": [
    {
      "kind": "vector",
      "fields": "text_vector",
      "vector": [0.0023, ...],
      "k": 10
    }
  ],
  "filter": "deal_stage eq 'won'",
  "top": 10
}
```
This finds opportunities that:
- Contain the word "healthcare" (text search)
- Are semantically similar to your vector (vector search)
- Have deal_stage = 'won' (filter)

---

## Environment Variables

Both versions use the same `.env` file:

```env
OPEN_AI_KEY=your_azure_openai_key
OPEN_AI_ENDPOINT=https://your-resource.openai.azure.com/
SEARCH_ENDPOINT=https://your-search-service.search.windows.net
SEARCH_KEY=your_search_admin_key
INDEX_NAME=your_index_name
EMBEDDING_MODEL=text-embedding-ada-002
CHAT_MODEL=gpt-4
```

## Testing

Both versions have identical interfaces and return the same results:

```python
# Works with both SDK and REST versions
engine = SalesAdvisorEngine()
result = engine.analyze_opportunity("We're pursuing a $50,000 deal...")

# Same return structure
{
    "success": True,
    "error_message": None,
    "extracted_attributes": {...},
    "relevant_stats": {...},
    "recommendation": "...",
    "won_matches": [...],
    "lost_matches": [...]
}
```

## Recommendation

**Use SDK Version (`sales_advisor_engine.py`) if**:
- You want easier development with type hints
- You prefer less verbose code
- You want automatic SDK updates and improvements

**Use REST Version (`sales_advisor_engine_rest.py`) if**:
- You want minimal dependencies
- You need full control over HTTP requests
- You're deploying to serverless/containerized environments
- You want to understand the underlying API calls
- You need to customize retry logic or timeouts

## Summary

Both versions provide identical functionality:
- ✅ Same API interface (`analyze_opportunity()`)
- ✅ Same return structure
- ✅ Same error handling
- ✅ Same business logic
- ✅ Same configuration

The only difference is **how** they communicate with Azure services:
- **SDK Version**: Uses Azure SDK libraries (easier, more features)
- **REST Version**: Uses direct HTTP calls (lighter, more control)

Choose based on your deployment requirements and preferences!

