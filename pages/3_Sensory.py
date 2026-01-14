"""
Sensory Page - Analyze and visualize sensory characteristics
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import (
    init_database, get_session, get_lot_by_number, get_all_lots,
    add_sensory_profile, get_sensory_profiles_by_lot
)

# Initialize database
init_database()

st.set_page_config(page_title="Sensory Analysis", page_icon="👃", layout="wide")

st.title("👃 Sensory Analysis & Profiling")
st.markdown("Analyze and visualize sensory characteristics of liquor LOTs")

# Tabs
tab1, tab2, tab3 = st.tabs([
    "📝 Add Sensory Profile", 
    "📊 View Sensory Data",
    "🔍 Compare LOTs"
])

# Tab 1: Add Sensory Profile
with tab1:
    st.subheader("Create Detailed Sensory Profile")
    
    try:
        session = get_session()
        lots = get_all_lots(session)
        
        if lots:
            lot_numbers = [lot.lot_number for lot in lots]
            selected_lot = st.selectbox("Select LOT", lot_numbers)
            
            if selected_lot:
                lot = get_lot_by_number(session, selected_lot)
                st.info(f"📦 Creating sensory profile for: {lot.product_name} (LOT {lot.lot_number})")
                
                with st.form("sensory_profile_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### Visual & Aromatic")
                        color_description = st.text_input(
                            "Color Description",
                            placeholder="e.g., Deep amber, crystal clear"
                        )
                        
                        aroma_notes = st.text_area(
                            "Aroma Notes",
                            placeholder="e.g., vanilla, oak, caramel, fruit",
                            help="Comma-separated descriptors"
                        )
                        
                        st.markdown("### Palate & Texture")
                        flavor_notes = st.text_area(
                            "Flavor Notes",
                            placeholder="e.g., spice, honey, citrus, chocolate",
                            help="Comma-separated descriptors"
                        )
                        
                        mouthfeel = st.text_input(
                            "Mouthfeel",
                            placeholder="e.g., smooth, full-bodied, creamy"
                        )
                    
                    with col2:
                        st.markdown("### Finish & Overall")
                        finish_description = st.text_area(
                            "Finish Description",
                            placeholder="Describe the aftertaste and lingering flavors"
                        )
                        
                        st.markdown("### Tasting Information")
                        taster_name = st.text_input(
                            "Taster Name",
                            placeholder="Your name or ID"
                        )
                        
                        tasting_date = st.date_input(
                            "Tasting Date",
                            value=datetime.now()
                        )
                    
                    submitted = st.form_submit_button("💾 Save Sensory Profile")
                    
                    if submitted:
                        if not taster_name:
                            st.error("❌ Taster name is required!")
                        else:
                            try:
                                profile_data = {
                                    'lot_number': selected_lot,
                                    'color_description': color_description,
                                    'aroma_notes': aroma_notes,
                                    'flavor_notes': flavor_notes,
                                    'mouthfeel': mouthfeel,
                                    'finish_description': finish_description,
                                    'taster_name': taster_name,
                                    'tasting_date': datetime.combine(tasting_date, datetime.min.time())
                                }
                                
                                add_sensory_profile(session, profile_data)
                                st.success(f"✅ Sensory profile saved for LOT {selected_lot}!")
                                st.balloons()
                            except Exception as e:
                                st.error(f"❌ Error saving profile: {str(e)}")
        else:
            st.warning("📭 No LOT data available. Add LOTs in the Data Entry page first.")
        
        session.close()
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Tab 2: View Sensory Data
with tab2:
    st.subheader("Sensory Profiles & Scores")
    
    try:
        session = get_session()
        lots = get_all_lots(session)
        
        if lots:
            # LOT selector
            lot_numbers = ['All LOTs'] + [lot.lot_number for lot in lots]
            view_lot = st.selectbox("Select LOT to View", lot_numbers)
            
            if view_lot == 'All LOTs':
                # Show all LOTs with sensory scores
                st.markdown("### All LOT Sensory Scores")
                
                data = []
                for lot in lots:
                    if lot.aroma_score or lot.taste_score or lot.finish_score or lot.overall_score:
                        data.append({
                            'LOT Number': lot.lot_number,
                            'Product': lot.product_name,
                            'Aroma': lot.aroma_score or 0,
                            'Taste': lot.taste_score or 0,
                            'Finish': lot.finish_score or 0,
                            'Overall': lot.overall_score or 0
                        })
                
                if data:
                    df = pd.DataFrame(data)
                    
                    # Display table
                    st.dataframe(df, use_container_width=True)
                    
                    # Visualization
                    fig = go.Figure()
                    
                    for category in ['Aroma', 'Taste', 'Finish', 'Overall']:
                        fig.add_trace(go.Bar(
                            name=category,
                            x=df['LOT Number'],
                            y=df[category]
                        ))
                    
                    fig.update_layout(
                        title="Sensory Scores by LOT",
                        xaxis_title="LOT Number",
                        yaxis_title="Score (0-100)",
                        barmode='group',
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("ℹ️ No sensory scores recorded yet.")
            
            else:
                # Show specific LOT details
                lot = get_lot_by_number(session, view_lot)
                
                if lot:
                    st.markdown(f"### {lot.product_name} (LOT {lot.lot_number})")
                    
                    # Chemical composition
                    with st.expander("🧪 Chemical Composition", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Alcohol Content", f"{lot.alcohol_content}% ABV")
                            st.metric("Acidity", f"{lot.acidity} pH")
                        with col2:
                            st.metric("Sugar Content", f"{lot.sugar_content} g/L")
                            st.metric("Tannin Level", f"{lot.tannin_level} mg/L")
                        with col3:
                            st.metric("Ester Concentration", f"{lot.ester_concentration} mg/L")
                            st.metric("Aldehyde Level", f"{lot.aldehyde_level} mg/L")
                    
                    # Sensory scores
                    if lot.aroma_score or lot.taste_score:
                        with st.expander("🎯 Sensory Scores", expanded=True):
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Aroma", f"{lot.aroma_score or 0:.1f}/100")
                            with col2:
                                st.metric("Taste", f"{lot.taste_score or 0:.1f}/100")
                            with col3:
                                st.metric("Finish", f"{lot.finish_score or 0:.1f}/100")
                            with col4:
                                st.metric("Overall", f"{lot.overall_score or 0:.1f}/100")
                            
                            # Radar chart
                            categories = ['Aroma', 'Taste', 'Finish', 'Overall']
                            values = [
                                lot.aroma_score or 0,
                                lot.taste_score or 0,
                                lot.finish_score or 0,
                                lot.overall_score or 0
                            ]
                            
                            fig = go.Figure()
                            fig.add_trace(go.Scatterpolar(
                                r=values,
                                theta=categories,
                                fill='toself'
                            ))
                            
                            fig.update_layout(
                                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                                showlegend=False,
                                title="Sensory Profile"
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Sensory profiles
                    profiles = get_sensory_profiles_by_lot(session, view_lot)
                    
                    if profiles:
                        with st.expander("📝 Tasting Notes", expanded=True):
                            for i, profile in enumerate(profiles, 1):
                                st.markdown(f"**Tasting #{i}** by {profile.taster_name} on {profile.tasting_date.strftime('%Y-%m-%d') if profile.tasting_date else 'N/A'}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if profile.color_description:
                                        st.write(f"**Color:** {profile.color_description}")
                                    if profile.aroma_notes:
                                        st.write(f"**Aroma:** {profile.aroma_notes}")
                                    if profile.flavor_notes:
                                        st.write(f"**Flavor:** {profile.flavor_notes}")
                                
                                with col2:
                                    if profile.mouthfeel:
                                        st.write(f"**Mouthfeel:** {profile.mouthfeel}")
                                    if profile.finish_description:
                                        st.write(f"**Finish:** {profile.finish_description}")
                                
                                st.divider()
                    
                    # Notes
                    if lot.notes:
                        with st.expander("📋 Additional Notes"):
                            st.write(lot.notes)
        
        session.close()
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Tab 3: Compare LOTs
with tab3:
    st.subheader("Compare Multiple LOTs")
    
    try:
        session = get_session()
        lots = get_all_lots(session)
        
        if lots and len(lots) >= 2:
            lot_numbers = [lot.lot_number for lot in lots]
            
            selected_lots = st.multiselect(
                "Select LOTs to Compare (2-5)",
                lot_numbers,
                max_selections=5
            )
            
            if len(selected_lots) >= 2:
                comparison_data = []
                
                for lot_num in selected_lots:
                    lot = get_lot_by_number(session, lot_num)
                    comparison_data.append({
                        'LOT': lot.lot_number,
                        'Product': lot.product_name,
                        'ABV %': lot.alcohol_content,
                        'pH': lot.acidity,
                        'Sugar': lot.sugar_content,
                        'Tannin': lot.tannin_level,
                        'Ester': lot.ester_concentration,
                        'Aldehyde': lot.aldehyde_level,
                        'Aroma Score': lot.aroma_score or 0,
                        'Taste Score': lot.taste_score or 0,
                        'Finish Score': lot.finish_score or 0,
                        'Overall Score': lot.overall_score or 0
                    })
                
                df = pd.DataFrame(comparison_data)
                
                # Display comparison table
                st.markdown("### 📊 Comparison Table")
                st.dataframe(df, use_container_width=True)
                
                # Chemical composition comparison
                st.markdown("### 🧪 Chemical Comparison")
                
                chemical_features = ['ABV %', 'pH', 'Sugar', 'Tannin', 'Ester', 'Aldehyde']
                
                fig = go.Figure()
                
                for lot_num in selected_lots:
                    lot_data = df[df['LOT'] == lot_num].iloc[0]
                    values = [lot_data[feat] for feat in chemical_features]
                    
                    fig.add_trace(go.Bar(
                        name=f"LOT {lot_num}",
                        x=chemical_features,
                        y=values
                    ))
                
                fig.update_layout(
                    title="Chemical Composition Comparison",
                    xaxis_title="Chemical Parameter",
                    yaxis_title="Value",
                    barmode='group',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Sensory scores comparison
                st.markdown("### 🎯 Sensory Scores Comparison")
                
                sensory_features = ['Aroma Score', 'Taste Score', 'Finish Score', 'Overall Score']
                
                fig2 = go.Figure()
                
                for lot_num in selected_lots:
                    lot_data = df[df['LOT'] == lot_num].iloc[0]
                    values = [lot_data[feat] for feat in sensory_features]
                    
                    fig2.add_trace(go.Scatterpolar(
                        r=values,
                        theta=[s.replace(' Score', '') for s in sensory_features],
                        fill='toself',
                        name=f"LOT {lot_num}"
                    ))
                
                fig2.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    title="Sensory Scores Radar Comparison"
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            
            elif len(selected_lots) == 1:
                st.info("ℹ️ Select at least 2 LOTs to compare")
        else:
            st.warning("⚠️ Need at least 2 LOT records to enable comparison.")
        
        session.close()
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
