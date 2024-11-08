import os
import json
import streamlit as st
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Connect to MongoDB
client = MongoClient(os.getenv('MONGO_CLIENT'))
db = client[os.getenv('DATABASE')]
collection = db[os.getenv('COLLECTION')]

# Functions

def find_calorie(food_item):
    template = """What is the calorie content of {food_item}? I just want the numbers and no text.
    If there are multiple foods, give the calories of each and the total as well, with the foods bulleted 
    one below the other. Ignore any time information, just mention the calories."""
    
    prompt = PromptTemplate(template=template, input_variables=["food_item"])

    try:
        model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
        llm_chain = LLMChain(llm=model, prompt=prompt)
        return llm_chain.run(food_item=food_item)
    
    except Exception as e:
        st.error(f"Error generating calorie content: {e}")
        return None


def extract_calories(food_item):
    date = datetime.now().strftime("%d/%m/%Y")
    
    template = """What is the calorie content of {food_item} just the food ignore the time? I want the name of the food and 
    calorie content in the form of a dictionary. Today's date is {date}, change the date according to the context with respect to 
    today's date and write it in DD/MM/YYYY format Example: 
    [{{"date":"DD/MM/YYYY", "item": "Apple", "calories": 95,"Suger content": 10 mg,"Carbs: " 20 mg, "Protein":15 mg, "fat" : 30 mg}}, 
    {{"date":"DD/MM/YYYY", "item": "Banana", "calories": 105, "Suger content": 30 mg,"Carbs: " 200 mg, "Protein":15 mg, "fat" : 13 mg}}]."""
    
    prompt = PromptTemplate(template=template, input_variables=["food_item", "date"])

    try:
        model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
        llm_chain = LLMChain(llm=model, prompt=prompt)
        result = llm_chain.run(food_item=food_item, date=date)

        st.write("Raw AI Response:", result)
        food_data = json.loads(result)
        return food_data
    
    except json.JSONDecodeError:
        st.error("Error parsing AI response. Ensure the response is in the correct JSON format.")
    except Exception as e:
        st.error(f"Error during model execution: {e}")
    return None


def add_to_mongo(food_data):
    try:
        collection.insert_many(food_data)
        st.success("Food data added to database.")
    except Exception as e:
        st.error(f"Error inserting data into MongoDB: {e}")


def get_consumed_foods():
    try:
        today = datetime.now().strftime("%d/%m/%Y")
        return list(collection.find({"date": today}, {"_id": 0})) 
    except Exception as e:
        st.error(f"Error retrieving data from MongoDB: {e}")
        return []


def nutritionist():
    st.title("Personal AI Nutritionist")

    st.subheader("Enter Food Item")
    food_input = st.text_input("Enter the food and quantity:", placeholder="e.g., 1 apple, 200g rice").strip()

    col_left, col_right = st.columns([1, 1])
    with col_left:
        if st.button("Find"):
            if food_input:
                result = find_calorie(food_input)
                if result:
                    st.write("Calorie Content:", result)
                else:
                    st.warning("Could not retrieve calorie information.")
            else:
                st.warning("Please enter a valid food item.")

    with col_right:
        if st.button("Ate"):
            if food_input:
                dict_result = extract_calories(food_input)
                if dict_result:
                    add_to_mongo(dict_result)
                    st.success(f"Added: {dict_result}")
                else:
                    st.warning("Could not retrieve calorie information.")
            else:
                st.warning("Please enter a valid food item.")

    st.subheader("Today's Consumed Foods")
    consumed_foods = get_consumed_foods()
    if consumed_foods:
        total_calories = sum(food['calories'] for food in consumed_foods)
        data = [{"Date": food['date'], "Food Item": food['item'], "Calories": food['calories']} 
                for food in consumed_foods]
        data.append({"Date": "", "Food Item": "Total", "Calories": total_calories})
        st.table(data)
    else:
        st.write("No food items consumed yet.")
