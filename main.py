import streamlit as st
import os
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import requests
import pyttsx3
import threading
import tempfile
from groq import Groq
from dotenv import load_dotenv
import json
import base64
from io import BytesIO
import datetime
import hashlib
import random

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="TRIP GENIE",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Vibrant CSS
st.markdown("""
<style>
/* ===== COLOR SYSTEM ===== */
:root {
    --primary: #2563EB;        /* Blue */
    --secondary: #9333EA;      /* Purple */
    --accent: #F97316;         /* Orange */
    --success: #22C55E;        /* Green */
    --bg-main: linear-gradient(135deg, #EFF6FF, #FFFFFF);
    --card-bg: #FFFFFF;
    --text-dark: #0F172A;
    --text-muted: #475569;
    --sidebar-bg: #0F172A;
    --sidebar-text: #E5E7EB;
    --border-radius: 14px;
    --shadow: 0 10px 25px rgba(0,0,0,0.08);
}

/* ===== APP BACKGROUND ===== */
html, body, .stApp {
    background: var(--bg-main) !important;
    color: var(--text-dark) !important;
    font-family: "Segoe UI", Roboto, sans-serif;
}

/* ===== HEADINGS ===== */
h1, h2, h3, h4 {
    color: var(--primary) !important;
    font-weight: 700;
}

p, li, span {
    color: var(--text-dark) !important;
    font-size: 16px;
}

/* ===== CARDS ===== */
.feature-card,
.travel-summary,
.weather-card {
    background: var(--card-bg) !important;
    border-radius: var(--border-radius);
    padding: 18px;
    box-shadow: var(--shadow);
    margin-bottom: 15px;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background: var(--sidebar-bg) !important;
}

section[data-testid="stSidebar"] * {
    color: var(--sidebar-text) !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important;
}

/* ===== INPUT FIELDS ===== */
input, textarea {
    background-color: #1E293B !important;
    color: #F8FAFC !important;
    border-radius: 10px !important;
    border: 1px solid #475569 !important;
}

/* ===== BUTTONS ===== */
.stButton button {
    background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
    color: white !important;
    font-weight: 700;
    border-radius: 12px;
    padding: 0.6rem 1.2rem;
    box-shadow: var(--shadow);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 15px 30px rgba(0,0,0,0.15);
    background: linear-gradient(135deg, var(--secondary), var(--primary)) !important;
}

/* ===== MAP & IMAGES ===== */
.image-item img {
    border-radius: 14px;
    box-shadow: var(--shadow);
}

/* ===== FOOTER TEXT ===== */
footer, .css-164nlkn {
    color: var(--text-muted) !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'travel_plan' not in st.session_state:
    st.session_state.travel_plan = None
if 'selected_location' not in st.session_state:
    st.session_state.selected_location = None
if 'selected_coords' not in st.session_state:
    st.session_state.selected_coords = None
if 'weather_data' not in st.session_state:
    st.session_state.weather_data = None
if 'location_images' not in st.session_state:
    st.session_state.location_images = []
if 'tts_played' not in st.session_state:
    st.session_state.tts_played = False
if 'user_session_id' not in st.session_state:
    # Create a unique session ID for the user
    st.session_state.user_session_id = hashlib.md5(str(datetime.datetime.now()).encode()).hexdigest()[:16]
if 'saved_plans' not in st.session_state:
    st.session_state.saved_plans = []
if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = {}

# API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
SERP_API_KEY = os.getenv("SERP_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")

def play_welcome_message():
    """Play welcome message using text-to-speech"""
    try:
        if not st.session_state.tts_played:
            def speak():
                engine = pyttsx3.init() 
                engine.setProperty('rate', 150)
                engine.setProperty('volume', 0.8)
                voices = engine.getProperty('voices')
                if voices:
                    engine.setProperty('voice', voices[0].id)
                engine.say("Welcome to your AI Travel Planner! Let's plan your perfect adventure!")
                engine.runAndWait()
            
            thread = threading.Thread(target=speak)
            thread.daemon = True
            thread.start()
            st.session_state.tts_played = True
    except Exception as e:
        st.warning(f"Text-to-speech not available: {str(e)}")

def get_weather_data(lat, lon, location_name):
    """Fetch weather data from OpenWeatherMap API"""
    try:
        if not OPENWEATHER_API_KEY:
            return None
        
        url = f"http://api.openweathermap.org/data/2.5/forecast"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric',
            'cnt': 5  # 5-day forecast
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Weather API error: {str(e)}")
        return None



def get_location_images(location_name):
    """Fetch better Unsplash images based on refined location query"""
    try:
        if not UNSPLASH_ACCESS_KEY:
            return []

        location_clean = location_name.split(",")[0].strip()
        keywords = ["travel", "landmark", "tourism", "attractions", "scenery"]
        query = f"{location_clean} {random.choice(keywords)}"

        url = "https://api.unsplash.com/search/photos"
        headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
        params = {
            'query': query,
            'per_page': 6,
            'orientation': 'landscape'
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [photo['urls']['regular'] for photo in data['results']]
        return []
    except Exception as e:
        st.error(f"Image API error: {str(e)}")
        return []


def reverse_geocode(lat, lon):
    """Get location name from coordinates"""
    try:
        geolocator = Nominatim(user_agent="travel_planner")
        coordinate_string = f"{lat}, {lon}"
        location = geolocator.reverse(coordinate_string)
        if location:
            return str(location)
        return f"Location at {lat:.4f}, {lon:.4f}"
    except Exception as e:
        return f"Location at {lat:.4f}, {lon:.4f}"

def get_user_location_from_ip():
    """Get user's current location using IP geolocation"""
    try:
        # Try ipinfo.io first (free tier: 50,000 requests/month)
        response = requests.get("https://ipinfo.io/json", timeout=5)
        if response.status_code == 200:
            data = response.json()
            city = data.get('city', '')
            region = data.get('region', '')
            country = data.get('country', '')
            
            # Format location string
            location_parts = [part for part in [city, region, country] if part]
            location_string = ', '.join(location_parts) if location_parts else 'Unknown Location'
            
            # Get coordinates if available
            loc = data.get('loc', '').split(',')
            lat, lon = (float(loc[0]), float(loc[1])) if len(loc) == 2 else (None, None)
            
            return {
                'location': location_string,
                'city': city,
                'region': region,
                'country': country,
                'latitude': lat,
                'longitude': lon,
                'raw_data': data
            }
    except Exception as e:
        pass
    
    try:
        # Fallback to ip-api.com (free tier: 1000 requests/hour)
        response = requests.get("http://ip-api.com/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                city = data.get('city', '')
                region = data.get('regionName', '')
                country = data.get('country', '')
                
                location_parts = [part for part in [city, region, country] if part]
                location_string = ', '.join(location_parts) if location_parts else 'Unknown Location'
                
                return {
                    'location': location_string,
                    'city': city,
                    'region': region,
                    'country': country,
                    'latitude': data.get('lat'),
                    'longitude': data.get('lon'),
                    'raw_data': data
                }
    except Exception as e:
        pass
    
    # Return default if all methods fail
    return {
        'location': 'Location not detected',
        'city': '',
        'region': '',
        'country': '',
        'latitude': None,
        'longitude': None,
        'raw_data': {}
    }

def initialize_user_location():
    """Initialize user location on first load"""
    if 'user_location_data' not in st.session_state:
        st.session_state.user_location_data = None
        st.session_state.location_fetched = False
    
    if not st.session_state.location_fetched:
        with st.spinner("Detecting your location..."):
            location_data = get_user_location_from_ip()
            st.session_state.user_location_data = location_data
            st.session_state.location_fetched = True


def search_destinations(query):
    """Search for destination information using SerpAPI"""
    try:
        if not SERP_API_KEY:
            return None
        
        url = "https://serpapi.com/search"
        params = {
            'q': f"{query} travel guide attractions",
            'api_key': SERP_API_KEY,
            'engine': 'google'
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Search API error: {str(e)}")
        return None

def generate_travel_plan(destination, duration, budget, travel_style, groq_api_key, from_location=None):
    """Generate travel plan using Groq API"""
    try:
        if not groq_api_key:
            st.error("Please provide your Groq API key")
            return None
        
        client = Groq(api_key=groq_api_key)
        
        # Get additional destination info if available
        search_info = ""
        if SERP_API_KEY:
            search_results = search_destinations(destination)
            if search_results and 'organic_results' in search_results:
                search_info = "\n\nRecent information about this destination:\n"
                for result in search_results['organic_results'][:3]:
                    search_info += f"- {result.get('title', '')}: {result.get('snippet', '')}\n"
        
        # Include from location context if available
        travel_context = ""
        if from_location and from_location != "Location not detected":
            travel_context = f"\n\nTraveler's Starting Location: {from_location}\nPlease consider transportation logistics and travel time from this starting point."
        
        prompt = f"""Create a comprehensive travel plan for {destination} for {duration} days.

Trip Details:
- Budget Level: {budget}
- Travel Style: {', '.join(travel_style)}
- Duration: {duration} days{travel_context}



{search_info}

Please provide a detailed itinerary including:

1. *Best Time to Visit* 🌞
   - Optimal seasons and months
   - Weather considerations

2. *Accommodation Recommendations* 🏨
   - {budget} budget options with specific names and areas
   - Booking tips

3. *Day-by-Day Itinerary* 🗺
   - Daily activities and attractions
   - Time estimates and logistics
   - Must-see highlights

4. *Food & Dining* 🍽
   - Local specialties to try
   - Restaurant recommendations
   - Food experiences

5. *Transportation* 🚗
   - How to get there
   - Local transportation options
   - Travel tips

6. *Budget Breakdown* 💰
   - Estimated costs for accommodation, food, activities
   - Money-saving tips

7. *Essential Tips* 💡
   - Cultural considerations
   - Safety tips
   - What to pack

Format the response with clear headings and bullet points. Make it practical and actionable."""

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating travel plan: {str(e)}")
        return None

def get_user_session_id():
    """Get or create user session ID"""
    return st.session_state.user_session_id

# REMOVE: Database functions

# Preferences: Save/load in session state only
def save_user_preferences_locally(budget, duration, travel_styles):
    st.session_state.user_preferences = {
        'preferred_budget': budget,
        'preferred_duration': duration,
        'preferred_travel_styles': travel_styles
    }
    return True

# Saved plans: Save/load in session state only
def save_travel_plan_locally(destination, duration, budget, travel_style, plan_content, latitude=None, longitude=None):
    plan = {
        'destination': destination,
        'duration_days': duration,
        'budget_level': budget,
        'travel_style': travel_style,
        'plan_content': plan_content,
        'latitude': latitude,
        'longitude': longitude,
        'created_at': datetime.datetime.now()
    }
    st.session_state.saved_plans.insert(0, plan)
    return True

def load_saved_travel_plans_locally():
    return st.session_state.saved_plans

def create_pdf_from_plan(travel_plan, destination):
    """Generate PDF from travel plan using HTML conversion"""
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Travel Plan - {destination}</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    color: #333; 
                    line-height: 1.6;
                }}
                h1 {{ 
                    color: #00A8E8; 
                    text-align: center; 
                    border-bottom: 3px solid #00A8E8;
                    padding-bottom: 10px;
                }}
                h2 {{ 
                    color: #FF6B6B; 
                    border-bottom: 2px solid #FF6B6B; 
                    padding-bottom: 5px; 
                }}
                h3 {{ 
                    color: #4ECDC4; 
                }}
                p, li {{ 
                    line-height: 1.6; 
                }}
                .header {{ 
                    text-align: center; 
                    margin-bottom: 30px; 
                }}
                .content {{ 
                    max-width: 800px; 
                    margin: 0 auto; 
                }}
                .date {{ 
                    text-align: right; 
                    color: #666; 
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🌎 AI Travel Plan</h1>
                <h2>Destination: {destination}</h2>
                <div class="date">Generated on: {datetime.datetime.now().strftime('%B %d, %Y')}</div>
            </div>
            <div class="content">
                {travel_plan.replace('', '<strong>').replace('', '</strong>').replace(chr(10), '<br>').replace('# ', '<h2>').replace('## ', '<h3>').replace('### ', '<h4>')}
            </div>
        </body>
        </html>
        """
        
        # Convert HTML to bytes for download
        pdf_bytes = html_content.encode('utf-8')
        return pdf_bytes
        
    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        return None

# Load user preferences on startup
# REMOVE: load_user_preferences()

# Initialize user location detection
initialize_user_location()

# Play welcome message
play_welcome_message()

# Main header
st.markdown("""
    <div class="main-header">
        <h1>🌎 AI Travel Planner</h1>
        <p style="font-size: 1.2rem; color: #666;">Plan your perfect adventure with AI assistance</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar - Trip Settings
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/airplane-take-off.png")
    st.title("🎯 Trip Settings")

    # API Keys
    groq_api_key = st.text_input("🔑 Groq API Key", type="password", value=GROQ_API_KEY)
    serpapi_key = st.text_input("🔑 SerpAPI Key", type="password", value=SERP_API_KEY)
    openweather_key = st.text_input("🌤 OpenWeather API Key", type="password", value=OPENWEATHER_API_KEY)
    unsplash_key = st.text_input("📸 Unsplash Access Key", type="password", value=UNSPLASH_ACCESS_KEY)
    
    # Update environment variables
    os.environ["GROQ_API_KEY"] = groq_api_key
    os.environ["SERP_API_KEY"] = serpapi_key
    os.environ["OPENWEATHER_API_KEY"] = openweather_key
    os.environ["UNSPLASH_ACCESS_KEY"] = unsplash_key
    
    st.divider()
    
    # User Location Section
    st.subheader("📍 Your Location")
    
    # Get detected location
    user_location_data = st.session_state.get('user_location_data', {})
    detected_location = user_location_data.get('location', 'Location not detected')
    
    # Create columns for location display and refresh button
    loc_col1, loc_col2 = st.columns([3, 1])
    
    with loc_col1:
        # Editable from location field
        from_location = st.text_input(
            "From Location", 
            value=detected_location,
            help="Your current location (auto-detected via IP). You can edit this manually if needed."
        )
    
    with loc_col2:
        st.write("")  # Empty space for alignment
        if st.button("🔄", help="Refresh location"):
            st.session_state.location_fetched = False
            st.rerun()
    
    # Show location details if available
    if user_location_data and user_location_data.get('city'):
        location_info = []
        if user_location_data.get('city'):
            location_info.append(f"City: {user_location_data['city']}")
        if user_location_data.get('region'):
            location_info.append(f"Region: {user_location_data['region']}")
        if user_location_data.get('country'):
            location_info.append(f"Country: {user_location_data['country']}")
        
        if location_info:
            st.caption(" | ".join(location_info))
    
    st.divider()
    
    # Load user preferences for defaults
    user_prefs = st.session_state.user_preferences
    default_budget = user_prefs.get('preferred_budget', 'Moderate') if user_prefs else 'Moderate'
    default_duration = user_prefs.get('preferred_duration', 5) if user_prefs else 5
    default_styles = user_prefs.get('preferred_travel_styles', ['Culture', 'Nature']) if user_prefs else ['Culture', 'Nature']
    
    # Trip parameters
    destination = st.text_input("🌍 To Destination", value=st.session_state.selected_location or "")
    duration = st.number_input("📅 Duration (days)", min_value=1, max_value=30, value=default_duration)
    budget = st.select_slider("💰 Budget Level", options=["Budget", "Moderate", "Luxury"], value=default_budget)
    travel_style = st.multiselect("🎯 Travel Style", 
                                 ["Culture", "Nature", "Adventure", "Relaxation", "Food", "Shopping"], 
                                 default_styles)
    
    # Save preferences button
    if st.button("💾 Save My Preferences"):
        if save_user_preferences_locally(budget, duration, travel_style):
            st.success("Preferences saved!")
        else:
            st.info("Preferences saved locally.")
    
    st.divider()
    
    # Saved Travel Plans Section
    st.subheader("📚 Your Saved Plans")
    saved_plans = load_saved_travel_plans_locally()
    
    if saved_plans:
        for plan in saved_plans[:3]:  # Show recent 3 plans
            with st.expander(f"📍 {plan['destination']} ({plan['duration_days']} days)"):
                st.write(f"*Budget:* {plan['budget_level']}")
                st.write(f"*Style:* {', '.join(plan['travel_style']) if plan['travel_style'] else 'Not specified'}")
                st.write(f"*Created:* {plan['created_at'].strftime('%Y-%m-%d')}")
                
                if st.button(f"🔄 Load Plan", key=f"load_{plan['destination']}"):
                    st.session_state.travel_plan = plan['plan_content']
                    st.session_state.selected_location = plan['destination']
                    if plan['latitude'] and plan['longitude']:
                        st.session_state.selected_coords = [plan['latitude'], plan['longitude']]
                    st.rerun()
    else:
        st.info("No saved plans yet. Create your first travel plan!")

# Main content layout
col1, col2 = st.columns([1, 1])

with col1:
    # Interactive Map Section
    st.markdown("""
        <div class="feature-card">
            <h3>🗺 Select Your Destination</h3>
            <p>Click on the map to select your travel destination</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Create map
    m = folium.Map(location=[20.0, 0.0], zoom_start=2)
    
    # Add marker if location is selected
    if st.session_state.selected_coords:
        folium.Marker(
            st.session_state.selected_coords, 
            popup=f"Selected: {st.session_state.selected_location}",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
    
    # Display map with container styling
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    map_data = st_folium(m, width=400, height=300)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle map clicks
    if map_data['last_object_clicked_tooltip'] or map_data['last_clicked']:
        if map_data['last_clicked']:
            lat = map_data['last_clicked']['lat']
            lon = map_data['last_clicked']['lng']
            location_name = reverse_geocode(lat, lon)
            st.session_state.selected_location = location_name
            st.session_state.selected_coords = [lat, lon]
            
            st.success(f"📍 Selected: {location_name}")
            st.info(f"📐 Coordinates: {lat:.4f}, {lon:.4f}")

with col2:
    # Weather Information
    if st.session_state.selected_coords and openweather_key:
        st.markdown("""
            <div class="feature-card">
                <h3>🌤 Weather Forecast</h3>
            </div>
        """, unsafe_allow_html=True)
        
        lat, lon = st.session_state.selected_coords
        weather_data = get_weather_data(lat, lon, st.session_state.selected_location)
        
        if weather_data:
            st.markdown('<div class="weather-card">', unsafe_allow_html=True)
            current = weather_data['list'][0]
            st.markdown(f"🌡 Current:** {current['main']['temp']:.1f}°C")
            st.markdown(f"📝 Description:** {current['weather'][0]['description'].title()}")
            st.markdown(f"💧 Humidity:** {current['main']['humidity']}%")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 5-day forecast
            st.markdown("📅 5-Day Forecast:")
            for i, forecast in enumerate(weather_data['list'][:5]):
                date = forecast['dt_txt'].split(' ')[0]
                temp = forecast['main']['temp']
                desc = forecast['weather'][0]['description']
                st.markdown(f"• {date}: {temp:.1f}°C, {desc.title()}")
        else:
            st.info("Weather data unavailable. Add your OpenWeather API key for forecasts.")
    
    # Location Images
    if st.session_state.selected_location:
        st.markdown("""
            <div class="feature-card">
                <h3>📸 Destination Gallery</h3>
            </div>
        """, unsafe_allow_html=True)
        
        if unsplash_key:
            if st.button("🖼 Load Images"):
                with st.spinner("Loading destination images..."):
                    city_only = st.session_state.selected_location.split(",")[0].strip()
                images = get_location_images(city_only)
                st.session_state.location_images = images
            
            if st.session_state.location_images:
                st.markdown('<div class="image-gallery">', unsafe_allow_html=True)
                for idx, img_url in enumerate(st.session_state.location_images[:4]):
                    st.markdown(f'''
                        <div class="image-item">
                            <img src="{img_url}" alt="Destination Image {idx+1}" />
                        </div>
                    ''', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Add your Unsplash API key to view destination images.")

# Travel Plan Generation Section
st.divider()

# Summary Display
if destination:
    st.markdown(f"""
        <div class="travel-summary">
            <h4>Welcome to your personal AI Travel Assistant! 🌟</h4>
            <p><strong>Destination:</strong> {destination}</p>
            <p><strong>Duration:</strong> {duration} days</p>
            <p><strong>Budget:</strong> {budget}</p>
            <p><strong>Style:</strong> {', '.join(travel_style) if travel_style else 'Not specified'}</p>
        </div>
    """, unsafe_allow_html=True)

# Generate Plan
col1, col2 = st.columns([3, 1])
with col1:
    if st.button("✨ Generate My Perfect Travel Plan", type="primary"):
        if destination and groq_api_key:
            with st.spinner("🔍 Planning your trip..."):
                travel_plan = generate_travel_plan(destination, duration, budget, travel_style, groq_api_key, from_location)
                if travel_plan:
                    st.session_state.travel_plan = travel_plan
                    st.markdown(travel_plan)
                    # Save plan locally
                    coords = st.session_state.selected_coords
                    lat, lon = (coords[0], coords[1]) if coords else (None, None)
                    save_travel_plan_locally(destination, duration, budget, travel_style, travel_plan, lat, lon)
                    st.success("Travel plan saved to your collection!")
        elif not destination:
            st.warning("Please enter a destination first.")
        else:
            st.warning("Please provide your Groq API key.")

with col2:
    if st.session_state.travel_plan:
        # PDF Export
        pdf_data = create_pdf_from_plan(st.session_state.travel_plan, destination)
        if pdf_data:
            st.download_button(
                label="📄 Download PDF",
                data=pdf_data,
                file_name=f"travel_plan_{destination.replace(' ', '_')}.html",
                mime="text/html",
                help="Download your travel plan as HTML file"
            )

# Display existing travel plan
if st.session_state.travel_plan:
    st.divider()
    st.markdown("### Your Travel Plan")
    st.markdown(st.session_state.travel_plan)

# Q&A Section
st.divider()
qa_expander = st.expander("🤔 Ask a specific question about your destination or travel plan", expanded=False)
with qa_expander:
    question = st.text_input("Your question:", placeholder="e.g., What's the best local food to try?")
    if st.button("Get Answer", key="qa_button"):
        if question and groq_api_key:
            with st.spinner("🔍 Finding answer..."):
                context_prompt = f"""
                Based on the destination {destination}, answer this question: {question}
                
                {"Context from travel plan: " + st.session_state.travel_plan if st.session_state.travel_plan else ""}
                
                Provide a helpful, detailed answer about {destination}.
                """
                
                try:
                    client = Groq(api_key=groq_api_key)
                    response = client.chat.completions.create(
                        messages=[{"role": "user", "content": context_prompt}],
                        model="llama-3.3-70b-versatile",
                        temperature=0.7,
                        max_tokens=500
                    )
                    answer = response.choices[0].message.content
                    st.markdown(answer)
                except Exception as e:
                    st.error(f"Error getting answer: {str(e)}")
        elif not question:
            st.warning("Please enter your question.")
        elif not groq_api_key:
            st.warning("Please provide your Groq API key.")

# Footer
st.divider()
st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🌎 AI Travel Planner - Plan your perfect adventure with artificial intelligence</p>
        <p>Add your API keys in the sidebar to unlock all features</p>
    </div>
""", unsafe_allow_html=True)