import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
import july
from july.utils import date_range
from nutrition import calculate_daily_totals, get_consumed_foods

# Load environment variables
load_dotenv(dotenv_path=".env")

# MongoDB setup
MONGO_CLIENT = os.getenv("MONGO_CLIENT")
DATABASE = os.getenv("DATABASE")
USER_COLLECTION = os.getenv("USER_COLLECTION")
FOOD_COLLECTION = os.getenv("FOOD_COLLECTION")

client = MongoClient(MONGO_CLIENT)
db = client[DATABASE]
user_collection = db[USER_COLLECTION]
food_collection = db[FOOD_COLLECTION]


def dashboard():
    # # Ensure the user is logged in
    # if "user_email" not in st.session_state:
    #     st.warning("Please log in first.")
    #     return


    # records = food_collection.find({"user_email": user_email})
    # new_user = pd.DataFrame(records)

    # # Check if data is empty
    # if new_user.empty:
    #     st.info("No food data available. Start logging your meals!")
    #     return

    # Ensure the user is logged in
    if "user_email" not in st.session_state or not st.session_state.user_email:
        st.warning("Please log in first.")
        return

    # Access user_email from session state
    user_email = st.session_state.user_email

    # Retrieve data based on the user's email
    records = food_collection.find({"user_email": user_email})
    new_user = pd.DataFrame(records)

    # Check if data is empty
    if new_user.empty:
        st.info("No food data available. Start logging your meals!")
        return

    # Fetch user profile and food data
    user_email = st.session_state["user_email"]
    user_profile = user_collection.find_one({"email": user_email})
    records = food_collection.find({"user_email": user_email})
    data = pd.DataFrame(records)

    # Display user dashboard
    st.title(f"{user_profile.get('username', 'User')} Nutrition Dashboard")
    st.write(f"Logged in as: {user_email}")

    # Profile update section
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        height = st.number_input("Height (cm)", value=int(user_profile.get("height", 0)), step=1)
    with col2:
        weight = st.number_input("Weight (kg)", value=int(user_profile.get("weight", 0)), step=1)
    with col3:
        activity_level = st.selectbox(
            "Activity Level",
            ["Sedentary", "Lightly active", "Moderately active", "Very active", "Super active"],
            index=["Sedentary", "Lightly active", "Moderately active", "Very active", "Super active"]
            .index(user_profile.get("activity_level", "Moderately active"))
        )
    with col4:
        calorie_limit = st.number_input("Calorie Limit", value=int(user_profile.get("calorie_limit", 0)), step=1)

    if st.button("Update Profile"):
        update_result = user_collection.update_one(
            {"email": user_email},
            {
                "$set": {
                    "height": str(height),
                    "weight": str(weight),
                    "activity_level": activity_level,
                    "calorie_limit": calorie_limit
                }
            }
        )
        if update_result.modified_count > 0:
            st.success("Profile updated successfully!")
        else:
            st.info("No changes were made.")

    # Calculate limits and totals
    gender = user_profile.get("gender", "Male")
    sugar_limit = 36 if gender == "Male" else 25

    foods_data, display_foods = get_consumed_foods(user_email)
    totals = calculate_daily_totals(foods_data)

    # Calorie and Sugar Pie Charts
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(generate_pie_chart("Calorie", calorie_limit, totals["total_calories"]))
    with col2:
        st.plotly_chart(generate_pie_chart("Sugar", sugar_limit, totals["total_sugar"]))

    # Daily Calories Line Chart
    data["date"] = pd.to_datetime(data["date"], format="%d/%m/%Y")
    daily_calories = data.groupby("date")["calories"].sum().reset_index()
    st.line_chart(daily_calories.set_index("date"))

    # Nutritional Balance Radar Chart
    nutrient_limits = {
        "Sugar": sugar_limit,
        "Carbs": 300,
        "Protein": 60,
        "Fat": 70
    }
    # consumed_nutrients = {
    #     "Sugar": totals["total_sugar"],
    #     "Carbs": totals["total_carbs"],
    #     "Protein": totals["total_protein"],
    #     "Fat": totals["total_fat"]
    # }

    consumed_nutrients = {
    "Sugar": round(totals["total_sugar"], 2),
    "Carbs": round(totals["total_carbs"], 2),
    "Protein": round(totals["total_protein"], 2),
    "Fat": round(totals["total_fat"], 2)
}


    col1, col2 = st.columns([2,1])
    with col1:
        st.plotly_chart(generate_radar_chart(nutrient_limits, consumed_nutrients))
    with col2:
        st.header("Daily Nutritional Summary")
        summary_df = pd.DataFrame(list(consumed_nutrients.items()), columns=["Nutrient", "Amount"])
        st.table(summary_df)

    # Feedback Section
    exceeded_nutrients = [
        nutrient for nutrient, value in consumed_nutrients.items()
        if value > nutrient_limits[nutrient]
    ]
    if exceeded_nutrients:
        st.warning(f"You have exceeded your limits for: {', '.join(exceeded_nutrients)}")
    else:
        st.success("Great job! You are within your nutritional limits.")

    data["date"] = pd.to_datetime(data["date"])

    # Define the current date and calculate six months ago
    today = datetime.today()
    six_months_ago = today - timedelta(days=6 * 30)

    # Generate a full date range for the past six months
    full_date_range = pd.date_range(six_months_ago, today, freq="D")

    # Group by date and sum calories (strip time to match granularity)
    data["date"] = data["date"].dt.date  # Keep only the date part
    daily_calories = (
        data.groupby("date")["calories"]
        .sum()
        .reset_index()
        .rename(columns={"calories": "daily_calories"})
    )

    # Create a DataFrame for the full date range
    full_date_range_df = pd.DataFrame({"date": full_date_range})
    full_date_range_df["date"] = full_date_range_df["date"].dt.date  # Keep only the date part

    # Merge the full date range with daily calorie data
    merged_daily_calories = (
        full_date_range_df
        .merge(daily_calories, on="date", how="left")
        .fillna(0)  
    )

    merged_daily_calories["daily_calories"] = merged_daily_calories["daily_calories"].astype(int)

    # Print outputs
    # print("Full Date Range (Head):\n", full_date_range_df.head())
    # print("\nDaily Calories (Merged):\n", merged_daily_calories.tail())
    # print("\nToday's Total Calories:\n", daily_calories.loc[daily_calories["date"] == today.date(), "daily_calories"].sum())

    max_calories = merged_daily_calories["daily_calories"].max()
    merged_daily_calories["normalized_calories"] = merged_daily_calories["daily_calories"] / max_calories

    # Extract date and normalized calorie values
    heatmap_dates = merged_daily_calories["date"]
    heatmap_values = merged_daily_calories["normalized_calories"].values

    # Create the heatmap
    heatmap = july.heatmap(
        heatmap_dates,
        heatmap_values,
        title="Calorie Consumption",
        cmap="github"
    )
    st.pyplot(heatmap.get_figure())


def generate_pie_chart(title, limit, consumed):
    labels = ["Total", "Consumed"]
    values = [limit, consumed]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.5)])
    fig.update_layout(annotations=[{"text": title, "x": 0.5, "y": 0.5, "font_size": 20, "showarrow": False}])
    return fig


def generate_radar_chart(nutrient_limits, consumed_nutrients):
    normalized_values = [
        consumed_nutrients[nutrient] / nutrient_limits[nutrient]
        for nutrient in nutrient_limits.keys()
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=normalized_values + [normalized_values[0]],  # Close the loop
        theta=list(nutrient_limits.keys()) + [list(nutrient_limits.keys())[0]],
        fill='toself',
        name='Consumed'
    ))
    fig.add_trace(go.Scatterpolar(
        r=[1] * len(nutrient_limits) + [1],  # Reference circle for limits
        theta=list(nutrient_limits.keys()) + [list(nutrient_limits.keys())[0]],
        mode='lines',
        name='Limit'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(max(normalized_values), 1.5)])),
        showlegend=True,
        title="Nutritional Balance Radar Chart"
    )
    return fig


if __name__ == "__main__":
    dashboard()
