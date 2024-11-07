import os
import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
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





# Nutritionist Tab 
def nutritionist():
    st.title("Personal AI Nutritionist")

    # Define the layout with columns
    # col1 = st.columns([5], gap="large")  # col1 takes more space for center layout

    # Food input and calorie information in the main column (col1)
    # with col1:
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

    # # Daily calorie needs calculation in the side column (col2)
    # with col2:
    #     st.subheader("Calorie Calculator")
    #     weight = st.number_input("Weight (kg)", min_value=0.0)
    #     height = st.number_input("Height (cm)", min_value=0.0)
    #     age = st.number_input("Age", min_value=0)
    #     gender = st.selectbox("Gender", ["male", "female"])

    #     # Activity level dropdown with multiplier values
    #     activity_level = st.selectbox(
    #         "Activity Level",
    #         options=[
    #             ("Sedentary (little or no exercise)", 1.2),
    #             ("Lightly active (light exercise/sports 1-3 days/week)", 1.375),
    #             ("Moderately active (moderate exercise/sports 3-5 days/week)", 1.55),
    #             ("Very active (hard exercise/sports 6-7 days a week)", 1.725),
    #             ("Super active (very hard exercise & physical job)", 1.9)
    #         ],
    #         format_func=lambda x: x[0]
    #     )

    #     if st.button("Calculate Daily Calories"):
    #         tdee = calculate_daily_calories(weight, height, age, gender, activity_level[1])
    #         if tdee:
    #             st.write(f"Estimated Daily Caloric Needs: {tdee:.2f} calories")






def fetch_monthly_calorie_data():
    try:
        today = datetime.now()
        start_of_month = today.replace(day=1)
        records = list(collection.find(
            {"date": {"$gte": start_of_month.strftime("%d/%m/%Y"), "$lte": today.strftime("%d/%m/%Y")}},
            {"_id": 0}
        ))
        return records
    except Exception as e:
        st.error(f"Error retrieving monthly data from MongoDB: {e}")
        return []




# Calculate total calories for each day in the month
def calculate_daily_calorie_totals(records):
    daily_calories = {}
    for record in records:
        date = record['date']
        calories = record['calories']
        daily_calories[date] = daily_calories.get(date, 0) + calories
    return daily_calories




# Function to calculate daily calorie limit based on BMR and activity level
def calculate_daily_calorie_limit(weight, height, activity_level):
    # Basal Metabolic Rate (BMR) calculation using Mifflin-St Jeor Equation
    bmr = 10 * weight + 6.25 * height - 5 * 25 + 5  # Assuming age 25, male; adjust as needed
    activity_multipliers = {
        "Sedentary": 1.2,
        "Lightly active": 1.375,
        "Moderately active": 1.55,
        "Very active": 1.725,
        "Super active": 1.9
    }
    return int(bmr * activity_multipliers.get(activity_level, 1.2))




# Dashboard Tab
def dashboard():
    st.title("Calorie Consumption Dashboard")

    # Mock user profile for demo purposes
    user_profile = {
        "height": 170,
        "weight": 70,
        "activity_level": "Moderately active"
    }

    # Editable User Profile Section
    st.subheader("User Profile")
    col1, col2, col3 = st.columns(3)
    with col1:
        user_profile['height'] = st.number_input("Height (cm)", value=user_profile['height'])
    with col2:
        user_profile['weight'] = st.number_input("Weight (kg)", value=user_profile['weight'])
    with col3:
        user_profile['activity_level'] = st.selectbox(
            "Activity Level",
            ["Sedentary", "Lightly active", "Moderately active", "Very active", "Super active"],
            index=["Sedentary", "Lightly active", "Moderately active", "Very active", "Super active"].index(user_profile['activity_level'])
        )

    # Calculate calorie limit based on user inputs
    user_profile['calorie_limit'] = calculate_daily_calorie_limit(
        weight=user_profile['weight'],
        height=user_profile['height'],
        activity_level=user_profile['activity_level']
    )

    # Display calculated daily calorie limit
    st.write(f"**Calculated Daily Calorie Limit:** {user_profile['calorie_limit']} calories")

    # Calorie Consumption for the Current Month
    st.subheader("Calorie Consumption This Month")
    monthly_records = fetch_monthly_calorie_data()
    daily_totals = calculate_daily_calorie_totals(monthly_records)
    monthly_data_df = pd.DataFrame.from_dict(daily_totals, orient='index', columns=['Calories'])
    st.line_chart(monthly_data_df)

    # Today's Calorie Consumption Donut Chart
    calories_consumed_today = daily_totals.get(datetime.now().strftime("%d/%m/%Y"), 0)
    calories_remaining_today = max(0, user_profile['calorie_limit'] - calories_consumed_today)
    st.subheader(f"Today's Calorie Consumption ({calories_consumed_today}/{user_profile['calorie_limit']} calories)")
    fig = go.Figure(data=[go.Pie(
        labels=['Calories Consumed', 'Calories Remaining'],
        values=[calories_consumed_today, calories_remaining_today],
        hole=0.7
    )])
    fig.update_layout(showlegend=True, title_text="Calorie Consumption vs. Limit")
    st.plotly_chart(fig)

    # Streak Calculation for Days within Calorie Limit
    st.subheader("Calorie Limit Streak")
    streak_days = 0
    is_streak_active = True
    for date in sorted(daily_totals.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"), reverse=True):
        if daily_totals[date] <= user_profile['calorie_limit']:
            if is_streak_active:
                streak_days += 1
        else:
            is_streak_active = False
    st.write(f"You have stayed within your calorie limit for {streak_days} day(s) in a row.")


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
