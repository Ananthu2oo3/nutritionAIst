# NutritionAIst


## Create an Environment
conda create -p venv python==3.12


## Active ENV
conda activate venv/


## Install requirements
pip install -r requirements.txt


## Setup ENV

Create a .env file

    GOOGLE_API_KEY = "api_key"
    MONGO_CLIENT = "mongo_connection_link"
    DATABASE = "db_name"
    COLLECTION = "collection_name"

## Run

streamlit run app.py