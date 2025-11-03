#!/bin/bash

# Navigate to the app directory
cd /home/site/wwwroot

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Start Streamlit app
streamlit run streamlit_app.py --server.port 8000 --server.address 0.0.0.0 --server.headless true

