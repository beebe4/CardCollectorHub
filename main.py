import streamlit as st
from components.add_deck import render_add_deck
from components.view_collection import render_view_collection
from components.statistics import render_statistics
from components.search import render_search
from components.wishlist import render_wishlist

st.set_page_config(
    page_title="Playing Card Collection Manager",
    page_icon="🎴",
    layout="wide"
)

def main():
    st.title("🎴 Playing Card Collection Manager")
    
    # Navigation
    pages = {
        "View Collection": render_view_collection,
        "Add New Deck": render_add_deck,
        "Wishlist": render_wishlist,
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
