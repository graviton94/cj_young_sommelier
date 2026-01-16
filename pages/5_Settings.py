"""
Settings Page - Manage analysis indices, units, and GCMS configuration
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import (
    init_database, get_session, 
    get_all_indices, add_analysis_index, 
    update_analysis_index, delete_analysis_index
)

# Initialize database
init_database()

st.set_page_config(page_title="설정", page_icon="⚙️", layout="wide")

st.title("⚙️ 시스템 설정")
st.markdown("분석 항목, GCMS 데이터 양식 및 향미 Hint를 관리합니다")

# Tabs
tab1, tab2 = st.tabs(["📊 기본 분석 항목 관리", "🔬 GCMS 물질 및 향미 관리"])

# Tab 1: Basic Analysis Items
with tab1:
    st.subheader("기본 화학 분석 항목 설정")
    st.info("💡 이곳에서 설정한 '항목명'과 '단위'가 데이터 입력 페이지에 반영됩니다.")
    
    try:
        session = get_session()
        basic_indices = get_all_indices(session, basic_only=True)
        
        # Display as table
        data = []
        for idx in basic_indices:
            data.append({
                'ID': idx.id,
                '코드': idx.code,
                '항목명': idx.name,
                '단위': idx.unit,
                '최소값': idx.min_value,
                '최대값': idx.max_value,
                'Step': idx.step,
                '표시 순서': idx.display_order
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df.style.highlight_max(axis=0), use_container_width=True)
        
        st.markdown("### 항목 수정")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            selected_id = st.selectbox(
                "수정할 항목 선택", 
                options=[d['ID'] for d in data],
                format_func=lambda x: next((d['항목명'] for d in data if d['ID'] == x), str(x))
            )
        
        if selected_id:
            idx = next((i for i in basic_indices if i.id == selected_id), None)
            if idx:
                with st.form("edit_basic_index"):
                    new_name = st.text_input("항목명", value=idx.name)
                    new_unit = st.text_input("단위", value=idx.unit)
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        new_min = st.number_input("최소값", value=float(idx.min_value or 0))
                    with c2:
                        new_max = st.number_input("최대값 (없음=0)", value=float(idx.max_value or 0))
                    with c3:
                        new_step = st.number_input("입력 단위 (Step)", value=float(idx.step or 0.1), format="%.2f")
                    
                    submitted = st.form_submit_button("💾 설정 저장")
                    
                    if submitted:
                        update_dict = {
                            'name': new_name,
                            'unit': new_unit,
                            'min_value': new_min,
                            'max_value': new_max if new_max > 0 else None,
                            'step': new_step
                        }
                        update_analysis_index(session, selected_id, update_dict)
                        st.success("✅ 설정이 업데이트되었습니다! 페이지를 새로고침하면 적용됩니다.")
                        st.balloons()
        
        session.close()
    except Exception as e:
        st.error(f"❌ 오류: {str(e)}")

# Tab 2: GCMS Management
with tab2:
    st.subheader("GCMS 물질 관리 및 향미 Hint 설정")
    st.markdown("""
    GCMS 데이터 업로드 시 사용할 헤더 매핑과, 각 물질별 향미 힌트를 설정합니다.
    - **CSV 헤더**: 분석 기기에서 나오는 raw data의 헤더명
    - **향미 Hint**: AI 리포트 생성에 사용될 향미 특성 설명
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
                    '물질명 (코드)': idx.code,
                    '표시 이름': idx.name,
                    '단위': idx.unit,
                    'CSV 헤더': idx.csv_header,
                    '향미 Hint': idx.flavor_hint
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("등록된 GCMS 물질이 없습니다.")
            
        st.divider()
        
        col_l, col_r = st.columns(2)
        
        with col_l:
            st.subheader("➕ 새 물질 추가")
            with st.form("add_gcms_item"):
                code = st.text_input("물질 코드 (영문/숫자)", help="예: ethyl_acetate").lower().replace(" ", "_")
                name = st.text_input("표시 이름", help="예: Ethyl Acetate")
                unit = st.text_input("단위", value="mg/L")
                csv_header = st.text_input("CSV/Excel 헤더명", help="업로드 파일의 컬럼명과 일치해야 함")
                flavor_hint = st.text_area("향미 Hint", help="예: 과일향, 파인애플, 달콤함")
                
                submitted = st.form_submit_button("➕ 물질 등록")
                
                if submitted:
                    if not code or not name:
                        st.error("❌ 물질 코드와 이름은 필수입니다.")
                    else:
                        # Check duplicate
                        existing = next((i for i in gcms_indices if i.code == code), None)
                        if existing:
                            st.error("❌ 이미 존재하는 코드입니다.")
                        else:
                            new_item = {
                                'code': code,
                                'name': name,
                                'unit': unit,
                                'is_gcms': 1,
                                'csv_header': csv_header,
                                'flavor_hint': flavor_hint
                            }
                            add_analysis_index(session, new_item)
                            st.success(f"✅ {name} 등록 완료!")
                            st.rerun()

        with col_r:
            st.subheader("✏️ 물질 수정/삭제")
            if gcms_indices:
                to_edit = st.selectbox(
                    "수정할 물질 선택",
                    options=[idx.id for idx in gcms_indices],
                    format_func=lambda x: next((f"{i.name} ({i.code})" for i in gcms_indices if i.id == x), str(x))
                )
                
                target = next((i for i in gcms_indices if i.id == to_edit), None)
                
                if target:
                    with st.form("edit_gcms_item"):
                        e_name = st.text_input("표시 이름", value=target.name)
                        e_unit = st.text_input("단위", value=target.unit)
                        e_header = st.text_input("CSV/Excel 헤더명", value=target.csv_header or "")
                        e_hint = st.text_area("향미 Hint", value=target.flavor_hint or "")
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            edit_submit = st.form_submit_button("💾 수정 저장")
                        with c2:
                            delete_submit = st.form_submit_button("🗑️ 삭제", type="primary")
                        
                        if edit_submit:
                            update_dict = {
                                'name': e_name,
                                'unit': e_unit,
                                'csv_header': e_header,
                                'flavor_hint': e_hint
                            }
                            update_analysis_index(session, target.id, update_dict)
                            st.success("✅ 수정되었습니다!")
                            st.rerun()
                            
                        if delete_submit:
                            delete_analysis_index(session, target.id)
                            st.success("✅ 삭제되었습니다!")
                            st.rerun()
        
        session.close()
    except Exception as e:
        st.error(f"❌ 오류: {str(e)}")
