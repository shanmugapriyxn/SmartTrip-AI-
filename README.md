# SmartTrip AI – AI-Powered Intelligent Travel Planning System

SmartTrip AI is an AI-powered travel planning web application that helps users plan personalized trips using artificial intelligence.  
The system generates detailed travel itineraries based on user preferences such as destination, budget, duration, and travel style.

---

## Features

- AI-generated personalized travel itineraries using Large Language Models (LLMs)
- Interactive destination selection using maps (OpenStreetMap + Folium)
- Real-time weather forecasting using OpenWeather API
- Destination image gallery using Unsplash API
- Ask follow-up travel questions with AI (Q&A feature)
- Save and reuse travel plans using session storage
- Download generated travel plans for offline use
- Modern and responsive UI built with Streamlit and custom CSS

---

## Tech Stack

**Frontend**
- Streamlit
- HTML, CSS (Custom UI Styling)

**Backend & AI**
- Python
- Groq LLM API (AI itinerary generation)

**APIs & Libraries**
- OpenWeather API (Weather forecast)
- Unsplash API (Destination images)
- SerpAPI (Travel search insights)
- Folium (Interactive maps)
- Geopy (Reverse geocoding)

---

## Project Structure
SmartTrip-AI/
│── main.py
│── requirements.txt
│── README.md
│── .env


## Installation & Setup

1. Clone the repository

git clone https://github.com/your-username/SmartTrip-AI.git
cd SmartTrip-AI
Create and activate a virtual environment

bash
Copy code
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
Install dependencies

bash
Copy code
pip install -r requirements.txt
Add API keys in .env

env
Copy code
GROQ_API_KEY=your_groq_api_key
SERP_API_KEY=your_serpapi_key
OPENWEATHER_API_KEY=your_openweather_api_key
UNSPLASH_ACCESS_KEY=your_unsplash_access_key
Run the application

bash
Copy code
streamlit run main.py
Use Case
Personalized trip planning using AI

Demonstration of LLM-based recommendation systems

Real-time API integration in Python applications



