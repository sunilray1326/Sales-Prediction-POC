# Sales Recommendation Advisor - Azure Deployment Guide

## 📁 Deployment Files Overview

Your `Azure SDK Approach` folder now contains everything needed to deploy the Streamlit app to Azure App Service.

### 🎯 Start Here

**New to Azure deployment?** → Read `QUICKSTART_DEPLOYMENT.md` (5-minute guide)

**Want detailed instructions?** → Read `README_DEPLOYMENT.md` (comprehensive guide)

**Ready to deploy?** → Use `DEPLOYMENT_CHECKLIST.md` to track your progress

**Quick reference?** → See `DEPLOYMENT_SUMMARY.md`

---

## 📋 File Structure

```
Azure SDK Approach/
│
├── 🚀 APPLICATION FILES
│   ├── streamlit_app.py              # Main Streamlit application
│   ├── Cline_stats.json              # Statistics data
│   └── qualitative_stats.json        # Qualitative insights
│
├── ⚙️ DEPLOYMENT CONFIGURATION
│   ├── requirements.txt              # Python dependencies
│   ├── startup.sh                    # Azure startup script
│   ├── .deployment                   # Deployment config
│   ├── Dockerfile                    # Docker configuration (optional)
│   ├── .dockerignore                 # Docker ignore file
│   └── .env.template                 # Environment variables template
│
├── 🤖 AUTOMATED DEPLOYMENT SCRIPTS
│   ├── deploy_azure.ps1              # Windows PowerShell script
│   └── deploy_azure.sh               # Linux/Mac Bash script
│
└── 📚 DOCUMENTATION
    ├── README_AZURE_DEPLOYMENT.md    # This file - Start here
    ├── QUICKSTART_DEPLOYMENT.md      # 5-minute quick start
    ├── README_DEPLOYMENT.md          # Comprehensive guide
    ├── DEPLOYMENT_SUMMARY.md         # Complete summary
    └── DEPLOYMENT_CHECKLIST.md       # Step-by-step checklist
```

---

## 🚀 Three Ways to Deploy

### 1️⃣ Automated Script (Easiest - 5 minutes)

**For Windows:**
```powershell
cd "c:\Sunil Ray\Github\Sales Prediction POC\Azure SDK Approach"
.\deploy_azure.ps1
```

**For Linux/Mac:**
```bash
cd "c:/Sunil Ray/Github/Sales Prediction POC/Azure SDK Approach"
chmod +x deploy_azure.sh
./deploy_azure.sh
```

The script will:
- ✅ Create all Azure resources
- ✅ Configure settings
- ✅ Deploy your app
- ✅ Provide the URL

---

### 2️⃣ Azure Portal (No CLI - 5 minutes)

1. **Create Web App** in Azure Portal
   - Python 3.11, Linux, B1 tier or higher

2. **Add Environment Variables** in Configuration
   - See `.env.template` for required variables

3. **Deploy Code** via ZIP or VS Code
   - Include: `streamlit_app.py`, `requirements.txt`, `startup.sh`, `*.json`

See `QUICKSTART_DEPLOYMENT.md` for detailed steps.

---

### 3️⃣ Azure CLI (For Developers - 5 minutes)

```bash
# Login
az login

# Create resources
az group create --name sales-advisor-rg --location eastus
az appservice plan create --name sales-advisor-plan --resource-group sales-advisor-rg --sku B1 --is-linux
az webapp create --resource-group sales-advisor-rg --plan sales-advisor-plan --name sales-advisor-app --runtime "PYTHON:3.11"

# Set environment variables (update values)
az webapp config appsettings set --resource-group sales-advisor-rg --name sales-advisor-app --settings \
  OPEN_AI_KEY="your-key" \
  OPEN_AI_ENDPOINT="your-endpoint" \
  SEARCH_ENDPOINT="your-search-endpoint" \
  SEARCH_KEY="your-search-key" \
  INDEX_NAME="your-index-name" \
  EMBEDDING_MODEL="your-embedding-model" \
  CHAT_MODEL="your-chat-model" \
  SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
  WEBSITE_STARTUP_FILE="startup.sh"

# Deploy
cd "Azure SDK Approach"
az webapp up --resource-group sales-advisor-rg --name sales-advisor-app --runtime "PYTHON:3.11"
```

---

## 📝 Prerequisites

Before deploying, you need:

### Azure Resources
- ✅ Azure subscription (active)
- ✅ Azure OpenAI Service with deployed models
- ✅ Azure Cognitive Search with populated index

### Tools (for script/CLI methods)
- ✅ Azure CLI installed
- ✅ PowerShell (Windows) or Bash (Linux/Mac)

### Information Required
- ✅ Azure OpenAI API Key
- ✅ Azure OpenAI Endpoint
- ✅ Azure Search Endpoint
- ✅ Azure Search Admin Key
- ✅ Search Index Name
- ✅ Embedding Model Deployment Name
- ✅ Chat Model Deployment Name

**Tip**: Copy `.env.template` to `.env` and fill in your values for reference.

---

## 🎯 Recommended Deployment Path

### First Time Deploying?

1. **Read** `QUICKSTART_DEPLOYMENT.md` (2 minutes)
2. **Gather** all required credentials
3. **Choose** deployment method:
   - Easiest: Automated script
   - No CLI: Azure Portal
   - Most control: Azure CLI
