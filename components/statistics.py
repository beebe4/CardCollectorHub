import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from database import db

def render_statistics():
    st.header("Collection Statistics")
    
    df = db.get_all_decks()
    
    if df.empty:
        st.info("Add some decks to see statistics!")
        return
    
    # Basic statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Decks", len(df))
    
    with col2:
        total_value = df['purchase_price'].sum()
        st.metric("Total Collection Value", f"${total_value:,.2f}")
    
    with col3:
        avg_price = df['purchase_price'].mean()
        st.metric("Average Deck Price", f"${avg_price:,.2f}")
    
    # Manufacturer Distribution
    st.subheader("Decks by Manufacturer")
    fig_manufacturer = px.pie(
        df,
        names='manufacturer',
        values='purchase_price',
        title='Collection Value by Manufacturer'
    )
    st.plotly_chart(fig_manufacturer)
    
    # Condition Distribution
    st.subheader("Condition Distribution")
    condition_count = df['condition'].value_counts()
    fig_condition = px.bar(
        x=condition_count.index,
        y=condition_count.values,
        title='Decks by Condition'
    )
    st.plotly_chart(fig_condition)
    
    # Price Timeline
    st.subheader("Purchase History")
    fig_timeline = px.scatter(
        df.sort_values('purchase_date'),
        x='purchase_date',
        y='purchase_price',
        title='Purchase Price Timeline',
        hover_data=['deck_name']
    )
    st.plotly_chart(fig_timeline)
