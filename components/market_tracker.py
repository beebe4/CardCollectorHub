import streamlit as st
import pandas as pd
import plotly.express as px
from database import db

def render_market_tracker():
    st.header("Market Value Tracker")
    
    # Get all decks for selection
    decks_df = db.get_all_decks()
    
    if decks_df.empty:
        st.info("Add some decks to start tracking market values!")
        return
        
    # Add new market value form
    with st.expander("Update Market Value", expanded=False):
        with st.form("market_value_form"):
            # Select deck
            selected_deck = st.selectbox(
                "Select Deck",
                options=decks_df.index,
                format_func=lambda x: f"{decks_df.loc[x, 'deck_name']} - {decks_df.loc[x, 'manufacturer']}"
            )
            
            # Market value details
            market_price = st.number_input("Market Price ($)", min_value=0.0, step=0.01)
            source = st.selectbox(
                "Source",
                ["eBay", "CardMarket", "Portfolio52", "Other"]
            )
            condition = st.selectbox(
                "Condition",
                ["Mint", "Near Mint", "Excellent", "Good", "Fair", "Poor"]
            )
            notes = st.text_area("Notes (Optional)", 
                               help="Add any relevant details about the market value")
            
            submit = st.form_submit_button("Update Market Value")
            
            if submit:
                try:
                    market_data = {
                        'market_price': market_price,
                        'source': source,
                        'condition': condition,
                        'notes': notes
                    }
                    
                    db.update_market_value(decks_df.loc[selected_deck, 'id'], market_data)
                    st.success("Market value updated successfully!")
                except Exception as e:
                    st.error(f"Error updating market value: {str(e)}")
    
    # Display market values and analytics
    try:
        market_values_df = db.get_market_values()
        
        if not market_values_df.empty:
            # Overview metrics
            col1, col2, col3 = st.columns(3)
            
            total_market_value = market_values_df.groupby('deck_id')['market_price'].last().sum()
            total_purchase_value = market_values_df['purchase_price'].sum()
            value_change = ((total_market_value - total_purchase_value) / total_purchase_value) * 100
            
            with col1:
                st.metric("Total Market Value", f"${total_market_value:,.2f}")
            with col2:
                st.metric("Total Purchase Value", f"${total_purchase_value:,.2f}")
            with col3:
                st.metric("Value Change", f"{value_change:+.1f}%")
            
            # Market value trends
            st.subheader("Market Value Trends")
            
            # Group by deck and get latest market values
            latest_values = market_values_df.sort_values('updated_at').groupby('deck_id').last()
            
            fig = px.bar(
                latest_values,
                x='deck_name',
                y=['market_price', 'purchase_price'],
                title='Current Market Value vs Purchase Price',
                barmode='group',
                labels={
                    'deck_name': 'Deck',
                    'value': 'Price ($)',
                    'variable': 'Type'
                }
            )
            st.plotly_chart(fig)
            
            # Detailed market value history
            st.subheader("Market Value History")
            for deck_id in market_values_df['deck_id'].unique():
                deck_data = market_values_df[market_values_df['deck_id'] == deck_id].iloc[0]
                
                with st.expander(f"{deck_data['deck_name']} - {deck_data['manufacturer']}"):
                    deck_history = market_values_df[market_values_df['deck_id'] == deck_id].sort_values('updated_at')
                    
                    # Price history chart
                    fig = px.line(
                        deck_history,
                        x='updated_at',
                        y='market_price',
                        title='Price History',
                        labels={
                            'updated_at': 'Date',
                            'market_price': 'Market Price ($)'
                        }
                    )
                    st.plotly_chart(fig)
                    
                    # History table
                    st.dataframe(
                        deck_history[['updated_at', 'market_price', 'source', 'condition', 'notes']],
                        column_config={
                            'updated_at': st.column_config.DatetimeColumn('Date'),
                            'market_price': st.column_config.NumberColumn('Market Price', format='$%.2f'),
                            'source': 'Source',
                            'condition': 'Condition',
                            'notes': 'Notes'
                        }
                    )
        else:
            st.info("No market values recorded yet. Use the form above to start tracking market values!")
            
    except Exception as e:
        st.error(f"Error loading market values: {str(e)}")
