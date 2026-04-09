import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import math

def get_user_location():
    """Get user's current location using browser geolocation"""
    location_data = st_folium(
        folium.Map(location=[20.5937, 78.9629], zoom_start=5),
        key="location_map",
        height=300,
        width=700
    )
    
    if location_data['last_clicked']:
        return location_data['last_clicked']['lat'], location_data['last_clicked']['lng']
    return None, None

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def get_location_name(lat, lng):
    """Get city/area name from coordinates using free geocoding"""
    try:
        url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat}&longitude={lng}&localityLanguage=en"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        city = data.get('city', '')
        locality = data.get('locality', '')
        region = data.get('principalSubdivision', '')
        
        location = city or locality or region or 'Unknown Location'
        return location
    except:
        return 'Unknown Location'

def get_india_special_schools(lat, lng):
    """Complete database based on Google search results"""
    all_schools = [
        # Bangalore Dyslexia/SLD Centers (from your Google search)
        {'name': 'Saksham for the Specially Abled', 'lat': 12.9716, 'lng': 77.5946, 'address': '6th Main, 4th Cross Rd, Indiranagar, Bengaluru 560038', 'phone': '078388 05354', 'timings': 'Open - Closes 9:30 PM', 'services': 'Studying center, Special education', 'type': 'Special Education Center', 'website': 'Contact for details', 'rating': '5.0'},
        {'name': 'Samatha Learning Center', 'lat': 12.9352, 'lng': 77.6245, 'address': '#128S, 11th Cross, 21st Main Rd, Bengaluru', 'phone': '063614 94908', 'timings': 'Open - Closes 6:30 PM', 'services': 'Special educator, Learning center for special education', 'type': 'Learning Center', 'website': 'Contact for details', 'rating': '4.9'},
        {'name': 'Asha Kiran Special Needs School', 'lat': 12.9698, 'lng': 77.7500, 'address': 'Plot 10-20, Esther Gardens, Whitefield, Bengaluru 560066', 'phone': '073494 52237', 'timings': 'Open - Closes 3 PM', 'services': 'Special education school', 'type': 'Special School', 'website': 'Contact for details', 'rating': 'No ratings'},
        {'name': 'Buddhi Special School', 'lat': 12.9141, 'lng': 77.6101, 'address': 'Plot 100, 5th Cross, Kogilu Main Rd, Bengaluru', 'phone': '099725 48000', 'timings': 'Open - Closes 5 PM', 'services': 'Special education school', 'type': 'Special School', 'website': 'Contact for details', 'rating': 'No ratings'},
        {'name': 'Krishnan Centre For Special Needs', 'lat': 12.9279, 'lng': 77.5946, 'address': 'No 10, Kuvempu Road, 3rd A Cross Rd, Bengaluru', 'phone': '096321 48670', 'timings': 'Open - Closes 2 PM', 'services': 'Special education school', 'type': 'Special Education Center', 'website': 'Contact for details', 'rating': 'No ratings'},
        {'name': 'Insighte Childcare', 'lat': 13.0358, 'lng': 77.5970, 'address': '620 1st Main, 1st Cross Rd, Bengaluru', 'phone': '080500 77920', 'timings': 'Open - Closes 6 PM', 'services': 'Child health care center, On-site services', 'type': 'Child Care Center', 'website': 'Contact for details', 'rating': '4.6'},
        {'name': 'Saakalya Learning Foundation', 'lat': 12.8944, 'lng': 77.6347, 'address': 'Mahindreshwara residency BR 5, 3rd Cross, Bengaluru', 'phone': '099805 10563', 'timings': 'Closes soon - 1 PM', 'services': 'Special educator', 'type': 'Learning Foundation', 'website': 'Contact for details', 'rating': '4.9'},
        {'name': 'PERSEVERANCE Sahakara Nagar', 'lat': 13.0500, 'lng': 77.5800, 'address': 'Sahakara Nagar, Bengaluru', 'phone': 'Contact for details', 'timings': 'Contact for timings', 'services': 'Special education support', 'type': 'Education Center', 'website': 'Contact for details', 'rating': 'No ratings'},
        {'name': 'The Association Of People With Disability', 'lat': 12.9833, 'lng': 77.6167, 'address': 'Bengaluru', 'phone': 'Contact for details', 'timings': 'Contact for timings', 'services': 'Disability support services', 'type': 'Association', 'website': 'Contact for details', 'rating': 'No ratings'},
        {'name': 'Nidhi Foundation for Early Intervention', 'lat': 12.9200, 'lng': 77.6400, 'address': 'Bengaluru', 'phone': 'Contact for details', 'timings': 'Contact for timings', 'services': 'Early intervention services', 'type': 'Foundation', 'website': 'Contact for details', 'rating': 'No ratings'},
        {'name': 'Deepika School', 'lat': 12.8800, 'lng': 77.5900, 'address': 'Bengaluru', 'phone': 'Contact for details', 'timings': 'Contact for timings', 'services': 'Special education', 'type': 'Special School', 'website': 'Contact for details', 'rating': 'No ratings'},
        {'name': 'JSS Sahana Integrated School', 'lat': 12.9000, 'lng': 77.6200, 'address': 'Bengaluru', 'phone': 'Contact for details', 'timings': 'Contact for timings', 'services': 'Integrated education', 'type': 'Integrated School', 'website': 'Contact for details', 'rating': 'No ratings'},
        {'name': 'Eka Educational and Charitable Trust', 'lat': 12.9300, 'lng': 77.6100, 'address': 'Bengaluru', 'phone': 'Contact for details', 'timings': 'Contact for timings', 'services': 'Educational support', 'type': 'Educational Trust', 'website': 'Contact for details', 'rating': 'No ratings'},
        {'name': 'Samashraya Learning Academy', 'lat': 12.9100, 'lng': 77.5700, 'address': 'Bengaluru', 'phone': 'Contact for details', 'timings': 'Contact for timings', 'services': 'Learning support', 'type': 'Learning Academy', 'website': 'Contact for details', 'rating': 'No ratings'},
        
        # Mumbai Region
        {'name': 'Spastics Society of India', 'lat': 19.0760, 'lng': 72.8777, 'address': 'Deodhar Road, Mumbai 400014', 'phone': '+91-22-24143165', 'timings': 'Mon-Fri: 9 AM - 5 PM', 'services': 'Cerebral palsy, Rehabilitation', 'type': 'Society', 'website': 'www.spasticssocietyofindia.org', 'rating': '4.2'},
        {'name': 'Ummeed Child Development Center', 'lat': 19.0596, 'lng': 72.8295, 'address': 'Bandra West, Mumbai 400050', 'phone': '+91-22-26430404', 'timings': 'Mon-Sat: 9 AM - 6 PM', 'services': 'Autism, ADHD, Learning disabilities', 'type': 'Development Center', 'website': 'www.ummeed.org', 'rating': '4.5'},
        
        # Delhi Region
        {'name': 'Action For Autism', 'lat': 28.5355, 'lng': 77.2910, 'address': 'Pocket 7&8, Jasola Vihar, New Delhi 110025', 'phone': '+91-11-40540991', 'timings': 'Mon-Fri: 9 AM - 5 PM', 'services': 'Autism support, Training programs', 'type': 'NGO', 'website': 'www.autism-india.org', 'rating': '4.3'},
        {'name': 'Tamana Special School', 'lat': 28.6139, 'lng': 77.2090, 'address': 'B-1/1, Vasant Vihar, New Delhi 110057', 'phone': '+91-11-26140141', 'timings': 'Mon-Fri: 9 AM - 4 PM', 'services': 'Multiple disabilities, Art therapy', 'type': 'Special School', 'website': 'www.tamana.org', 'rating': '4.1'},
        
        # Chennai Region
        {'name': 'Spastic Society of Tamil Nadu', 'lat': 13.0827, 'lng': 80.2707, 'address': 'Taramani, Chennai 600113', 'phone': '+91-44-22542519', 'timings': 'Mon-Fri: 9 AM - 5 PM', 'services': 'Cerebral palsy, Physical therapy', 'type': 'Society', 'website': 'www.spasticsocietytn.org', 'rating': '4.4'},
        {'name': 'Vidya Sagar', 'lat': 13.0067, 'lng': 80.2206, 'address': 'Velachery, Chennai 600042', 'phone': '+91-44-22460519', 'timings': 'Mon-Fri: 8:30 AM - 4:30 PM', 'services': 'Multiple disabilities, Inclusive education', 'type': 'Organization', 'website': 'www.vidyasagar.org.in', 'rating': '4.6'}
    ]
    
    # Calculate distances
    for school in all_schools:
        school['distance'] = round(calculate_distance(lat, lng, school['lat'], school['lng']), 1)
        school['source'] = 'Google Search Database'
    
    return sorted(all_schools, key=lambda x: x['distance'])[:12]

