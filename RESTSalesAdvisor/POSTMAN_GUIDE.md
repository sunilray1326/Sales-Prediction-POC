# Postman Testing Guide for Sales Advisor APIs

This guide shows you how to test the Azure APIs using Postman, explained in simple terms for non-technical users.

---

## 🎯 What You'll Learn

By the end of this guide, you'll be able to:
1. ✅ Convert text to numbers (embeddings) using Azure OpenAI
2. ✅ Search for similar sales opportunities using Azure Search
3. ✅ Get AI recommendations using Azure OpenAI Chat

---

## 📋 Prerequisites

Before you start, you need:

1. **Postman** installed on your computer ([Download here](https://www.postman.com/downloads/))
2. **Azure OpenAI** resource with:
   - Your API key
   - Your endpoint URL
   - Deployed models (embedding and chat)
3. **Azure Cognitive Search** resource with:
   - Your API key
   - Your endpoint URL
   - An index with sales data

---

## 🔑 Step 1: Gather Your Credentials

### Find Your Azure OpenAI Information

1. Go to [Azure Portal](https://portal.azure.com)
2. Find your Azure OpenAI resource
3. Click "Keys and Endpoint"
4. Copy these values:
   - **Endpoint**: `https://your-name.openai.azure.com/`
   - **Key 1**: `abc123xyz456...` (long string of letters and numbers)
5. Go to "Model deployments" → "Manage Deployments"
6. Note your deployment names:
   - **Embedding model**: Usually `text-embedding-ada-002`
   - **Chat model**: Usually `gpt-4` or `gpt-35-turbo`

### Find Your Azure Search Information

1. Go to [Azure Portal](https://portal.azure.com)
2. Find your Azure Cognitive Search resource
3. Click "Keys"
4. Copy these values:
   - **URL**: `https://your-search.search.windows.net`
   - **Primary admin key**: `xyz789abc123...`
5. Click "Indexes"
6. Note your index name: Usually `sales-opportunities` or similar

---

## 🛠️ Step 2: Set Up Postman Environment

### Create Environment Variables

1. Open Postman
2. Click "Environments" (left sidebar)
3. Click "+" to create new environment
4. Name it: `Azure Sales Advisor`
5. Add these variables:

| Variable Name | Initial Value | Current Value | Example |
|---------------|---------------|---------------|---------|
| `openai_endpoint` | Your OpenAI URL | Your OpenAI URL | `https://mycompany-ai.openai.azure.com` |
| `openai_key` | Your OpenAI key | Your OpenAI key | `abc123xyz456...` |
| `search_endpoint` | Your Search URL | Your Search URL | `https://mycompany-search.search.windows.net` |
| `search_key` | Your Search key | Your Search key | `xyz789abc123...` |
| `embedding_model` | Your embedding deployment | Your embedding deployment | `text-embedding-ada-002` |
| `chat_model` | Your chat deployment | Your chat deployment | `gpt-4` |
| `index_name` | Your index name | Your index name | `sales-opportunities` |

6. Click "Save"
7. Select this environment from the dropdown (top right)

---

## 📝 Step 3: Create API Requests

### Request 1: Get Embedding (Convert Text to Numbers)

**What this does**: Converts your sales opportunity description into a list of 1536 numbers that represent its meaning.

#### Setup in Postman:

1. Click "New" → "HTTP Request"
2. Name it: `1. Get Embedding`
3. Set method to: `POST`
4. Set URL to:
   ```
   {{openai_endpoint}}/openai/deployments/{{embedding_model}}/embeddings?api-version=2024-12-01-preview
   ```

5. Click "Headers" tab and add:
   
   | Key | Value |
   |-----|-------|
   | `Content-Type` | `application/json` |
   | `api-key` | `{{openai_key}}` |

6. Click "Body" tab:
   - Select "raw"
   - Select "JSON" from dropdown
   - Paste this:
   ```json
   {
     "input": "We're pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX-2000 product. The sales rep is John Smith."
   }
   ```

7. Click "Save"

#### Test It:

1. Click "Send"
2. You should see a response like:
   ```json
   {
     "data": [
       {
         "embedding": [0.0023, -0.0091, 0.0045, ... 1536 numbers]
       }
     ]
   }
   ```
3. ✅ Success! You've converted text to a vector!

#### What to Do with the Result:

- Copy the entire `embedding` array (all 1536 numbers)
- You'll use this in the next request
- **Tip**: In Postman, you can save this to a variable:
  - Go to "Tests" tab
  - Add this code:
    ```javascript
    var response = pm.response.json();
    pm.environment.set("embedding_vector", JSON.stringify(response.data[0].embedding));
    ```
  - Now the vector is saved as `{{embedding_vector}}`

---

### Request 2: Search for Similar Opportunities

**What this does**: Finds the 10 most similar past sales opportunities from your database.

#### Setup in Postman:

1. Click "New" → "HTTP Request"
2. Name it: `2. Search Similar Won Deals`
3. Set method to: `POST`
4. Set URL to:
   ```
   {{search_endpoint}}/indexes/{{index_name}}/docs/search?api-version=2023-11-01
   ```

5. Click "Headers" tab and add:
   
   | Key | Value |
   |-----|-------|
   | `Content-Type` | `application/json` |
   | `api-key` | `{{search_key}}` |

6. Click "Body" tab:
   - Select "raw"
   - Select "JSON" from dropdown
   - Paste this:
   ```json
   {
     "search": null,
     "vectorQueries": [
       {
         "kind": "vector",
         "fields": "text_vector",
         "vector": {{embedding_vector}},
         "k": 10,
         "exhaustive": false
       }
     ],
     "filter": "deal_stage eq 'won'",
     "select": "opportunity_id,content,deal_stage,product,account_sector,sales_rep,account_region,sales_price,revenue_from_deal,sales_cycle_duration,deal_value_ratio,Notes",
     "top": 10
   }
   ```

7. Click "Save"

#### Test It:

1. Make sure you ran Request 1 first (to get the embedding)
2. Click "Send"
3. You should see a response like:
   ```json
   {
     "value": [
       {
         "@search.score": 0.95,
         "opportunity_id": "OPP-12345",
         "product": "GTX-2000",
         "account_sector": "Healthcare",
         "deal_stage": "won",
         ...
       },
       ...
     ]
   }
   ```
4. ✅ Success! You found similar opportunities!

#### Understanding the Response:

- `value` = List of similar opportunities
- `@search.score` = How similar (0.0 to 1.0, higher is more similar)
- Each item has all the fields you requested in `select`
- Results are sorted by similarity (most similar first)

---

### Request 3: Get AI Recommendation

**What this does**: Asks the AI to analyze your opportunity and give you advice.

#### Setup in Postman:

1. Click "New" → "HTTP Request"
2. Name it: `3. Get AI Recommendation`
3. Set method to: `POST`
4. Set URL to:
   ```
   {{openai_endpoint}}/openai/deployments/{{chat_model}}/chat/completions?api-version=2024-12-01-preview
   ```

5. Click "Headers" tab and add:
   
   | Key | Value |
   |-----|-------|
   | `Content-Type` | `application/json` |
   | `api-key` | `{{openai_key}}` |

6. Click "Body" tab:
   - Select "raw"
   - Select "JSON" from dropdown
   - Paste this:
   ```json
   {
     "messages": [
       {
         "role": "system",
         "content": "You are a sales advisor AI that helps analyze sales opportunities and provides recommendations."
       },
       {
         "role": "user",
         "content": "Analyze this opportunity: We're pursuing a $50,000 deal with a healthcare company in the Northeast for our GTX-2000 product. What are the key success factors?"
       }
     ],
     "temperature": 0.7,
     "max_tokens": 1000
   }
   ```

7. Click "Save"

#### Test It:

1. Click "Send"
2. You should see a response like:
   ```json
   {
     "choices": [
       {
         "message": {
           "role": "assistant",
           "content": "Based on the opportunity details, here are the key success factors:\n\n1. Healthcare sector expertise...\n2. Regional knowledge of Northeast market...\n..."
         }
       }
     ]
   }
   ```
3. ✅ Success! The AI gave you a recommendation!

#### Understanding the Response:

- `choices[0].message.content` = The AI's response text
- This is the recommendation you're looking for
- Copy this text to use in your sales strategy

---

## 🎓 Understanding the Parameters

### Embedding API Parameters

| Parameter | What to Put | Why |
|-----------|-------------|-----|
| `input` | Your sales opportunity text | The text you want to convert to numbers |

**That's it!** Just one parameter.

### Chat API Parameters

| Parameter | What to Put | Why | Example |
|-----------|-------------|-----|---------|
| `messages` | List of conversation messages | Tells the AI what to do | See examples below |
| `temperature` | Number 0.0 to 2.0 | Controls creativity | `0.0` = focused, `1.0` = creative |
| `max_tokens` | Number (e.g., 1000) | Maximum response length | `1000` = ~750 words |
| `seed` | Any number (e.g., 12345) | Makes responses consistent | `12345` |

**Message Roles**:
- `system` = Instructions for the AI (how to behave)
- `user` = Your question or request
- `assistant` = AI's previous responses (for multi-turn conversations)

**Example Messages**:

Simple question:
```json
{
  "messages": [
    {
      "role": "user",
      "content": "What is the capital of France?"
    }
  ]
}
```

With instructions:
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful geography teacher."
    },
    {
      "role": "user",
      "content": "What is the capital of France?"
    }
  ]
}
```

Multi-turn conversation:
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "What is 2+2?"
    },
    {
      "role": "assistant",
      "content": "2+2 equals 4."
    },
    {
      "role": "user",
      "content": "What about 3+3?"
    }
  ]
}
```

### Search API Parameters

| Parameter | What to Put | Why | Example |
|-----------|-------------|-----|---------|
| `search` | Text or `null` | Keyword search (use `null` for vector-only) | `null` or `"healthcare"` |
| `vectorQueries` | Vector search config | Find similar items using embeddings | See below |
| `filter` | Filter expression | Limit results (like SQL WHERE) | `"deal_stage eq 'won'"` |
| `select` | Comma-separated field names | Which fields to return | `"opportunity_id,product"` |
| `top` | Number | How many results | `10` |

**Vector Query Sub-Parameters**:

| Sub-Parameter | What to Put | Why |
|---------------|-------------|-----|
| `kind` | Always `"vector"` | Type of search |
| `fields` | Field name with vectors | Where vectors are stored (usually `"text_vector"`) |
| `vector` | The 1536 numbers from embedding API | What to search for |
| `k` | Number (e.g., 10) | How many similar items to find |
| `exhaustive` | `true` or `false` | `false` = faster, `true` = more accurate |

**Filter Examples**:

| What You Want | Filter Expression |
|---------------|-------------------|
| Only won deals | `"deal_stage eq 'won'"` |
| Only lost deals | `"deal_stage eq 'lost'"` |
| Deals over $10,000 | `"sales_price gt 10000"` |
| Healthcare sector | `"account_sector eq 'Healthcare'"` |
| Won healthcare deals | `"deal_stage eq 'won' and account_sector eq 'Healthcare'"` |
| Deals over $10k or under $1k | `"sales_price gt 10000 or sales_price lt 1000'"` |

---

## 🔍 Parsing Responses - Simple Guide

### Embedding Response

**What you get**:
```json
{
  "data": [
    {
      "embedding": [0.0023, -0.0091, ...]
    }
  ]
}
```

**What you need**: `data[0].embedding`

**In Postman**: 
- Look at the response
- Find `data` → click to expand
- Find `[0]` → click to expand
- Find `embedding` → this is your vector!

---

### Chat Response

**What you get**:
```json
{
  "choices": [
    {
      "message": {
        "content": "Here is my answer..."
      }
    }
  ]
}
```

**What you need**: `choices[0].message.content`

**In Postman**:
- Look at the response
- Find `choices` → click to expand
- Find `[0]` → click to expand
- Find `message` → click to expand
- Find `content` → this is the AI's answer!

---

### Search Response

**What you get**:
```json
{
  "value": [
    {
      "@search.score": 0.95,
      "opportunity_id": "OPP-123",
      "product": "GTX-2000",
      ...
    },
    ...
  ]
}
```

**What you need**: `value` (the whole list)

**In Postman**:
- Look at the response
- Find `value` → click to expand
- Each item `[0]`, `[1]`, etc. is one opportunity
- `@search.score` shows how similar it is

---

## ❓ Troubleshooting

### Error: "401 Unauthorized"

**Problem**: Your API key is wrong or missing

**Solution**:
1. Check the `api-key` header is set
2. Make sure you copied the full key (no spaces)
3. Make sure you're using the right key:
   - OpenAI key for OpenAI APIs
   - Search key for Search API

### Error: "404 Not Found"

**Problem**: The URL is wrong

**Solution**:
1. Check your endpoint URL is correct
2. Check your deployment names are correct
3. Check your index name is correct
4. Make sure there are no typos

### Error: "400 Bad Request"

**Problem**: The request body has an error

**Solution**:
1. Make sure the JSON is valid (no missing commas, brackets)
2. Check all required parameters are included
3. Check parameter values are the right type (text vs number)

### No Results from Search

**Problem**: Search returns empty list

**Solution**:
1. Check your index has data
2. Try removing the filter
3. Try a different vector
4. Check the field name in `fields` is correct

---

## 💡 Pro Tips

### Tip 1: Save Responses as Variables

In the "Tests" tab of any request, add:

```javascript
// Save embedding
var response = pm.response.json();
pm.environment.set("embedding_vector", JSON.stringify(response.data[0].embedding));
```

```javascript
// Save AI response
var response = pm.response.json();
pm.environment.set("ai_response", response.choices[0].message.content);
```

### Tip 2: Chain Requests

1. Run embedding request → saves vector
2. Run search request → uses saved vector
3. Run chat request → uses search results

### Tip 3: Create a Collection

1. Create collection: "Sales Advisor"
2. Add all 3 requests
3. Click "Run" to run all at once
4. Great for testing!

### Tip 4: Use Pre-request Scripts

Add this to "Pre-request Script" tab to log what you're sending:

```javascript
console.log("Sending request to:", pm.request.url);
console.log("Headers:", pm.request.headers);
console.log("Body:", pm.request.body);
```

---

## 🎉 You're Done!

You now know how to:
- ✅ Convert text to embeddings
- ✅ Search for similar opportunities
- ✅ Get AI recommendations
- ✅ Parse responses
- ✅ Troubleshoot errors

**Next Steps**:
- Try with your own sales opportunities
- Experiment with different filters
- Adjust temperature for different AI responses
- Build a complete workflow in Postman

Happy testing! 🚀

