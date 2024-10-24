import streamlit as st
from database import db

def render_search():
    st.header("Search Collection")
    
    search_query = st.text_input("Search decks by name, manufacturer, or notes")
    
    if search_query:
        results = db.search_decks(search_query)
        
        if not results:
            st.info("No decks found matching your search.")
            return
        
        for deck in results:
            with st.expander(f"{deck['deck_name']} - {deck['manufacturer']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Release Year:** {deck['release_year']}")
                    st.write(f"**Condition:** {deck['condition']}")
                    st.write(f"**Purchase Date:** {deck['purchase_date']}")
                    st.write(f"**Purchase Price:** ${deck['purchase_price']}")
                
                with col2:
                    if deck['image_data']:
                        st.image(deck['image_data'])
                
                if deck['notes']:
                    st.write("**Notes:**")
                    st.write(deck['notes'])