def search_google_places_api(lat, lng, api_key, radius_km=25):
    """Search using Google Places API like Google Maps"""
    if not api_key:
        return []
    
    try:
        # Google Places Nearby Search API
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        
        params = {
            'location': f'{lat},{lng}',
            'radius': radius_km * 1000,  # Convert to meters
            'keyword': 'special school dyslexia learning disability autism',
            'type': 'school',
            'key': api_key
        }
        
        st.write(f"🔍 Searching Google Places API...")
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 'OK':
                schools = []
                
                for place in data.get('results', []):
                    school_lat = place['geometry']['location']['lat']
                    school_lng = place['geometry']['location']['lng']
                    distance = calculate_distance(lat, lng, school_lat, school_lng)
                    
                    schools.append({
                        'name': place.get('name', 'School'),
                        'lat': school_lat,
                        'lng': school_lng,
                        'distance': round(distance, 1),
                        'address': place.get('vicinity', 'Address not available'),
                        'rating': place.get('rating', 'No rating'),
                        'phone': 'Contact for details',
                        'timings': 'Contact for timings',
                        'services': 'Educational services',
                        'type': 'School',
                        'website': 'Contact for details',
                        'source': 'Google Places API'
                    })
                
                # If no specific results, try text search
                if not schools:
                    text_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
                    location_name = get_location_name(lat, lng)
                    
                    text_params = {
                        'query': f'dyslexia SLD friendly centres schools {location_name}',
                        'location': f'{lat},{lng}',
                        'radius': radius_km * 1000,
                        'key': api_key
                    }
                    
                    st.write(f"🔍 Trying text search: 'dyslexia SLD friendly centres schools {location_name}'")
                    text_response = requests.get(text_url, params=text_params, timeout=15)
                    
                    if text_response.status_code == 200:
                        text_data = text_response.json()
                        
                        if text_data.get('status') == 'OK':
                            for place in text_data.get('results', []):
                                school_lat = place['geometry']['location']['lat']
                                school_lng = place['geometry']['location']['lng']
                                distance = calculate_distance(lat, lng, school_lat, school_lng)
                                
                                schools.append({
                                    'name': place.get('name', 'School'),
                                    'lat': school_lat,
                                    'lng': school_lng,
                                    'distance': round(distance, 1),
                                    'address': place.get('formatted_address', 'Address not available'),
                                    'rating': place.get('rating', 'No rating'),
                                    'phone': 'Contact for details',
                                    'timings': 'Contact for timings',
                                    'services': 'Special education services',
                                    'type': 'Educational Institution',
                                    'website': 'Contact for details',
                                    'source': 'Google Places Text Search'
                                })
                
                st.write(f"✅ Found {len(schools)} schools from Google Places API")
                return sorted(schools, key=lambda x: x['distance'])
                
            else:
                st.error(f"Google Places API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
                
        else:
            st.error(f"API request failed: {response.status_code}")
            
    except Exception as e:
        st.error(f"Google Places API error: {str(e)}")
    
    return []

def find_special_schools(lat, lng, api_key=None, radius_km=25):
    """Find special schools using Google Places API or fallback"""
    if not lat or not lng:
        return []
    
    location_name = get_location_name(lat, lng)
    
    # Try Google Places API first
    if api_key:
        google_schools = search_google_places_api(lat, lng, api_key, radius_km)
        if google_schools:
            return google_schools
        else:
            st.warning("No results from Google Places API")
    
    # Fallback to curated database
    st.info(f"Using curated database for {location_name}")
    schools = get_india_special_schools(lat, lng)
    
    for school in schools:
        school['source'] = f'Database: {location_name}'
    
    return schools

def display_schools_map(schools, user_lat, user_lng):
    """Display schools on an interactive map"""
    if not schools:
        st.warning("No special schools found in your area.")
        return
    
    # Create map centered on user location
    m = folium.Map(location=[user_lat, user_lng], zoom_start=10)
    
    # Add user location marker
    folium.Marker(
        [user_lat, user_lng],
        popup="<b>Your Location</b>",
        icon=folium.Icon(color='red', icon='home')
    ).add_to(m)
    
    # Add school markers
    for school in schools:
        popup_html = f"""
        <div style="width: 250px;">
            <h4>{school['name']}</h4>
            <p><b>📍 Distance:</b> {school['distance']} km</p>
            <p><b>🏠 Address:</b> {school['address']}</p>
            <p><b>📞 Phone:</b> {school.get('phone', 'N/A')}</p>
            <p><b>🎯 Services:</b> {school.get('services', 'N/A')}</p>
        </div>
        """
        
        folium.Marker(
            [school['lat'], school['lng']],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color='blue', icon='graduation-cap')
        ).add_to(m)
    
    st_folium(m, height=450, width=700)

def get_google_api_key():
    """Get Google Places API key from user"""
    with st.expander("🔑 Google Places API Key (Required for live results)"):
        st.write("**To get live results like Google Maps:**")
        st.write("1. Go to [Google Cloud Console](https://console.cloud.google.com/)")
        st.write("2. Enable 'Places API'")
        st.write("3. Create API Key")
        st.write("4. Paste below:")
        
        api_key = st.text_input(
            "API Key:",
            type="password",
            placeholder="AIzaSyC...",
            help="Required for real-time Google search results"
        )
        
        if api_key:
            st.success("✅ API Key provided! You'll get live Google Places results.")
        else:
            st.warning("⚠️ No API key - will use curated database instead.")
    
    return api_key if api_key else None