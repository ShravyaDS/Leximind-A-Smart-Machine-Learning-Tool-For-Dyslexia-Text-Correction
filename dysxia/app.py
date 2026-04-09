import streamlit as st
import tempfile
import os
from user_utils import register_user, valid_credentials
import time
import sys
import base64
print(">>> Running with Python executable:", sys.executable)


if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ''
if 'page' not in st.session_state:
    st.session_state.page = "login"
if 'schools_data' not in st.session_state:
    st.session_state.schools_data = None
if 'user_location' not in st.session_state:
    st.session_state.user_location = None


def login_page():
    st.title(" Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if valid_credentials(email, password):
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.success(f"Welcome back, {email}!")
                st.session_state.page = "index"
                st.rerun()
            else:
                st.error("Invalid email or password")


def register_page():
    st.title(" Register")
    with st.form("register_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        terms = st.checkbox("I accept the terms and conditions")
        submitted = st.form_submit_button("Sign Up")
        if submitted:
            if not all([name, email, password, confirm]):
                st.error("Please fill out all fields")
            elif password != confirm:
                st.error("Passwords do not match")
            elif not terms:
                st.error("You must accept the terms and conditions")
            elif not register_user(name, email, password):
                st.error("Email already registered")
            else:
                st.success("Registration successful! Please log in.")
                st.session_state.page = "login"
                st.rerun()

def add_bg_from_local(image_file):
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        [data-testid="stHeader"] {{
            background: rgba(0, 0, 0, 0);
        }}
        [data-testid="stToolbar"] {{
            right: 2rem;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def index_page():
    st.title("Dyslexia Prediction")
    add_bg_from_local('background.jpg')
    st.write(f"Logged in as: {st.session_state.user_email}")
    
    # Add tabs for different features
    tab1, tab2 = st.tabs([" Text Analysis", " School Management"])
    
    with tab1:
        uploaded_file = st.file_uploader(
            "Upload your doc scanned image", type=['png', 'jpg', 'jpeg'])

    if uploaded_file is not None:
        if st.button("Process Image", key="process_image"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name
            try:
                with st.spinner(" Processing image... Please wait..."):
                    start_time = time.time()  # ⏱ Start timer
                    from dyslexia_auto import process_image_for_dyslexia
                    results = process_image_for_dyslexia(tmp_path)

                st.success(" Processing completed!")

                st.subheader("OCR Text:")
                st.write(results["ocr"])

                st.subheader("Spell Corrected:")
                st.write(results["spell_corrected"])

                st.subheader("Grammar Corrected:")
                st.write(results["grammar_corrected"])

                st.subheader("Transformer Refined:")
                st.write(results["transformer_refined"])

                #  Compare final vs raw OCR
                final_text = results["final"][-1]
                if final_text.strip() == results["ocr"].strip():
                    st.subheader("Final: No sign of Dyslexia Detected ")
                else:
                    st.subheader("Final: Dyslexia Detected ")
                st.markdown(
                    f"""
                        <div style="
                            border: 2px solid #1DB954;  /* Spotify green */
                            padding: 16px;
                            border-radius: 10px;
                            background-color: #121212; /* dark background */
                            color: #E0E0E0;  /* light grey text */
                            font-weight: bold;
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            box-shadow: 0 4px 8px rgba(29, 185, 84, 0.4);
                            ">
                            {final_text}
                        </div>
                        """, unsafe_allow_html=True)
                end_time = time.time()
                processing_time = end_time - start_time
                st.info(f"⏱ Processing time: {processing_time:.2f} seconds")

            finally:
                os.remove(tmp_path)
    

    
    with tab2:
        st.subheader(" School Management System")
        
        from school_db import SchoolDatabase
        db = SchoolDatabase()
        
        # Sub-tabs for different management functions
        mgmt_tab1, mgmt_tab2, mgmt_tab3 = st.tabs([" View Schools", " Add School", " Search Schools"])
        
        with mgmt_tab1:
            st.subheader(" Schools by District")
            
            # Add refresh button
            if st.button(" Refresh Database with Latest Karnataka Schools"):
                db.insert_sample_data()
                st.success(" Database refreshed with latest Karnataka schools data!")
                st.rerun()
            
            # District selector
            districts = db.get_all_districts()
            if districts:
                district_options = {f"{d['name']}, {d['state']}": d['id'] for d in districts}
                selected_district = st.selectbox(
                    "Select District:",
                    options=list(district_options.keys()),
                    key="district_selector"
                )
                
                if selected_district:
                    district_id = district_options[selected_district]
                    schools = db.get_schools_by_district(district_id)
                    
                    if schools:
                        st.success(f"Found {len(schools)} schools in {selected_district}")
                        
                        for i, school in enumerate(schools, 1):
                            with st.expander(f" {i}. {school['name']}"):
                                col1, col2 = st.columns([2, 1])
                                
                                with col1:
                                    st.write(f" Address: {school['address']}")
                                    if school['phone']:
                                        st.write(f" Phone: {school['phone']}")
                                    if school['email']:
                                        st.write(f" Email: {school['email']}")
                                    if school['website']:
                                        st.write(f"Website: {school['website']}")
                                    if school['services']:
                                        st.write(f"Services: {school['services']}")
                                    if school['timings']:
                                        st.write(f"Timings: {school['timings']}")
                                    if school['type']:
                                        st.write(f"Type: {school['type']}")
                                
                                with col2:
                                    if school['rating']:
                                        st.metric("Rating", f"⭐ {school['rating']}")
                                    
                                    if school['latitude'] and school['longitude']:
                                        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={school['latitude']},{school['longitude']}"
                                        st.link_button("📍 Get Directions", maps_url)
                    else:
                        st.info(f"No schools found in {selected_district}")
            else:
                st.error("No districts found in database")
        
        with mgmt_tab2:
            st.subheader("➕ Add New School")
            
            with st.form("add_school_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    school_name = st.text_input("School Name *")
                    
                    # District selector for adding school
                    districts = db.get_all_districts()
                    if districts:
                        district_options = {f"{d['name']}, {d['state']}": d['id'] for d in districts}
                        selected_district_add = st.selectbox(
                            "Select District *:",
                            options=list(district_options.keys()),
                            key="district_add_selector"
                        )
                    
                    address = st.text_area("Address")
                    phone = st.text_input("Phone Number")
                    email = st.text_input("Email")
                
                with col2:
                    website = st.text_input("Website")
                    school_type = st.selectbox("School Type", [
                        "Special School", "Institute", "Hospital", "Society", 
                        "Trust", "Organization", "Special Needs Center", "Other"
                    ])
                    services = st.text_area("Services Offered")
                    timings = st.text_input("Operating Hours")
                    rating = st.number_input("Rating (1-5)", min_value=1.0, max_value=5.0, step=0.1, value=None)
                
                # Location coordinates
                st.subheader("📍 Location Coordinates (Optional)")
                loc_col1, loc_col2 = st.columns(2)
                with loc_col1:
                    latitude = st.number_input("Latitude", value=None, format="%.6f")
                with loc_col2:
                    longitude = st.number_input("Longitude", value=None, format="%.6f")
                
                submitted = st.form_submit_button("➕ Add School")
                
                if submitted:
                    if not school_name or not selected_district_add:
                        st.error("Please fill in required fields (School Name and District)")
                    else:
                        school_data = {
                            'name': school_name,
                            'district_id': district_options[selected_district_add],
                            'address': address,
                            'phone': phone,
                            'email': email,
                            'website': website,
                            'latitude': latitude,
                            'longitude': longitude,
                            'services': services,
                            'timings': timings,
                            'type': school_type,
                            'rating': rating
                        }
                        
                        if db.add_school(school_data):
                            st.success(f" School '{school_name}' added successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to add school. Please try again.")
            
            # Add new district section
            st.subheader("🏛️ Add New District")
            with st.form("add_district_form"):
                dist_col1, dist_col2 = st.columns(2)
                with dist_col1:
                    district_name = st.text_input("District Name")
                with dist_col2:
                    state_name = st.text_input("State")
                
                dist_submitted = st.form_submit_button("➕ Add District")
                
                if dist_submitted:
                    if not district_name or not state_name:
                        st.error("Please fill in both district name and state")
                    else:
                        if db.add_district(district_name, state_name):
                            st.success(f" District '{district_name}, {state_name}' added successfully!")
                            st.rerun()
                        else:
                            st.error("❌ District already exists or failed to add.")
        
        with mgmt_tab3:
            st.subheader("🔍 Search Schools")
            
            search_query = st.text_input("Search by school name, services, or type:")
            
            if search_query:
                search_results = db.search_schools(search_query)
                
                if search_results:
                    st.success(f"Found {len(search_results)} schools matching '{search_query}'")
                    
                    for i, school in enumerate(search_results, 1):
                        with st.expander(f" {i}. {school['name']} - {school['district_name']}, {school['state']}"):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write(f"**📍 Address:** {school['address']}")
                                if school['phone']:
                                    st.write(f"**📞 Phone:** {school['phone']}")
                                if school['email']:
                                    st.write(f"**📧 Email:** {school['email']}")
                                if school['website']:
                                    st.write(f"**🌐 Website:** {school['website']}")
                                if school['services']:
                                    st.write(f"**🎯 Services:** {school['services']}")
                                if school['timings']:
                                    st.write(f"**🕒 Timings:** {school['timings']}")
                                if school['type']:
                                    st.write(f"**🏷️ Type:** {school['type']}")
                            
                            with col2:
                                if school['rating']:
                                    st.metric("Rating", f"⭐ {school['rating']}")
                                
                                if school['latitude'] and school['longitude']:
                                    maps_url = f"https://www.google.com/maps/dir/?api=1&destination={school['latitude']},{school['longitude']}"
                                    st.link_button("📍 Get Directions", maps_url)
                else:
                    st.info(f"No schools found matching '{search_query}'")
            else:
                st.info("Enter a search term to find schools")

    if st.button("Logout", key="logout_button"):
        st.session_state.logged_in = False
        st.session_state.user_email = ''
        st.session_state.page = "login"
        st.rerun()


# Main navigation logic
if st.session_state.logged_in:
    index_page()
else:
    if st.session_state.page == "login":
        login_page()
        if st.button("Create an account"):
            st.session_state.page = "register"
            st.rerun()
    elif st.session_state.page == "register":
        register_page()
        if st.button("Back to login"):
            st.session_state.page = "login"
            st.rerun()
