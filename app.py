import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
import json


load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))


consumed_foods = []

def find_calorie(food_item):
    """Generate a chain to find calorie content of food items."""
    template = """What is the calorie content of {food_item}? I just want the numbers and no text. 
    If there are multiple foods, give the calories of each and the total as well, with the foods bulleted 
    one below the other."""
    
    prompt = PromptTemplate(template=template, input_variables=["food_item"])

    try:
        model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
        llm_chain = LLMChain(llm=model, prompt=prompt)
        return llm_chain.run(food_item=food_item)

    except Exception as e:
        st.error(f"Error generating calorie content: {e}")
        return None


def extract_calories(food_item):
    """Extract food items and their calorie counts from the result as a dictionary."""
    template = """What is the calorie content of {food_item}? I want the name of the food and calorie content in the form 
    of a dictionary. Example: [{{"item": "Apple", "calories": 95}}, {{"item": "Banana", "calories": 105}}]"""  # Escaped braces

    prompt = PromptTemplate(template=template, input_variables=["food_item"])

    try:
        model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)

        llm_chain = prompt | model
        result = llm_chain.invoke({"food_item": food_item})
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
                # Append the result to the consumed_foods list
                consumed_foods.extend(dict_result)  # Add all items to the consumed_foods list
                st.success(f"Added: {dict_result}")
            else:
                st.warning("Could not retrieve calorie information.")
        else:
            st.warning("Please enter a valid food item.")
    

    # Display the consumed foods
    if consumed_foods:
        total_calories = sum(food['calories'] for food in consumed_foods)
        
        # Create a list of dictionaries for consumed foods and their calorie counts
        data = [{"Food Item": food['item'], "Calories": food['calories']} for food in consumed_foods]
        
        # Append the total to the list as a dictionary
        data.append({"Food Item": "Total", "Calories": total_calories})
        
        # Display the data as a table
        st.table(data)
    else:
        st.write("No food items consumed yet.")

if __name__ == "__main__":
    main()
