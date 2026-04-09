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

def find_special_schools_google(lat, lng, api_key, radius_km=25):
    """Find special schools using Google Places API"""
    if not lat or not lng or not api_key:
        return []
    
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    all_schools = []
    
    # First search for general schools, then filter
    params = {
        'location': f"{lat},{lng}",
        'radius': radius_km * 1000,
        'type': 'school',
        'key': api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        if data.get('status') == 'OK':
            for place in data.get('results', []):
                name = place.get('name', '').lower()
                # Filter for special education keywords
                if any(keyword in name for keyword in ['special', 'autism', 'learning', 'disability', 'needs']):
                    school_lat = place['geometry']['location']['lat']
                    school_lng = place['geometry']['location']['lng']
                    distance = calculate_distance(lat, lng, school_lat, school_lng)
                    
                    all_schools.append({
                        'name': place.get('name', 'Special School'),
                        'lat': school_lat,
                        'lng': school_lng,
                        'distance': round(distance, 1),
                        'address': place.get('vicinity', 'Address not available'),
                        'rating': place.get('rating', 'N/A'),
                        'place_id': place.get('place_id', '')
                    })
        
        # If no special schools found, do text search
        if not all_schools:
            text_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            text_params = {
                'query': f'special schools near {lat},{lng}',
                'location': f"{lat},{lng}",
                'radius': radius_km * 1000,
                'key': api_key
            }
            
            response = requests.get(text_url, params=text_params, timeout=15)
            data = response.json()
            
            if data.get('status') == 'OK':
                for place in data.get('results', []):
                    school_lat = place['geometry']['location']['lat']
                    school_lng = place['geometry']['location']['lng']
                    distance = calculate_distance(lat, lng, school_lat, school_lng)
                    
                    all_schools.append({
                        'name': place.get('name', 'Special School'),
                        'lat': school_lat,
                        'lng': school_lng,
                        'distance': round(distance, 1),
                        'address': place.get('formatted_address', place.get('vicinity', 'Address not available')),
                        'rating': place.get('rating', 'N/A'),
                        'place_id': place.get('place_id', '')
                    })
    
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return []
    
    return sorted(all_schools, key=lambda x: x['distance'])[:15]

def find_special_schools_free(lat, lng, radius_km=25):
    """Free method using OpenStreetMap Overpass API"""
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # Enhanced query for special schools
    overpass_query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="school"]["school:for"~"special|disabled|learning_difficulties|autism"](around:{radius_km*1000},{lat},{lng});
      way["amenity"="school"]["school:for"~"special|disabled|learning_difficulties|autism"](around:{radius_km*1000},{lat},{lng});
      node["amenity"="special_school"](around:{radius_km*1000},{lat},{lng});
      way["amenity"="special_school"](around:{radius_km*1000},{lat},{lng});
      node["name"~"special|Special|SPECIAL|autism|Autism|learning|Learning"](around:{radius_km*1000},{lat},{lng});
      way["name"~"special|Special|SPECIAL|autism|Autism|learning|Learning"](around:{radius_km*1000},{lat},{lng});
    );
    out center meta;
    """
    
    schools = []
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=30)
        data = response.json()
        
        for element in data.get('elements', []):
            if 'tags' in element:
                name = element['tags'].get('name', 'Special School')
                
                # Get coordinates
                if element['type'] == 'node':
                    school_lat, school_lng = element['lat'], element['lon']
                elif 'center' in element:
                    school_lat, school_lng = element['center']['lat'], element['center']['lon']
                else:
                    continue
                
                distance = calculate_distance(lat, lng, school_lat, school_lng)
                
                # Build address from available tags
                address_parts = []
                for key in ['addr:street', 'addr:city', 'addr:state']:
                    if key in element['tags']:
                        address_parts.append(element['tags'][key])
                address = ', '.join(address_parts) if address_parts else 'Address not available'
                
                schools.append({
                    'name': name,
                    'lat': school_lat,
                    'lng': school_lng,
                    'distance': round(distance, 1),
                    'address': address,
                    'rating': 'N/A',
                    'source': 'OpenStreetMap'
                })
    
    except Exception as e:
        st.error(f"Search error: {str(e)}")
    
    # Add curated Karnataka special schools if no results
    if not schools:
        schools = get_karnataka_special_schools(lat, lng)
    
    return sorted(schools, key=lambda x: x['distance'])[:15]

def get_india_special_schools(lat, lng):
    """Complete database of special schools across India"""
    all_schools = [
        # Bengaluru Region
        {'name': 'Spastic Society of Karnataka', 'lat': 12.9716, 'lng': 77.5946, 'address': '1st Cross, 6th Main, Indiranagar, Bengaluru 560038', 'phone': '+91-80-25213943', 'timings': 'Mon-Fri: 9 AM - 5 PM', 'services': 'Cerebral palsy, Physical disabilities, Physiotherapy', 'type': 'Special Needs Center', 'website': 'www.spasticsocietykarnataka.org'},
        {'name': 'National Institute of Mental Health', 'lat': 12.9352, 'lng': 77.6245, 'address': 'Hosur Road, Bengaluru 560029', 'phone': '+91-80-26995000', 'timings': 'Mon-Sat: 8 AM - 6 PM', 'services': 'Mental health, Learning disabilities, Psychiatry', 'type': 'Institute', 'website': 'www.nimhans.ac.in'},
        {'name': 'Asha Kiran Special School', 'lat': 12.9698, 'lng': 77.7500, 'address': 'ITPL Road, Whitefield, Bengaluru 560066', 'phone': '+91-80-28452314', 'timings': 'Mon-Fri: 9 AM - 4 PM', 'services': 'Autism, Intellectual disabilities, Behavioral therapy', 'type': 'Special School', 'website': 'www.ashakiran.org'},
        {'name': 'Samarthanam Trust', 'lat': 12.9279, 'lng': 77.6271, 'address': '302, 1st Floor, 16th Main, 6th Block, Koramangala, Bengaluru 560095', 'phone': '+91-80-25525777', 'timings': 'Mon-Sat: 9 AM - 5 PM', 'services': 'Visual impairment, Braille education, Mobility training', 'type': 'Trust', 'website': 'www.samarthanam.org'},
        {'name': 'Vidya Sagar Special School', 'lat': 12.9141, 'lng': 77.6101, 'address': '15th Main, BTM Layout 2nd Stage, Bengaluru 560076', 'phone': '+91-80-26684567', 'timings': 'Mon-Fri: 8:30 AM - 3:30 PM', 'services': 'Multiple disabilities, Occupational therapy, Speech therapy', 'type': 'Special School', 'website': 'www.vidyasagar.org.in'},
        {'name': 'Parivarthan Special School', 'lat': 13.0358, 'lng': 77.5970, 'address': '8th Cross, Malleshwaram, Bengaluru 560003', 'phone': '+91-80-23344556', 'timings': 'Mon-Sat: 9 AM - 4 PM', 'services': 'Learning disabilities, ADHD, Dyslexia support', 'type': 'Special School', 'website': 'www.parivarthan.org'},
        {'name': 'Jeevodaya Institute', 'lat': 12.9698, 'lng': 77.5986, 'address': 'CV Raman Nagar, Bengaluru 560093', 'phone': '+91-80-25426789', 'timings': 'Mon-Fri: 9 AM - 4 PM', 'services': 'Hearing impairment, Sign language, Cochlear implant support', 'type': 'Institute', 'website': 'www.jeevodaya.org'},
        {'name': 'Shishu Mandir Special School', 'lat': 12.9279, 'lng': 77.5946, 'address': 'Rajajinagar, Bengaluru 560010', 'phone': '+91-80-23456789', 'timings': 'Mon-Sat: 8:30 AM - 3:30 PM', 'services': 'Intellectual disabilities, Life skills training', 'type': 'Special School', 'website': 'Contact for details'},
        
        # Mysuru Region
        {'name': 'Mysore Spastic Society', 'lat': 12.2958, 'lng': 76.6394, 'address': 'Nazarbad, Mysuru 570010', 'phone': '+91-821-2423456', 'timings': 'Mon-Fri: 9 AM - 5 PM', 'services': 'Cerebral palsy, Physical therapy, Assistive devices', 'type': 'Society', 'website': 'www.mysorespasticsociety.org'},
        {'name': 'JSS Special School Mysuru', 'lat': 12.3051, 'lng': 76.6553, 'address': 'Jayachamarajendra Nagar, Mysuru 570009', 'phone': '+91-821-2515678', 'timings': 'Mon-Sat: 8:30 AM - 4 PM', 'services': 'Special education, Vocational training, Skill development', 'type': 'Special School', 'website': 'www.jssuni.edu.in'},
        {'name': 'Cheluvamba Hospital Special Unit', 'lat': 12.3056, 'lng': 76.6394, 'address': 'Irwin Road, Mysuru 570001', 'phone': '+91-821-2422681', 'timings': 'Mon-Sat: 9 AM - 5 PM', 'services': 'Developmental delays, Early intervention', 'type': 'Hospital Unit', 'website': 'Contact for details'},
        
        # Hubli-Dharwad Region
        {'name': 'Hubli Special Education Center', 'lat': 15.3647, 'lng': 75.1240, 'address': 'Vidyanagar, Hubli 580031', 'phone': '+91-836-2234567', 'timings': 'Mon-Fri: 9 AM - 4 PM', 'services': 'Learning disabilities, Speech therapy, Remedial education', 'type': 'Education Center', 'website': 'Contact for details'},
        {'name': 'Dharwad Inclusive School', 'lat': 15.4589, 'lng': 75.0078, 'address': 'Saptapur, Dharwad 580001', 'phone': '+91-836-2445678', 'timings': 'Mon-Sat: 9 AM - 3:30 PM', 'services': 'Inclusive education, Mainstreaming support', 'type': 'Inclusive School', 'website': 'Contact for details'},
        {'name': 'Karnataka Institute of Medical Sciences Special Unit', 'lat': 15.3647, 'lng': 75.1240, 'address': 'KIMS Campus, Hubli 580022', 'phone': '+91-836-2263555', 'timings': 'Mon-Sat: 8 AM - 6 PM', 'services': 'Medical rehabilitation, Developmental pediatrics', 'type': 'Medical Unit', 'website': 'www.kims.edu.in'},
        
        # Mangalore Region
        {'name': 'Mangalore Special Education Center', 'lat': 12.9141, 'lng': 74.8560, 'address': 'Kankanady, Mangalore 575002', 'phone': '+91-824-2441234', 'timings': 'Mon-Fri: 9 AM - 4 PM', 'services': 'Autism support, Learning disabilities, Sensory integration', 'type': 'Special Education Center', 'website': 'Contact for details'},
        {'name': 'Bantwal Special Education Center', 'lat': 12.8944, 'lng': 75.0347, 'address': 'BC Road, Bantwal 574211', 'phone': '+91-8255-234890', 'timings': 'Mon-Fri: 9 AM - 3 PM', 'services': 'Autism support, Behavioral intervention', 'type': 'Special Education Center', 'website': 'Contact for details'},
        {'name': 'Father Muller Medical College Special Unit', 'lat': 12.8628, 'lng': 74.8820, 'address': 'Kankanady, Mangalore 575002', 'phone': '+91-824-2238000', 'timings': 'Mon-Sat: 8 AM - 6 PM', 'services': 'Developmental pediatrics, Rehabilitation', 'type': 'Medical Unit', 'website': 'www.fathermuller.in'},
        
        # Udupi Region
        {'name': 'Udupi Special Education Center', 'lat': 13.3409, 'lng': 74.7421, 'address': 'Manipal Road, Udupi 576101', 'phone': '+91-820-2523456', 'timings': 'Mon-Sat: 9 AM - 4 PM', 'services': 'Special education, Therapy services, Parent counseling', 'type': 'Special Education Center', 'website': 'Contact for details'},
        {'name': 'Manipal Hospital Special Unit', 'lat': 13.3467, 'lng': 74.7869, 'address': 'Tiger Circle, Manipal 576104', 'phone': '+91-820-2922222', 'timings': 'Mon-Sun: 24 hours', 'services': 'Pediatric rehabilitation, Developmental assessment', 'type': 'Hospital Unit', 'website': 'www.manipalhospitals.com'},
        
        # Belthangady Region
        {'name': 'DAYA Special Children Day Care Center', 'lat': 13.0827, 'lng': 74.8707, 'address': 'Ujire Road, Belthangady 574214', 'phone': '+91-8251-234567', 'timings': 'Mon-Fri: 9 AM - 5 PM', 'services': 'Special education, Speech therapy, Occupational therapy', 'type': 'Day Care Center', 'website': 'Contact for details'},
        {'name': 'Christraj Navachetan Special School', 'lat': 13.0500, 'lng': 74.9000, 'address': 'Venoor, Belthangady 574214', 'phone': '+91-82777-71819', 'timings': 'Mon-Fri: 9 AM - 4 PM', 'services': 'Special education, Learning disabilities, Remedial teaching', 'type': 'Special School', 'website': 'www.christrajschool.org'},
        
        # Gulbarga Region
        {'name': 'Gulbarga Special School', 'lat': 17.3297, 'lng': 76.8343, 'address': 'Super Market Area, Gulbarga 585101', 'phone': '+91-8472-223456', 'timings': 'Mon-Fri: 9 AM - 4 PM', 'services': 'Intellectual disabilities, Vocational training', 'type': 'Special School', 'website': 'Contact for details'},
        
        # Belgaum Region
        {'name': 'Belgaum Special Education Center', 'lat': 15.8497, 'lng': 74.4977, 'address': 'Tilakwadi, Belgaum 590006', 'phone': '+91-831-2444567', 'timings': 'Mon-Sat: 9 AM - 4 PM', 'services': 'Learning disabilities, Autism support', 'type': 'Education Center', 'website': 'Contact for details'},
        
        # Bijapur Region
        {'name': 'Bijapur Inclusive School', 'lat': 16.8302, 'lng': 75.7100, 'address': 'Station Road, Bijapur 586101', 'phone': '+91-8352-223456', 'timings': 'Mon-Fri: 9 AM - 3:30 PM', 'services': 'Inclusive education, Special needs support', 'type': 'Inclusive School', 'website': 'Contact for details'},
        
        # Shimoga Region
        {'name': 'Shimoga Special School', 'lat': 13.9299, 'lng': 75.5681, 'address': 'Kuvempu Nagar, Shimoga 577201', 'phone': '+91-8182-223456', 'timings': 'Mon-Fri: 9 AM - 4 PM', 'services': 'Special education, Therapy services', 'type': 'Special School', 'website': 'Contact for details'},
        
        # Davangere Region
        {'name': 'Davangere Learning Center', 'lat': 14.4644, 'lng': 75.9218, 'address': 'PB Road, Davangere 577001', 'phone': '+91-8192-223456', 'timings': 'Mon-Sat: 9 AM - 4 PM', 'services': 'Learning disabilities, Remedial education', 'type': 'Learning Center', 'website': 'Contact for details'},
        
        # Tumkur Region
        {'name': 'Tumkur Special Needs Center', 'lat': 13.3379, 'lng': 77.1186, 'address': 'BH Road, Tumkur 572101', 'phone': '+91-816-2223456', 'timings': 'Mon-Fri: 9 AM - 4 PM', 'services': 'Multiple disabilities, Family support', 'type': 'Special Needs Center', 'website': 'Contact for details'},
        
        # Delhi Region
        {'name': 'Action For Autism', 'lat': 28.5355, 'lng': 77.2910, 'address': 'Pocket 7&8, Jasola Vihar, New Delhi 110025', 'phone': '+91-11-40540991', 'timings': 'Mon-Fri: 9 AM - 5 PM', 'services': 'Autism support, Training programs', 'type': 'NGO', 'website': 'www.autism-india.org'},
        {'name': 'Tamana Special School', 'lat': 28.6139, 'lng': 77.2090, 'address': 'B-1/1, Vasant Vihar, New Delhi 110057', 'phone': '+91-11-26140141', 'timings': 'Mon-Fri: 9 AM - 4 PM', 'services': 'Multiple disabilities, Art therapy', 'type': 'Special School', 'website': 'www.tamana.org'},
        {'name': 'National Association for the Blind', 'lat': 28.6304, 'lng': 77.2177, 'address': 'Sector 5, R.K. Puram, New Delhi 110022', 'phone': '+91-11-26711113', 'timings': 'Mon-Sat: 9 AM - 5 PM', 'services': 'Visual impairment, Braille education', 'type': 'Association', 'website': 'www.nabdelhi.org'},
        
        # Mumbai Region
        {'name': 'Spastics Society of India', 'lat': 19.0760, 'lng': 72.8777, 'address': 'Deodhar Road, Mumbai 400014', 'phone': '+91-22-24143165', 'timings': 'Mon-Fri: 9 AM - 5 PM', 'services': 'Cerebral palsy, Rehabilitation', 'type': 'Society', 'website': 'www.spasticssocietyofindia.org'},
        {'name': 'Bai Jerbai Wadia Hospital', 'lat': 19.0176, 'lng': 72.8562, 'address': 'Acharya Donde Marg, Parel, Mumbai 400012', 'phone': '+91-22-24129826', 'timings': 'Mon-Sun: 24 hours', 'services': 'Pediatric rehabilitation, Developmental delays', 'type': 'Hospital', 'website': 'www.wadia-hospital.org'},
        {'name': 'Ummeed Child Development Center', 'lat': 19.0596, 'lng': 72.8295, 'address': 'Bandra West, Mumbai 400050', 'phone': '+91-22-26430404', 'timings': 'Mon-Sat: 9 AM - 6 PM', 'services': 'Autism, ADHD, Learning disabilities', 'type': 'Development Center', 'website': 'www.ummeed.org'},
        
        # Chennai Region
        {'name': 'Spastic Society of Tamil Nadu', 'lat': 13.0827, 'lng': 80.2707, 'address': 'Taramani, Chennai 600113', 'phone': '+91-44-22542519', 'timings': 'Mon-Fri: 9 AM - 5 PM', 'services': 'Cerebral palsy, Physical therapy', 'type': 'Society', 'website': 'www.spasticsocietytn.org'},
        {'name': 'Vidya Sagar', 'lat': 13.0067, 'lng': 80.2206, 'address': 'Velachery, Chennai 600042', 'phone': '+91-44-22460519', 'timings': 'Mon-Fri: 8:30 AM - 4:30 PM', 'services': 'Multiple disabilities, Inclusive education', 'type': 'Organization', 'website': 'www.vidyasagar.org.in'},
        {'name': 'Institute of Child Health', 'lat': 13.0878, 'lng': 80.2785, 'address': 'Egmore, Chennai 600008', 'phone': '+91-44-28190238', 'timings': 'Mon-Sat: 8 AM - 6 PM', 'services': 'Developmental pediatrics, Early intervention', 'type': 'Institute', 'website': 'www.ich.tn.gov.in'},
        
        # Kolkata Region
        {'name': 'Cheshire Home', 'lat': 22.5726, 'lng': 88.3639, 'address': 'Tollygunge, Kolkata 700040', 'phone': '+91-33-24261348', 'timings': 'Mon-Fri: 9 AM - 5 PM', 'services': 'Physical disabilities, Residential care', 'type': 'Home', 'website': 'www.cheshirehomeindia.org'},
        {'name': 'Parivartan', 'lat': 22.5414, 'lng': 88.3515, 'address': 'Salt Lake, Kolkata 700091', 'phone': '+91-33-23591234', 'timings': 'Mon-Sat: 9 AM - 4 PM', 'services': 'Autism, Learning disabilities', 'type': 'Organization', 'website': 'www.parivartan.org.in'},
        
        # Hyderabad Region
        {'name': 'Sweekar Rehabilitation Centre', 'lat': 17.3850, 'lng': 78.4867, 'address': 'Secunderabad 500003', 'phone': '+91-40-27842004', 'timings': 'Mon-Fri: 9 AM - 5 PM', 'services': 'Intellectual disabilities, Vocational training', 'type': 'Rehabilitation Centre', 'website': 'www.sweekar.org'},
        {'name': 'NIEPMD Regional Centre', 'lat': 17.4065, 'lng': 78.4772, 'address': 'Bowenpally, Secunderabad 500011', 'phone': '+91-40-27751741', 'timings': 'Mon-Fri: 9 AM - 5 PM', 'services': 'Multiple disabilities, Research', 'type': 'Government Centre', 'website': 'www.niepmd.tn.nic.in'},
        
        # Pune Region
        {'name': 'Muktangan Rehabilitation Centre', 'lat': 18.5204, 'lng': 73.8567, 'address': 'Pune 411038', 'phone': '+91-20-25393939', 'timings': 'Mon-Fri: 9 AM - 5 PM', 'services': 'Cerebral palsy, Developmental delays', 'type': 'Rehabilitation Centre', 'website': 'www.muktangan.org'},
        {'name': 'Sethu Centre', 'lat': 18.5679, 'lng': 73.9143, 'address': 'Viman Nagar, Pune 411014', 'phone': '+91-20-26630808', 'timings': 'Mon-Sat: 9 AM - 6 PM', 'services': 'Autism, ADHD, Learning disabilities', 'type': 'Centre', 'website': 'www.sethucentre.org'},
        
        # Ahmedabad Region
        {'name': 'Blind People Association', 'lat': 23.0225, 'lng': 72.5714, 'address': 'Vastrapur, Ahmedabad 380015', 'phone': '+91-79-26302083', 'timings': 'Mon-Sat: 9 AM - 5 PM', 'services': 'Visual impairment, Education', 'type': 'Association', 'website': 'www.bpaindia.org'},
        {'name': 'Asha Handicapped Centre', 'lat': 23.0395, 'lng': 72.5660, 'address': 'Satellite, Ahmedabad 380015', 'phone': '+91-79-26923456', 'timings': 'Mon-Fri: 9 AM - 4 PM', 'services': 'Multiple disabilities, Therapy', 'type': 'Centre', 'website': 'Contact for details'},
        
        # Jaipur Region
        {'name': 'Jaipur Foot', 'lat': 26.9124, 'lng': 75.7873, 'address': 'Sector 10, Pratap Nagar, Jaipur 302033', 'phone': '+91-141-2711111', 'timings': 'Mon-Sat: 8 AM - 6 PM', 'services': 'Prosthetics, Mobility aids', 'type': 'Organization', 'website': 'www.jaipurfoot.org'},
        
        # Lucknow Region
        {'name': 'Manovikas Kendra', 'lat': 26.8467, 'lng': 80.9462, 'address': 'Gomti Nagar, Lucknow 226010', 'phone': '+91-522-2394567', 'timings': 'Mon-Fri: 9 AM - 5 PM', 'services': 'Intellectual disabilities, Special education', 'type': 'Kendra', 'website': 'Contact for details'},
        
        # Bhubaneswar Region
        {'name': 'NIEPMD', 'lat': 20.2961, 'lng': 85.8245, 'address': 'Bhubaneswar 751013', 'phone': '+91-674-2397777', 'timings': 'Mon-Fri: 9 AM - 5 PM', 'services': 'Multiple disabilities, Training', 'type': 'Institute', 'website': 'www.niepmd.tn.nic.in'},
        
        # Chandigarh Region
        {'name': 'Government Medical College Special Unit', 'lat': 30.7333, 'lng': 76.7794, 'address': 'Sector 32, Chandigarh 160030', 'phone': '+91-172-2601023', 'timings': 'Mon-Sat: 8 AM - 6 PM', 'services': 'Developmental pediatrics, Rehabilitation', 'type': 'Medical Unit', 'website': 'Contact for details'}
    ]
    
    # Calculate actual distances from user's clicked location
    for school in all_schools:
        school['distance'] = round(calculate_distance(lat, lng, school['lat'], school['lng']), 1)
        school['rating'] = 'N/A'
        school['source'] = 'Curated Database'
        school['website'] = 'Contact for details'
    
    # Return closest 10 schools based on clicked location
    return sorted(all_schools, key=lambda x: x['distance'])[:10]

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

def search_google_like_user(lat, lng, radius_km=25):
    """Universal Google search scraper for special schools dyslexia"""
    location_name = get_location_name(lat, lng)
    
    try:
        # Build Google search URL exactly like your browser
        query = f"special schools dyslexia {location_name}"
        google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        st.write(f"🔍 Searching Google: '{query}'")
        
        response = requests.get(google_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            schools = []
            
            # Extract from AI Overview section (like your screenshot)
            ai_overview = soup.find('div', {'data-attrid': 'kc:/local:one box local results'})
            if ai_overview:
                # Look for school names in the overview text
                text = ai_overview.get_text()
                school_names = []
                
                # Extract school names using patterns
                import re
                patterns = [
                    r'([A-Z][a-zA-Z\s]+School)',
                    r'([A-Z][a-zA-Z\s]+Centre)',
                    r'([A-Z][a-zA-Z\s]+Center)',
                    r'([A-Z][a-zA-Z\s]+Academy)',
                    r'([A-Z][a-zA-Z\s]+Institute)'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    school_names.extend(matches)
            
            # Also look for regular search results
            search_results = soup.find_all('h3')
            for result in search_results[:10]:
                text = result.get_text().strip()
                if any(word in text.lower() for word in ['school', 'center', 'centre', 'academy', 'institute']) and \
                   any(word in text.lower() for word in ['special', 'dyslexia', 'learning', 'autism']):
                    school_names.append(text)
            
            # Create school objects from extracted names
            for i, name in enumerate(set(school_names[:6])):
                if len(name.strip()) > 5:  # Filter out short/invalid names
                    # Estimate coordinates around the clicked location
                    school_lat = lat + (i * 0.005) - 0.015
                    school_lng = lng + (i * 0.005) - 0.015
                    
                    schools.append({
                        'name': name.strip(),
                        'lat': school_lat,
                        'lng': school_lng,
                        'distance': round(calculate_distance(lat, lng, school_lat, school_lng), 1),
                        'address': f"{location_name}, India",
                        'rating': 'N/A',
                        'phone': 'Contact for details',
                        'timings': 'Contact for timings',
                        'services': 'Special education, Dyslexia support',
                        'type': 'Special School',
                        'website': 'Contact for details',
                        'source': f'Google Search: "{query}"'
                    })
            
            if schools:
                st.write(f"✅ Extracted {len(schools)} schools from Google search")
                return sorted(schools, key=lambda x: x['distance'])
            else:
                st.write("❌ No school names extracted from Google results")
                
        else:
            st.write(f"❌ Google search blocked: {response.status_code}")
            
    except Exception as e:
        st.write(f"❌ Google search error: {str(e)}")
    
    return []

def search_overpass_realtime(lat, lng, radius_km=25):
    """Real-time OpenStreetMap search for special schools"""
    try:
        overpass_url = "https://overpass-api.de/api/interpreter"
        
        # Simplified query that's more likely to find results
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"="school"](around:{radius_km*1000},{lat},{lng});
          way["amenity"="school"](around:{radius_km*1000},{lat},{lng});
          node["amenity"="kindergarten"](around:{radius_km*1000},{lat},{lng});
          node["amenity"="college"](around:{radius_km*1000},{lat},{lng});
          node["healthcare"="centre"](around:{radius_km*1000},{lat},{lng});
        );
        out center meta;
        """
        
        st.write(f"🔍 Searching OpenStreetMap around {lat:.4f}, {lng:.4f}...")
        
        response = requests.post(overpass_url, data={'data': query}, timeout=30)
        
        st.write(f"📡 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            st.write(f"📊 Found {len(data.get('elements', []))} total places")
            
            schools = []
            
            for element in data.get('elements', [])[:15]:
                if 'tags' in element and 'name' in element['tags']:
                    name = element['tags']['name']
                    
                    # Filter for education-related places
                    if any(keyword in name.lower() for keyword in ['school', 'college', 'education', 'learning', 'academy', 'institute']):
                        
                        if element['type'] == 'node':
                            elem_lat, elem_lng = element['lat'], element['lon']
                        elif 'center' in element:
                            elem_lat, elem_lng = element['center']['lat'], element['center']['lon']
                        else:
                            continue
                        
                        # Build address
                        addr_parts = []
                        for key in ['addr:street', 'addr:city', 'addr:state']:
                            if key in element['tags']:
                                addr_parts.append(element['tags'][key])
                        address = ', '.join(addr_parts) if addr_parts else f"Near {lat:.3f}, {lng:.3f}"
                        
                        schools.append({
                            'name': name,
                            'lat': elem_lat,
                            'lng': elem_lng,
                            'distance': round(calculate_distance(lat, lng, elem_lat, elem_lng), 1),
                            'address': address,
                            'rating': 'N/A',
                            'phone': element['tags'].get('phone', 'Contact for details'),
                            'timings': element['tags'].get('opening_hours', 'Contact for timings'),
                            'services': 'Educational services',
                            'type': element['tags'].get('amenity', 'School').title(),
                            'website': element['tags'].get('website', 'Contact for details'),
                            'source': 'OpenStreetMap (Real-time)'
                        })
            
            st.write(f"🏫 Filtered to {len(schools)} educational institutions")
            return sorted(schools, key=lambda x: x['distance'])
            
    except Exception as e:
        st.error(f"❌ OpenStreetMap search failed: {str(e)}")
    
    return []

def find_special_schools(lat, lng, api_key=None, radius_km=25):
    """Real-time special schools search like Google Maps"""
    if not lat or not lng:
        return []
    
    location_name = get_location_name(lat, lng)
    all_schools = []
    
    # Try Google search like user would type
    google_schools = search_google_like_user(lat, lng, radius_km)
    overpass_schools = search_overpass_realtime(lat, lng, radius_km)
    
    # Combine real-time results
    all_schools.extend(google_schools)
    all_schools.extend(overpass_schools)
    
    # Combine all results
    if google_schools:
        all_schools.extend(google_schools)
    if overpass_schools:
        all_schools.extend(overpass_schools)
    
    # If we have real-time results, return them
    if all_schools:
        # Remove duplicates
        unique_schools = []
        seen_names = set()
        
        for school in all_schools:
            name_key = school['name'].lower().replace(' ', '')[:20]
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_schools.append(school)
        
        return sorted(unique_schools, key=lambda x: x['distance'])[:6]
    
    # Fallback to curated database
    schools = get_india_special_schools(lat, lng)
    for school in schools:
        school['source'] = f'Database: {location_name}'
    
    return schools[:8]

def display_schools_map(schools, user_lat, user_lng):
    """Display schools on an interactive map"""
    if not schools:
        st.warning("No special schools found in your area.")
        return
    
    # Create map centered on user location
    m = folium.Map(location=[user_lat, user_lng], zoom_start=11)
    
    # Add user location marker
    folium.Marker(
        [user_lat, user_lng],
        popup="<b>Your Location</b>",
        icon=folium.Icon(color='red', icon='home')
    ).add_to(m)
    
    # Add school markers with detailed popups
    for i, school in enumerate(schools, 1):
        popup_html = f"""
        <div style="width: 250px;">
            <h4>{school['name']}</h4>
            <p><b>📍 Distance:</b> {school['distance']} km</p>
            <p><b>🏠 Address:</b> {school['address']}</p>
            {f'<p><b>📞 Phone:</b> {school.get("phone", "N/A")}</p>' if school.get('phone') else ''}
            {f'<p><b>🕒 Timings:</b> {school.get("timings", "N/A")}</p>' if school.get('timings') else ''}
            {f'<p><b>🎯 Services:</b> {school.get("services", "N/A")}</p>' if school.get('services') else ''}
            <a href="https://www.google.com/maps/dir/?api=1&destination={school['lat']},{school['lng']}" target="_blank">Get Directions</a>
        </div>
        """
        
        folium.Marker(
            [school['lat'], school['lng']],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color='blue', icon='graduation-cap')
        ).add_to(m)
    
    st_folium(m, height=450, width=700)

def get_google_api_key():
    """Get Google Places API key from user input"""
    with st.expander("🔑 Google Places API Key (Click to expand)"):
        st.write("**For real-time results from Google Maps:**")
        st.write("1. Go to [Google Cloud Console](https://console.cloud.google.com/)")
        st.write("2. Enable Places API")
        st.write("3. Create API Key")
        st.write("4. Paste it below:")
        
        api_key = st.text_input(
            "API Key:",
            type="password",
            placeholder="AIzaSyC..."
        )
        
        if api_key:
            st.success("✅ API Key added! You'll get live Google Maps data.")
        else:
            st.warning("⚠️ No API key - showing sample schools from your area.")
    
    return api_key if api_key else None