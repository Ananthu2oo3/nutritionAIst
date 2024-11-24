import streamlit as st
from auth import login, sign_up
from nutrition import nutritionist
from dash import dashboard
from health_safety import health

def app():
    st.sidebar.title("Navigation")

    # Initialize session state variables
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "user_email" not in st.session_state:
        st.session_state.user_email = ""

    # Check login state
    if not st.session_state.logged_in:
        auth_option = st.sidebar.radio("Choose", ["Log In", "Sign Up"])
        if auth_option == "Log In":
            login()
        elif auth_option == "Sign Up":
            sign_up()
    else:
        option = st.sidebar.radio("Navigate", ["Dashboard", "Nutritionist", "Food Quality","Log Out"])

        if option == "Dashboard":
            dashboard()
        elif option == "Nutritionist":
            nutritionist()
        elif option == "Food Quality":
            health()
        elif option == "Log Out":
            st.session_state.clear()
            st.success("You have been logged out.")
            st.experimental_rerun()

if __name__ == "__main__":
    app()
