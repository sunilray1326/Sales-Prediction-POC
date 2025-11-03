# Deploying Sales Recommendation Advisor to Azure App Service

This guide will help you deploy the Streamlit application to Azure as a Web App.

## Prerequisites

1. **Azure Account** - Active Azure subscription
2. **Azure CLI** - Install from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
3. **Required Azure Resources**:
   - Azure OpenAI Service with deployed models (Chat and Embedding)
   - Azure Cognitive Search with populated index
   - Environment variables configured

## Deployment Options

### Option 1: Deploy via Azure Portal (Recommended for Beginners)

#### Step 1: Create Azure Web App

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **"Create a resource"** → Search for **"Web App"**
3. Click **"Create"**
4. Fill in the details:
   - **Subscription**: Select your subscription
   - **Resource Group**: Create new or select existing
   - **Name**: Choose a unique name (e.g., `sales-advisor-app`)
   - **Publish**: Select **Code**
   - **Runtime stack**: Select **Python 3.11**
   - **Operating System**: **Linux**
   - **Region**: Choose your preferred region
   - **Pricing Plan**: Select appropriate plan (B1 or higher recommended)
5. Click **"Review + Create"** → **"Create"**

#### Step 2: Configure Application Settings

1. Once the Web App is created, go to the resource
2. Navigate to **"Configuration"** under Settings
3. Click **"New application setting"** and add the following environment variables:
   - `OPEN_AI_KEY` = Your Azure OpenAI API Key
   - `OPEN_AI_ENDPOINT` = Your Azure OpenAI Endpoint
   - `SEARCH_ENDPOINT` = Your Azure Cognitive Search Endpoint
   - `SEARCH_KEY` = Your Azure Cognitive Search Key
   - `INDEX_NAME` = Your Search Index Name
   - `EMBEDDING_MODEL` = Your Embedding Model Deployment Name
   - `CHAT_MODEL` = Your Chat Model Deployment Name
   - `SCM_DO_BUILD_DURING_DEPLOYMENT` = `true`
   - `WEBSITE_STARTUP_FILE` = `startup.sh`
4. Click **"Save"**

#### Step 3: Deploy Code

**Option A: Deploy from Local Git**

1. In your Web App, go to **"Deployment Center"**
2. Select **"Local Git"** as source
3. Click **"Save"**
4. Copy the Git Clone Uri
5. In your terminal, navigate to the `Azure SDK Approach` folder:
   ```bash
   cd "c:\Sunil Ray\Github\Sales Prediction POC\Azure SDK Approach"
   ```
6. Initialize git (if not already):
   ```bash
   git init
   git add .
   git commit -m "Initial deployment"
   ```
7. Add Azure remote and push:
   ```bash
   git remote add azure <Git Clone Uri from step 4>
   git push azure master
   ```

**Option B: Deploy via ZIP**

1. Create a ZIP file of the `Azure SDK Approach` folder contents:
   - Include: `streamlit_app.py`, `requirements.txt`, `startup.sh`, `Cline_stats.json`, `qualitative_stats.json`
2. In Azure Portal, go to your Web App
3. Navigate to **"Advanced Tools"** → **"Go"** (Kudu)
4. Click **"Tools"** → **"Zip Push Deploy"**
5. Drag and drop your ZIP file

**Option C: Deploy via VS Code**

1. Install **Azure App Service** extension in VS Code
2. Sign in to Azure
3. Right-click on the `Azure SDK Approach` folder
4. Select **"Deploy to Web App"**
5. Follow the prompts

#### Step 4: Verify Deployment

1. Go to your Web App in Azure Portal
2. Click **"Browse"** or navigate to `https://<your-app-name>.azurewebsites.net`
3. The Streamlit app should load

---

### Option 2: Deploy via Azure CLI

#### Step 1: Login to Azure

```bash
az login
```

#### Step 2: Create Resource Group (if needed)

```bash
az group create --name sales-advisor-rg --location eastus
```

#### Step 3: Create App Service Plan

```bash
az appservice plan create --name sales-advisor-plan --resource-group sales-advisor-rg --sku B1 --is-linux
```

#### Step 4: Create Web App

```bash
az webapp create --resource-group sales-advisor-rg --plan sales-advisor-plan --name sales-advisor-app --runtime "PYTHON:3.11"
```

#### Step 5: Configure Environment Variables

