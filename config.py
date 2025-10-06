# Configuration file for Databricks credentials
# Copy this file to config.py and update with your actual credentials
import os

from dotenv import load_dotenv

load_dotenv()
    
    # Check for Databricks token (may already be loaded in environment)
databricks_token = os.getenv("DATABRICKS_TOKEN")

DATABRICKS_CONFIG = {
    'token': databricks_token,  # Replace with your actual Databricks token
    'endpoints': {
        'claude-sonnet-4': 'https://dbc-3735add4-1cb6.cloud.databricks.com/serving-endpoints/databricks-claude-sonnet-4/invocations',
        'llama-3-70b': 'https://dbc-3735add4-1cb6.cloud.databricks.com/serving-endpoints/databricks-meta-llama-3-3-70b-instruct/invocations'
    }
}

# Instructions to get Databricks token:
# 1. Go to your Databricks workspace
# 2. Click on your user profile (top right)
# 3. Go to User Settings
# 4. Go to Access Tokens tab
# 5. Generate new token
# 6. Copy the token and replace 'YOUR_DATABRICKS_TOKEN_HERE' above
