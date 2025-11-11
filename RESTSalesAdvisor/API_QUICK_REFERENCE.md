# Azure APIs Quick Reference Card

One-page reference for all Azure API calls used in Sales Advisor.

---

## 🔑 1. Embeddings API - Convert Text to Vector

### URL
```
POST https://{your-resource}.openai.azure.com/openai/deployments/{model}/embeddings?api-version=2024-12-01-preview
```

### Headers
```
Content-Type: application/json
api-key: {your-openai-key}
```

### Request Body
```json
{
  "input": "Your text here"
}
```

### Response
```json
{
  "data": [
    {
      "embedding": [0.0023, -0.0091, ... 1536 numbers]
    }
  ]
}
```

### What You Need
`data[0].embedding` = The vector (1536 numbers)

---

## 💬 2. Chat Completions API - Talk to AI

### URL
```
POST https://{your-resource}.openai.azure.com/openai/deployments/{model}/chat/completions?api-version=2024-12-01-preview
```

### Headers
```
Content-Type: application/json
api-key: {your-openai-key}
```

### Request Body
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant"
    },
    {
      "role": "user",
      "content": "Your question here"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "seed": 12345
}
```

### Response
```json
{
  "choices": [
    {
      "message": {
        "content": "AI's answer here"
      }
    }
  ]
}
```

### What You Need
`choices[0].message.content` = The AI's answer

---

## 🔍 3. Vector Search API - Find Similar Items

### URL
```
POST https://{your-search}.search.windows.net/indexes/{index-name}/docs/search?api-version=2023-11-01
```

### Headers
```
Content-Type: application/json
api-key: {your-search-key}
```

### Request Body
```json
{
  "search": null,
  "vectorQueries": [
    {
      "kind": "vector",
      "fields": "text_vector",
      "vector": [0.0023, -0.0091, ... paste 1536 numbers here],
      "k": 10,
      "exhaustive": false
    }
  ],
  "filter": "deal_stage eq 'won'",
  "select": "opportunity_id,product,account_sector,sales_rep",
  "top": 10
}
```

### Response
```json
{
  "value": [
    {
      "@search.score": 0.95,
      "opportunity_id": "OPP-123",
      "product": "GTX-2000",
      ...
    }
  ]
}
```

### What You Need
`value` = List of similar items (sorted by score)

---

## 📊 Parameter Reference

### Chat API - Temperature Values

| Value | Behavior | Use For |
|-------|----------|---------|
| 0.0 | Very focused, deterministic | Data extraction, JSON output |
| 0.1 | Mostly focused | Recommendations with consistency |
| 0.5 | Balanced | General questions |
| 0.7 | Creative | Writing, brainstorming |
| 1.0+ | Very creative | Story writing, poetry |

### Chat API - Message Roles

| Role | Who | Purpose |
|------|-----|---------|
| `system` | Instructions | Tell AI how to behave |
| `user` | You | Your questions/requests |
| `assistant` | AI | AI's previous responses |

### Search API - Filter Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `eq` | Equals | `"product eq 'GTX-2000'"` |
| `ne` | Not equals | `"deal_stage ne 'lost'"` |
| `gt` | Greater than | `"sales_price gt 10000"` |
| `ge` | Greater or equal | `"sales_price ge 10000"` |
| `lt` | Less than | `"sales_price lt 50000"` |
| `le` | Less or equal | `"sales_price le 50000"` |
| `and` | Both conditions | `"product eq 'GTX-2000' and deal_stage eq 'won'"` |
| `or` | Either condition | `"sales_price gt 100000 or deal_stage eq 'won'"` |

### Search API - Common Filters

| What You Want | Filter Expression |
|---------------|-------------------|
| Won deals only | `"deal_stage eq 'won'"` |
| Lost deals only | `"deal_stage eq 'lost'"` |
| Healthcare sector | `"account_sector eq 'Healthcare'"` |
| Northeast region | `"account_region eq 'Northeast'"` |
| Deals over $10k | `"sales_price gt 10000"` |
| Specific product | `"product eq 'GTX-2000'"` |
| Won healthcare deals | `"deal_stage eq 'won' and account_sector eq 'Healthcare'"` |
| High-value deals | `"sales_price gt 50000 and deal_stage eq 'won'"` |

---

## 🔄 Complete Workflow

```
1. Get Embedding
   Input: "We're pursuing a healthcare deal..."
   Output: [0.0023, -0.0091, ... 1536 numbers]
   
2. Search Won Deals
   Input: Vector + filter "deal_stage eq 'won'"
   Output: 10 similar won opportunities
   
3. Search Lost Deals
   Input: Same vector + filter "deal_stage eq 'lost'"
   Output: 10 similar lost opportunities
   
4. Extract Attributes
   Input: "Extract product, sector from: ..."
   Output: {"product": "GTX-2000", "sector": "Healthcare"}
   
5. Generate Recommendation
   Input: Opportunity + Won deals + Lost deals + Stats
   Output: AI recommendation text
```

---

## 🎯 Response Parsing Cheat Sheet

### Embedding Response
```
Get: response.data[0].embedding
Type: Array of 1536 numbers
Use: For vector search
```

### Chat Response
```
Get: response.choices[0].message.content
Type: String (text)
Use: AI's answer
```

### Search Response
```
Get: response.value
Type: Array of objects
Each has: @search.score + your selected fields
Sorted: By score (highest first)
```

---

## ⚠️ Common Errors

| Error Code | Meaning | Fix |
|------------|---------|-----|
| 401 | Wrong API key | Check api-key header |
| 404 | URL not found | Check endpoint, deployment, index names |
| 400 | Bad request | Check JSON syntax, required parameters |
| 429 | Too many requests | Wait and retry |
| 500 | Server error | Retry after a moment |

---

## 📝 Postman Environment Variables

```
openai_endpoint = https://your-resource.openai.azure.com
openai_key = your-key-here
search_endpoint = https://your-search.search.windows.net
search_key = your-key-here
embedding_model = text-embedding-ada-002
chat_model = gpt-4
index_name = sales-opportunities
```

Use in URLs: `{{openai_endpoint}}/openai/deployments/{{embedding_model}}/...`

---

## 🚀 Quick Start Checklist

- [ ] Get Azure OpenAI endpoint and key
- [ ] Get Azure Search endpoint and key
- [ ] Note deployment names (embedding, chat)
- [ ] Note index name
- [ ] Set up Postman environment
- [ ] Test embedding API
- [ ] Test chat API
- [ ] Test search API
- [ ] Chain them together!

---

## 💡 Pro Tips

1. **Save vectors**: Use Postman Tests tab to save embedding to variable
2. **Use collections**: Group all 3 APIs in one collection
3. **Environment per project**: Create separate environments for dev/prod
4. **Log requests**: Use Pre-request Scripts to log what you're sending
5. **Test incrementally**: Test each API separately before chaining

---

## 📚 Full Documentation

- **Detailed Guide**: See `REST_API_VERSION_GUIDE.md`
- **Postman Tutorial**: See `POSTMAN_GUIDE.md`
- **Quick Start**: See `QUICK_START_REST.md`

---

**Print this page and keep it handy while testing!** 📄

