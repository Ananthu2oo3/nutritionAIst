import os
import json
import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime


load_dotenv()
MONGO_CLIENT = os.getenv("MONGO_CLIENT")
DATABASE = os.getenv("DATABASE")
FOOD_COLLECTION = os.getenv("FOOD_COLLECTION")

client = MongoClient(MONGO_CLIENT)
db = client[DATABASE]
food_collection = db[FOOD_COLLECTION]


def add_to_mongo(food_data, user_email):
    try:
        
        food_data["user_email"] = user_email
        food_collection.insert_one(food_data)
        st.success("Food data successfully added to the database.")

    except Exception as e:
        st.error(f"Error: {e}")



def get_consumed_foods(email):
    try:
        today = datetime.now().strftime("%d/%m/%Y")
        # Get all documents for the user from today
        foods = list(food_collection.find(
            {
                "date": today,
                "user_email": email
            },
            {"_id": 0}
        ))
        

        display_foods = []
        for food in foods:
            display_food = {
                "Item": food["item"],
                "Calories": food["calories"],
                "Carbs": food["carbs"],
                "Protein": food["protein"],
                "Fat": food["fat"],
                "Sugar": food["sugar_content"]
            }
            display_foods.append(display_food)
            
        return foods, display_foods  
        
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return [], []


def find_calorie(food_item):
    template = "What is the calorie content of {food_item}? Provide only the numeric value."
    prompt = PromptTemplate(template=template, input_variables=["food_item"])
    try:
        model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
        chain = LLMChain(llm=model, prompt=prompt)
        result = chain.run(food_item=food_item)
        # Clean the result to get only numeric value
        return result.strip()
    except Exception as e:
        st.error(f"Error: {e}")
        return None
    

def extract_calories(food_item):
    date = datetime.now().strftime("%d/%m/%Y")
    
    # Modified template to ensure numeric values without units in JSON
    template = """
    I want the calorie content, carbohydrates, proteins, fats, and sugar content of {food_item}.
    Today's date is {date}. Provide ONLY the JSON data in this exact format, using NUMBERS WITHOUT UNITS:
    {{
        "date": "{date}",
        "item": "{food_item}",
        "calories": in mg,
        "sugar_content": in mg,
        "carbs": in mg,
        "protein": in mg,
        "fat": in mg
    }}
    """
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["food_item", "date"]
    )

    try:
        model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
        llm_chain = LLMChain(llm=model, prompt=prompt)
        result = llm_chain.run(food_item=food_item, date=date)

        # Clean the response before parsing
        result = result.strip()
        
        # Log raw response for debugging
        st.write("Raw AI Response:", result)
        
        # Parse JSON response
        food_data = json.loads(result)
        
 
        numeric_fields = ["calories", "sugar_content", "carbs", "protein", "fat"]
        for field in numeric_fields:
            if not isinstance(food_data[field], (int, float)):
                raise ValueError(f"{field} must be a number")
                
        return food_data
    
    except json.JSONDecodeError as e:
        st.error(f"Error parsing AI response: {str(e)}")
        st.write("Problematic response:", result)
    except Exception as e:
        st.error(f"Error during model execution: {str(e)}")
    
    return None



def calculate_daily_totals(foods):
    totals = {
        "total_calories": 0,
        "total_carbs": 0,
        "total_protein": 0,
        "total_fat": 0,
        "total_sugar": 0
    }
    
    for food in foods:
        try:
            
            def extract_number(value):
                if isinstance(value, (int, float)):
                    return float(value)
                elif isinstance(value, str):
                    
                    return float(''.join(c for c in value if c.isdigit() or c == '.'))
                return 0

            totals["total_calories"] += extract_number(food["calories"])
            totals["total_carbs"] += extract_number(food["carbs"])
            totals["total_protein"] += extract_number(food["protein"])
            totals["total_fat"] += extract_number(food["fat"])
            totals["total_sugar"] += extract_number(food["sugar_content"])
                    
        except (ValueError, KeyError) as e:
            st.warning(f"Skipping invalid entry: {food.get('item', 'unknown food')}")
            continue
    
    return totals


def nutritionist():
    st.title("Nutritionist")
    
    if "user_email" not in st.session_state:
        st.warning("Please log in first.")
        return

    user_email = st.session_state["user_email"]
    st.write(f"Logged in as: {user_email}")

    st.subheader("Log your food items")
    food_item = st.text_input("Enter food item with quantity (e.g., '100g rice' or '1 apple')")

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Find Calories"):
            if food_item:
                result = find_calorie(food_item)
                if result:
                    st.write("Calories:", result)
    
    with col2:
        if st.button("Add to Consumed List"):
            if food_item:
                data = extract_calories(food_item)
                if data:
                    add_to_mongo(data, user_email)

    st.subheader("Today's Consumed Foods")
    foods_data, display_foods = get_consumed_foods(user_email)
    
    if display_foods:  
        
        st.table(display_foods)
        
        try:
            totals = calculate_daily_totals(foods_data)
            st.subheader("Daily Totals")
            st.write(f"Total Calories: {totals['total_calories']:.1f} kcal")
            st.write(f"Total Carbs: {totals['total_carbs']:.1f} g")
            st.write(f"Total Protein: {totals['total_protein']:.1f} g")
            st.write(f"Total Fat: {totals['total_fat']:.1f} g")
            st.write(f"Total Sugar: {totals['total_sugar']:.1f} g")
        except Exception as e:
            st.error(f"Error calculating totals: {str(e)}")

    else:
        st.write("No foods logged today.")