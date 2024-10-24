import streamlit as st
from datetime import datetime
from database import db
from utils import validate_image, validate_deck_data

def render_add_deck():
    st.header("Add New Deck")
    
    # Add tabs for single deck and bulk import
    tab1, tab2 = st.tabs(["Add Single Deck", "Bulk Import"])
    
    with tab1:
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
                
                # Validate deck data
                validation_errors = validate_deck_data(deck_data)
                if validation_errors:
                    for error in validation_errors:
                        st.error(error)
                    return
                
                # Process image if provided
                image_data = None
                if image_file:
                    image_data, error = validate_image(image_file)
                    if error:
                        st.error(f"Image error: {error}")
                        return
                
                try:
                    db.add_deck(deck_data, image_data)
                    st.success("Deck added successfully!")
                    st.session_state.clear()
                except Exception as e:
                    st.error(f"Error adding deck: {str(e)}")
    
    with tab2:
        st.write("Upload a CSV file with deck information")
        st.write("Required columns: deck_name, manufacturer, release_year, condition, purchase_date (YYYY-MM-DD), purchase_price")
        st.write("Optional columns: notes")
        
        csv_file = st.file_uploader("Upload CSV", type=['csv'])
        
        if csv_file:
            from utils import parse_bulk_import_data
            
            decks, errors = parse_bulk_import_data(csv_file)
            
            if errors:
                st.error("Errors found in CSV file:")
                for error in errors:
                    st.error(error)
            
            if decks:
                if st.button(f"Import {len(decks)} Decks"):
                    success_count = 0
                    for deck in decks:
                        try:
                            db.add_deck(deck)
                            success_count += 1
                        except Exception as e:
                            st.error(f"Error adding deck {deck['deck_name']}: {str(e)}")
                    
                    if success_count > 0:
                        st.success(f"Successfully imported {success_count} decks!")
