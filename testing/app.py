import streamlit as st
from nutrition import nutritionist
from dashboard import dashboard
from health_safety import health

def main():
    st.sidebar.title("Navigation")
    option = st.sidebar.radio("Go to", ["Nutritionist", "Dashboard","Nutrition Quality"])

    if option == "Nutritionist":
        nutritionist()
    elif option == "Dashboard":
        dashboard()
    elif option == "Nutrition Quality":
        health()

if __name__ == "__main__":
    main()
