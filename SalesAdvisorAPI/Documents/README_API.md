# 🚀 Sales Advisor REST API

AI-powered sales opportunity analysis and recommendation service built with FastAPI.

---

## 📋 Overview

The Sales Advisor API provides intelligent sales recommendations by analyzing your opportunity against historical data using Azure OpenAI and Azure Cognitive Search.

**Key Features:**
- ✅ **AI-Powered Analysis** - LLM-based recommendations using GPT-4
- ✅ **Historical Insights** - Compare against similar won/lost deals
- ✅ **Win Probability Improvements** - Get top 3 actionable recommendations
- ✅ **Secure Authentication** - API key-based access control
- ✅ **Rate Limiting** - 10 requests per hour per API key
- ✅ **Auto-Generated Docs** - Interactive Swagger UI at `/docs`
- ✅ **Production Ready** - Designed for Azure App Service deployment

---

## 🎯 Quick Start

### 1. Local Development

```bash
# Navigate to SalesAdvisorService directory
cd SalesAdvisorService

# Install dependencies
pip install -r requirements_api.txt

# Set up environment variables (create .env file)
OPEN_AI_KEY=your-azure-openai-key
OPEN_AI_ENDPOINT=https://your-resource.openai.azure.com/
SEARCH_ENDPOINT=https://your-search-service.search.windows.net
SEARCH_KEY=your-search-admin-key
INDEX_NAME=your-index-name
EMBEDDING_MODEL=text-embedding-ada-002
CHAT_MODEL=gpt-4o
API_KEYS=test-key-1,test-key-2

# Run the API
uvicorn api:app --reload --port 8000

# API will be available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### 2. Test the API

```bash
# Health check (no auth required)
curl http://localhost:8000/health

# Analyze opportunity (requires API key)
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-1" \
  -d '{
    "opportunity_description": "We are pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX Plus Pro product. The sales rep is John Smith."
  }'
```

---

## 📚 API Endpoints

### `GET /health`
Health check endpoint (no authentication required)

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "azure_services": {
    "openai": "connected",
    "cognitive_search": "connected"
  }
}
```

---

### `POST /api/v1/analyze`
Analyze a sales opportunity and get recommendations

**Authentication:** Required (X-API-Key header)

**Rate Limit:** 10 requests per hour per API key

**Request:**
```json
{
  "opportunity_description": "We are pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX Plus Pro product. The sales rep is John Smith."
}
```

**Response:**
```json
{
  "success": true,
  "recommendation": "Based on analysis of similar deals...",
  "extracted_attributes": {
    "product": "GTX Plus Pro",
    "sector": "Healthcare",
    "region": "Northeast",
    "current_rep": "John Smith",
    "sales_price": 50000.0,
    "expected_revenue": null
  },
  "win_probability_improvements": [
    {
      "rank": 1,
      "recommendation": "Switch to GTX Plus Pro",
      "uplift_percent": 15.5,
      "confidence": "High",
      "source_type": "Quantitative simulation",
      "explanation": "This recommendation is based on quantitative simulation showing 15.50% improvement in win rate."
    }
  ],
  "similar_won_deals": [...],
  "similar_lost_deals": [...],
  "statistics": {...}
}
```

---

## 🔐 Authentication

All API endpoints (except `/health`) require authentication using an API key.

**Header:**
```
X-API-Key: your-secret-api-key
```

**Example:**
```bash
curl -H "X-API-Key: your-secret-api-key" https://api.example.com/api/v1/analyze
```

**Managing API Keys:**
- API keys are configured via the `API_KEYS` environment variable
- Format: Comma-separated list (e.g., `API_KEYS=key1,key2,key3`)
- Keys can be rotated without downtime by adding new keys before removing old ones

---

## ⚡ Rate Limiting

**Limit:** 10 requests per hour per API key

**Response when limit exceeded (429):**
```json
{
  "detail": "Rate limit exceeded. You can analyze 10 opportunities per hour. Please wait 3540 seconds before trying again."
}
```

**Headers:**
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets
- `Retry-After`: Seconds to wait before retrying

---

## 📖 Documentation

### Interactive API Documentation

**Swagger UI:** `http://localhost:8000/docs`
- Try out endpoints directly in browser
- See request/response schemas
- Test authentication

**ReDoc:** `http://localhost:8000/redoc`
- Clean, readable documentation
- Better for sharing with non-technical users

---

## 🚀 Deployment

### Azure App Service (Recommended)

See [AZURE_DEPLOYMENT_GUIDE.md](AZURE_DEPLOYMENT_GUIDE.md) for complete deployment instructions.

**Quick Deploy:**
```bash
# Create resources
az group create --name rg-sales-advisor --location eastus
az appservice plan create --name plan-sales-advisor --resource-group rg-sales-advisor --sku B1 --is-linux
az webapp create --resource-group rg-sales-advisor --plan plan-sales-advisor --name sales-advisor-api --runtime "PYTHON:3.11"

# Configure environment variables
az webapp config appsettings set --resource-group rg-sales-advisor --name sales-advisor-api --settings \
  OPEN_AI_KEY="..." SEARCH_KEY="..." API_KEYS="..." ...

# Deploy
Compress-Archive -Path api.py,models.py,sales_advisor_engine.py,prompts.py,*.json,requirements_api.txt -DestinationPath deploy.zip
az webapp deployment source config-zip --resource-group rg-sales-advisor --name sales-advisor-api --src deploy.zip
```

---

## 🧪 Testing

See [API_TESTING_GUIDE.md](API_TESTING_GUIDE.md) in this folder for comprehensive testing examples.

