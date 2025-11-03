# Azure Deployment Checklist

Use this checklist to track your deployment progress.

## Pre-Deployment Preparation

### Azure Account & Resources
- [ ] Azure subscription is active
- [ ] Azure CLI installed (if using scripts/CLI method)
- [ ] Logged into Azure Portal
- [ ] Azure OpenAI Service deployed
- [ ] Chat model deployed in Azure OpenAI
- [ ] Embedding model deployed in Azure OpenAI
- [ ] Azure Cognitive Search service created
- [ ] Search index created and populated with data

### Gather Required Information
- [ ] Azure OpenAI API Key: `____________________`
- [ ] Azure OpenAI Endpoint: `____________________`
- [ ] Azure Search Endpoint: `____________________`
- [ ] Azure Search Admin Key: `____________________`
- [ ] Search Index Name: `____________________`
- [ ] Embedding Model Deployment Name: `____________________`
- [ ] Chat Model Deployment Name: `____________________`

### Choose Deployment Method
- [ ] Automated Script (Windows PowerShell)
- [ ] Automated Script (Linux/Mac Bash)
- [ ] Azure Portal (Manual)
- [ ] Azure CLI (Manual)
- [ ] Docker Container

---

## Deployment Steps

### If Using Automated Script

- [ ] Open PowerShell (Windows) or Terminal (Linux/Mac)
- [ ] Navigate to `Azure SDK Approach` folder
- [ ] Run deployment script:
  - Windows: `.\deploy_azure.ps1`
  - Linux/Mac: `chmod +x deploy_azure.sh && ./deploy_azure.sh`
- [ ] Enter all required credentials when prompted
- [ ] Wait for deployment to complete (5-10 minutes)
- [ ] Note the app URL: `https://________________.azurewebsites.net`

### If Using Azure Portal

#### Step 1: Create Web App
- [ ] Go to Azure Portal
- [ ] Click "Create a resource"
- [ ] Search for "Web App"
- [ ] Fill in details:
  - [ ] Name: `____________________`
  - [ ] Runtime: Python 3.11
  - [ ] OS: Linux
  - [ ] Region: `____________________`
  - [ ] Pricing: B1 or higher
- [ ] Click "Review + Create" → "Create"
- [ ] Wait for deployment to complete

#### Step 2: Configure Application Settings
- [ ] Go to your Web App resource
- [ ] Click "Configuration" under Settings
- [ ] Add application settings (click "+ New application setting" for each):
  - [ ] `OPEN_AI_KEY` = [your value]
  - [ ] `OPEN_AI_ENDPOINT` = [your value]
  - [ ] `SEARCH_ENDPOINT` = [your value]
  - [ ] `SEARCH_KEY` = [your value]
  - [ ] `INDEX_NAME` = [your value]
  - [ ] `EMBEDDING_MODEL` = [your value]
  - [ ] `CHAT_MODEL` = [your value]
  - [ ] `WEBSITE_STARTUP_FILE` = `startup.sh`
  - [ ] `SCM_DO_BUILD_DURING_DEPLOYMENT` = `true`
- [ ] Click "Save" at the top
- [ ] Confirm when prompted

#### Step 3: Deploy Code
Choose one method:

**Option A: ZIP Deploy**
- [ ] Create ZIP file with these files:
  - [ ] `streamlit_app.py`
  - [ ] `requirements.txt`
  - [ ] `startup.sh`
  - [ ] `Cline_stats.json`
  - [ ] `qualitative_stats.json`
- [ ] Go to Web App → Advanced Tools → Go
- [ ] Click Tools → Zip Push Deploy
- [ ] Drag and drop ZIP file
- [ ] Wait for deployment

**Option B: VS Code**
- [ ] Install Azure App Service extension
- [ ] Sign in to Azure
- [ ] Right-click `Azure SDK Approach` folder
- [ ] Select "Deploy to Web App"
- [ ] Choose your Web App
- [ ] Confirm deployment

**Option C: Local Git**
- [ ] In Web App, go to Deployment Center
- [ ] Select "Local Git"
- [ ] Copy Git Clone URI
- [ ] In terminal, navigate to `Azure SDK Approach`
- [ ] Run:
  ```bash
  git init
  git add .
  git commit -m "Initial deployment"
  git remote add azure [Git Clone URI]
  git push azure master
  ```

### If Using Azure CLI

- [ ] Open terminal
- [ ] Login: `az login`
- [ ] Create resource group:
  ```bash
  az group create --name sales-advisor-rg --location eastus
  ```
- [ ] Create App Service plan:
  ```bash
  az appservice plan create --name sales-advisor-plan --resource-group sales-advisor-rg --sku B1 --is-linux
  ```
