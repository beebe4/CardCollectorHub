import streamlit as st
from components.add_deck import render_add_deck
from components.view_collection import render_view_collection
from components.statistics import render_statistics
from components.search import render_search
from components.wishlist import render_wishlist
from components.market_tracker import render_market_tracker
from components.share_collection import render_share_collection, render_shared_collection

st.set_page_config(
    page_title="Playing Card Collection Manager",
    page_icon="🎴",
    layout="wide"
)

def main():
    st.title("🎴 Playing Card Collection Manager")
    
    # Check if viewing a shared collection
    query_params = st.query_params
    if 'share' in query_params:
        render_shared_collection(query_params['share'][0])
        return
    
    # Navigation
    pages = {
        "View Collection": render_view_collection,
        "Add New Deck": render_add_deck,
        "Market Tracker": render_market_tracker,
        "Wishlist": render_wishlist,
        "Share Collection": render_share_collection,
        "Statistics": render_statistics,
        "Search": render_search
    }
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(pages.keys()))
    
    # Render selected page
    pages[selection]()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("Made with ❤️ for card collectors")

if __name__ == "__main__":
    main()
