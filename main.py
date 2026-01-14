"""
CJ Young Sommelier - AI-driven Liquor Analytics Platform

Main Streamlit application entry point for tracking LOT-specific chemical changes,
predicting sensory scores, and generating flavor reports.
"""

import streamlit as st
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="CJ Young Sommelier",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application landing page"""
    
    st.title("🍷 CJ Young Sommelier")
    st.subheader("AI-driven Liquor Analytics & Flavor Prediction Platform")
    
    st.markdown("""
    Welcome to the CJ Young Sommelier platform! This application helps you:
    
    - **Track LOT-specific chemical changes** in your liquor inventory
    - **Predict sensory scores** using machine learning regression models
    - **Generate flavor reports** powered by Google Gemini AI
    
    ### Getting Started
    
    Use the navigation menu on the left to access different features:
    
    1. **📊 Data Entry** - Input and manage LOT chemical composition data
    2. **🎯 Prediction** - Predict sensory scores based on chemical profiles
    3. **👃 Sensory** - Analyze and visualize sensory characteristics
    4. **📝 Report** - Generate comprehensive flavor reports with AI
    
    ### About the Platform
    
    This platform combines chemical analysis with machine learning and AI to provide
    actionable insights for liquor quality assessment and flavor profiling.
    """)
    
    # Display system status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Database", "Ready", delta="SQLite")
    
    with col2:
        st.metric("ML Model", "Ready", delta="sklearn")
    
    with col3:
        st.metric("AI Engine", "Ready", delta="Gemini")
    
    # Information section
    with st.expander("ℹ️ System Information"):
        st.info("""
        **Technology Stack:**
        - Frontend: Streamlit
        - Database: SQLite with SQLAlchemy
        - Machine Learning: scikit-learn, pandas
        - AI: Google Gemini
        
        **Data Storage:**
        - Chemical data stored in local SQLite database
        - Knowledge base for reference materials
        """)

if __name__ == "__main__":
    main()
