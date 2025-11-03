#!/bin/bash

# Bash script to deploy Streamlit app to Azure App Service
# Usage: ./deploy_azure.sh

# Configuration - UPDATE THESE VALUES
RESOURCE_GROUP="sales-advisor-rg"
APP_NAME="sales-advisor-app"
LOCATION="eastus"
APP_SERVICE_PLAN="sales-advisor-plan"
SKU="B1"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting deployment to Azure...${NC}"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}Azure CLI is not installed. Please install it from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli${NC}"
    exit 1
fi

# Prompt for environment variables
read -p "Enter your Azure OpenAI Key: " OPEN_AI_KEY
read -p "Enter your Azure OpenAI Endpoint: " OPEN_AI_ENDPOINT
read -p "Enter your Azure Cognitive Search Endpoint: " SEARCH_ENDPOINT
read -p "Enter your Azure Cognitive Search Key: " SEARCH_KEY
read -p "Enter your Search Index Name: " INDEX_NAME
read -p "Enter your Embedding Model Deployment Name: " EMBEDDING_MODEL
read -p "Enter your Chat Model Deployment Name: " CHAT_MODEL

# Login to Azure
echo -e "${YELLOW}Logging in to Azure...${NC}"
az login

# Create Resource Group
echo -e "${YELLOW}Creating resource group...${NC}"
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create App Service Plan
echo -e "${YELLOW}Creating App Service Plan...${NC}"
az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --sku $SKU --is-linux

# Create Web App
echo -e "${YELLOW}Creating Web App...${NC}"
az webapp create --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --name $APP_NAME --runtime "PYTHON:3.11"

# Configure startup command
echo -e "${YELLOW}Configuring startup command...${NC}"
az webapp config set --resource-group $RESOURCE_GROUP --name $APP_NAME --startup-file "startup.sh"

# Set environment variables
echo -e "${YELLOW}Setting environment variables...${NC}"
az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $APP_NAME --settings \
  OPEN_AI_KEY="$OPEN_AI_KEY" \
  OPEN_AI_ENDPOINT="$OPEN_AI_ENDPOINT" \
  SEARCH_ENDPOINT="$SEARCH_ENDPOINT" \
  SEARCH_KEY="$SEARCH_KEY" \
  INDEX_NAME="$INDEX_NAME" \
  EMBEDDING_MODEL="$EMBEDDING_MODEL" \
  CHAT_MODEL="$CHAT_MODEL" \
  SCM_DO_BUILD_DURING_DEPLOYMENT="true" \
  WEBSITE_STARTUP_FILE="startup.sh"

# Deploy code
echo -e "${YELLOW}Deploying application code...${NC}"
az webapp up --resource-group $RESOURCE_GROUP --name $APP_NAME --runtime "PYTHON:3.11"

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${CYAN}Your app is available at: https://$APP_NAME.azurewebsites.net${NC}"

# Ask to open browser
read -p "Do you want to open the app in your browser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open "https://$APP_NAME.azurewebsites.net"
    elif command -v open &> /dev/null; then
        open "https://$APP_NAME.azurewebsites.net"
    else
        echo "Please open https://$APP_NAME.azurewebsites.net in your browser"
    fi
fi

