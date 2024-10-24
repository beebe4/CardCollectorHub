import streamlit as st
from database import db

def render_wishlist():
    st.header("Wishlist")
    
    # Add new wishlist item form
    with st.expander("Add New Wishlist Item", expanded=False):
        with st.form("add_wishlist_form"):
            deck_name = st.text_input("Deck Name*")
            manufacturer = st.text_input("Manufacturer*")
            expected_price = st.number_input("Expected Price ($)", min_value=0.0, step=0.01)
            priority = st.slider("Priority", 1, 5, 3, 
                               help="1 = Lowest priority, 5 = Highest priority")
            notes = st.text_area("Notes")
            
            submit = st.form_submit_button("Add to Wishlist")
            
            if submit:
                if not deck_name or not manufacturer:
                    st.error("Deck name and manufacturer are required!")
                    return
                
                wishlist_data = {
                    'deck_name': deck_name,
                    'manufacturer': manufacturer,
                    'expected_price': expected_price,
                    'priority': priority,
                    'notes': notes
                }
                
                try:
                    db.add_to_wishlist(wishlist_data)
                    st.success("Item added to wishlist!")
                    st.session_state.clear()
                except Exception as e:
                    st.error(f"Error adding to wishlist: {str(e)}")
    
    # Display wishlist
    df = db.get_wishlist()
    
    if df.empty:
        st.info("Your wishlist is empty. Add some decks you'd like to acquire!")
        return
    
    # Display wishlist items grouped by priority
    for priority in range(5, 0, -1):
        priority_items = df[df['priority'] == priority]
        if not priority_items.empty:
            st.subheader(f"Priority {priority} Items")
            
            for _, item in priority_items.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{item['deck_name']}** by {item['manufacturer']}")
                        if item['notes']:
                            st.write(f"*Notes:* {item['notes']}")
                    
                    with col2:
                        st.write(f"Expected: ${item['expected_price']:.2f}")
                    
                    with col3:
                        if st.button("Remove", key=f"remove_{item['id']}"):
                            try:
                                db.remove_from_wishlist(item['id'])
                                st.success("Item removed from wishlist!")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error removing item: {str(e)}")
                    
                    st.markdown("---")
