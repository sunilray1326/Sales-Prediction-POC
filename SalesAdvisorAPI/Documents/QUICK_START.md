# ⚡ Quick Start Guide - Sales Advisor API

Get your Sales Advisor API up and running in 5 minutes!

---

## 🎯 For Local Testing (Development)

### Step 1: Install Dependencies (1 minute)

```bash
cd SalesAdvisorService
pip install -r requirements_api.txt
```

### Step 2: Configure Environment (2 minutes)

```bash
# Copy the template
copy .env.template .env

# Edit .env file and add your Azure credentials:
# - OPEN_AI_KEY
# - OPEN_AI_ENDPOINT
# - SEARCH_ENDPOINT
# - SEARCH_KEY
# - INDEX_NAME
# - EMBEDDING_MODEL
# - CHAT_MODEL
# - API_KEYS
```

### Step 3: Start the Server (1 minute)

```bash
# Option A: Using the startup script (recommended)
python start_api.py

# Option B: Using uvicorn directly
uvicorn api:app --reload --port 8000
```

### Step 4: Test It! (1 minute)

Open your browser and go to: **http://localhost:8000/docs**

Or test with cURL:
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key-1" \
  -d '{
    "opportunity_description": "We are pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX Plus Pro product."
  }'
```

**Done! 🎉** Your API is running locally.

---

## 🚀 For Azure Deployment (Production)

### Step 1: Prepare Files (1 minute)

Make sure you have these files in `SalesAdvisorService/`:
- ✅ api.py
- ✅ models.py
- ✅ sales_advisor_engine.py
- ✅ prompts.py
- ✅ quantitative_stats.json
- ✅ qualitative_stats.json
- ✅ requirements_api.txt

### Step 2: Create Azure Resources (3 minutes)

```bash
# Login to Azure
az login

# Set variables (customize these)
RESOURCE_GROUP="rg-sales-advisor"
LOCATION="eastus"
APP_NAME="sales-advisor-api"  # Must be globally unique!

# Create resources
az group create --name $RESOURCE_GROUP --location $LOCATION

az appservice plan create \
  --name plan-sales-advisor \
  --resource-group $RESOURCE_GROUP \
  --sku B1 \
  --is-linux

az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan plan-sales-advisor \
  --name $APP_NAME \
  --runtime "PYTHON:3.11"
```

### Step 3: Configure Environment Variables (2 minutes)

```bash
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    OPEN_AI_KEY="your-key" \
    OPEN_AI_ENDPOINT="https://your-resource.openai.azure.com/" \
    SEARCH_ENDPOINT="https://your-search.search.windows.net" \
    SEARCH_KEY="your-key" \
    INDEX_NAME="your-index" \
    EMBEDDING_MODEL="text-embedding-ada-002" \
    CHAT_MODEL="gpt-4o" \
    API_KEYS="production-key-1,production-key-2" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true"
```

### Step 4: Deploy (2 minutes)

```bash
# Create deployment package
Compress-Archive -Path api.py,models.py,sales_advisor_engine.py,prompts.py,quantitative_stats.json,qualitative_stats.json,requirements_api.txt -DestinationPath deploy.zip -Force

# Deploy to Azure
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --src deploy.zip
```

### Step 5: Configure Startup Command (1 minute)

```bash
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --startup-file "gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app --bind 0.0.0.0:8000"
```

### Step 6: Test Your Deployment (1 minute)

```bash
# Get your app URL
az webapp show --resource-group $RESOURCE_GROUP --name $APP_NAME --query "defaultHostName" -o tsv

# Test health endpoint
curl https://$APP_NAME.azurewebsites.net/health

# Test analysis endpoint
curl -X POST https://$APP_NAME.azurewebsites.net/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: production-key-1" \
  -d '{
    "opportunity_description": "We are pursuing a $50,000 deal with a healthcare company."
  }'
```

**Done! 🎉** Your API is live on Azure!

---

## 📖 API Usage Examples

### Python

```python
import requests

response = requests.post(
    "https://sales-advisor-api.azurewebsites.net/api/v1/analyze",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": "your-api-key"
    },
    json={
        "opportunity_description": "We are pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX Plus Pro product."
    }
)

result = response.json()
print(result["recommendation"])
```

### JavaScript

```javascript
fetch("https://sales-advisor-api.azurewebsites.net/api/v1/analyze", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": "your-api-key"
  },
  body: JSON.stringify({
    opportunity_description: "We are pursuing a $50,000 deal with a healthcare company."
  })
})
.then(response => response.json())
.then(data => console.log(data.recommendation));
```

### cURL

```bash
curl -X POST https://sales-advisor-api.azurewebsites.net/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"opportunity_description": "We are pursuing a $50,000 deal with a healthcare company."}'
```

---

## 🔑 Key Information

**API Endpoint:** `POST /api/v1/analyze`

**Authentication:** Include `X-API-Key` header with your API key

**Rate Limit:** 10 requests per hour per API key

**Request Format:**
```json
{
  "opportunity_description": "Your sales opportunity description here (10-5000 characters)"
}
```

**Response Format:**
```json
{
  "success": true,
  "recommendation": "AI-generated recommendation",
  "extracted_attributes": {...},
  "win_probability_improvements": [...],
  "similar_won_deals": [...],
  "similar_lost_deals": [...],
  "statistics": {...}
}
```

---

## 📚 Documentation Links

- **Interactive API Docs:** `/docs` (Swagger UI)
- **Alternative Docs:** `/redoc` (ReDoc)
- **Full Deployment Guide:** [AZURE_DEPLOYMENT_GUIDE.md](AZURE_DEPLOYMENT_GUIDE.md)
- **Testing Guide:** [API_TESTING_GUIDE.md](API_TESTING_GUIDE.md)
- **Complete README:** [README_API.md](README_API.md)

---

## 🆘 Troubleshooting

**Problem:** "Missing API key" error
- **Solution:** Add `X-API-Key` header to your request

**Problem:** "Rate limit exceeded" error
- **Solution:** Wait for the rate limit window to reset (shown in error message)

**Problem:** Application error on Azure
- **Solution:** Check logs with `az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME`

**Problem:** Slow responses
- **Solution:** This is normal! LLM processing takes 10-30 seconds

**Problem:** "Product/Sector/Region not found in stats"
- **Solution:** This is NOT an error! The API handles this gracefully by returning top alternatives. See [GRACEFUL_ERROR_HANDLING.md](GRACEFUL_ERROR_HANDLING.md) in this folder

---

## ✅ Checklist

### Local Development
- [ ] Dependencies installed
- [ ] .env file configured
- [ ] Server starts without errors
- [ ] Health endpoint returns 200 OK
- [ ] Analysis endpoint works with API key
- [ ] Interactive docs accessible at /docs

### Azure Deployment
- [ ] Azure resources created
- [ ] Environment variables configured
- [ ] Application deployed
- [ ] Startup command set
- [ ] Health endpoint accessible
- [ ] Analysis endpoint works
- [ ] HTTPS enabled

**You're all set! 🚀**

