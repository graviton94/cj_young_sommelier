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
tab1, tab2, tab3, tab4 = st.tabs(["⚗️ 화학 성분 분석 관리", "👅 관능 점수 (T/C 비교분석) 관리", "🧪 향미 관리지표 (Flavor Indicators) 관리", "🔬 GCMS 물질 항목 관리"])

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
            st.dataframe(df, use_container_width=True, hide_index=True)
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

# ==========================================
# Tab 4: GCMS Management
# ==========================================
with tab4:
    st.subheader("GCMS 물질 관리 및 향미 Hint 설정")
    st.markdown("""
    화학 라이브러리(PubChem, RDKit)를 활용하여 GCMS 물질을 검색하고 등록합니다.
    - **자동 생성**: CAS 번호나 물질명을 입력하면 SMILES, 분자량, 구조 등을 자동으로 가져옵니다.
    - **필수 입력**: '물질명' 혹은 'CAS 번호'
    """)
    
    try:
        session = get_session()
        gcms_indices = get_all_indices(session, gcms_only=True)
        
        # Display existing
        st.markdown("### 📋 등록된 GCMS 물질 목록")
        
        if gcms_indices:
            data = []
            for idx in gcms_indices:
                data.append({
                    'ID': idx.id,
                    '표시 이름': idx.name,
                    # '단위': idx.unit, # Removed
                    'CAS': idx.cas_number,
                    'MW': idx.molecular_weight,
                    'LogP': getattr(idx, 'log_p', None),
                    '작용기': getattr(idx, 'functional_groups', None),
                    '향미 Hint': idx.flavor_hint
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("등록된 GCMS 물질이 없습니다.")
            
        st.divider()
        
        col_l, col_r = st.columns(2, gap=COL_GAP)
        
        # --- LEFT: ADD NEW ITEM ---
        with col_l:
            st.subheader("➕ 새 물질 검색 및 추가")
            
            # Step 1: Search
            with st.container(): # Group search UI
                search_query = st.text_input("물질 검색 (CAS 번호 또는 영문명)", key="search_q")
                search_btn = st.button("🔍 PubChem 검색")
                
                if 'found_chem' not in st.session_state:
                    st.session_state['found_chem'] = None
                    
                if search_btn and search_query:
                    with st.spinner("PubChem 검색 및 속성 계산 중..."):
                        info = lookup_compound(search_query)
                        if info and not info.get('error'):
                            # Calculate Properties
                            if info.get('smiles'):
                                props = get_rdkit_properties(info['smiles'])
                                if props and not props.get('error'):
                                    info.update(props)
                            
                            st.session_state['found_chem'] = info
                            # Generate Image
                            if info.get('smiles'):
                                img = get_molecule_image(info['smiles'])
                                st.session_state['found_chem']['image'] = img
                        else:
                            st.error(f"❌ 검색 실패: {info.get('error') if info else '결과 없음'}")
                            st.session_state['found_chem'] = None
            
            # Step 2: Form with Pre-filled data
            found = st.session_state.get('found_chem')
            
            if found:
                st.info(f"✅ 확인됨: {found.get('name')}")
                if found.get('image'):
                    st.image(found['image'], caption="2D Structure", width=150)
            
            with st.form("add_gcms_item"):
                # Pre-fill values
                default_name = found.get('name', '') if found else ''
                default_cas = found.get('cas_number', '') if found else ''
                default_smiles = found.get('smiles', '') if found else ''
                default_mw = float(found.get('molecular_weight', 0.0)) if found else 0.0
                default_formula = found.get('molecular_formula', '') if found else ''
                default_logp = float(found.get('log_p', 0.0)) if found and found.get('log_p') else 0.0
                default_groups = found.get('functional_groups', '') if found else ''
                
                c1, c2 = st.columns(2)
                with c1:
                    name = st.text_input("표시 이름*", value=default_name)
                    # unit removed
                    cas = st.text_input("CAS 번호", value=default_cas)
                
                with c2:
                    mw = st.number_input("분자량 (g/mol)", value=default_mw)
                    logp = st.number_input("LogP", value=default_logp, format="%.2f")
                
                # Parse default groups string to list
                default_groups_list = [x.strip() for x in default_groups.split(',')] if default_groups else []
                # Ensure all defaults are in options (sanity check)
                all_options = list(FUNCTIONAL_GROUP_PATTERNS.keys())
                # Filter valid
                default_groups_list = [x for x in default_groups_list if x in all_options]
                
                groups_list = st.multiselect("작용기 (Functional Groups)", options=all_options, default=default_groups_list)
                groups = ", ".join(groups_list)

                formula = st.text_input("화학식", value=default_formula)
                smiles = st.text_area("SMILES (구조)", value=default_smiles, height=70)
                # csv_header already removed
                flavor_hint = st.text_area("향미 Hint", help="예: 과일향, 파인애플, 달콤함")
                
                submitted = st.form_submit_button("➕ 물질 등록")
                
                if submitted:
                    if not name:
                        st.error("❌ 표시 이름은 필수입니다.")
                    else:
                        # Auto-generate code for GCMS
                        code = generate_code(name)
                        if cas:
                             code = f"gcms_cas_{cas}"
                        
                        # Check collision
                        while next((i for i in gcms_indices if i.code == code), None):
                            code = f"{code}_{uuid.uuid4().hex[:4]}"

                        new_item = {
                            'code': code,
                            'name': name,
                            'unit': 'Area', # Default
                            'is_gcms': 1,
                            'flavor_hint': flavor_hint,
                            'cas_number': cas,
                            'smiles': smiles,
                            'molecular_weight': mw,
                            'molecular_formula': formula,
                            'log_p': logp,
                            'functional_groups': groups,
                            'category': 'gcms'
                        }
                        add_analysis_index(session, new_item)
                        st.success(f"✅ {name} 등록 완료!")
                        st.session_state['found_chem'] = None # Reset
                        st.rerun()

        # --- RIGHT: EDIT EXISTING ---
        with col_r:
            st.subheader("✏️ 물질 수정/삭제")
            if gcms_indices:
                to_edit = st.selectbox(
                    "수정할 물질 선택",
                    options=[idx.id for idx in gcms_indices],
                    format_func=lambda x: next((f"{i.name}" for i in gcms_indices if i.id == x), str(x))
                )
                
                target = next((i for i in gcms_indices if i.id == to_edit), None)
                
                if target:
                    # Show image if SMILES exists
                    if target.smiles:
                        img = get_molecule_image(target.smiles)
                        if img:
                            st.image(img, caption="Current Structure", width=150)
                            
                    with st.form("edit_gcms_item"):
                        e_name = st.text_input("표시 이름", value=target.name)
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            e_cas = st.text_input("CAS 번호", value=target.cas_number or "")
                            e_mw = st.number_input("분자량", value=float(target.molecular_weight or 0.0))
                            e_logp = st.number_input("LogP", value=float(getattr(target, 'log_p', 0.0) or 0.0))

                        with c2:
                            e_formula = st.text_input("화학식", value=target.molecular_formula or "")
                            
                            # Functional Groups Multiselect
                            current_groups_str = getattr(target, 'functional_groups', "") or ""
                            current_groups_list = [x.strip() for x in current_groups_str.split(',')] if current_groups_str else []
                            all_options = list(FUNCTIONAL_GROUP_PATTERNS.keys())
                            current_groups_list = [x for x in current_groups_list if x in all_options]
                            
                            e_groups_list = st.multiselect("작용기", options=all_options, default=current_groups_list, key="edit_groups")
                            e_groups = ", ".join(e_groups_list)

                        
                        e_smiles = st.text_area("SMILES", value=target.smiles or "")
                        
                        e_hint = st.text_area("향미 Hint", value=target.flavor_hint or "")
                        
                        c_a, c_b = st.columns(2)
                        with c_a:
                            edit_submit = st.form_submit_button("💾 수정 저장")
                        with c_b:
                            delete_submit = st.form_submit_button("🗑️ 삭제", type="primary")
                        
                        if edit_submit:
                            update_dict = {
                                'name': e_name,
                                'flavor_hint': e_hint,
                                'cas_number': e_cas,
                                'smiles': e_smiles,
                                'molecular_weight': e_mw,
                                'molecular_formula': e_formula,
                                'log_p': e_logp,
                                'functional_groups': e_groups
                            }
                            update_analysis_index(session, target.id, update_dict)
                            st.success("✅ 수정되었습니다!")
                            st.rerun()
                            
                        if delete_submit:
                            delete_analysis_index(session, target.id)
                            st.success("✅ 삭제되었습니다!")
                            st.rerun()
            else:
                st.info("수정할 물질이 없습니다.")
        
        session.close()
    except Exception as e:
        st.error(f"❌ 오류: {str(e)}")
