To be able to deploy the Web App correctly, need to determine the Python packages we are using in the Streamlit App along with 
Streamlit version. Use below commands to determine the versions of the packages used in the Streamlit App.


Determine the version of azure-core
=====================================
pip show azure-core
Name: azure-core
Version: 1.35.1

Determine the version of azure-search-documents
================================================
pip show azure-search-documents
Name: azure-search-documents
Version: 11.6.0

Determine the version of OpenAI
================================
pip show openai
Name: openai
Version: 2.3.0

Determine the version of python-dotenv
=======================================
pip show python-dotenv
Name: python-dotenv
Version: 1.1.1

Determine the version of streamlit
===================================
pip show streamlit
Name: streamlit
Version: 1.51.0

Create ZIP File 
tar -a -c -f "streamlitapp.zip" streamlit_app.py requirements.txt quantitative_stats.json qualitative_stats.json 

Create Resource Group and where to cretae, location like East US
Not Executed ==> az group create --name rg-sunil --location eastus
I already have rg-sunil resource Group created and going to same for this web app, so not creating a new resource group. 

Create App Service Plan
az appservice plan create --name salesadvplan --resource-group rg-sunil --sku B1 --is-linux

Create the web app
az webapp create --resource-group rg-sunil --plan salesadvplan --name salesadv --runtime "PYTHON|3.13.9"

Set start up command
az webapp config appsettings set --resource-group rg-sunil --name salesadv --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true WEBSITE_NODE_DEFAULT_VERSION=18.17.0 STARTUP_COMMAND="streamlit run --server.port $PORT --server.address 0.0.0.0 --server.headless true streamlit_app.py"

Enable application monitoring insights
az monitor app-insights component create --app salesadv --location eastus --resource-group rg-sunil

Deploy the code
az webapp deployment source config-zip --resource-group rg-sunil --name salesadv --src streamlitapp.zip

Get URL of the deployed web app
az webapp show --resource-group rg-sunil --name salesadv --query defaultHostName

