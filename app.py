import streamlit as st
import pandas as pd
import joblib

# --- Load the Saved Model and Columns ---
model = joblib.load('model/property_price_predictor.pkl')
model_columns = joblib.load('model/model_columns.pkl')

# --- App Title and Description ---
st.title(' Cardiff Property Price Predictor')
st.write('This app uses an XGBoost model to predict property prices in Cardiff based on your inputs.')

# --- Create Input Fields for User ---
st.header('Enter Property Details')

# Create columns for a cleaner layout
col1, col2 = st.columns(2)

with col1:
    bedrooms = st.number_input('Bedrooms', min_value=1, max_value=10, value=3, step=1)
    bathrooms = st.number_input('Bathrooms', min_value=1, max_value=10, value=1, step=1)
    
with col2:
    # Use hardcoded lists based on your data exploration
    property_type = st.selectbox('Property Type', options=['Flat', 'Terraced', 'Semi-Detached', 'Detached', 'Apartment', 'Bungalow'])
    tenure = st.selectbox('Tenure', options=['FREEHOLD', 'LEASEHOLD'])

# --- Prediction Logic ---
if st.button('Predict Price'):
    try:
        # Create a DataFrame for the input data with all the model columns
        input_df = pd.DataFrame(columns=model_columns)
        # Add a single row of zeros
        input_df.loc[0] = 0

        # --- Set the user's input values ---
        # Note: We are not using latitude/longitude as user inputs for simplicity
        input_df['bedrooms'] = bedrooms
        input_df['bathrooms'] = bathrooms
        
        # --- Set the one-hot encoded columns ---
        # Set the correct property_type column to 1
        prop_type_col = 'property_type_' + property_type
        if prop_type_col in input_df.columns:
            input_df[prop_type_col] = 1
        
        # Set the correct tenure column to 1
        tenure_col = 'tenure_' + tenure
        if tenure_col in input_df.columns:
            input_df[tenure_col] = 1

        # Make sure all columns are in the correct order
        input_df = input_df[model_columns]
        
        # Make the prediction
        prediction = model.predict(input_df)[0]
        
        # Display the result
        st.success(f'Predicted Property Price: £{prediction:,.0f}')
        
    except Exception as e:
        st.error(f"An error occurred: {e}")