```bash
az webapp config appsettings set --resource-group sales-advisor-rg --name sales-advisor-app --settings \
  OPEN_AI_KEY="<your-openai-key>" \
  OPEN_AI_ENDPOINT="<your-openai-endpoint>" \
  SEARCH_ENDPOINT="<your-search-endpoint>" \
  SEARCH_KEY="<your-search-key>" \
  INDEX_NAME="<your-index-name>" \
  EMBEDDING_MODEL="<your-embedding-model>" \
  CHAT_MODEL="<your-chat-model>" \
  SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
  WEBSITE_STARTUP_FILE="startup.sh"
```

#### Step 6: Deploy Code

Navigate to the `Azure SDK Approach` folder and deploy:

```bash
cd "c:\Sunil Ray\Github\Sales Prediction POC\Azure SDK Approach"
az webapp up --resource-group sales-advisor-rg --name sales-advisor-app --runtime "PYTHON:3.11"
```

#### Step 7: View Logs (if needed)

```bash
az webapp log tail --resource-group sales-advisor-rg --name sales-advisor-app
```

---

### Option 3: Deploy via Docker (Advanced)

If you prefer containerization, you can create a Dockerfile and deploy as a container.

#### Create Dockerfile

Create a file named `Dockerfile` in the `Azure SDK Approach` folder:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8000", "--server.address=0.0.0.0", "--server.headless=true"]
```

#### Build and Push to Azure Container Registry

```bash
# Create ACR
az acr create --resource-group sales-advisor-rg --name salesadvisoracr --sku Basic

# Build and push image
az acr build --registry salesadvisoracr --image sales-advisor:latest .

# Create Web App from container
az webapp create --resource-group sales-advisor-rg --plan sales-advisor-plan --name sales-advisor-app --deployment-container-image-name salesadvisoracr.azurecr.io/sales-advisor:latest
```

---

## Troubleshooting

### App Not Starting

1. Check logs in Azure Portal: **Web App** → **Log stream**
2. Verify all environment variables are set correctly
3. Ensure `startup.sh` has execute permissions
4. Check that `Cline_stats.json` and `qualitative_stats.json` are included in deployment

### Port Issues

- Azure App Service expects the app to listen on port 8000 (configured in `startup.sh`)
- Streamlit is configured to use port 8000 in the startup script

### Missing Dependencies

- Ensure `requirements.txt` includes all necessary packages
- Check build logs in Deployment Center

### Environment Variables Not Loading

- Verify all variables are set in **Configuration** → **Application settings**
- Restart the Web App after adding/changing settings

### File Not Found Errors

- Ensure `Cline_stats.json` and `qualitative_stats.json` are in the same directory as `streamlit_app.py`
- Check file paths in the code use relative paths

---

## Post-Deployment

### Enable HTTPS

Azure Web Apps come with free SSL certificates. HTTPS is enabled by default.

### Custom Domain (Optional)

1. Go to **Custom domains** in your Web App
2. Add your custom domain
3. Configure DNS records as instructed

### Scaling

1. Go to **Scale up (App Service plan)** to change pricing tier
2. Go to **Scale out (App Service plan)** to add instances

### Monitoring

1. Enable **Application Insights** for monitoring and diagnostics
2. View metrics in **Monitoring** → **Metrics**

---

## Security Best Practices

1. **Never commit `.env` files** to version control
2. Use **Azure Key Vault** for sensitive credentials
3. Enable **Managed Identity** for Azure resource access
4. Restrict access using **Authentication/Authorization** settings
5. Use **Private Endpoints** for Azure services if needed

---

## Cost Optimization

- Use **B1 Basic** tier for development/testing
- Scale to **S1 Standard** or higher for production
- Enable **Auto-scaling** based on metrics
- Monitor costs in **Cost Management**

---

## Support

For issues or questions:
- Check Azure App Service documentation
- Review Streamlit deployment guides
- Check application logs for errors

---

## Quick Reference

**App URL**: `https://<your-app-name>.azurewebsites.net`

**Required Files**:
- `streamlit_app.py` - Main application
- `requirements.txt` - Python dependencies
- `startup.sh` - Startup script
- `Cline_stats.json` - Statistics data
- `qualitative_stats.json` - Qualitative insights data
- `.deployment` - Deployment configuration

**Environment Variables**:
- `OPEN_AI_KEY`
- `OPEN_AI_ENDPOINT`
- `SEARCH_ENDPOINT`
- `SEARCH_KEY`
- `INDEX_NAME`
- `EMBEDDING_MODEL`
- `CHAT_MODEL`

