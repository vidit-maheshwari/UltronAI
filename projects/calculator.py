import streamlit as st

title = "Streamlit Calculator"

st.title(title)

# Function to handle calculations
def calculator():
    expression = st.text_input('Expression:', '')
    
    # Create columns for buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button('7'): expression += '7'
        if st.button('4'): expression += '4'
        if st.button('1'): expression += '1'
        if st.button('C'): expression = ''

    with col2:
        if st.button('8'): expression += '8'
        if st.button('5'): expression += '5'
        if st.button('2'): expression += '2'
        if st.button('0'): expression += '0'

    with col3:
        if st.button('9'): expression += '9'
        if st.button('6'): expression += '6'
        if st.button('3'): expression += '3'
        if st.button('.'): expression += '."

    with col4:
        if st.button('÷'): expression += '/'
        if st.button('×'): expression += '*'
        if st.button('-'): expression += '-'
        if st.button('+'): expression += '+'
        if st.button('='): 
            try:
                result = eval(expression)
                expression = str(result)

    st.write("Result: ", expression)

# Call the calculator function
calculator()

# Run the app using: streamlit run calculator.py