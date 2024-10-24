import streamlit as st
import pandas as pd
from database import db
from utils import prepare_export_data

def render_view_collection():
    st.header("Card Collection")
    
    # Get all decks
    df = db.get_all_decks()
    
    if df.empty:
        st.info("No decks in your collection yet. Add some decks to get started!")
        return
    
    # Add filter controls
    col1, col2 = st.columns(2)
    with col1:
        manufacturer_filter = st.multiselect(
            "Filter by Manufacturer",
            options=sorted(df['manufacturer'].unique())
        )
    
    with col2:
        condition_filter = st.multiselect(
            "Filter by Condition",
            options=sorted(df['condition'].unique())
        )
    
    # Apply filters
    if manufacturer_filter:
        df = df[df['manufacturer'].isin(manufacturer_filter)]
    if condition_filter:
        df = df[df['condition'].isin(condition_filter)]
    
    # Display table
    display_df = df.drop(columns=['image_data'])
    st.dataframe(
        display_df,
        column_config={
            "purchase_price": st.column_config.NumberColumn(
                "Purchase Price",
                format="$%.2f"
            ),
            "created_at": st.column_config.DatetimeColumn(
                "Added On",
                format="DD/MM/YYYY"
            )
        }
    )
    
    # Export functionality
    if st.button("Export to CSV"):
        export_df = prepare_export_data(df)
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="card_collection.csv",
            mime="text/csv"
        )
