"""
Settings Page - Manage analysis indices, units, and GCMS configuration
"""

import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path
import json

# Add project root to path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from src.database import (
    init_database, get_session, 
    get_all_indices, add_analysis_index, 
    update_analysis_index, delete_analysis_index
)
from src.chem_utils import lookup_compound, get_molecule_image, get_rdkit_properties, FUNCTIONAL_GROUP_PATTERNS

# Initialize database
init_database()

st.set_page_config(page_title="설정", page_icon="⚙️", layout="wide")

st.title("⚙️ 시스템 설정")
st.markdown("분석 항목, GCMS 데이터 양식 및 향미 Hint를 관리합니다")

# Tabs
tab1, tab2, tab3 = st.tabs(["⚗️ 화학 성분 분석 관리", "👅 관능 점수 (T/C 비교분석) 관리", "🧪 향미 관리지표 (Flavor Indicators) 관리"])

# Common styles
COL_GAP = "large"

import uuid

def generate_code(name):
    """Generate a unique internal code from name"""
    # Simple slugify: Ethyl Acetate -> ethyl_acetate
    # If Korean or special chars, fallback to uuid
    import re
    if re.match(r'^[a-zA-Z0-9\s]+$', name):
        slug = name.lower().replace(' ', '_')
        return slug
    return f"item_{uuid.uuid4().hex[:8]}"

# Helper for rendering Basic/Sensory tabs (since they share logic)
def render_index_management(category, tab_label):
    st.subheader(f"{tab_label} 설정")
    st.info("💡 이곳에서 설정한 '항목명'과 '입력 범위'가 데이터 입력 페이지에 반영됩니다.")
    
    try:
        session = get_session()
        indices = get_all_indices(session, category=category)
        
        # Display as table
        if indices:
            data = []
            for idx in indices:
                data.append({
                    'ID': idx.id,
                    '항목명': idx.name,
                    '단위': idx.unit,
                    '하한치': idx.min_value,
                    '상한치': idx.max_value,
                    '입력 단위': idx.step,
                    '표시 순서': idx.display_order
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("등록된 항목이 없습니다.")
        
        st.divider()
        
        col_l, col_r = st.columns(2, gap=COL_GAP)
        
        # --- LEFT: ADD NEW ITEM ---
        with col_l:
            st.subheader("➕ 새 항목 추가")
            with st.form(f"add_{category}_item"):
                # Code input removed - auto-generated
                name = st.text_input("항목명", help="화면에 표시될 이름 (예: 향 점수)")
                unit = st.text_input("단위", value="점" if category == 'sensory' else "")
                
                c3, c4, c5 = st.columns(3)
                with c3:
                    min_val = st.number_input("하한치", value=0.0)
                with c4:
                    max_val = st.number_input("상한치 (0=없음)", value=100.0 if category == 'sensory' else 0.0)
                with c5:
                    step = st.number_input("입력 단위", value=1.0 if category == 'sensory' else 0.1)
                
                order = st.number_input("표시 순서", value=len(indices)+1, step=1)
                
                submitted = st.form_submit_button("➕ 항목 등록")
                
                if submitted:
                    if not name:
                        st.error("❌ 항목명은 필수입니다.")
                    else:
                        # Auto-generate code
                        code = generate_code(name)
                        
                        # Check collision just in case (though uuid makes it rare)
                        while next((i for i in indices if i.code == code), None):
                            code = f"{code}_{uuid.uuid4().hex[:4]}"

                        new_item = {
                            'code': code,
                            'name': name,
                            'unit': unit,
                            'min_value': min_val,
                            'max_value': max_val if max_val > 0 else None,
                            'step': step,
                            'display_order': order,
                            'category': category
                        }
                        add_analysis_index(session, new_item)
                        st.success("✅ 등록되었습니다!")
                        st.rerun()

        # --- RIGHT: EDIT EXISTING ---
        with col_r:
            st.subheader("✏️ 항목 수정/삭제")
            
            if indices:
                selected_id = st.selectbox(
                    "수정할 항목 선택", 
                    options=[d.id for d in indices],
                    format_func=lambda x: next((d.name for d in indices if d.id == x), str(x)),
                    key=f"select_{category}"
                )
                
                target = next((i for i in indices if i.id == selected_id), None)
                
                if target:
                    with st.form(f"edit_{category}_item"):
                        e_name = st.text_input("항목명", value=target.name)
                        e_unit = st.text_input("단위", value=target.unit)
                        
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            e_min = st.number_input("하한치", value=float(target.min_value or 0))
                        with c2:
                            e_max = st.number_input("상한치 (0=없음)", value=float(target.max_value or 0))
                        with c3:
                            e_step = st.number_input("입력 단위", value=float(target.step or 0.1), format="%.2f")
                        
                        e_order = st.number_input("표시 순서", value=int(target.display_order or 0), step=1)
                        
                        c_a, c_b = st.columns(2)
                        with c_a:
                            edit_submit = st.form_submit_button("💾 수정 저장")
                        with c_b:
                            delete_submit = st.form_submit_button("🗑️ 삭제", type="primary")
                        
                        if edit_submit:
                            update_dict = {
                                'name': e_name,
                                'unit': e_unit,
                                'min_value': e_min,
                                'max_value': e_max if e_max > 0 else None,
                                'step': e_step,
                                'display_order': e_order
                            }
                            update_analysis_index(session, selected_id, update_dict)
                            st.success("✅ 수정되었습니다!")
                            st.rerun()
                        
                        if delete_submit:
                            delete_analysis_index(session, selected_id)
                            st.success("✅ 삭제되었습니다!")
                            st.rerun()
            else:
                st.info("수정할 항목이 없습니다.")
        
        session.close()
    except Exception as e:
        st.error(f"❌ 오류: {str(e)}")

# Tab 1: Basic Analysis Items
with tab1:
    render_index_management('basic', '⚗️ 화학 성분 분석')

# Tab 2: Sensory Scores
with tab2:
    render_index_management('sensory', '👅 관능 점수 (T/C 비교분석)')


# Tab 3: Flavor Indicators
with tab3:
    render_index_management('flavor_indicator', '🧪 향미 관리지표 (Flavor Indicators)')
