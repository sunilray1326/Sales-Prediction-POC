# PowerShell script to deploy Streamlit app to Azure App Service
# Usage: .\deploy_azure.ps1

# Configuration - UPDATE THESE VALUES
$RESOURCE_GROUP = "sales-advisor-rg"
$APP_NAME = "sales-advisor-app"
$LOCATION = "eastus"
$APP_SERVICE_PLAN = "sales-advisor-plan"
$SKU = "B1"

# Environment Variables - UPDATE THESE VALUES
$OPEN_AI_KEY = Read-Host "Enter your Azure OpenAI Key"
$OPEN_AI_ENDPOINT = Read-Host "Enter your Azure OpenAI Endpoint"
$SEARCH_ENDPOINT = Read-Host "Enter your Azure Cognitive Search Endpoint"
$SEARCH_KEY = Read-Host "Enter your Azure Cognitive Search Key"
$INDEX_NAME = Read-Host "Enter your Search Index Name"
$EMBEDDING_MODEL = Read-Host "Enter your Embedding Model Deployment Name"
$CHAT_MODEL = Read-Host "Enter your Chat Model Deployment Name"

Write-Host "Starting deployment to Azure..." -ForegroundColor Green

# Check if Azure CLI is installed
try {
    az --version | Out-Null
} catch {
    Write-Host "Azure CLI is not installed. Please install it from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Red
    exit 1
}

# Login to Azure
Write-Host "Logging in to Azure..." -ForegroundColor Yellow
az login

# Create Resource Group
Write-Host "Creating resource group..." -ForegroundColor Yellow
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create App Service Plan
Write-Host "Creating App Service Plan..." -ForegroundColor Yellow
az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --sku $SKU --is-linux

# Create Web App
Write-Host "Creating Web App..." -ForegroundColor Yellow
az webapp create --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --name $APP_NAME --runtime "PYTHON:3.11"

# Configure startup command
Write-Host "Configuring startup command..." -ForegroundColor Yellow
az webapp config set --resource-group $RESOURCE_GROUP --name $APP_NAME --startup-file "startup.sh"

# Set environment variables
Write-Host "Setting environment variables..." -ForegroundColor Yellow
az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $APP_NAME --settings `
  OPEN_AI_KEY="$OPEN_AI_KEY" `
  OPEN_AI_ENDPOINT="$OPEN_AI_ENDPOINT" `
  SEARCH_ENDPOINT="$SEARCH_ENDPOINT" `
  SEARCH_KEY="$SEARCH_KEY" `
  INDEX_NAME="$INDEX_NAME" `
  EMBEDDING_MODEL="$EMBEDDING_MODEL" `
  CHAT_MODEL="$CHAT_MODEL" `
  SCM_DO_BUILD_DURING_DEPLOYMENT="true" `
  WEBSITE_STARTUP_FILE="startup.sh"

# Deploy code
Write-Host "Deploying application code..." -ForegroundColor Yellow
az webapp up --resource-group $RESOURCE_GROUP --name $APP_NAME --runtime "PYTHON:3.11"

Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "Your app is available at: https://$APP_NAME.azurewebsites.net" -ForegroundColor Cyan

# Open the app in browser
$openBrowser = Read-Host "Do you want to open the app in your browser? (Y/N)"
if ($openBrowser -eq "Y" -or $openBrowser -eq "y") {
    Start-Process "https://$APP_NAME.azurewebsites.net"
}

