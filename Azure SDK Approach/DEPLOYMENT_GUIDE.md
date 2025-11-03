# 🚀 Azure Web App Deployment Guide for Streamlit Sales Recommendation Advisor

## 📋 Prerequisites

1. **Azure Subscription** - Active Azure account
2. **Azure CLI** - Installed on your machine ([Download here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
3. **Git** - For deployment (optional, can use ZIP deploy)
4. **Your Azure Credentials:**
   - Azure OpenAI API Key & Endpoint
   - Azure Cognitive Search Key & Endpoint
   - Index Name
   - Model Names (Chat & Embedding)

---

## 🔧 Method 1: Deploy via Azure Portal (Easiest)

### Step 1: Create Azure Web App

1. **Login to Azure Portal**: https://portal.azure.com
2. Click **"Create a resource"**
3. Search for **"Web App"** and click **Create**
4. Fill in the details:
   - **Subscription**: Select your subscription
   - **Resource Group**: Create new or select existing
   - **Name**: `sales-recommendation-app` (must be globally unique)
   - **Publish**: `Code`
   - **Runtime stack**: `Python 3.11`
   - **Operating System**: `Linux`
   - **Region**: Choose closest to you (e.g., `East US`)
   - **Pricing Plan**: Select `B1` (Basic) or higher
5. Click **"Review + Create"** → **"Create"**
6. Wait for deployment to complete (~2-3 minutes)

### Step 2: Configure Application Settings (Environment Variables)

1. Go to your Web App resource
2. In the left menu, click **"Configuration"** (under Settings)
3. Click **"+ New application setting"** and add each of these:

   | Name | Value |
   |------|-------|
   | `OPEN_AI_KEY` | Your Azure OpenAI API Key |
   | `OPEN_AI_ENDPOINT` | Your Azure OpenAI Endpoint |
   | `SEARCH_ENDPOINT` | Your Azure Search Endpoint |
   | `SEARCH_KEY` | Your Azure Search Key |
   | `INDEX_NAME` | Your Index Name |
   | `EMBEDDING_MODEL` | Your Embedding Model Name |
   | `CHAT_MODEL` | Your Chat Model Name |
   | `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |
   | `WEBSITE_HTTPLOGGING_RETENTION_DAYS` | `7` |

4. Click **"Save"** at the top
5. Click **"Continue"** when prompted

### Step 3: Configure Startup Command

1. Still in **"Configuration"**
2. Click on **"General settings"** tab
3. In **"Startup Command"** field, enter:
   ```bash
   bash startup.sh
   ```
4. Click **"Save"**

### Step 4: Deploy Your Code

**Option A: Using ZIP Deploy (Recommended for first-time)**

1. **Prepare deployment package:**
   - Open PowerShell in your project directory
   - Run these commands:
   ```powershell
   cd "Azure SDK Approach"
   Compress-Archive -Path streamlit_app.py,Cline_stats.json,qualitative_stats.json,requirements.txt,startup.sh,.streamlit -DestinationPath deploy.zip -Force
   ```

2. **Deploy via Azure CLI:**
   ```powershell
   # Login to Azure
   az login
   
   # Deploy the ZIP file
   az webapp deployment source config-zip --resource-group <YOUR_RESOURCE_GROUP> --name <YOUR_APP_NAME> --src deploy.zip
   ```
   
   Replace:
   - `<YOUR_RESOURCE_GROUP>` with your resource group name
   - `<YOUR_APP_NAME>` with your web app name (e.g., `sales-recommendation-app`)

**Option B: Using Local Git Deploy**

1. In Azure Portal, go to your Web App
2. Click **"Deployment Center"** (left menu)
3. Select **"Local Git"** → **"Save"**
4. Copy the **Git Clone Uri**
5. In PowerShell:
   ```powershell
   cd "Azure SDK Approach"
   git init
   git add .
   git commit -m "Initial deployment"
   git remote add azure <GIT_CLONE_URI>
   git push azure master
   ```

**Option C: Using VS Code Azure Extension**

1. Install **Azure App Service** extension in VS Code
2. Click Azure icon in sidebar
3. Sign in to Azure
4. Right-click your Web App → **"Deploy to Web App"**
5. Select the `Azure SDK Approach` folder

### Step 5: Verify Deployment

1. Go to your Web App in Azure Portal
2. Click **"Overview"**
3. Click the **URL** (e.g., `https://sales-recommendation-app.azurewebsites.net`)
4. Wait 2-3 minutes for first startup
5. Your Streamlit app should load!

### Step 6: Monitor Logs (If Issues Occur)

1. In Azure Portal, go to your Web App
2. Click **"Log stream"** (left menu under Monitoring)
3. Watch for any errors during startup
4. Common issues:
   - Missing environment variables
   - Port configuration
   - Package installation errors

---

## 🔧 Method 2: Deploy via Azure CLI (Advanced)

### Complete CLI Deployment Script

```powershell
# Variables
$RESOURCE_GROUP = "sales-app-rg"
$APP_NAME = "sales-recommendation-app"
$LOCATION = "eastus"
$APP_SERVICE_PLAN = "sales-app-plan"

# Login
az login

# Create Resource Group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create App Service Plan (Linux, Python)
az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --sku B1 --is-linux

# Create Web App
az webapp create --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --name $APP_NAME --runtime "PYTHON:3.11"

# Configure startup command
az webapp config set --resource-group $RESOURCE_GROUP --name $APP_NAME --startup-file "bash startup.sh"

# Set environment variables
az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $APP_NAME --settings `
    OPEN_AI_KEY="<YOUR_OPENAI_KEY>" `
    OPEN_AI_ENDPOINT="<YOUR_OPENAI_ENDPOINT>" `
    SEARCH_ENDPOINT="<YOUR_SEARCH_ENDPOINT>" `
    SEARCH_KEY="<YOUR_SEARCH_KEY>" `
    INDEX_NAME="<YOUR_INDEX_NAME>" `
    EMBEDDING_MODEL="<YOUR_EMBEDDING_MODEL>" `
    CHAT_MODEL="<YOUR_CHAT_MODEL>" `
    SCM_DO_BUILD_DURING_DEPLOYMENT="true"

# Deploy code (from Azure SDK Approach folder)
cd "Azure SDK Approach"
Compress-Archive -Path streamlit_app.py,Cline_stats.json,qualitative_stats.json,requirements.txt,startup.sh,.streamlit -DestinationPath deploy.zip -Force
az webapp deployment source config-zip --resource-group $RESOURCE_GROUP --name $APP_NAME --src deploy.zip

# Open the app in browser
az webapp browse --resource-group $RESOURCE_GROUP --name $APP_NAME
```

---

## 🔍 Troubleshooting

### Issue 1: App Not Loading / 502 Error
**Solution:**
- Check Log Stream in Azure Portal
- Verify all environment variables are set correctly
- Ensure startup command is: `bash startup.sh`
- Check if port 8000 is configured in startup.sh

### Issue 2: Module Not Found Errors
**Solution:**
- Verify `requirements.txt` is deployed
- Check Log Stream for pip install errors
- Ensure `SCM_DO_BUILD_DURING_DEPLOYMENT=true` is set

### Issue 3: Streamlit Not Starting
**Solution:**
- Check `startup.sh` has correct permissions
- Verify Streamlit config in `.streamlit/config.toml`
- Check port configuration (should be 8000)

### Issue 4: Environment Variables Not Loading
**Solution:**
- Don't use `.env` file in Azure (use App Settings instead)
- Verify all variables are set in Configuration → Application Settings
- Restart the Web App after changing settings

### Issue 5: Files Not Found (JSON files)
**Solution:**
- Ensure `Cline_stats.json` and `qualitative_stats.json` are in the deployment package
- Check file paths in `streamlit_app.py` use `Path(__file__).parent`

---

## 📊 Cost Estimation

**Basic Tier (B1):**
- ~$13-15 USD/month
- 1.75 GB RAM
- 100 GB storage
- Suitable for development/testing

**Standard Tier (S1):**
- ~$70 USD/month
- 1.75 GB RAM
- 50 GB storage
- Better for production

**Premium Tier (P1V2):**
- ~$80 USD/month
- 3.5 GB RAM
- 250 GB storage
- Best performance

---

## 🔒 Security Best Practices

1. **Never commit `.env` file** to Git
2. **Use Azure Key Vault** for sensitive credentials (advanced)
3. **Enable HTTPS only** in Web App settings
4. **Restrict access** using Azure AD authentication (optional)
5. **Monitor costs** using Azure Cost Management

---

## 🎯 Next Steps After Deployment

1. **Custom Domain**: Add your own domain name
2. **SSL Certificate**: Enable custom SSL (free with App Service)
3. **Scaling**: Configure auto-scaling rules
4. **Monitoring**: Set up Application Insights
5. **CI/CD**: Set up GitHub Actions for automatic deployment

---

## 📞 Support

If you encounter issues:
1. Check Azure Portal → Web App → Log Stream
2. Review deployment logs in Deployment Center
3. Check Application Insights (if enabled)
4. Azure Support: https://azure.microsoft.com/support/

---

## ✅ Deployment Checklist

- [ ] Azure Web App created
- [ ] Python 3.11 runtime selected
- [ ] All environment variables configured
- [ ] Startup command set to `bash startup.sh`
- [ ] Code deployed (ZIP/Git/VS Code)
- [ ] App accessible via URL
- [ ] Logs checked for errors
- [ ] Test all features working

---

**🎉 Congratulations! Your Streamlit app is now live on Azure!**

