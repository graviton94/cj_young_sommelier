"""
Data Entry Page - Input and manage LOT chemical composition data
"""

import streamlit as st
from datetime import datetime
import sys
import os
from pathlib import Path

# Add project root to path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from src.database import (
    init_database, get_session, add_lot_data, get_all_lots,
    get_lot_by_number, get_lot_by_id, update_lot_data, delete_lot_data,
    get_all_indices, get_lot_measurements
)

# Initialize database
init_database()

st.set_page_config(page_title="데이터 입력", page_icon="📊", layout="wide")

st.title("📊 LOT 데이터 입력 및 관리")
st.markdown("주류 LOT의 화학 성분 데이터를 입력하고 관리합니다")

# Tabs for different operations
tab1, tab2 = st.tabs(["➕ 데이터 입력", "✏️ 수정/삭제"])

# ==========================================
# Tab 1: Data Entry (New LOT vs Existing)
# ==========================================
with tab1:
    st.subheader("데이터 입력")
    # Removed "숙성 LOT 분석" as requested
    entry_type = "신규 LOT 등록" 
    st.info("신규 LOT 정보를 등록합니다. (정밀 분석이나 숙성 데이터는 '향미 상세 분석' 메뉴를 이용해주세요.)")
    
    session = get_session()
    selected_existing_lot = None
    
    # Common Basic Info (4 Columns)
    st.markdown("### 📦 입고 원료 정보")
    c1, c2, c3, c4 = st.columns(4)
    
    # 1. Admission Date
    with c1:
        if entry_type == "신규 LOT 등록":
            admission_date = st.date_input("📅 입고일 (Admission)", value=datetime.now())
        else:
            # Use existing admission date if available, else today (disabled)
            default_date = selected_existing_lot.admission_date if (selected_existing_lot and selected_existing_lot.admission_date) else datetime.now()
            admission_date = st.date_input("📅 입고일 (Admission)", value=default_date, disabled=True)

    # 2. LOT Number
    # 2. LOT Number
    with c2:
        lot_number_input = st.text_input("🔢 LOT 번호", help="새로운 LOT 번호")
    
    # 3. Product Name
    with c3:
        product_name_input = st.text_input("🏷️ 제품명")

    # 4. Analysis Date
    with c4:
        production_date = st.date_input("🔬 분석일 (Analysis)", value=datetime.now())
        
    # Determine Final LOT Number used for logic
    if entry_type == "신규 LOT 등록":
        final_lot_number = lot_number_input.strip()
    else:
        final_lot_number = selected_existing_lot.lot_number if selected_existing_lot else ""

    st.divider()
    
    # Chemical Analysis
    st.markdown("### ⚗️ 화학 성분 분석")
    indices_basic = get_all_indices(session, category='basic')
    
    chemical_inputs = {}
    if not indices_basic:
        st.warning("등록된 화학 분석 항목이 없습니다. 설정 페이지에서 추가해주세요.")
    else:
        # Batch processing for row-based layout (Horizontal Tabbing)
        for i in range(0, len(indices_basic), 4):
            cols_b = st.columns(4)
            batch = indices_basic[i:i+4]
            for j, idx in enumerate(batch):
                with cols_b[j]:
                    # Special default for New LOT vs Existing
                    default_val = 0.0
                    
                    # Check for Alcohol (Methanol optional?)
                    label = f"🧪 {idx.name} ({idx.unit})"
                    if 'alcohol' in idx.code.lower() or '알코올' in idx.name:
                        label += " *"
                    
                    fmt = "%.4f" # Default format
                    if '밀도' in idx.name or 'density' in idx.code.lower() or '비중' in idx.name:
                        fmt = "%.5f"
                    elif 'pH' in idx.name or 'ph' in idx.code.lower():
                        fmt = "%.2f"
                    
                    val = st.number_input(
                        label,
                        min_value=float(idx.min_value) if idx.min_value is not None else 0.0,
                        max_value=float(idx.max_value) if idx.max_value is not None else None,
                        step=float(idx.step) if idx.step else 0.00001 if '밀도' in idx.name else 0.1,
                        format=fmt,
                        key=f"input_{idx.code}"
                    )
                    chemical_inputs[idx.code] = val
    
    # Sensory Scores are shown by default for New LOT
    do_sensory = True

    sensory_inputs = {}
    selected_control_id = 0

    if do_sensory:
        # Sensory Scores (T/C Comparison)
        st.markdown("### 👅 관능 점수 (T/C 비교분석)")
        st.info("""- T = Test Sample(분석 대상), C = Control Sample(비교 대상)
- T 샘플에서 강하게 느껴질수록 +, C 샘플에서 강하게 느껴질수록 -이며, 각 항목의 입력 범위는 -4 ~ +4, 종합 차이의 범위는 0 ~ 8 입니다.""")
        
        # Control Sample Selection
        # Control Sample Selection
        st.markdown("**⚖️ 비교 대상(C) 선택** (기준: 입고일 / LOT No. / 제품명 / 분석일)")
        all_lots_for_control = get_all_lots(session)
        
        control_options = {}
        control_options[0] = "비교 없음"
        
        for lot in all_lots_for_control:
            # Allow selecting same lot for aging comparison
            
            admission_str = lot.admission_date.strftime("%Y-%m-%d") if lot.admission_date else "입고일미등록"
            production_str = lot.production_date.strftime("%Y-%m-%d") if lot.production_date else "분석일미등록"
            
            label = f"입고일 : {admission_str} / LOT No. : {lot.lot_number} / 제품명 : {lot.product_name} / 분석일 : {production_str}"
            control_options[lot.id] = label
        
        selected_control_id = st.selectbox(
            "비교 대상 선택",
            options=list(control_options.keys()),
            format_func=lambda x: control_options[x],
            help="관능 점수 비교를 위한 Control Sample 선택"
        )
        
        if selected_control_id == 0:
             st.warning("⚠️ 비교 대상을 선택하면 관능 점수 입력 항목이 표시됩니다.")
        
        if selected_control_id > 0: 
            st.divider()
            indices_sensory = get_all_indices(session, category='sensory')
            
            if not indices_sensory: # Fallback
                    c_s1, c_s2 = st.columns(2)
                    with c_s1:
                        aroma = st.number_input("👃 향 점수", -4.0, 4.0, value=0.0)
                        taste = st.number_input("👅 맛 점수", -4.0, 4.0, value=0.0)
                    with c_s2:
                        finish = st.number_input("🕰️ 여운 점수", -4.0, 4.0, value=0.0)
                        overall = st.number_input("⭐ 종합 점수", -4.0, 4.0, value=0.0, help="""0 = 완전히 동일함

2 = 경미한 차이로, 설명하기 어려운 수준

4 = 기존 소비자라면 식별 가능한 수준

6 = 일반 소비자라도 식별 가능하고, 차이점을 설명 가능한 수준

8 = 완전히 다른 제품으로 인지되는 수준""")
                    sensory_inputs = {'aroma_score': aroma, 'taste_score': taste, 'finish_score': finish, 'overall_score': overall}
            else:
                    # Batch processing for Sensory Indices
                    for i in range(0, len(indices_sensory), 4):
                        cols_s = st.columns(4)
                        batch = indices_sensory[i:i+4]
                        for j, idx in enumerate(batch):
                            with cols_s[j]:
                                # Determine Emoji
                                emoji = "🍷"
                                name_lower = idx.name.lower()
                                code_lower = idx.code.lower()
                                
                                if 'aroma' in code_lower or '향' in name_lower: emoji = "👃"
                                elif 'taste' in code_lower or '맛' in name_lower: emoji = "👅"
                                elif 'finish' in code_lower or '여운' in name_lower: emoji = "🕰️"
                                elif 'overall' in code_lower or '종합' in name_lower: emoji = "⭐"
                                
                                # Determine help text
                                help_text = None
                                if '종합' in idx.name or 'Overall' in idx.name:
                                    help_text = """0 = 완전히 동일함

2 = 경미한 차이로, 설명하기 어려운 수준

4 = 기존 소비자라면 식별 가능한 수준

6 = 일반 소비자라도 식별 가능하고, 차이점을 설명 가능한 수준

8 = 완전히 다른 제품으로 인지되는 수준"""
                                
                                # Calculate min/max/default
                                min_v = float(idx.min_value) if idx.min_value is not None else -4.0
                                max_v = float(idx.max_value) if idx.max_value is not None else 4.0
                                default_v = 0.0
                                if min_v > default_v: default_v = min_v
                                if max_v < default_v: default_v = max_v
                                
                                val = st.number_input(
                                    f"{emoji} {idx.name}", 
                                    min_value=min_v,
                                    max_value=max_v,
                                    value=default_v,
                                    step=float(idx.step) if idx.step else 0.5,
                                    key=f"sensory_{idx.code}",
                                    help=help_text
                                )
                                
                                # Route to appropriate storage
                                if idx.code in ['aroma_score', 'taste_score', 'finish_score', 'overall_score']:
                                    sensory_inputs[idx.code] = val
                                else:
                                    chemical_inputs[idx.code] = val
    
    st.markdown("---")
    notes = st.text_area("메모/비고")
    
    submitted = st.button("💾 데이터 저장", type="primary")
    
    if submitted:
        if not final_lot_number:
            st.error("❌ LOT 번호는 필수입니다.")
        elif not product_name_input:
            st.error("❌ 제품명은 필수입니다.")
        else:
            # Validation based on entry type
            validation_passed = True
            
            if entry_type == "신규 LOT 등록":
                # New LOT: Chemical fields required (except methanol)
                missing_fields = []
                
                # Check chemical inputs (exclude methanol)
                for code, value in chemical_inputs.items():
                    # Find the index for this code
                    idx = next((i for i in indices_basic if i.code == code), None) # Use indices_basic from above
                    if not idx:
                        continue
                    
                    # Skip if display name contains '메탄올'
                    if '메탄올' in idx.name:
                        continue
                    
                    if value is None:
                        missing_fields.append(idx.name)
                
                # Sensory scores are now optional (0 allowed)
                
                if missing_fields:
                    st.error(f"❌ 신규 LOT 등록 시 화학 성분 항목(메탄올 제외)은 필수입니다. 누락된 항목: {', '.join(missing_fields[:5])}{'...' if len(missing_fields) > 5 else ''}")
                    validation_passed = False
            
            else:
                # Existing LOT: Only alcohol_content required
                alcohol_code = 'alcohol_content'
                # Find acutal code if different
                # But typically it's this.
                # Just check if we have any inputs
                
                # Check alcohol specifically
                # Since we don't have direct access to 'alcohol_code' variable from loop easily, 
                # we assume 'alcohol_content' or similar logic exists.
                # Actually, let's just trust the user input for now or do a quick check
                has_alcohol = any('alcohol' in k or '알코올' in k for k, v in chemical_inputs.items() if v > 0)
                if not has_alcohol and entry_type == "숙성 LOT 분석":
                     # Maybe alcohol isn't re-measured every time? 
                     # Original code enforced it. Let's keep validation if possible.
                     pass 
                
                # For other fields with 0, retain previous values
                if validation_passed and selected_existing_lot:
                    # Get previous measurements
                    from src.database import LotMeasurement
                    prev_measurements = session.query(LotMeasurement).filter(
                        LotMeasurement.lot_id == selected_existing_lot.id
                    ).all()
                    prev_data = {m.index_code: m.value for m in prev_measurements}
                    
                    # Retain previous values if new value is 0
                    for code, value in chemical_inputs.items():
                        if value == 0.0 and code in prev_data:
                            chemical_inputs[code] = prev_data[code]
                    
                    # Retain previous sensory scores if 0
                    for code in ['aroma_score', 'taste_score', 'finish_score', 'overall_score']:
                        if sensory_inputs.get(code, 0.0) == 0.0:
                            prev_value = getattr(selected_existing_lot, code, 0.0)
                            if prev_value:
                                sensory_inputs[code] = prev_value
            
            if validation_passed:
                # Prepare data dictionary
                data = {
                    'lot_number': final_lot_number,
                    'product_name': product_name_input,
                    'production_date': datetime.combine(production_date, datetime.min.time()),
                    'notes': notes,
                    'measurements': chemical_inputs 
                }
                
                if admission_date:
                    data['admission_date'] = datetime.combine(admission_date, datetime.min.time())
                
                # Add control sample reference if selected
                if selected_control_id > 0:
                    data['control_sample_id'] = selected_control_id
                
                # Add sensory standard fields
                data.update(sensory_inputs)
                
                success = add_lot_data(session, data)
                
                if success:
                    st.success(f"✅ LOT {final_lot_number} 데이터 저장 완료!")
                else:
                    st.error("❌ 저장 실패")
                    
    session.close()

