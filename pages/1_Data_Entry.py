"""
Data Entry Page - Input and manage LOT chemical composition data
"""

import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import (
    init_database, get_session, add_lot_data, get_all_lots,
    get_lot_by_number, update_lot_data, delete_lot_data
)

# Initialize database
init_database()

st.set_page_config(page_title="Data Entry", page_icon="📊", layout="wide")

st.title("📊 LOT Data Entry & Management")
st.markdown("Input and manage chemical composition data for liquor LOTs")

# Tabs for different operations
tab1, tab2, tab3 = st.tabs(["➕ Add New LOT", "📋 View All LOTs", "✏️ Edit/Delete LOT"])

# Tab 1: Add New LOT
with tab1:
    st.subheader("Enter New LOT Data")
    
    with st.form("new_lot_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            lot_number = st.text_input("LOT Number *", help="Unique identifier for this LOT")
            product_name = st.text_input("Product Name *", help="Name of the liquor product")
            production_date = st.date_input("Production Date", value=datetime.now())
        
        with col2:
            st.markdown("### Chemical Composition")
            alcohol_content = st.number_input(
                "Alcohol Content (% ABV)", 
                min_value=0.0, max_value=100.0, value=40.0, step=0.1
            )
            acidity = st.number_input(
                "Acidity (pH)", 
                min_value=0.0, max_value=14.0, value=7.0, step=0.1
            )
            sugar_content = st.number_input(
                "Sugar Content (g/L)", 
                min_value=0.0, value=0.0, step=0.1
            )
        
        col3, col4 = st.columns(2)
        
        with col3:
            tannin_level = st.number_input(
                "Tannin Level (mg/L)", 
                min_value=0.0, value=0.0, step=0.1
            )
            ester_concentration = st.number_input(
                "Ester Concentration (mg/L)", 
                min_value=0.0, value=0.0, step=0.1
            )
        
        with col4:
            aldehyde_level = st.number_input(
                "Aldehyde Level (mg/L)", 
                min_value=0.0, value=0.0, step=0.1
            )
        
        st.markdown("### Sensory Scores (Optional)")
        st.caption("Leave blank if you want to predict scores. Enter values if you have actual tasting results.")
        
        col5, col6 = st.columns(2)
        
        with col5:
            aroma_score = st.number_input(
                "Aroma Score (0-100)", 
                min_value=0.0, max_value=100.0, value=0.0, step=0.1
            )
            taste_score = st.number_input(
                "Taste Score (0-100)", 
                min_value=0.0, max_value=100.0, value=0.0, step=0.1
            )
        
        with col6:
            finish_score = st.number_input(
                "Finish Score (0-100)", 
                min_value=0.0, max_value=100.0, value=0.0, step=0.1
            )
            overall_score = st.number_input(
                "Overall Score (0-100)", 
                min_value=0.0, max_value=100.0, value=0.0, step=0.1
            )
        
        notes = st.text_area("Additional Notes", help="Any additional observations or comments")
        
        submitted = st.form_submit_button("💾 Save LOT Data")
        
        if submitted:
            if not lot_number or not product_name:
                st.error("❌ LOT Number and Product Name are required!")
            else:
                try:
                    session = get_session()
                    
                    # Check if LOT already exists
                    existing = get_lot_by_number(session, lot_number)
                    if existing:
                        st.error(f"❌ LOT {lot_number} already exists! Use Edit tab to update.")
                    else:
                        lot_data = {
                            'lot_number': lot_number,
                            'product_name': product_name,
                            'alcohol_content': alcohol_content,
                            'acidity': acidity,
                            'sugar_content': sugar_content,
                            'tannin_level': tannin_level,
                            'ester_concentration': ester_concentration,
                            'aldehyde_level': aldehyde_level,
                            'aroma_score': aroma_score if aroma_score > 0 else None,
                            'taste_score': taste_score if taste_score > 0 else None,
                            'finish_score': finish_score if finish_score > 0 else None,
                            'overall_score': overall_score if overall_score > 0 else None,
                            'production_date': datetime.combine(production_date, datetime.min.time()),
                            'notes': notes
                        }
                        
                        add_lot_data(session, lot_data)
                        st.success(f"✅ LOT {lot_number} saved successfully!")
                        st.balloons()
                    
                    session.close()
                except Exception as e:
                    st.error(f"❌ Error saving data: {str(e)}")

# Tab 2: View All LOTs
with tab2:
    st.subheader("All LOT Records")
    
    try:
        session = get_session()
        lots = get_all_lots(session)
        
        if lots:
            st.info(f"📦 Total LOTs in database: {len(lots)}")
            
            # Convert to display format
            import pandas as pd
            
            data = []
            for lot in lots:
                data.append({
                    'LOT Number': lot.lot_number,
                    'Product': lot.product_name,
                    'ABV %': lot.alcohol_content,
                    'pH': lot.acidity,
                    'Sugar (g/L)': lot.sugar_content,
                    'Production Date': lot.production_date.strftime('%Y-%m-%d') if lot.production_date else 'N/A',
                    'Entry Date': lot.entry_date.strftime('%Y-%m-%d') if lot.entry_date else 'N/A'
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"lot_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("📭 No LOT data found. Add some data in the 'Add New LOT' tab.")
        
        session.close()
    except Exception as e:
        st.error(f"❌ Error retrieving data: {str(e)}")

# Tab 3: Edit/Delete LOT
with tab3:
    st.subheader("Edit or Delete LOT Data")
    
    try:
        session = get_session()
        lots = get_all_lots(session)
        
        if lots:
            lot_numbers = [lot.lot_number for lot in lots]
            selected_lot = st.selectbox("Select LOT to Edit/Delete", lot_numbers)
            
            if selected_lot:
                lot = get_lot_by_number(session, selected_lot)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### Editing LOT: {selected_lot}")
                
                with col2:
                    if st.button("🗑️ Delete LOT", type="secondary"):
                        try:
                            delete_lot_data(session, selected_lot)
                            st.success(f"✅ LOT {selected_lot} deleted!")
                            # Clear the confirm state after successful deletion
                            if 'confirm_delete' in st.session_state:
                                del st.session_state['confirm_delete']
                            # Wait a moment before suggesting refresh
                            st.info("💡 Refresh the page to see updated list")
                        except Exception as e:
                            st.error(f"❌ Error deleting LOT: {str(e)}")
                
                # Edit form
                with st.form("edit_lot_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_product_name = st.text_input("Product Name", value=lot.product_name)
                        new_alcohol = st.number_input("Alcohol Content (%)", value=float(lot.alcohol_content or 0))
                        new_acidity = st.number_input("Acidity (pH)", value=float(lot.acidity or 0))
                        new_sugar = st.number_input("Sugar Content (g/L)", value=float(lot.sugar_content or 0))
                    
                    with col2:
                        new_tannin = st.number_input("Tannin Level (mg/L)", value=float(lot.tannin_level or 0))
                        new_ester = st.number_input("Ester Concentration (mg/L)", value=float(lot.ester_concentration or 0))
                        new_aldehyde = st.number_input("Aldehyde Level (mg/L)", value=float(lot.aldehyde_level or 0))
                    
                    new_notes = st.text_area("Notes", value=lot.notes or "")
                    
                    update_submitted = st.form_submit_button("💾 Update LOT")
                    
                    if update_submitted:
                        update_dict = {
                            'product_name': new_product_name,
                            'alcohol_content': new_alcohol,
                            'acidity': new_acidity,
                            'sugar_content': new_sugar,
                            'tannin_level': new_tannin,
                            'ester_concentration': new_ester,
                            'aldehyde_level': new_aldehyde,
                            'notes': new_notes
                        }
                        
                        update_lot_data(session, selected_lot, update_dict)
                        st.success(f"✅ LOT {selected_lot} updated successfully!")
        else:
            st.warning("📭 No LOT data available to edit.")
        
        session.close()
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
