import streamlit as st
from database import db
import pandas as pd
from datetime import datetime, timedelta

def render_share_collection():
    st.header("Share Collection")
    
    # Get all decks
    df = db.get_all_decks()
    
    if df.empty:
        st.info("Add some decks to your collection before sharing!")
        return
    
    # Create new share
    st.subheader("Create New Share")
    
    with st.form("share_collection_form"):
        name = st.text_input("Share Name*", 
                         help="Give this shared collection a name")
        
        description = st.text_area("Description",
                               help="Add optional details about this shared collection")
        
        selected_decks = st.multiselect(
            "Select Decks to Share*",
            options=df.index,
            format_func=lambda x: f"{df.loc[x, 'deck_name']} - {df.loc[x, 'manufacturer']}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            is_public = st.checkbox("Make Public", 
                                help="Allow anyone with the link to view this collection")
        
        with col2:
            expires = st.checkbox("Set Expiration", 
                             help="Set an expiration date for this share")
        
        if expires:
            expiry_date = st.date_input(
                "Expires On",
                min_value=datetime.now().date(),
                value=datetime.now().date() + timedelta(days=7)
            )
        else:
            expiry_date = None
        
        submitted = st.form_submit_button("Create Share Link")
        
        if submitted:
            if not name or not selected_decks:
                st.error("Share name and at least one deck are required!")
                return
            
            try:
                # Convert deck indices to IDs
                deck_ids = [df.iloc[idx]['id'] for idx in selected_decks]
                
                # Create share
                share_id = db.create_shared_collection(
                    name=name,
                    description=description,
                    deck_ids=deck_ids,
                    expires_at=datetime.combine(expiry_date, datetime.max.time()) if expires else None,
                    is_public=is_public
                )
                
                # Show success and share link
                st.success("Share created successfully!")
                share_url = f"{st.get_option('server.baseUrlPath')}/shared/{share_id}"
                st.code(share_url, language="text")
                
                # Add copy button
                st.button("Copy Link", on_click=lambda: st.write(f"```{share_url}```"))
            except Exception as e:
                st.error(f"Failed to create share: {str(e)}")
    
    # List active shares
    st.subheader("Active Shares")
    try:
        shares_df = db.get_active_shared_collections()
        
        if shares_df.empty:
            st.info("No active shares found.")
            return
        
        for _, share in shares_df.iterrows():
            with st.expander(f"{share['name']} ({len(share['deck_ids'])} decks)"):
                st.write(f"**Created:** {share['created_at'].strftime('%Y-%m-%d %H:%M')}")
                if share['expires_at']:
                    st.write(f"**Expires:** {share['expires_at'].strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Public:** {'Yes' if share['is_public'] else 'No'}")
                if share['description']:
                    st.write(f"**Description:** {share['description']}")
                
                share_url = f"{st.get_option('server.baseUrlPath')}/shared/{share['share_id']}"
                st.code(share_url, language="text")
                
    except Exception as e:
        st.error(f"Failed to load active shares: {str(e)}")

def render_shared_collection(share_id):
    try:
        collection = db.get_shared_collection(share_id)
        
        if not collection:
            st.error("This shared collection does not exist or has expired.")
            return
        
        st.title(collection['name'])
        
        if collection['description']:
            st.write(collection['description'])
        
        st.write(f"**Shared on:** {collection['created_at'].strftime('%Y-%m-%d %H:%M')}")
        if collection['expires_at']:
            st.write(f"**Expires on:** {collection['expires_at'].strftime('%Y-%m-%d %H:%M')}")
        
        if not collection['decks']:
            st.info("This shared collection is empty.")
            return
        
        # Display decks in a nice grid
        st.subheader("Decks in this Collection")
        
        for deck in collection['decks']:
            with st.container():
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**{deck['deck_name']}**")
                    st.write(f"Manufacturer: {deck['manufacturer']}")
                    st.write(f"Release Year: {deck['release_year']}")
                    st.write(f"Condition: {deck['condition']}")
                
                if deck.get('notes'):
                    st.write(f"*{deck['notes']}*")
                
                st.markdown("---")
        
    except Exception as e:
        st.error(f"Error loading shared collection: {str(e)}")
