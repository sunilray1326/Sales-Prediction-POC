# Quick Start: Deploy to Azure in 5 Minutes

This guide will help you deploy the Sales Recommendation Advisor Streamlit app to Azure App Service quickly.

## Prerequisites Checklist

- [ ] Azure account with active subscription
- [ ] Azure CLI installed ([Download here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
- [ ] Azure OpenAI Service deployed with Chat and Embedding models
- [ ] Azure Cognitive Search with populated index
- [ ] Environment variable values ready (see below)

## Required Information

Before starting, gather these values:

1. **OPEN_AI_KEY** - Your Azure OpenAI API key
2. **OPEN_AI_ENDPOINT** - Your Azure OpenAI endpoint URL
3. **SEARCH_ENDPOINT** - Your Azure Cognitive Search endpoint URL
4. **SEARCH_KEY** - Your Azure Cognitive Search admin key
5. **INDEX_NAME** - Your search index name
6. **EMBEDDING_MODEL** - Your embedding model deployment name
7. **CHAT_MODEL** - Your chat model deployment name

## Deployment Methods

### Method 1: Automated Script (Easiest) ⭐

**For Windows (PowerShell):**

```powershell
cd "c:\Sunil Ray\Github\Sales Prediction POC\Azure SDK Approach"
.\deploy_azure.ps1
```

**For Linux/Mac (Bash):**

```bash
cd "c:/Sunil Ray/Github/Sales Prediction POC/Azure SDK Approach"
chmod +x deploy_azure.sh
./deploy_azure.sh
```

The script will:
1. Prompt you for all required values
2. Create all Azure resources
3. Deploy your application
4. Provide the URL to access your app

**Estimated time: 5-10 minutes**

---

### Method 2: Azure Portal (No CLI Required)

#### Step 1: Create Web App (2 minutes)

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **"+ Create a resource"** → Search **"Web App"**
3. Fill in:
   - **Name**: `sales-advisor-app` (must be globally unique)
   - **Runtime**: Python 3.11
   - **Operating System**: Linux
   - **Region**: Choose nearest region
   - **Pricing**: B1 Basic or higher
4. Click **"Review + Create"** → **"Create"**

#### Step 2: Configure Settings (2 minutes)

1. Go to your new Web App
2. Click **"Configuration"** (left menu under Settings)
3. Click **"+ New application setting"** for each:
   - `OPEN_AI_KEY` = [your value]
   - `OPEN_AI_ENDPOINT` = [your value]
   - `SEARCH_ENDPOINT` = [your value]
   - `SEARCH_KEY` = [your value]
   - `INDEX_NAME` = [your value]
   - `EMBEDDING_MODEL` = [your value]
   - `CHAT_MODEL` = [your value]
   - `WEBSITE_STARTUP_FILE` = `startup.sh`
   - `SCM_DO_BUILD_DURING_DEPLOYMENT` = `true`
4. Click **"Save"** at the top

#### Step 3: Deploy Code (1 minute)

**Option A: ZIP Deploy**

1. Create a ZIP file containing:
   - `streamlit_app.py`
   - `requirements.txt`
   - `startup.sh`
   - `Cline_stats.json`
   - `qualitative_stats.json`
2. In Azure Portal, go to your Web App
3. Click **"Advanced Tools"** → **"Go"**
4. Click **"Tools"** → **"Zip Push Deploy"**
5. Drag and drop your ZIP file

**Option B: VS Code Extension**

1. Install **Azure App Service** extension in VS Code
2. Sign in to Azure
3. Right-click the `Azure SDK Approach` folder
4. Select **"Deploy to Web App"**
5. Choose your Web App

#### Step 4: Access Your App

1. In Azure Portal, click **"Browse"** or go to:
   ```
   https://sales-advisor-app.azurewebsites.net
   ```

**Estimated time: 5 minutes**

---

### Method 3: Azure CLI (For Developers)

```bash
# 1. Login
az login

# 2. Set variables (update these)
RESOURCE_GROUP="sales-advisor-rg"
APP_NAME="sales-advisor-app"
LOCATION="eastus"

# 3. Create resources
az group create --name $RESOURCE_GROUP --location $LOCATION
az appservice plan create --name sales-advisor-plan --resource-group $RESOURCE_GROUP --sku B1 --is-linux
az webapp create --resource-group $RESOURCE_GROUP --plan sales-advisor-plan --name $APP_NAME --runtime "PYTHON:3.11"

# 4. Set environment variables (update values)
az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $APP_NAME --settings \
  OPEN_AI_KEY="your-key" \
  OPEN_AI_ENDPOINT="your-endpoint" \
  SEARCH_ENDPOINT="your-search-endpoint" \
  SEARCH_KEY="your-search-key" \
  INDEX_NAME="your-index-name" \
  EMBEDDING_MODEL="your-embedding-model" \
  CHAT_MODEL="your-chat-model" \
  SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
  WEBSITE_STARTUP_FILE="startup.sh"

# 5. Deploy
cd "Azure SDK Approach"
az webapp up --resource-group $RESOURCE_GROUP --name $APP_NAME --runtime "PYTHON:3.11"
```

**Estimated time: 5 minutes**

---

## Verification

After deployment, verify your app is working:

1. Navigate to your app URL: `https://<your-app-name>.azurewebsites.net`
2. You should see the Sales Recommendation Advisor interface
3. Try entering a sample opportunity to test functionality

## Troubleshooting

### App shows "Application Error"

**Solution**: Check logs
1. Go to Azure Portal → Your Web App
2. Click **"Log stream"** (left menu)
3. Look for errors

Common issues:
- Missing environment variables → Add them in Configuration
- Wrong Python version → Ensure Python 3.11 is selected
- Missing files → Ensure all files are deployed

### App is slow to start

**Solution**: This is normal for the first request. Azure App Service may take 1-2 minutes to cold start.

### "Module not found" errors

**Solution**: Ensure `requirements.txt` is deployed and contains all dependencies.

### Can't access Azure resources

**Solution**: 
1. Verify environment variables are correct
2. Check Azure OpenAI and Search endpoints are accessible
3. Verify API keys are valid

## View Logs

**In Azure Portal:**
1. Go to your Web App
2. Click **"Log stream"**

**Via CLI:**
```bash
az webapp log tail --resource-group sales-advisor-rg --name sales-advisor-app
```

## Update Your App

To deploy updates:

**Via CLI:**
```bash
cd "Azure SDK Approach"
az webapp up --resource-group sales-advisor-rg --name sales-advisor-app
```

**Via Portal:**
- Use ZIP deploy again with updated files

## Cost Estimate

- **B1 Basic Plan**: ~$13/month
- **S1 Standard Plan**: ~$70/month (recommended for production)
- Azure OpenAI and Search costs are separate

## Next Steps

- [ ] Set up custom domain
- [ ] Enable Application Insights for monitoring
- [ ] Configure auto-scaling for production
- [ ] Set up CI/CD pipeline
- [ ] Enable authentication if needed

## Support

For detailed instructions, see [README_DEPLOYMENT.md](README_DEPLOYMENT.md)

For Azure support: https://azure.microsoft.com/support/

---

**Your app should now be live! 🎉**

Access it at: `https://<your-app-name>.azurewebsites.net`

