"""
Report Page - Generate comprehensive flavor reports using Google Gemini AI
"""

import streamlit as st
import sys
from pathlib import Path
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import init_database, get_session, get_all_lots, get_lot_by_number, get_sensory_profiles_by_lot
from src.llm import GeminiFlavorReporter, test_gemini_connection
from src.analysis import SensoryPredictor

# Initialize database
init_database()

st.set_page_config(page_title="AI Reports", page_icon="📝", layout="wide")

st.title("📝 AI-Powered Flavor Reports")
st.markdown("Generate comprehensive flavor reports using Google Gemini AI")

# Check API key configuration
api_key_configured = os.getenv('GEMINI_API_KEY') is not None

if not api_key_configured:
    st.warning("⚠️ **Gemini API Key Not Configured**")
    st.info("""
    To use AI-powered reports, you need to set up your Google Gemini API key:
    
    1. Get an API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
    2. Create a `.env` file in the project root (or set environment variable)
    3. Add: `GEMINI_API_KEY=your_api_key_here`
    
    You can also enter the API key below for this session:
    """)
    
    temp_api_key = st.text_input("Enter Gemini API Key (temporary)", type="password")
    
    if temp_api_key:
        os.environ['GEMINI_API_KEY'] = temp_api_key
        if st.button("Test Connection"):
            if test_gemini_connection(temp_api_key):
                st.success("✅ API key is valid! You can now generate reports.")
                api_key_configured = True
            else:
                st.error("❌ Invalid API key or connection failed.")

