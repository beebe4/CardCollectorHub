import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from database import db
import pandas as pd
from datetime import datetime, timedelta

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
    
    # Year-over-year collection growth
    st.subheader("Collection Growth")
    df['year'] = pd.to_datetime(df['purchase_date']).dt.year
    yearly_growth = df.groupby('year').agg({
        'id': 'count',
        'purchase_price': 'sum'
    }).reset_index()
    yearly_growth['cumulative_decks'] = yearly_growth['id'].cumsum()
    
    fig_growth = go.Figure()
    fig_growth.add_trace(go.Bar(
        x=yearly_growth['year'],
        y=yearly_growth['id'],
        name='Decks Added'
    ))
    fig_growth.add_trace(go.Line(
        x=yearly_growth['year'],
        y=yearly_growth['cumulative_decks'],
        name='Total Decks',
        yaxis='y2'
    ))
    fig_growth.update_layout(
        title='Year-over-Year Collection Growth',
        yaxis=dict(title='Decks Added'),
        yaxis2=dict(title='Total Decks', overlaying='y', side='right')
    )
    st.plotly_chart(fig_growth)
    
    # Value appreciation over time
    st.subheader("Collection Value Growth")
    yearly_growth['cumulative_value'] = yearly_growth['purchase_price'].cumsum()
    fig_value = px.line(
        yearly_growth,
        x='year',
        y='cumulative_value',
        title='Total Collection Value Over Time'
    )
    fig_value.update_layout(
        yaxis_title='Total Value ($)',
        xaxis_title='Year'
    )
    st.plotly_chart(fig_value)
    
    # Manufacturer Distribution
    st.subheader("Collection Distribution")
    col1, col2 = st.columns(2)
    
    with col1:
        fig_manufacturer = px.pie(
            df,
            names='manufacturer',
            values='purchase_price',
            title='Value by Manufacturer'
        )
        st.plotly_chart(fig_manufacturer)
    
    with col2:
        condition_stats = df['condition'].value_counts()
        fig_condition = px.pie(
            values=condition_stats.values,
            names=condition_stats.index,
            title='Condition Distribution'
        )
        st.plotly_chart(fig_condition)
    
    # Collection Completion Metrics
    st.subheader("Collection Completion Metrics")
    total_manufacturers = len(df['manufacturer'].unique())
    total_conditions = len(df['condition'].unique())
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Unique Manufacturers", total_manufacturers)
    
    with col2:
        avg_decks_per_manufacturer = len(df) / total_manufacturers
        st.metric("Avg Decks per Manufacturer", f"{avg_decks_per_manufacturer:.1f}")
    
    with col3:
        condition_completion = (total_conditions / 6) * 100  # 6 possible conditions
        st.metric("Condition Coverage", f"{condition_completion:.1f}%")
