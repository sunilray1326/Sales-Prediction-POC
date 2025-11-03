# 🚀 Quick Deployment Guide

## 🎯 Fastest Way to Deploy (3 Options)

### Option 1: Automated PowerShell Script (Recommended)

```powershell
cd "Azure SDK Approach"
.\deploy_to_azure.ps1
```

Follow the prompts to enter:
- Resource Group Name
- Web App Name (must be globally unique)
- Azure Region
- Your Azure credentials (OpenAI, Search, etc.)

**Time: ~10 minutes**

---

### Option 2: Manual Azure Portal Deployment

1. **Create Web App** in Azure Portal
   - Runtime: Python 3.11
   - OS: Linux
   - Plan: B1 or higher

2. **Configure Settings**
   - Add environment variables in Configuration
   - Set startup command: `bash startup.sh`

3. **Deploy Code**
   ```powershell
   cd "Azure SDK Approach"
   Compress-Archive -Path streamlit_app.py,Cline_stats.json,qualitative_stats.json,requirements.txt,startup.sh,.streamlit -DestinationPath deploy.zip -Force
   az webapp deployment source config-zip --resource-group <YOUR_RG> --name <YOUR_APP> --src deploy.zip
   ```

**Time: ~15 minutes**

---

### Option 3: Azure CLI One-Liner

```powershell
# Set variables
$RG="sales-app-rg"
$APP="sales-rec-app-123"
$LOC="eastus"

# Deploy
az group create -n $RG -l $LOC
az appservice plan create -n "$APP-plan" -g $RG --sku B1 --is-linux
az webapp create -g $RG -p "$APP-plan" -n $APP --runtime "PYTHON:3.11"
az webapp config set -g $RG -n $APP --startup-file "bash startup.sh"

# Set your environment variables (replace with your values)
az webapp config appsettings set -g $RG -n $APP --settings `
    OPEN_AI_KEY="your-key" `
    OPEN_AI_ENDPOINT="your-endpoint" `
    SEARCH_ENDPOINT="your-search-endpoint" `
    SEARCH_KEY="your-search-key" `
    INDEX_NAME="your-index" `
    EMBEDDING_MODEL="text-embedding-ada-002" `
    CHAT_MODEL="gpt-4" `
    SCM_DO_BUILD_DURING_DEPLOYMENT="true"

# Deploy code
cd "Azure SDK Approach"
Compress-Archive -Path streamlit_app.py,Cline_stats.json,qualitative_stats.json,requirements.txt,startup.sh,.streamlit -DestinationPath deploy.zip -Force
az webapp deployment source config-zip -g $RG -n $APP --src deploy.zip
```

**Time: ~8 minutes**

---

## 📋 Required Environment Variables

Make sure you have these ready:

| Variable | Example |
|----------|---------|
| `OPEN_AI_KEY` | `abc123...` |
| `OPEN_AI_ENDPOINT` | `https://your-openai.openai.azure.com/` |
| `SEARCH_ENDPOINT` | `https://your-search.search.windows.net` |
| `SEARCH_KEY` | `xyz789...` |
| `INDEX_NAME` | `sales-opportunities` |
| `EMBEDDING_MODEL` | `text-embedding-ada-002` |
| `CHAT_MODEL` | `gpt-4` or `gpt-35-turbo` |

---

## 🔍 After Deployment

1. **Wait 2-3 minutes** for first startup
2. **Access your app**: `https://YOUR_APP_NAME.azurewebsites.net`
3. **Check logs** if issues: Azure Portal → Your Web App → Log Stream

---

## 📚 Full Documentation

See **DEPLOYMENT_GUIDE.md** for:
- Detailed step-by-step instructions
- Troubleshooting guide
- Cost estimation
- Security best practices
- Advanced configurations

---

## ✅ Deployment Checklist

- [ ] Azure CLI installed (`az --version`)
- [ ] Logged in to Azure (`az login`)
- [ ] Have all environment variables ready
- [ ] Chosen unique app name
- [ ] Selected Azure region
- [ ] Ready to deploy!

---

## 🆘 Quick Troubleshooting

**App not loading?**
- Check Log Stream in Azure Portal
- Verify all environment variables are set
- Ensure startup command is `bash startup.sh`

**502 Error?**
- Wait 2-3 minutes for startup
- Check if Python 3.11 is selected
- Verify port 8000 in startup.sh

**Module errors?**
- Check requirements.txt is deployed
- Verify `SCM_DO_BUILD_DURING_DEPLOYMENT=true`

---

## 💰 Estimated Cost

- **B1 Basic**: ~$13/month (good for testing)
- **S1 Standard**: ~$70/month (production)
- **P1V2 Premium**: ~$80/month (high performance)

---

**Need help?** Check DEPLOYMENT_GUIDE.md for detailed instructions!

