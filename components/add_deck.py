import streamlit as st
from datetime import datetime
from database import db

def render_add_deck():
    st.header("Add New Deck")
    
    with st.form("add_deck_form"):
        deck_name = st.text_input("Deck Name*", key="deck_name")
        manufacturer = st.text_input("Manufacturer*", key="manufacturer")
        release_year = st.number_input("Release Year", 
                                     min_value=1800, 
                                     max_value=datetime.now().year,
                                     value=datetime.now().year)
        
        condition = st.selectbox("Condition", 
                               ["Mint", "Near Mint", "Excellent", "Good", "Fair", "Poor"])
        
        purchase_date = st.date_input("Purchase Date")
        purchase_price = st.number_input("Purchase Price ($)", 
                                       min_value=0.0, 
                                       step=0.01)
        
        notes = st.text_area("Notes")
        image_file = st.file_uploader("Deck Image", type=['png', 'jpg', 'jpeg'])
        
        submit = st.form_submit_button("Add Deck")
        
        if submit:
            if not deck_name or not manufacturer:
                st.error("Deck name and manufacturer are required!")
                return
            
            deck_data = {
                'deck_name': deck_name,
                'manufacturer': manufacturer,
                'release_year': release_year,
                'condition': condition,
                'purchase_date': purchase_date,
                'purchase_price': purchase_price,
                'notes': notes
            }
            
            image_data = None
            if image_file:
                image_data = image_file.getvalue()
            
            try:
                db.add_deck(deck_data, image_data)
                st.success("Deck added successfully!")
                st.session_state.clear()
            except Exception as e:
                st.error(f"Error adding deck: {str(e)}")
