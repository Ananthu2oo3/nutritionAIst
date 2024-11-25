import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, date
import bcrypt
import os
import re

# Load environment variables
load_dotenv()
MONGO_CLIENT = os.getenv("MONGO_CLIENT")
DATABASE = os.getenv("DATABASE")
USER_COLLECTION = os.getenv("USER_COLLECTION")

client = MongoClient(MONGO_CLIENT)
db = client[DATABASE]
users_collection = db[USER_COLLECTION]

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')



def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))



def is_email_exists(email):
    return users_collection.find_one({"email": email}) is not None



def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None



def calculate_age(dob):
    if not dob or not isinstance(dob, date):  
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def calculate_calorie(gender,weight,height,age,activity_level):
    weight = float(weight)
    height = float(height)
    age    = float(age)

    activity_multipliers = {
        "Sedentary"         : 1.2,
        "Lightly active"    : 1.375,
        "Moderately active" : 1.55,
        "Very active"       : 1.725,
        "Super active"      : 1.9
    }


    if(gender == "Male"):
        bmr = 10 * weight + 6.25 * height - 5 * age + 5 
        calorie_limit = int(bmr * activity_multipliers.get(activity_level, 1.2))
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161   
        calorie_limit = int(bmr * activity_multipliers.get(activity_level, 1.2))
    
    return calorie_limit


def sign_up():
    st.title("Sign Up")
    username = st.text_input("Username", placeholder="Enter your username")
    email = st.text_input("Email", placeholder="Enter your email")
    gender = st.radio("Select your gender:", ("Male", "Female"))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        height = st.text_input("Height (cm)", placeholder="Enter your height")
    with col2:
        weight = st.text_input("Weight (kg)", placeholder="Enter your weight")
    with col3:
        activity_level = st.selectbox("Activity Level",["Sedentary", "Lightly active", "Moderately active", "Very active", "Super active"])


    dob = st.date_input("Enter your date of birth:", min_value=datetime(1900, 1, 1))
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
    submit = st.button("Sign Up")

    if submit:
        if not all([username, email, password, confirm_password]):
            st.error("All fields are required.")
            return
        if not validate_email(email):
            st.error("Invalid email format.")
            return
        if password != confirm_password:
            st.error("Passwords do not match.")
            return
        if is_email_exists(email):
            st.error("An account with this email already exists.")
            return

        hashed_pw = hash_password(password)
        age = calculate_age(dob)
        calorie_limit = calculate_calorie(gender,weight,height,age,activity_level)
        users_collection.insert_one({
            "username": username,
            "email"         : email,
            "gender"        : gender,
            "height"        : height,
            "weight"        : weight,
            "activity_level": activity_level,
            "dob"           : datetime.combine(dob, datetime.min.time()),
            "calorie_limit" : calorie_limit,
            "password"      : hashed_pw
        })
        st.success("Account created successfully! You can now log in.")
        st.info("Switch to the Log In tab to access your account.")

def login():
    st.title("Log In")
    email = st.text_input("Email", placeholder="Enter your email")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    submit = st.button("Log In")

    if submit:
        if not email or not password:
            st.error("Both email and password are required.")
            return

        user = users_collection.find_one({"email": email})
        if not user:
            st.error("No account found with this email.")
            return
        if not check_password(password, user["password"]):
            st.error("Incorrect password.")
            return

        st.session_state["logged_in"] = True
        st.session_state["username"] = user["username"]
        st.session_state["user_email"] = user["email"]
        st.success(f"Welcome back, {user['username']}!")
        