- [ ] Create Web App:
  ```bash
  az webapp create --resource-group sales-advisor-rg --plan sales-advisor-plan --name sales-advisor-app --runtime "PYTHON:3.11"
  ```
- [ ] Set environment variables (update values):
  ```bash
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
  ```
- [ ] Deploy code:
  ```bash
  cd "Azure SDK Approach"
  az webapp up --resource-group sales-advisor-rg --name sales-advisor-app --runtime "PYTHON:3.11"
  ```

---

## Post-Deployment Verification

### Check Deployment Status
- [ ] Go to Azure Portal → Your Web App
- [ ] Verify Status shows "Running"
- [ ] Check "Overview" for any errors

### Test Application
- [ ] Open app URL: `https://________________.azurewebsites.net`
- [ ] Verify page loads (may take 1-2 minutes on first load)
- [ ] Check that UI displays correctly
- [ ] Test with sample opportunity:
  ```
  We're pursuing a $50,000 deal with a healthcare company in the 
  Northeast region for our GTX-2000 product. The sales rep is 
  John Smith.
  ```
- [ ] Verify recommendation is generated
- [ ] Test follow-up questions
- [ ] Check that statistics display correctly

### Review Logs
- [ ] Go to Web App → Log stream
- [ ] Check for any errors or warnings
- [ ] Verify Streamlit started successfully

---

## Troubleshooting (If Issues Occur)

### App Shows "Application Error"
- [ ] Check all environment variables are set in Configuration
- [ ] Verify values are correct (no typos)
- [ ] Restart the Web App
- [ ] Check Log stream for specific errors

### App Won't Start
- [ ] Verify `startup.sh` is deployed
- [ ] Check `WEBSITE_STARTUP_FILE` is set to `startup.sh`
- [ ] Ensure Python 3.11 runtime is selected
- [ ] Review deployment logs in Deployment Center

### "Module not found" Errors
- [ ] Verify `requirements.txt` is deployed
- [ ] Check build logs show pip install succeeded
- [ ] Restart Web App

### Can't Connect to Azure Services
- [ ] Verify API keys are correct
- [ ] Check endpoints are accessible
- [ ] Test keys in Azure Portal
- [ ] Verify network/firewall settings

### Slow Performance
- [ ] First load is always slow (cold start)
- [ ] Consider upgrading to S1 or higher tier
- [ ] Enable "Always On" in Configuration → General settings

---

## Optional Enhancements

### Enable Application Insights
- [ ] Go to Web App → Application Insights
- [ ] Click "Turn on Application Insights"
- [ ] Create new or use existing resource
- [ ] Enable

### Configure Custom Domain
- [ ] Purchase domain
- [ ] Go to Web App → Custom domains
- [ ] Add custom domain
- [ ] Configure DNS records
- [ ] Verify domain

### Enable Authentication
- [ ] Go to Web App → Authentication
- [ ] Add identity provider
- [ ] Configure settings
- [ ] Test login

### Set Up Auto-Scaling
- [ ] Go to App Service Plan
- [ ] Click "Scale out"
- [ ] Add auto-scale rules
- [ ] Set min/max instances

### Configure CI/CD
- [ ] Set up GitHub repository
- [ ] Go to Web App → Deployment Center
- [ ] Connect to GitHub
- [ ] Configure build pipeline
- [ ] Test automated deployment

---

## Final Checklist

- [ ] Application is deployed and running
- [ ] All features tested and working
- [ ] Logs reviewed (no critical errors)
- [ ] Performance is acceptable
- [ ] Environment variables secured
- [ ] Monitoring enabled (Application Insights)
- [ ] Costs reviewed and acceptable
- [ ] Documentation saved for future reference
- [ ] Team members notified of deployment
- [ ] App URL shared: `https://________________.azurewebsites.net`

---

## Important URLs & Commands

**App URL**: `https://________________.azurewebsites.net`

**Azure Portal**: https://portal.azure.com

**View Logs**:
```bash
az webapp log tail --resource-group sales-advisor-rg --name sales-advisor-app
```

**Restart App**:
```bash
az webapp restart --resource-group sales-advisor-rg --name sales-advisor-app
```

**Update App**:
```bash
cd "Azure SDK Approach"
az webapp up --resource-group sales-advisor-rg --name sales-advisor-app
```

---

## Notes & Issues

Use this space to track any issues or notes during deployment:

```
Date: ___________
Issue: 


Resolution:


---

Date: ___________
Issue:


Resolution:


```

---

## Deployment Complete! 🎉

Once all items are checked, your Sales Recommendation Advisor is successfully deployed to Azure!

**Next Steps**:
1. Share the app URL with your team
2. Monitor usage and performance
3. Gather user feedback
4. Plan for scaling if needed
5. Set up regular backups/updates

**Congratulations on your successful deployment!**

