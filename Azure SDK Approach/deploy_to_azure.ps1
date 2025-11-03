# Azure Web App Deployment Script for Streamlit Sales Recommendation Advisor
# Run this script from PowerShell

Write-Host "🚀 Azure Web App Deployment Script" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Configuration - EDIT THESE VALUES
$RESOURCE_GROUP = Read-Host "Enter Resource Group Name (e.g., sales-app-rg)"
$APP_NAME = Read-Host "Enter Web App Name (must be globally unique, e.g., sales-rec-app-123)"
$LOCATION = Read-Host "Enter Azure Region (e.g., eastus, westus2, westeurope)"

Write-Host ""
Write-Host "📋 Configuration Summary:" -ForegroundColor Yellow
Write-Host "  Resource Group: $RESOURCE_GROUP"
Write-Host "  App Name: $APP_NAME"
Write-Host "  Location: $LOCATION"
Write-Host ""

$confirm = Read-Host "Continue with deployment? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "❌ Deployment cancelled." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Step 1: Logging in to Azure..." -ForegroundColor Green
az login

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Azure login failed. Please try again." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Step 2: Creating Resource Group..." -ForegroundColor Green
az group create --name $RESOURCE_GROUP --location $LOCATION

Write-Host ""
Write-Host "Step 3: Creating App Service Plan..." -ForegroundColor Green
$APP_SERVICE_PLAN = "$APP_NAME-plan"
az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --sku B1 --is-linux

Write-Host ""
Write-Host "Step 4: Creating Web App..." -ForegroundColor Green
az webapp create --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --name $APP_NAME --runtime "PYTHON:3.11"

Write-Host ""
Write-Host "Step 5: Configuring startup command..." -ForegroundColor Green
az webapp config set --resource-group $RESOURCE_GROUP --name $APP_NAME --startup-file "bash startup.sh"

Write-Host ""
Write-Host "Step 6: Setting environment variables..." -ForegroundColor Green
Write-Host "⚠️  You need to provide your Azure credentials:" -ForegroundColor Yellow
Write-Host ""

$OPEN_AI_KEY = Read-Host "Enter OPEN_AI_KEY"
$OPEN_AI_ENDPOINT = Read-Host "Enter OPEN_AI_ENDPOINT"
$SEARCH_ENDPOINT = Read-Host "Enter SEARCH_ENDPOINT"
$SEARCH_KEY = Read-Host "Enter SEARCH_KEY"
$INDEX_NAME = Read-Host "Enter INDEX_NAME"
$EMBEDDING_MODEL = Read-Host "Enter EMBEDDING_MODEL (e.g., text-embedding-ada-002)"
$CHAT_MODEL = Read-Host "Enter CHAT_MODEL (e.g., gpt-4)"

az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $APP_NAME --settings `
    OPEN_AI_KEY="$OPEN_AI_KEY" `
    OPEN_AI_ENDPOINT="$OPEN_AI_ENDPOINT" `
    SEARCH_ENDPOINT="$SEARCH_ENDPOINT" `
    SEARCH_KEY="$SEARCH_KEY" `
    INDEX_NAME="$INDEX_NAME" `
    EMBEDDING_MODEL="$EMBEDDING_MODEL" `
    CHAT_MODEL="$CHAT_MODEL" `
    SCM_DO_BUILD_DURING_DEPLOYMENT="true" `
    WEBSITE_HTTPLOGGING_RETENTION_DAYS="7"

Write-Host ""
Write-Host "Step 7: Creating deployment package..." -ForegroundColor Green
$deployPath = "deploy.zip"
if (Test-Path $deployPath) {
    Remove-Item $deployPath -Force
}

Compress-Archive -Path streamlit_app.py,Cline_stats.json,qualitative_stats.json,requirements.txt,startup.sh,.streamlit -DestinationPath $deployPath -Force

Write-Host ""
Write-Host "Step 8: Deploying code to Azure..." -ForegroundColor Green
az webapp deployment source config-zip --resource-group $RESOURCE_GROUP --name $APP_NAME --src $deployPath

Write-Host ""
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Your app will be available at:" -ForegroundColor Cyan
Write-Host "   https://$APP_NAME.azurewebsites.net" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏳ Please wait 2-3 minutes for the app to start..." -ForegroundColor Yellow
Write-Host ""
Write-Host "📊 To view logs:" -ForegroundColor Yellow
Write-Host "   1. Go to Azure Portal: https://portal.azure.com"
Write-Host "   2. Navigate to your Web App: $APP_NAME"
Write-Host "   3. Click 'Log stream' in the left menu"
Write-Host ""

$openBrowser = Read-Host "Open app in browser now? (yes/no)"
if ($openBrowser -eq "yes") {
    az webapp browse --resource-group $RESOURCE_GROUP --name $APP_NAME
}

Write-Host ""
Write-Host "🎉 Deployment script completed!" -ForegroundColor Green
Write-Host ""

