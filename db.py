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

# To find calorie content of food before eating
def find_calorie(food_item):
    template = """What is the calorie content of {food_item}? I just want the numbers and no text."""
    prompt = PromptTemplate(template=template, input_variables=["food_item"])

    try:
        model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
        llm_chain = LLMChain(llm=model, prompt=prompt)
        return llm_chain.run(food_item=food_item)
    
    except Exception as e:
        st.error(f"Error generating calorie content: {e}")
        return None

# Extract calories data and store in MongoDB
def extract_calories(food_item):
    date = datetime.now().strftime("%d/%m/%Y")
    template = """What is the calorie content of {food_item} just the food ignore the time? I want the name of the food and calorie content in JSON format."""
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

# Insert data into MongoDB
def add_to_mongo(food_data):
    try:
        collection.insert_many(food_data)
        st.success("Food data added to database.")
    except Exception as e:
        st.error(f"Error inserting data into MongoDB: {e}")

# Retrieve consumed foods for the current date
def get_consumed_foods():
    try:
        today = datetime.now().strftime("%d/%m/%Y")
        return list(collection.find({"date": today}, {"_id": 0})) 
    except Exception as e:
        st.error(f"Error retrieving data from MongoDB: {e}")
        return []

# Calculate daily calorie needs based on user inputs
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

# Retrieve monthly calorie data
def get_monthly_consumption():
    try:
        today = datetime.now()
        start_of_month = today.replace(day=1)
        records = list(collection.find({"date": {"$gte": start_of_month.strftime("%d/%m/%Y"), "$lte": today.strftime("%d/%m/%Y")}}, {"_id": 0}))
        return records
    except Exception as e:
        st.error(f"Error retrieving monthly data from MongoDB: {e}")
        return []

# Calculate daily calorie totals for the month
def calculate_daily_totals(records):
    daily_totals = {}
    for record in records:
        date = record['date']
        calories = record['calories']
        daily_totals[date] = daily_totals.get(date, 0) + calories
    return daily_totals

# Nutritionist Tab
def nutritionist():
    st.title("Personal AI Nutritionist")
    col1, spacer, col2 = st.columns([5, 0.3, 2], gap="large")

    with col1:
        with st.container():
            st.subheader("Enter Food Item")
            food_input = st.text_input("Enter the food and quantity:", placeholder="e.g., 1 apple, 200g rice").strip()

            col_left, col_right = st.columns([1, 1])
            with col_left:
                if st.button("Find"):
                    if food_input:
                        result = find_calorie(food_input)
                        st.write("Calorie Content:", result if result else "Could not retrieve calorie information.")
                    else:
                        st.warning("Please enter a valid food item.")
            with col_right:
                if st.button("Ate"):
                    if food_input:
                        dict_result = extract_calories(food_input)
                        add_to_mongo(dict_result if dict_result else [])
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

    with col2:
        st.subheader("Calorie Calculator")
        weight = st.number_input("Weight (kg)", min_value=0.0)
        height = st.number_input("Height (cm)", min_value=0.0)
        age = st.number_input("Age", min_value=0)
        gender = st.selectbox("Gender", ["male", "female"])

        activity_level = st.selectbox(
            "Activity Level",
            options=[
                ("Sedentary", 1.2),
                ("Lightly active", 1.375),
                ("Moderately active", 1.55),
                ("Very active", 1.725),
                ("Super active", 1.9)
            ],
            format_func=lambda x: x[0]
        )
        if st.button("Calculate Daily Calories"):
            tdee = calculate_daily_calories(weight, height, age, gender, activity_level[1])
            st.write(f"Estimated Daily Caloric Needs: {tdee:.2f} calories" if tdee else "")

# Dashboard Tab
def dashboard():
    st.title("Calorie Consumption Dashboard")
    user_profile = {
        "height": 170,
        "weight": 70,
        "activity_level": "Moderately active",
        "calorie_limit": 2000
    }
    st.subheader("User Profile")
    col1, col2, col3, col4 = st.columns(4)
    user_profile['height'] = st.number_input("Height (cm)", value=user_profile['height'])
    user_profile['weight'] = st.number_input("Weight (kg)", value=user_profile['weight'])
    user_profile['activity_level'] = st.selectbox(
        "Workout Level",
        ["Sedentary", "Lightly active", "Moderately active", "Very active", "Super active"],
        index=["Sedentary", "Lightly active", "Moderately active", "Very active", "Super active"].index(user_profile['activity_level'])
    )
    user_profile['calorie_limit'] = st.number_input("Daily Calorie Limit", value=user_profile['calorie_limit'], min_value=0)

    st.subheader("Calorie Consumption This Month")
    records = get_monthly_consumption()
    daily_totals = calculate_daily_totals(records)
    df = pd.DataFrame.from_dict(daily_totals, orient="index", columns=["Calories"])

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df.index, y=df["Calories"], mode="lines", name="Daily Calories"))
    fig1.update_layout(
        title="Daily Caloric Intake",
        xaxis_title="Date",
        yaxis_title="Calories"
    )
    st.plotly_chart(fig1)

    st.subheader("Today's Consumption")
    today_total = daily_totals.get(datetime.now().strftime("%d/%m/%Y"), 0)
    fig2 = go.Figure(data=[
        go.Pie(labels=["Calories Consumed", "Remaining"], values=[today_total, user_profile['calorie_limit'] - today_total])
    ])
    fig2.update_layout(title="Today's Calorie Breakdown")
    st.plotly_chart(fig2)

    st.subheader("Calorie Limit Streak")
    streak_count = sum(1 for total in daily_totals.values() if total <= user_profile['calorie_limit'])
    st.write(f"You've stayed within your calorie limit for {streak_count} consecutive days!")

# Main Code Execution
tab1, tab2 = st.tabs(["Nutritionist", "Dashboard"])
with tab1:
    nutritionist()
with tab2:
    dashboard()
