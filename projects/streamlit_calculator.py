import streamlit as st

def calculator():
    st.title("Streamlit Calculator")
    
    # Create input fields for numbers
    col1, col2, col3 = st.columns(3)
    with col1:
        num1 = st.number_input("Enter first number")
    with col2:
        operation = st.selectbox("Select operation", [ '+', '-', '*', '/' ]) 
    with col3:
        num2 = st.number_input("Enter second number")
    
    if st.button('Calculate'):
        try:
            if operation == '+':
                result = num1 + num2
            elif operation == '-':
                result = num1 - num2
            elif operation == '*':
                result = num1 * num2
            elif operation == '/':
                if num2 != 0:
                    result = num1 / num2
                else:
                    result = "Error: Division by zero"
            
            st.write(f"Result: {result}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

def main():
    calculator()

if __name__ == "__main__":
    main()