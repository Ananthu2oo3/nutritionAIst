import streamlit as st
import pytesseract
from PIL import Image
import cv2
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Define the function to rate food based on ingredients
def find_quality(ingredients):
    
    template = """These are the ingredients of a packed food product: {ingredients}. Rate the food out of 100 on how healthy 
    the product is with the help of its ingredients. Provide a clear justification for the rating in a given format 
    specifying numbers for sugar content, preservatives, nutritional value, and health issues this product might cause.
    
    Output format:
    {{
        "health_rating": <number>,
        "sugar_content": <number>,
        "preservatives": <number>,
        "nutritional_value": <number>,
        "health_issues": ["List of health issues"],
        "Justification": ["List of justification]
    }}
    """
    
    prompt = PromptTemplate(template=template, input_variables=["ingredients"])

    try:
        model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
        llm_chain = LLMChain(llm=model, prompt=prompt)
        response = llm_chain.run(ingredients=ingredients)

        st.write("### Debug: Raw Response")  # Debugging line
        st.text(response)  # Display raw response for troubleshooting
        
        # Check if the response is valid JSON
        try:
            rating_json = json.loads(response)  # Safely parse JSON
            return rating_json  # Return the parsed JSON
        except json.JSONDecodeError:
            st.error("Received non-JSON response. Please check the model output.")
            return None

    except Exception as e:
        st.error(f"Error generating health rating: {e}")
        return None

# Main function for the Streamlit app
def health():
    st.title("Food Product Health Rating using OCR")
    st.write("Upload an image of a food product's ingredient list to rate its health quality based on the ingredients.")

    # File uploader to upload an image
    uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        
        # Convert image to OpenCV format for processing
        opencv_image = np.array(image)
        opencv_image = cv2.cvtColor(opencv_image, cv2.COLOR_RGB2BGR)
        
        # Extract text from the image using OCR
        extracted_text = pytesseract.image_to_string(opencv_image)
        
        # Check if any text was extracted
        if extracted_text.strip():
            st.write("**Health Rating Based on Ingredients:**")
            rating_result = find_quality(extracted_text)
            
            # Parse the JSON result if it's not empty
            if rating_result:
                total_rating = rating_result.get("health_rating", 0)
                sugar_content = rating_result.get("sugar_content", 0)
                preservatives = rating_result.get("preservatives", 0)
                nutritional_value = rating_result.get("nutritional_value", 0)
                health_issues = rating_result.get("health_issues", [])  # Changed to list

                # Display metric cards
                col1, col2, col3 = st.columns(3)
                col1.metric("Sugar Content", f"{sugar_content}%", "High" if sugar_content > 50 else "Low")
                col2.metric("Preservatives", f"{preservatives}%", "High" if preservatives > 50 else "Low")
                col3.metric("Nutritional Value", f"{nutritional_value}%", "Good" if nutritional_value > 50 else "Low")

                # Display health issues as a bullet list
                if health_issues:  # Check if there are any health issues
                    st.write("### Health Issues:")
                    for issue in health_issues:  # Loop through health issues list
                        st.write(f"- **{issue}**")

                # Pie chart of total rating distribution
                fig, ax = plt.subplots()
                labels = ['Health Rating', 'Remaining']
                sizes = [total_rating, 100 - total_rating]
                colors = ['#4CAF50', '#FF6347']
                ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax.axis('equal')
                st.pyplot(fig)

            else:
                st.error("Received an empty response. Please try again.")
        else:
            st.error("No text detected in the image. Please try with a clearer image.")

# Run the health function if the script is executed
if __name__ == "__main__":
    health()
