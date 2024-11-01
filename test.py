# import os
# import streamlit as st
# import google.generativeai as genai
# from dotenv import load_dotenv
# from langchain.prompts import PromptTemplate
# from langchain.chains import LLMChain
# from langchain_google_genai import ChatGoogleGenerativeAI
# import re

# # Load environment variables
# load_dotenv()
# genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# # List to store consumed food items and their calorie counts
# consumed_foods = []

# def find_calorie():
#     """Generate a chain to find calorie content of food items."""
#     template = """What is the calorie content of {food_item}? I just want the numbers and no text. 
#     If there are multiple foods, give the calories of each and the total as well, with the foods bulleted 
#     one below the other."""
    
#     prompt = PromptTemplate(template=template, input_variables=["food_item"])

#     try:
#         model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
#         llm_chain = LLMChain(llm=model, prompt=prompt)
#         return llm_chain

#     except Exception as e:
#         st.error(f"Error initializing the AI model: {e}")
#         return None

# def extract_calories(result):
#     """Extract food items and their calorie counts from the result."""
#     calories = result.splitlines()
#     for line in calories:
#         if line.strip():  # Check if line is not empty
#             # Use regex to find the numeric part of the calorie count
#             match = re.search(r'(\d+)\s*calories?', line, re.IGNORECASE)
#             if match:
#                 item = line.split(":")[0].strip()  # Get the food item
#                 calorie_count = int(match.group(1))  # Extract numeric value
#                 consumed_foods.append((item, calorie_count))

# def main():
#     st.title("Calorie Content Finder")
#     food_input = st.text_input("Enter the food and quantity:").strip()

#     chain = find_calorie()

#     if st.button("Find"):
#         if food_input:
#             if chain:
#                 try:
#                     result = chain.run(food_item=food_input)
#                     st.write("Calorie Content:\n", result)

#                     # Extract calories and append to consumed_foods list
#                     extract_calories(result)

#                 except Exception as e:
#                     st.error(f"Error generating calorie content: {e}")
#             else:
#                 st.error("Chain could not be created. Check configuration.")
#         else:
#             st.write("Please enter a valid food item.")

#     # ATE button to display the table of consumed foods
#     if st.button("ATE"):
#         if consumed_foods:
#             total_calories = sum(calorie for _, calorie in consumed_foods)
#             # Create a table to display consumed foods and their calorie counts
#             data = [(item, calorie) for item, calorie in consumed_foods]
#             data.append(("Total", total_calories))
#             st.table(data)
#         else:
#             st.write("No food items consumed yet.")

# if __name__ == "__main__":
#     main()



import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
import re


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
        st.error(f"Error initializing the AI model: {e}")
        return None

# def extract_calories(result):
    # """Extract food items and their calorie counts from the result."""
    # calories = result.splitlines()
    # for line in calories:
    #     if line.strip():  
    #         match = re.search(r'(\d+)\s*calories?', line, re.IGNORECASE)
    #         if match:
    #             item = line.split(":")[0].strip()  # Get the food item
    #             calorie_count = int(match.group(1))  # Extract numeric value
    #             consumed_foods.append((item, calorie_count))


def extract_calories(food_item):

    template = """What is the calorie content of {food_item}? I want the name of the food and calorie content in the form 
    of a dictioinary. example: {"item": "Apple", "calories": 95}, {"item": "Banana", "calories": 105}"""
    prompt = PromptTemplate(template=template, input_variables=["food_item"])

    try:
        model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
        llm_chain = LLMChain(llm=model, prompt=prompt)
        return llm_chain.run(food_item=food_item)

    except Exception as e:
        st.error(f"Error initializing the AI model: {e}")
        return None


def main():
    st.title("Personal AI nutritionist")
    food_input = st.text_input("Enter the food and quantity:").strip()

    if st.button("Find"):
        if food_input:
            result = find_calorie(food_input)
            if result:
                st.write("Calorie Content:\n", result)
                # Extract calories and append to consumed_foods list
                # extract_calories(result)
            else:
                st.warning("Could not retrieve calorie information.")
        else:
            st.write("Please enter a valid food item.")


    if st.button("ATE"):
        if food_input:  
            dict = extract_calories(food_input)
            consumed_foods.append(dict)
            print(consumed_foods)
        else:
            st.warning("Could not retrieve calorie information.")

    # # Display the consumed foods
    # if consumed_foods:
    #     total_calories = sum(calorie for _, calorie in consumed_foods)
    #     # Create a table to display consumed foods and their calorie counts
    #     data = [(item, calorie) for item, calorie in consumed_foods]
    #     data.append(("Total", total_calories))
    #     st.table(data)
    # else:
    #     st.write("No food items consumed yet.")

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

