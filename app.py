import os
import json
import streamlit as st
import google.generativeai as genai

from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI


from datetime import datetime


load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))


consumed_foods = []

def find_calorie(food_item):
    """Generate a chain to find calorie content of food items."""
    template = """What is the calorie content of {food_item}? I just want the numbers and no text. 
    If there are multiple foods, give the calories of each and the total as well, with the foods bulleted 
    one below the other. If time is mentioned ignore it just mentiopn the calorie"""
    
    prompt = PromptTemplate(template=template, input_variables=["food_item"])

    try:
        model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
        llm_chain = LLMChain(llm=model, prompt=prompt)
        return llm_chain.run(food_item=food_item)

    except Exception as e:
        st.error(f"Error generating calorie content: {e}")
        return None


def extract_calories(food_item):

    date = datetime.now().date()

    template = """What is the calorie content of {food_item} just the food ignore the time?I want the name of the food and 
    calorie content in the form of a dictionary.Todays date is {date}, change the date accoding to the context with respect to 
    todays date and write it in DD/MM/YYYY format Example: [{{"date":"DD/MM/YYYY", "item": "Apple", "calories": 95}}, 
    {{"date":"DD/MM/YYYY", "item": "Banana", "calories": 105}}]."""

    prompt = PromptTemplate(template=template, input_variables=["food_item","date"])

    try:
        model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)

        llm_chain = prompt | model
        result = llm_chain.invoke({"food_item": food_item, "date": date})
        print("Model run successful")
        
        # Print the result for debugging
        st.write("Raw AI Response:", result.content) 

        food_data = json.loads(result.content) 
        return food_data

    except Exception as e:
        st.error(f"Error during model execution: {e}")  
        return None


def main():
    st.title("Personal AI Nutritionist")
    food_input = st.text_input("Enter the food and quantity:").strip()

    if st.button("Find"):
        if food_input:
            result = find_calorie(food_input)
            if result:
                st.write("Calorie Content:\n", result)
            else:
                st.warning("Could not retrieve calorie information.")
        else:
            st.warning("Please enter a valid food item.")

    if st.button("Ate"):
        if food_input:
            dict_result = extract_calories(food_input)
            if dict_result:
                consumed_foods.extend(dict_result)  
                st.success(f"Added: {dict_result}")

            else:
                st.warning("Could not retrieve calorie information.")
        else:
            st.warning("Please enter a valid food item.")
    

    # Display the consumed foods
    if consumed_foods:
        total_calories = sum(food['calories'] for food in consumed_foods)
        
        data = [{"Date": food['date'], "Food Item": food['item'], "Calories": food['calories']} for food in consumed_foods]
        data.append({"Food Item": "Total", "Calories": total_calories})
        
        # Display the data as a table
        st.table(data)
    else:
        st.write("No food items consumed yet.")

if __name__ == "__main__":
    main()