# Main functionality (only if API key is configured)
if api_key_configured or os.getenv('GEMINI_API_KEY'):
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Flavor Report",
        "🔬 Chemical Insights",
        "⚖️ Comparison Report",
        "🏷️ Sensory Descriptors"
    ])
    
    # Tab 1: Generate Flavor Report
    with tab1:
        st.subheader("Generate Comprehensive Flavor Report")
        
        try:
            session = get_session()
            lots = get_all_lots(session)
            
            if lots:
                lot_numbers = [lot.lot_number for lot in lots]
                selected_lot = st.selectbox("Select LOT for Report", lot_numbers)
                
                if selected_lot:
                    lot = get_lot_by_number(session, selected_lot)
                    
                    st.info(f"📦 Generating report for: {lot.product_name} (LOT {lot.lot_number})")
                    
                    # Display current data
                    with st.expander("📊 View LOT Data"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Chemical Composition:**")
                            st.write(f"- Alcohol Content: {lot.alcohol_content}% ABV")
                            st.write(f"- Acidity: {lot.acidity} pH")
                            st.write(f"- Sugar Content: {lot.sugar_content} g/L")
                            st.write(f"- Tannin Level: {lot.tannin_level} mg/L")
                            st.write(f"- Ester Concentration: {lot.ester_concentration} mg/L")
                            st.write(f"- Aldehyde Level: {lot.aldehyde_level} mg/L")
                        
                        with col2:
                            if lot.aroma_score:
                                st.markdown("**Sensory Scores:**")
                                st.write(f"- Aroma: {lot.aroma_score}/100")
                                st.write(f"- Taste: {lot.taste_score}/100")
                                st.write(f"- Finish: {lot.finish_score}/100")
                                st.write(f"- Overall: {lot.overall_score}/100")
                    
                    # Option to include predicted scores
                    use_predictions = False
                    if not lot.aroma_score:
                        st.info("ℹ️ No sensory scores recorded. You can include AI predictions in the report.")
                        use_predictions = st.checkbox("Include Predicted Sensory Scores", value=True)
                    
                    if st.button("🤖 Generate AI Flavor Report", type="primary"):
                        with st.spinner("Generating report with Gemini AI..."):
                            try:
                                reporter = GeminiFlavorReporter()
                                
                                # Prepare chemical data
                                chemical_data = {
                                    'alcohol_content': lot.alcohol_content,
                                    'acidity': lot.acidity,
                                    'sugar_content': lot.sugar_content,
                                    'tannin_level': lot.tannin_level,
                                    'ester_concentration': lot.ester_concentration,
                                    'aldehyde_level': lot.aldehyde_level
                                }
                                
                                # Prepare sensory scores
                                sensory_scores = None
                                if lot.aroma_score:
                                    sensory_scores = {
                                        'aroma_score': lot.aroma_score,
                                        'taste_score': lot.taste_score,
                                        'finish_score': lot.finish_score,
                                        'overall_score': lot.overall_score
                                    }
                                elif use_predictions:
                                    # Try to load model and predict
                                    try:
                                        model_path = Path(__file__).resolve().parent.parent / "data" / "models" / "sensory_predictor_random_forest.pkl"
                                        if model_path.exists():
                                            predictor = SensoryPredictor(model_type='random_forest')
                                            predictor.load_models(model_path)
                                            sensory_scores = predictor.predict(chemical_data)
                                            st.info("📊 Using ML-predicted sensory scores")
                                    except:
                                        pass
                                
                                # Get sensory notes if available
                                sensory_notes = None
                                profiles = get_sensory_profiles_by_lot(session, selected_lot)
                                if profiles:
                                    profile = profiles[0]  # Use most recent
                                    sensory_notes = {
                                        'color': profile.color_description,
                                        'aroma_notes': profile.aroma_notes,
                                        'flavor_notes': profile.flavor_notes,
                                        'mouthfeel': profile.mouthfeel,
                                        'finish': profile.finish_description
                                    }
                                
                                # Generate report
                                report = reporter.generate_flavor_report(
                                    chemical_data,
                                    sensory_scores,
                                    sensory_notes
                                )
                                
                                st.success("✅ Report generated successfully!")
                                
                                # Display report
                                st.markdown("---")
                                st.markdown("## 🍷 Flavor Report")
                                st.markdown(f"**Product:** {lot.product_name}")
                                st.markdown(f"**LOT:** {lot.lot_number}")
                                st.markdown("---")
                                st.markdown(report)
                                
                                # Download option
                                st.download_button(
                                    label="📥 Download Report",
                                    data=report,
                                    file_name=f"flavor_report_{selected_lot}.txt",
                                    mime="text/plain"
                                )
                                
                            except Exception as e:
                                st.error(f"❌ Error generating report: {str(e)}")
            else:
                st.warning("📭 No LOT data available. Add data in the Data Entry page first.")
            
            session.close()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # Tab 2: Chemical Insights
    with tab2:
        st.subheader("Chemical Composition Insights")
        
        try:
            session = get_session()
            lots = get_all_lots(session)
            
            if lots:
                lot_numbers = [lot.lot_number for lot in lots]
                selected_lot = st.selectbox("Select LOT for Chemical Analysis", lot_numbers, key="chem_insights")
                
                if selected_lot:
                    lot = get_lot_by_number(session, selected_lot)
                    
                    if st.button("🔬 Generate Chemical Insights", type="primary"):
                        with st.spinner("Analyzing chemical composition..."):
                            try:
                                reporter = GeminiFlavorReporter()
                                
                                chemical_data = {
                                    'alcohol_content': lot.alcohol_content,
                                    'acidity': lot.acidity,
                                    'sugar_content': lot.sugar_content,
                                    'tannin_level': lot.tannin_level,
                                    'ester_concentration': lot.ester_concentration,
                                    'aldehyde_level': lot.aldehyde_level,
                                    'product_name': lot.product_name,
                                    'lot_number': lot.lot_number
                                }
                                
                                insights = reporter.generate_chemical_insights(chemical_data)
                                
                                st.success("✅ Insights generated!")
                                st.markdown("---")
                                st.markdown(insights)
                                
                                st.download_button(
                                    label="📥 Download Insights",
                                    data=insights,
                                    file_name=f"chemical_insights_{selected_lot}.txt",
                                    mime="text/plain"
                                )
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("📭 No LOT data available.")
            
            session.close()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # Tab 3: Comparison Report
    with tab3:
        st.subheader("AI-Powered LOT Comparison")
        
        try:
            session = get_session()
            lots = get_all_lots(session)
            
            if lots and len(lots) >= 2:
                lot_numbers = [lot.lot_number for lot in lots]
                
                selected_lots = st.multiselect(
                    "Select LOTs to Compare (2-5)",
                    lot_numbers,
                    max_selections=5,
                    key="compare_lots"
                )
                
                if len(selected_lots) >= 2:
                    focus_lot = st.selectbox("Focus LOT (primary for comparison)", selected_lots)
                    
                    if st.button("⚖️ Generate Comparison Report", type="primary"):
                        with st.spinner("Generating comparison report..."):
                            try:
                                reporter = GeminiFlavorReporter()
                                
                                lot_data_list = []
                                for lot_num in selected_lots:
                                    lot = get_lot_by_number(session, lot_num)
                                    lot_data_list.append({
                                        'lot_number': lot.lot_number,
                                        'product_name': lot.product_name,
                                        'alcohol_content': lot.alcohol_content,
                                        'acidity': lot.acidity,
                                        'sugar_content': lot.sugar_content,
                                        'tannin_level': lot.tannin_level,
                                        'ester_concentration': lot.ester_concentration,
                                        'aldehyde_level': lot.aldehyde_level,
                                        'aroma_score': lot.aroma_score,
                                        'taste_score': lot.taste_score,
                                        'finish_score': lot.finish_score,
                                        'overall_score': lot.overall_score
                                    })
                                
                                report = reporter.generate_comparison_report(lot_data_list, focus_lot)
                                
                                st.success("✅ Comparison report generated!")
                                st.markdown("---")
                                st.markdown(report)
                                
                                st.download_button(
                                    label="📥 Download Comparison",
                                    data=report,
                                    file_name=f"comparison_report_{focus_lot}.txt",
                                    mime="text/plain"
                                )
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                else:
                    st.info("ℹ️ Select at least 2 LOTs to compare")
            else:
                st.warning("⚠️ Need at least 2 LOT records for comparison.")
            
            session.close()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # Tab 4: Sensory Descriptors
    with tab4:
        st.subheader("Generate Sensory Descriptors")
        
        st.info("💡 Get AI-generated sensory descriptors based on chemical composition and predicted scores")
        
        try:
            session = get_session()
            lots = get_all_lots(session)
            
            if lots:
                lot_numbers = [lot.lot_number for lot in lots]
                selected_lot = st.selectbox("Select LOT", lot_numbers, key="descriptors")
                
                if selected_lot:
                    lot = get_lot_by_number(session, selected_lot)
                    
                    if st.button("🏷️ Generate Descriptors", type="primary"):
                        with st.spinner("Generating sensory descriptors..."):
                            try:
                                reporter = GeminiFlavorReporter()
                                
                                chemical_data = {
                                    'alcohol_content': lot.alcohol_content,
                                    'acidity': lot.acidity,
                                    'sugar_content': lot.sugar_content,
                                    'tannin_level': lot.tannin_level,
                                    'ester_concentration': lot.ester_concentration,
                                    'aldehyde_level': lot.aldehyde_level
                                }
                                
                                # Get or predict sensory scores
                                predicted_scores = {
                                    'aroma_score': lot.aroma_score or 75,
                                    'taste_score': lot.taste_score or 75,
                                    'finish_score': lot.finish_score or 75,
                                    'overall_score': lot.overall_score or 75
                                }
                                
                                descriptors = reporter.generate_sensory_descriptors(
                                    chemical_data,
                                    predicted_scores
                                )
                                
                                st.success("✅ Descriptors generated!")
                                
                                # Display in columns
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("### 👃 Aroma Descriptors")
                                    for desc in descriptors.get('aroma', []):
                                        if desc:
                                            st.markdown(f"- {desc}")
                                    
                                    st.markdown("### 👅 Flavor Descriptors")
                                    for desc in descriptors.get('flavor', []):
                                        if desc:
                                            st.markdown(f"- {desc}")
                                
                                with col2:
                                    st.markdown("### 🥃 Mouthfeel Descriptors")
                                    for desc in descriptors.get('mouthfeel', []):
                                        if desc:
                                            st.markdown(f"- {desc}")
                                    
                                    st.markdown("### ✨ Finish Descriptors")
                                    for desc in descriptors.get('finish', []):
                                        if desc:
                                            st.markdown(f"- {desc}")
                                
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("📭 No LOT data available.")
            
            session.close()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

else:
    st.warning("⚠️ Please configure your Gemini API key to use this feature.")