# Tab 2 removed (Moved to consolidated Analysis Results page)

# ==========================================
# Tab 2: Edit / Delete
# ==========================================
with tab2:
    st.subheader("데이터 수정 및 삭제")
    
    session = get_session()
    
    # 1. Select LOT Number
    unique_lots = sorted(list(set([l.lot_number for l in get_all_lots(session)])))
    selected_lot_num = st.selectbox("LOT 번호 선택", unique_lots, key="edit_lot_select")
    
    if selected_lot_num:
        # 2. Show History for this LOT
        history = get_all_lots(session, lot_number=selected_lot_num)
        
        st.markdown(f"**'{selected_lot_num}'의 분석 이력 ({len(history)}건)**")
        
        # Display as selectable table or radio?
        # Table with ID is good.
        hist_data = []
        for h in history:
            hist_data.append({
                'ID': h.id,
                '분석일': h.production_date.strftime("%Y-%m-%d"),
                '메모': h.notes
            })
        st.table(hist_data)
        
        # 3. Select Specific Entry (ID)
        selected_id = st.selectbox(
            "관리할 분석 기록 선택 (ID - 분석일)", 
            [h.id for h in history],
            format_func=lambda x: next((f"{h.id} - {h.production_date.strftime('%Y-%m-%d')}" for h in history if h.id == x), x)
        )
        
        if selected_id:
            target_lot = next((h for h in history if h.id == selected_id), None)
            
            # --- ACTION SELECTION ---
            action = st.radio("작업 선택", ["수정", "삭제"], horizontal=True)
            
            st.divider()
            
            if action == "수정":
                with st.form("edit_lot_form"):
                    # Basic info
                    e_date = st.date_input("분석일", value=target_lot.production_date)
                    e_notes = st.text_area("메모", value=target_lot.notes)
                    
                    # Chemical inputs
                    st.markdown("### 화학 성분 수정")
                    cols = st.columns(3)
                    
                    # Fetch current measurements
                    from src.database import LotMeasurement
                    current_msmts = session.query(LotMeasurement).filter(LotMeasurement.lot_id == target_lot.id).all()
                    val_map = {m.index_code: m.value for m in current_msmts}
                    param_inputs = {}
                    
                    indices = get_all_indices(session, basic_only=True)
                    for i, idx in enumerate(indices):
                        with cols[i % 3]:
                            c_val = val_map.get(idx.code, 0.0)
                            n_val = st.number_input(f"{idx.name}", value=float(c_val), step=idx.step, key=f"edit_{idx.code}")
                            param_inputs[idx.code] = n_val
                            
                    submitted_edit = st.form_submit_button("💾 수정사항 저장")
                    
                    if submitted_edit:
                        u_data = {
                            'production_date': datetime.combine(e_date, datetime.min.time()),
                            'notes': e_notes,
                            'measurements': param_inputs
                        }
                        if update_lot_data(session, selected_id, u_data): 
                            # Need update_lot_data to support ID. (Already updated in previous step)
                            st.success("✅ 수정되었습니다.")
                            st.rerun()
                        else:
                            st.error("❌ 수정 실패")
                            
            elif action == "삭제":
                st.warning("⚠️ 삭제 작업은 되돌릴 수 없습니다.")
                
                del_mode = st.radio(
                    "삭제 범위", 
                    ["이 기록만 삭제 (해당 날짜의 분석 데이터)", "전체 LOT 삭제 (모든 이력 포함)"],
                    key="del_mode"
                )
                
                if st.button("🗑️ 영구 삭제 확인", type="primary"):
                    if "이 기록만 삭제" in del_mode:
                        if delete_lot_data(session, lot_id=selected_id):
                            st.success("✅ 해당 기록이 삭제되었습니다.")
                            st.rerun()
                    else:
                        if delete_lot_data(session, lot_number=selected_lot_num):
                            st.success(f"✅ LOT {selected_lot_num}의 모든 기록이 삭제되었습니다.")
                            st.rerun()

    session.close()