**Quick Tests:**

```bash
# Python
python -c "
import requests
r = requests.post('http://localhost:8000/api/v1/analyze',
    headers={'X-API-Key': 'test-key-1', 'Content-Type': 'application/json'},
    json={'opportunity_description': 'Test deal with healthcare company'})
print(r.json()['recommendation'][:200])
"

# cURL
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "X-API-Key: test-key-1" \
  -H "Content-Type: application/json" \
  -d '{"opportunity_description": "Test deal"}'
```

**Test Graceful Error Handling:**

```bash
# Test that API doesn't crash with invalid product/sector/region
cd ..
python test_missing_metrics.py
```

See [GRACEFUL_ERROR_HANDLING.md](GRACEFUL_ERROR_HANDLING.md) in this folder for details on how the API handles missing metrics.

---

## 📁 Project Structure

```
SalesAdvisorService/
├── api.py                      # FastAPI application (main entry point)
├── models.py                   # Pydantic request/response models
├── sales_advisor_engine.py     # Business logic engine
├── prompts.py                  # LLM prompts
├── quantitative_stats.json     # Statistical data
├── qualitative_stats.json      # Qualitative insights data
├── requirements_api.txt        # Python dependencies
├── README_API.md              # This file
├── AZURE_DEPLOYMENT_GUIDE.md  # Deployment instructions
└── API_TESTING_GUIDE.md       # Testing examples
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPEN_AI_KEY` | Yes | Azure OpenAI API key | `abc123...` |
| `OPEN_AI_ENDPOINT` | Yes | Azure OpenAI endpoint URL | `https://your-resource.openai.azure.com/` |
| `SEARCH_ENDPOINT` | Yes | Azure Cognitive Search endpoint | `https://your-search.search.windows.net` |
| `SEARCH_KEY` | Yes | Azure Cognitive Search admin key | `xyz789...` |
| `INDEX_NAME` | Yes | Search index name | `sales-opportunities` |
| `EMBEDDING_MODEL` | Yes | Embedding model deployment name | `text-embedding-ada-002` |
| `CHAT_MODEL` | Yes | Chat model deployment name | `gpt-4o` |
| `API_KEYS` | Yes | Comma-separated API keys for authentication | `key1,key2,key3` |

---

## 🛠️ Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements_api.txt

# Run with auto-reload
uvicorn api:app --reload --port 8000

# Run with custom host/port
uvicorn api:app --host 0.0.0.0 --port 8080
```

### Running Tests

```bash
# Install test dependencies
pip install pytest httpx

# Run tests (if test file exists)
pytest test_api.py -v
```

### Code Quality

```bash
# Format code
black api.py models.py

# Lint code
flake8 api.py models.py

# Type checking
mypy api.py models.py
```

---

## 🐛 Troubleshooting

### Issue: "Missing API key"

**Solution:** Include `X-API-Key` header in your request
```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/analyze
```

### Issue: "Rate limit exceeded"

**Solution:** Wait for the rate limit window to reset (shown in error message) or use a different API key

### Issue: "Application Error" on Azure

**Solution:** Check logs
```bash
az webapp log tail --resource-group rg-sales-advisor --name sales-advisor-api
```

Common causes:
- Missing environment variables
- Incorrect Azure credentials
- Missing files in deployment package

### Issue: Slow response times

**Solutions:**
- Upgrade Azure App Service plan to higher tier
- Check Azure OpenAI quota and throttling
- Enable Application Insights to identify bottlenecks

---

## 📊 Performance

**Expected Response Times:**
- Health check: < 100ms
- Analysis endpoint: 10-30 seconds (depends on LLM processing)

**Scalability:**
- Supports multiple concurrent requests
- Rate limiting prevents abuse
- Can scale horizontally with Azure App Service

**Optimization Tips:**
- Use caching for frequently accessed data
- Implement Redis for distributed rate limiting
- Enable Application Insights for monitoring

---

## 🔒 Security

### Best Practices

1. **Use HTTPS only** in production
2. **Rotate API keys regularly** (every 90 days recommended)
3. **Store secrets in Azure Key Vault** (not environment variables)
4. **Enable Application Insights** for monitoring
5. **Configure CORS** to allow only trusted domains
6. **Use Azure AD authentication** for enterprise deployments

### CORS Configuration

Edit `api.py` to specify allowed origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specify exact domains
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

---

## 💰 Cost Estimation

**Monthly Costs (Approximate):**

| Service | Tier | Cost |
|---------|------|------|
| Azure App Service | B1 (Basic) | $13 |
| Azure OpenAI | Pay-per-use | $50-200 |
| Azure Cognitive Search | Basic | $75 |
| **Total** | | **$138-288/month** |

**Cost Optimization:**
- Use B1 tier for dev/test, upgrade to S1/P1V2 for production
- Monitor Azure OpenAI usage and set spending limits
- Use Free tier for Application Insights (5GB/month included)

---

## 📞 Support

**Documentation:**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure OpenAI Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)

**Troubleshooting:**
1. Check logs: `az webapp log tail --resource-group rg-sales-advisor --name sales-advisor-api`
2. Verify environment variables are set correctly
3. Test locally first: `uvicorn api:app --reload`
4. Check Azure service health: https://status.azure.com/

---

## 📝 License

This project is part of the Sales Prediction POC.

---

## 🎉 Quick Links

- **Interactive Docs:** `/docs` (Swagger UI)
- **Alternative Docs:** `/redoc` (ReDoc)
- **Health Check:** `/health`
- **Main Endpoint:** `/api/v1/analyze`

**Your API is ready to deploy! 🚀**


