# 🚀 Azure App Service Deployment Guide

Complete step-by-step guide to deploy the Sales Advisor REST API to Azure App Service.

---

## 📋 Prerequisites

1. **Azure Account** with active subscription
2. **Azure CLI** installed ([Download here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
3. **Python 3.9+** installed locally
4. **Git** installed (optional, for deployment)

---


# 1. Create Azure resources
az group create --name rg-sales-advisor --location eastus
az appservice plan create --name plan-sales-advisor --resource-group rg-sales-advisor --sku B1 --is-linux
az webapp create --resource-group rg-sales-advisor --plan plan-sales-advisor --name sales-advisor-api --runtime "PYTHON:3.11"

# 2. Set environment variables
az webapp config appsettings set --resource-group rg-sales-advisor --name sales-advisor-api --settings \
  OPEN_AI_KEY="your-key" \
  SEARCH_KEY="your-key" \
  API_KEYS="production-key-1,production-key-2" \
  # ... (see AZURE_DEPLOYMENT_GUIDE.md for all variables)

# 3. Create deployment package
Compress-Archive -Path api.py,models.py,sales_advisor_engine.py,prompts.py,*.json,requirements_api.txt -DestinationPath deploy.zip -Force

# 4. Deploy
az webapp deployment source config-zip --resource-group rg-sales-advisor --name sales-advisor-api --src deploy.zip

# Done! Your API is live at https://sales-advisor-api.azurewebsites.net


## 🎯 Quick Deployment (5 Steps)

### Step 1: Prepare Your Files

Create a deployment package with these files:
```
SalesAdvisorService/
├── api.py                      # FastAPI application
├── models.py                   # Pydantic models
├── sales_advisor_engine.py     # Business logic engine
├── prompts.py                  # LLM prompts
├── quantitative_stats.json     # Statistics data
├── qualitative_stats.json      # Statistics data
├── requirements_api.txt        # Python dependencies
└── .env                        # Environment variables (for local testing only)
```

**Important**: Do NOT include `.env` file in deployment. We'll set environment variables in Azure.

---

### Step 2: Login to Azure

```bash
# Login to Azure
az login

# Set your subscription (if you have multiple)
az account set --subscription "Your-Subscription-Name"

# Verify you're logged in
az account show
```

---

### Step 3: Create Azure Resources

```bash
# Set variables (customize these)
RESOURCE_GROUP="rg-sales-advisor"
LOCATION="eastus"
APP_SERVICE_PLAN="plan-sales-advisor"
WEB_APP_NAME="sales-advisor-api"  # Must be globally unique

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create App Service Plan (B1 tier - $13/month, suitable for production)
az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --sku B1 --is-linux

# Create Web App with Python 3.11 runtime
az webapp create --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --name $WEB_APP_NAME --runtime "PYTHON:3.11"

---

### Step 4: Configure Environment Variables

Set all required environment variables in Azure App Service:

```bash
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --settings \
    OPEN_AI_KEY="your-azure-openai-key" \
    OPEN_AI_ENDPOINT="https://your-resource.openai.azure.com/" \
    SEARCH_ENDPOINT="https://your-search-service.search.windows.net" \
    SEARCH_KEY="your-search-admin-key" \
    INDEX_NAME="your-index-name" \
    EMBEDDING_MODEL="text-embedding-ada-002" \
    CHAT_MODEL="gpt-4o" \
    API_KEYS="your-secret-api-key-1,your-secret-api-key-2" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true"
```

**Important**: Replace all placeholder values with your actual Azure credentials.

**API_KEYS**: Comma-separated list of API keys that clients will use to authenticate.

---

### Step 5: Deploy the Application

#### Option A: Deploy from Local Directory (Recommended)

```bash
# Navigate to SalesAdvisorService directory
cd "c:\Sunil Ray\Github\Sales Prediction POC\SalesAdvisorService"

# Create ZIP file for deployment
# PowerShell:
Compress-Archive -Path api.py,models.py,sales_advisor_engine.py,prompts.py,quantitative_stats.json,qualitative_stats.json,requirements.txt -DestinationPath deploy.zip -Force

# Deploy the ZIP file
az webapp deployment source config-zip --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --src deploy.zip


#### Option B: Deploy from Git Repository

```bash
# Configure deployment from local Git
az webapp deployment source config-local-git \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME

# Get the Git URL
GIT_URL=$(az webapp deployment source show \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --query "repoUrl" -o tsv)

# Add Azure as a remote and push
git remote add azure $GIT_URL
git add .
git commit -m "Deploy Sales Advisor API"
git push azure main
```

---

### Step 6: Configure Startup Command

```bash
# Set the startup command for FastAPI
az webapp config set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --startup-file "gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app --bind 0.0.0.0:8000"

---

## ✅ Verify Deployment

### Check Deployment Status

```bash
# Get the app URL
az webapp show --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --query "defaultHostName" -o tsv

Your API will be available at: `https://{WEB_APP_NAME}.azurewebsites.net`

### Test the API

```bash
# Test health endpoint (no auth required)
curl https://{WEB_APP_NAME}.azurewebsites.net/health

# Test analysis endpoint (requires API key)
curl -X POST https://{WEB_APP_NAME}.azurewebsites.net/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-1" \
  -d '{
    "opportunity_description": "We are pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX Plus Pro product."
  }'
```

---

## 📊 Monitor Your Application

### View Logs

```bash
# Stream live logs
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME

# Download logs
az webapp log download \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --log-file logs.zip
```

### Enable Application Insights (Recommended)

```bash
# Create Application Insights
az monitor app-insights component create --app sales-advisor-insights --location $LOCATION --resource-group $RESOURCE_GROUP

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show --app sales-advisor-insights --resource-group $RESOURCE_GROUP --query "instrumentationKey" -o tsv)

# Configure Web App to use Application Insights
az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --settings APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY

---

## 🔧 Troubleshooting

### Issue: "Application Error" or 500 Error

**Solution**: Check logs for errors
```bash
az webapp log tail --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME
```

Common causes:
- Missing environment variables
- Incorrect Azure credentials
- Missing dependencies in requirements_api.txt

### Issue: "Invalid API Key"

**Solution**: Verify API_KEYS environment variable is set correctly
```bash
az webapp config appsettings list \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --query "[?name=='API_KEYS']"
```

### Issue: Rate Limit Not Working Across Instances

**Solution**: For production with multiple instances, use Redis for rate limiting:

1. Create Azure Cache for Redis
2. Update `api.py` to use Redis instead of in-memory storage
3. Add `redis` to requirements_api.txt

### Issue: Slow Response Times

**Solutions**:
- Upgrade App Service Plan to higher tier (S1, P1V2)
- Enable Application Insights to identify bottlenecks
- Consider caching frequently accessed data

---

## 🔐 Security Best Practices

### 1. Rotate API Keys Regularly

```bash
# Update API keys without downtime
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --settings API_KEYS="new-key-1,new-key-2,old-key-1"

# After clients migrate, remove old keys
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --settings API_KEYS="new-key-1,new-key-2"
```

### 2. Enable HTTPS Only

```bash
az webapp update \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --https-only true
```

### 3. Configure CORS (if needed)

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

### 4. Use Azure Key Vault (Advanced)

Store secrets in Azure Key Vault instead of environment variables:

```bash
# Create Key Vault
az keyvault create \
  --name sales-advisor-vault \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Store secrets
az keyvault secret set --vault-name sales-advisor-vault --name "OpenAIKey" --value "your-key"
az keyvault secret set --vault-name sales-advisor-vault --name "SearchKey" --value "your-key"

# Grant Web App access to Key Vault
az webapp identity assign --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME
```

---

## 💰 Cost Optimization

### Estimated Monthly Costs

| Resource | Tier | Cost/Month |
|----------|------|------------|
| App Service Plan | B1 (Basic) | ~$13 |
| Azure OpenAI | Pay-per-use | ~$50-200 (depends on usage) |
| Azure Cognitive Search | Basic | ~$75 |
| **Total** | | **~$138-288/month** |

### Cost Saving Tips

1. **Use B1 tier for development/testing** - Upgrade to S1/P1V2 for production
2. **Monitor Azure OpenAI usage** - Set spending limits in Azure Portal
3. **Use Free tier for Application Insights** - 5GB/month included
4. **Auto-scale only when needed** - Configure scale rules based on CPU/memory

---

## 🔄 Update Deployment

### Update Code

```bash
# Make changes to your code
# Create new ZIP file
Compress-Archive -Path api.py,models.py,sales_advisor_engine.py,prompts.py,quantitative_stats.json,qualitative_stats.json,requirements_api.txt -DestinationPath deploy.zip -Force

# Deploy update
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --src deploy.zip
```

### Update Environment Variables

```bash
# Update specific setting
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --settings CHAT_MODEL="gpt-4o-mini"
```

### Restart Application

```bash
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME
```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure OpenAI Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)
- [Azure Cognitive Search Documentation](https://docs.microsoft.com/en-us/azure/search/)

---

## 🆘 Support

If you encounter issues:

1. Check the logs: `az webapp log tail --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME`
2. Verify environment variables are set correctly
3. Test locally first: `uvicorn api:app --reload`
4. Check Azure service health: https://status.azure.com/

---

## ✅ Deployment Checklist

- [ ] Azure CLI installed and logged in
- [ ] Resource group created
- [ ] App Service Plan created
- [ ] Web App created with Python 3.11 runtime
- [ ] All environment variables configured (OPEN_AI_KEY, SEARCH_KEY, API_KEYS, etc.)
- [ ] Application deployed (ZIP or Git)
- [ ] Startup command configured
- [ ] HTTPS-only enabled
- [ ] Health endpoint tested
- [ ] Analysis endpoint tested with API key
- [ ] Application Insights enabled (optional but recommended)
- [ ] Logs reviewed for errors
- [ ] API documentation accessible at /docs

**Your API is now live! 🎉**


