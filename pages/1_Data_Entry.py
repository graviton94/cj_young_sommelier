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
    get_lot_by_number, update_lot_data, delete_lot_data,
    get_all_indices, get_lot_measurements
)

# Initialize database
init_database()

st.set_page_config(page_title="데이터 입력", page_icon="📊", layout="wide")

st.title("📊 LOT 데이터 입력 및 관리")
st.markdown("주류 LOT의 화학 성분 데이터를 입력하고 관리합니다")

# Tabs for different operations
tab1, tab2, tab3 = st.tabs(["➕ 새 LOT 추가", "📋 전체 LOT 보기", "✏️ LOT 수정/삭제"])

# Tab 1: Add New LOT
with tab1:
    st.subheader("새 LOT 데이터 입력")
    
    with st.form("new_lot_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            lot_number = st.text_input("LOT 번호 *", help="이 LOT의 고유 식별자")
            product_name = st.text_input("제품명 *", help="주류 제품명")
            production_date = st.date_input("생산일", value=datetime.now())
        
        # Dynamic Chemical Inputs
        st.markdown("### 화학 성분")
        
        session = get_session()
        try:
            # Fetch configured indices
            indices = get_all_indices(session, basic_only=True)
            
            # Prepare dictionary to capture inputs
            chemical_inputs = {}
            
            # Create a grid layout (3 columns)
            cols = st.columns(3)
            
            for i, idx in enumerate(indices):
                with cols[i % 3]:
                    val = st.number_input(
                        f"{idx.name} ({idx.unit})",
                        min_value=float(idx.min_value) if idx.min_value is not None else 0.0,
                        max_value=float(idx.max_value) if idx.max_value is not None else None,
                        step=float(idx.step) if idx.step else 0.1,
                        key=f"new_{idx.code}"
                    )
                    chemical_inputs[idx.code] = val
                    
        except Exception as e:
            st.error(f"설정 로드 오류: {str(e)}")
            indices = []
            chemical_inputs = {}
            
        st.divider()
        st.markdown("### 관능 점수 (선택사항)")
        st.caption("점수를 예측하려면 비워두세요. 실제 시음 결과가 있으면 값을 입력하세요.")
        
        col5, col6 = st.columns(2)
        
        with col5:
            aroma_score = st.number_input("향 점수 (0-100)", min_value=0.0, max_value=100.0, step=0.1)
            taste_score = st.number_input("맛 점수 (0-100)", min_value=0.0, max_value=100.0, step=0.1)
        
        with col6:
            finish_score = st.number_input("여운 점수 (0-100)", min_value=0.0, max_value=100.0, step=0.1)
            overall_score = st.number_input("종합 점수 (0-100)", min_value=0.0, max_value=100.0, step=0.1)
        
        notes = st.text_area("추가 메모", help="추가 관찰 사항이나 코멘트")
        
        submitted = st.form_submit_button("💾 LOT 데이터 저장")
        
        if submitted:
            if not lot_number or not product_name:
                st.error("❌ LOT 번호와 제품명은 필수 항목입니다!")
            else:
                try:
                    # Check if LOT already exists
                    existing = get_lot_by_number(session, lot_number)
                    if existing:
                        st.error(f"❌ LOT {lot_number}은(는) 이미 존재합니다! 수정 탭을 사용하세요.")
                    else:
                        # Combine base data with dynamic chemical inputs
                        lot_data = {
                            'lot_number': lot_number,
                            'product_name': product_name,
                            'aroma_score': aroma_score if aroma_score > 0 else None,
                            'taste_score': taste_score if taste_score > 0 else None,
                            'finish_score': finish_score if finish_score > 0 else None,
                            'overall_score': overall_score if overall_score > 0 else None,
                            'production_date': datetime.combine(production_date, datetime.min.time()),
                            'notes': notes,
                            **chemical_inputs  # Unpack dynamic inputs
                        }
                        
                        add_lot_data(session, lot_data)
                        st.success(f"✅ LOT {lot_number}이(가) 성공적으로 저장되었습니다!")
                        st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ 데이터 저장 오류: {str(e)}")
        
        session.close()

# Tab 2: View All LOTs
with tab2:
    st.subheader("전체 LOT 기록")
    
    try:
        session = get_session()
        lots = get_all_lots(session)
        indices = get_all_indices(session, basic_only=True)
        
        if lots:
            st.info(f"📦 데이터베이스 총 LOT 수: {len(lots)}")
            
            import pandas as pd
            
            data = []
            for lot in lots:
                # Basic info
                row = {
                    'LOT 번호': lot.lot_number,
                    '제품명': lot.product_name,
                    '생산일': lot.production_date.strftime('%Y-%m-%d') if lot.production_date else 'N/A',
                }
                
                # Fetch measurements (efficiently? for now loop is fine for small N)
                measurements = get_lot_measurements(session, lot.lot_number)
                msmt_map = {m.index_code: m.value for m in measurements}
                
                # Add dynamic columns based on indices configuration
                for idx in indices:
                    # Check if it's a standard column or dynamic measurement
                    val = None
                    if hasattr(lot, idx.code):
                        val = getattr(lot, idx.code)
                    else:
                        val = msmt_map.get(idx.code)
                        
                    row[f"{idx.name} ({idx.unit})"] = val
                
                data.append(row)
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 CSV로 다운로드",
                data=csv,
                file_name=f"lot_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("📭 LOT 데이터가 없습니다. '새 LOT 추가' 탭에서 데이터를 추가하세요.")
        
        session.close()
    except Exception as e:
        st.error(f"❌ 데이터 조회 오류: {str(e)}")

# Tab 3: Edit/Delete LOT
with tab3:
    st.subheader("LOT 데이터 수정 또는 삭제")
    
    try:
        session = get_session()
        lots = get_all_lots(session)
        indices = get_all_indices(session, basic_only=True)
        
        if lots:
            lot_numbers = [lot.lot_number for lot in lots]
            selected_lot = st.selectbox("수정/삭제할 LOT 선택", lot_numbers)
            
            if selected_lot:
                lot = get_lot_by_number(session, selected_lot)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### 수정 중: LOT {selected_lot}")
                
                with col2:
                    if st.button("🗑️ LOT 삭제", type="secondary"):
                        try:
                            delete_lot_data(session, selected_lot)
                            st.success(f"✅ LOT {selected_lot}이(가) 삭제되었습니다!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ LOT 삭제 오류: {str(e)}")
                
                # Edit form
                with st.form("edit_lot_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_product_name = st.text_input("제품명", value=lot.product_name)
                    
                    st.subheader("화학 성분 수정")
                    
                    # Fetch existing measurements
                    measurements = get_lot_measurements(session, lot.lot_number)
                    msmt_map = {m.index_code: m.value for m in measurements}
                    
                    edit_inputs = {}
                    cols = st.columns(3)
                    
                    for i, idx in enumerate(indices):
                        # Determine current value
                        current_val = 0.0
                        if hasattr(lot, idx.code):
                            v = getattr(lot, idx.code)
                            current_val = float(v) if v is not None else 0.0
                        else:
                            v = msmt_map.get(idx.code)
                            current_val = float(v) if v is not None else 0.0
                        
                        with cols[i % 3]:
                            val = st.number_input(
                                f"{idx.name} ({idx.unit})",
                                min_value=float(idx.min_value) if idx.min_value is not None else 0.0,
                                max_value=float(idx.max_value) if idx.max_value is not None else None,
                                step=float(idx.step) if idx.step else 0.1,
                                value=current_val,
                                key=f"edit_{idx.code}"
                            )
                            edit_inputs[idx.code] = val
                    
                    st.divider()
                    new_notes = st.text_area("메모", value=lot.notes or "")
                    
                    update_submitted = st.form_submit_button("💾 LOT 업데이트")
                    
                    if update_submitted:
                        update_dict = {
                            'product_name': new_product_name,
                            'notes': new_notes,
                            **edit_inputs
                        }
                        
                        update_lot_data(session, selected_lot, update_dict)
                        st.success(f"✅ LOT {selected_lot}이(가) 성공적으로 업데이트되었습니다!")
        else:
            st.warning("📭 수정할 LOT 데이터가 없습니다.")
        
        session.close()
    except Exception as e:
        st.error(f"❌ 오류: {str(e)}")
