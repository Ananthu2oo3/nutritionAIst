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



# To find the calorie before eating
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





# To find and add in DB
def extract_calories(food_item):
    date = datetime.now().strftime("%d/%m/%Y")
    
    
    template = """What is the calorie content of {food_item} just the food ignore the time? I want the name of the food and 
    calorie content in the form of a dictionary. Today's date is {date}, change the date according to the context with respect to 
    today's date and write it in DD/MM/YYYY format Example: [{{"date":"DD/MM/YYYY", "item": "Apple", "calories": 95}}, 
    {{"date":"DD/MM/YYYY", "item": "Banana", "calories": 105}}]."""
     
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





# Insert to DB
def add_to_mongo(food_data):
    try:
        collection.insert_many(food_data)
        st.success("Food data added to database.")
    except Exception as e:
        st.error(f"Error inserting data into MongoDB: {e}")






# Retrieve from DB
def get_consumed_foods():
    try:
        today = datetime.now().strftime("%d/%m/%Y")
        print(today)
        return list(collection.find({"date": today}, {"_id": 0})) 
    
    except Exception as e:
        st.error(f"Error retrieving data from MongoDB: {e}")
        return []




# Calorie needs calculator
def calculate_daily_calories(weight, height, age, gender, activity_multiplier):
    if gender.lower() == 'male':
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    elif gender.lower() == 'female':
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    else:
        st.error("Invalid gender input. Please enter 'male' or 'female'.")
        return None
    
    tdee = bmr * activity_multiplier
    return tdee

# # nutritionist Tab
# def nutritionist():
#     st.title("Personal AI Nutritionist")
#     food_input = st.text_input("Enter the food and quantity:").strip()

#     if st.button("Find"):
#         if food_input:
#             result = find_calorie(food_input)
#             if result:
#                 st.write("Calorie Content:", result)
#             else:
#                 st.warning("Could not retrieve calorie information.")
#         else:
#             st.warning("Please enter a valid food item.")

#     if st.button("Ate"):
#         if food_input:
#             dict_result = extract_calories(food_input)
#             if dict_result:
#                 add_to_mongo(dict_result)
#                 st.success(f"Added: {dict_result}")
#             else:
#                 st.warning("Could not retrieve calorie information.")
#         else:
#             st.warning("Please enter a valid food item.")

#     # Display consumed foods in a table
#     consumed_foods = get_consumed_foods()
#     col1, col2 = st.columns(2)
    
#     # Consumed foods table
#     with col1:
#         st.subheader("Today's Consumed Foods")
#         if consumed_foods:
#             total_calories = sum(food['calories'] for food in consumed_foods)
#             data = [{"Date": food['date'], "Food Item": food['item'], "Calories": food['calories']} 
#                     for food in consumed_foods]
#             data.append({"Date": "", "Food Item": "Total", "Calories": total_calories})
#             st.table(data)
#         else:
#             st.write("No food items consumed yet.")

#     # Daily calorie needs calculation
#     with col2:
#         st.subheader("Daily Calorie Needs Calculator")
#         weight = st.number_input("Weight (kg)", min_value=0.0)
#         height = st.number_input("Height (cm)", min_value=0.0)
#         age = st.number_input("Age", min_value=0)
#         gender = st.selectbox("Gender", ["male", "female"])

#         # Activity level dropdown with multiplier values
#         activity_level = st.selectbox(
#             "Activity Level",
#             options=[
#                 ("Sedentary (little or no exercise)", 1.2),
#                 ("Lightly active (light exercise/sports 1-3 days/week)", 1.375),
#                 ("Moderately active (moderate exercise/sports 3-5 days/week)", 1.55),
#                 ("Very active (hard exercise/sports 6-7 days a week)", 1.725),
#                 ("Super active (very hard exercise & physical job)", 1.9)
#             ],
#             format_func=lambda x: x[0]
#         )
        
#         if st.button("Calculate Daily Calories"):
#             tdee = calculate_daily_calories(weight, height, age, gender, activity_level[1])
#             if tdee:
#                 st.write(f"Estimated Daily Caloric Needs: {tdee:.2f} calories")



# Nutritionist Tab with Improved UI
def nutritionist():
    st.title("Personal AI Nutritionist")

    # Define the layout with columns
    col1, spacer, col2 = st.columns([5, 0.3, 2], gap="large")  # col1 takes more space for center layout

    # Food input and calorie information in the main column (col1)
    with col1:
        with st.container():
            # Center-aligned text input and buttons
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

            # Display consumed foods in a table
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

    # Daily calorie needs calculation in the side column (col2)
    with col2:
        st.subheader("Calorie Calculator")
        weight = st.number_input("Weight (kg)", min_value=0.0)
        height = st.number_input("Height (cm)", min_value=0.0)
        age = st.number_input("Age", min_value=0)
        gender = st.selectbox("Gender", ["male", "female"])

        # Activity level dropdown with multiplier values
        activity_level = st.selectbox(
            "Activity Level",
            options=[
                ("Sedentary (little or no exercise)", 1.2),
                ("Lightly active (light exercise/sports 1-3 days/week)", 1.375),
                ("Moderately active (moderate exercise/sports 3-5 days/week)", 1.55),
                ("Very active (hard exercise/sports 6-7 days a week)", 1.725),
                ("Super active (very hard exercise & physical job)", 1.9)
            ],
            format_func=lambda x: x[0]
        )

        if st.button("Calculate Daily Calories"):
            tdee = calculate_daily_calories(weight, height, age, gender, activity_level[1])
            if tdee:
                st.write(f"Estimated Daily Caloric Needs: {tdee:.2f} calories")




# nutritionist Tab
# def nutritionist():

#     st.title("Personal AI Nutritionist")
#     food_input = st.text_input("Enter the food and quantity:").strip()
    
#     if st.button("Find"):
#         if food_input:
#             result = find_calorie(food_input)
#             if result:
#                 st.write("Calorie Content:", result)
#             else:
#                 st.warning("Could not retrieve calorie information.")
#         else:
#             st.warning("Please enter a valid food item.")


#     if st.button("Ate"):
#         if food_input:
#             dict_result = extract_calories(food_input)
#             if dict_result:
#                 add_to_mongo(dict_result)
#                 st.success(f"Added: {dict_result}")
#             else:
#                 st.warning("Could not retrieve calorie information.")
#         else:
#             st.warning("Please enter a valid food item.")
    
#     # Display consumed foods in a table
#     consumed_foods = get_consumed_foods()
#     if consumed_foods:
#         total_calories = sum(food['calories'] for food in consumed_foods)
#         data = [{"Date": food['date'], "Food Item": food['item'], "Calories": food['calories']} 
#                 for food in consumed_foods]
#         data.append({"Date": "", "Food Item": "Total", "Calories": total_calories})

#         st.table(data)
#     else:
#         st.write("No food items consumed yet.")




# Dashboard Page
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
