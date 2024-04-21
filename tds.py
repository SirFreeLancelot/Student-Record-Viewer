import streamlit as st

st.title("Find Max Number of Three Numbers")

col1, col2, col3 = st.columns(3)

with col1:
    num1 = st.number_input("Enter the first number")

with col2:
    num2 = st.number_input("Enter the second number")

with col3:
    num3 = st.number_input("Enter the third number")

st.write(f"The maximum number is {max(num1, num2, num3)}")