4. **Follow** `DEPLOYMENT_CHECKLIST.md` step-by-step
5. **Verify** deployment works
6. **Celebrate** 🎉

### Already Familiar with Azure?

1. Run automated script OR
2. Use Azure CLI commands above
3. Done in 5 minutes!

---

## 📊 What Gets Deployed

### Required Files (Must Deploy)
```
✅ streamlit_app.py          # Main application
✅ requirements.txt          # Python dependencies  
✅ startup.sh               # Startup script
✅ Cline_stats.json         # Statistics data
✅ qualitative_stats.json   # Qualitative insights
```

### Configuration (Set in Azure)
```
✅ Environment variables (7 required)
✅ Startup file: startup.sh
✅ Runtime: Python 3.11
✅ OS: Linux
```

### Not Deployed (Development files)
```
❌ Other .py files (ClineSalesRecommendation.py, etc.)
❌ Documentation (.md files)
❌ Deployment scripts (.ps1, .sh)
❌ .env files (use Azure Configuration instead)
```

---

## ✅ Verification Steps

After deployment:

1. **Check Status**: Azure Portal → Web App → Overview (should show "Running")
2. **Open App**: `https://your-app-name.azurewebsites.net`
3. **Test**: Enter a sample sales opportunity
4. **Verify**: Recommendations are generated
5. **Review Logs**: Check for any errors

---

## 🐛 Troubleshooting

### App won't start?
- Check environment variables in Configuration
- Verify `startup.sh` is deployed
- Review logs in Log stream

### "Module not found" error?
- Ensure `requirements.txt` is deployed
- Check build logs

### Can't connect to Azure services?
- Verify API keys and endpoints
- Test credentials in Azure Portal

**See `README_DEPLOYMENT.md` for detailed troubleshooting.**

---

## 💰 Cost Estimate

- **B1 Basic**: ~$13/month (dev/test)
- **S1 Standard**: ~$70/month (production)
- Plus: Azure OpenAI and Search usage

**Tip**: Start with B1, scale up as needed.

---

## 🔐 Security Reminders

- ❌ Never commit `.env` files to Git
- ✅ Use Azure Key Vault for production
- ✅ Enable HTTPS (default)
- ✅ Configure authentication if needed
- ✅ Monitor access logs

---

## 📚 Documentation Guide

| Document | Purpose | When to Use |
|----------|---------|-------------|
| `README_AZURE_DEPLOYMENT.md` | Overview & navigation | Start here |
| `QUICKSTART_DEPLOYMENT.md` | 5-minute quick start | First deployment |
| `README_DEPLOYMENT.md` | Comprehensive guide | Detailed instructions |
| `DEPLOYMENT_SUMMARY.md` | Complete reference | Quick lookup |
| `DEPLOYMENT_CHECKLIST.md` | Step-by-step tracker | During deployment |

---

## 🎓 Learning Path

### Beginner
1. Read `QUICKSTART_DEPLOYMENT.md`
2. Use automated script
3. Follow `DEPLOYMENT_CHECKLIST.md`

### Intermediate
1. Skim `README_DEPLOYMENT.md`
2. Use Azure Portal method
3. Customize as needed

### Advanced
1. Use Azure CLI
2. Customize Dockerfile
3. Set up CI/CD pipeline

---

## 🔄 Updating Your App

After initial deployment, to update:

```bash
cd "Azure SDK Approach"
az webapp up --resource-group sales-advisor-rg --name sales-advisor-app
```

Or redeploy via Portal/VS Code.

---

## 📞 Getting Help

- **Azure Issues**: Check `README_DEPLOYMENT.md` troubleshooting section
- **Deployment Questions**: Review `DEPLOYMENT_SUMMARY.md`
- **Step-by-Step Help**: Use `DEPLOYMENT_CHECKLIST.md`
- **Azure Support**: https://azure.microsoft.com/support/

---

## ✨ Quick Commands Reference

### View Logs
```bash
az webapp log tail --resource-group sales-advisor-rg --name sales-advisor-app
```

### Restart App
```bash
az webapp restart --resource-group sales-advisor-rg --name sales-advisor-app
```

### Update App
```bash
az webapp up --resource-group sales-advisor-rg --name sales-advisor-app
```

### Delete Resources (cleanup)
```bash
az group delete --name sales-advisor-rg
```

---

## 🎉 Ready to Deploy?

Choose your path:

- **🚀 Quick Start**: Open `QUICKSTART_DEPLOYMENT.md`
- **📋 Guided**: Open `DEPLOYMENT_CHECKLIST.md`
- **📖 Detailed**: Open `README_DEPLOYMENT.md`
- **🤖 Automated**: Run `deploy_azure.ps1` or `deploy_azure.sh`

**Good luck with your deployment!** 🎊

---

## 📝 Notes

After deployment, your app will be available at:
```
https://your-app-name.azurewebsites.net
```

Remember to:
- ✅ Test thoroughly
- ✅ Monitor performance
- ✅ Set up alerts
- ✅ Plan for scaling
- ✅ Keep credentials secure

---

**Questions?** Check the documentation files or Azure support resources.

**Success?** Share your app URL with your team! 🎉

