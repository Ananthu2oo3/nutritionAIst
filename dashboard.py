import os
import json
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# MongoDB client setup
client = MongoClient("mongodb://localhost:27017")
db = client["nutritionAIst"]
collection = db["calorie"]

# Function to fetch monthly calorie consumption data
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
def render_dashboard():
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
    option = st.sidebar.radio("Go to", ["Dashboard"])

    if option == "Dashboard":
        render_dashboard()

if __name__ == "__main__":
    main()
