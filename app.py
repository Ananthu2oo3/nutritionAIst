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


load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))


client = MongoClient("mongodb://localhost:27017")
db = client["nutritionAIst"]
collection = db["calorie"]



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
    print(date)
    
    template = """What is the calorie content of {food_item} just the food ignore the time? I want the name of the food and 
    calorie content in the form of a dictionary. Today's date is {date}, change the date according to the context with respect to 
    today's date and write it in DD/MM/YYYY format Example: [{{"date":"DD/MM/YYYY", "item": "Apple", "calories": 95}}, 
    {{"date":"DD/MM/YYYY", "item": "Banana", "calories": 105}}]."""
     
    prompt = PromptTemplate(template=template, input_variables=["food_item", "date"])

    try:
        model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
        llm_chain = LLMChain(llm=model, prompt=prompt)
        result = llm_chain.run(food_item=food_item, date=date)

        # Display raw AI response for debugging
        st.write("Raw AI Response:", result)

        # Parse JSON response from AI
        food_data = json.loads(result)
        return food_data
    except json.JSONDecodeError:
        st.error("Error parsing AI response. Ensure the response is in the correct JSON format.")
    except Exception as e:
        st.error(f"Error during model execution: {e}")
    return None

# Define the function to insert consumed food data into MongoDB
def add_to_mongo(food_data):
    try:
        collection.insert_many(food_data)
        st.success("Food data added to database.")
    except Exception as e:
        st.error(f"Error inserting data into MongoDB: {e}")

# Retrieve consumed foods from MongoDB
def get_consumed_foods():
    try:
        return list(collection.find({}, {"_id": 0}))  # Exclude MongoDB’s default '_id' field
    except Exception as e:
        st.error(f"Error retrieving data from MongoDB: {e}")
        return []

# Define the nutritionist application logic
def nutritionist():
    st.title("Personal AI Nutritionist")
    food_input = st.text_input("Enter the food and quantity:").strip()

    if st.button("Find"):
        if food_input:
            result = find_calorie(food_input)
            if result:
                st.write("Calorie Content:", result)
            else:
                st.warning("Could not retrieve calorie information.")
        else:
            st.warning("Please enter a valid food item.")

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
    
    # Display consumed foods in a table
    consumed_foods = get_consumed_foods()
    if consumed_foods:
        total_calories = sum(food['calories'] for food in consumed_foods)
        data = [{"Date": food['date'], "Food Item": food['item'], "Calories": food['calories']} 
                for food in consumed_foods]
        data.append({"Date": "", "Food Item": "Total", "Calories": total_calories})

        st.table(data)
    else:
        st.write("No food items consumed yet.")

# Define an empty dashboard page
def dashboard():
    st.title("Dashboard")
    st.write("This is an empty dashboard page.")

# Main application function
def main():
    st.sidebar.title("Navigation")
    option = st.sidebar.radio("Go to", ["Nutritionist", "Dashboard"])

    if option == "Nutritionist":
        nutritionist()
    elif option == "Dashboard":
        dashboard()

if __name__ == "__main__":
    main()
