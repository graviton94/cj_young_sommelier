
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import os
from datetime import datetime

# Add project root to path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from src.database import (
    get_session, get_all_indices, get_lot_by_id,
    FlavorAnalysis, FlavorMeasurement, LotMeasurement, LOTData, AnalysisIndex
)

# Upload directory (for download checks)
UPLOAD_DIR = Path("data/gcms_uploads")

st.set_page_config(page_title="분석 결과", page_icon="📋", layout="wide")

st.title("📋 전체 분석 결과")
st.markdown("모든 시제품 및 LOT의 분석 이력을 통합 조회 및 관리합니다.")

# Tabs for View and Management
tab_view, tab_manage = st.tabs(["📊 분석 결과 조회", "⚙️ 데이터 관리 (수정/삭제)"])

session = get_session()

def fetch_unified_data(session_obj):
    # 1. Fetch Detailed Analysis (FlavorAnalysis)
    detailed_records = session_obj.query(FlavorAnalysis).all()
    # 2. Fetch Standard Analysis (LOTData)
    standard_records = session_obj.query(LOTData).all()
    # Get all indices for columns mapping
    all_indices = session_obj.query(AnalysisIndex).all()
    code_to_name = {idx.code: idx.name for idx in all_indices}

    unified_data = []
    covered_lots = set()

    # 1. Process Unified Analysis Records (FlavorAnalysis)
    for r in detailed_records:
        a_type = getattr(r, 'analysis_type', None)
        
        # Mapping Types: 입고검사, 숙성중, 타제품
        label_type = "숙성중" # Default for detailed
        if r.is_prototype or a_type == 'prototype':
             label_type = "타제품"
        elif a_type == 'initial':
             label_type = "입고검사"
             if r.lot_id:
                 covered_lots.add(r.lot_id)
        elif a_type == 'aging':
             label_type = "숙성중"
        
        # LOT info and Sample Name
        lot_no = ""
        sample_display = r.sample_name
        id_str = ""
        
        if r.lot_id:
            lot_info = get_lot_by_id(session_obj, r.lot_id)
            if lot_info:
                lot_no = lot_info.lot_number
                sample_display = lot_info.product_name
                ad_s = lot_info.admission_date.strftime("%Y-%m-%d") if lot_info.admission_date else "입고일미등록"
                pr_s = lot_info.production_date.strftime("%Y-%m-%d") if lot_info.production_date else "분석일미등록"
                id_str = f"입고일 : {ad_s} / LOT : {lot_no} / 제품명 : {sample_display} / 분석일 : {pr_s}"
        else:
            # Prototype / 타제품
            id_str = f"타제품/시제품 : {r.sample_name} / 분석일 : {r.analysis_date.strftime('%Y-%m-%d') if r.analysis_date else ''}"
        
        item = {
            'ID': f"D-{r.id}", # D for Detailed (FlavorAnalysis)
            '구분': label_type,
            'LOT': lot_no,
            '샘플명': sample_display,
            '분석일': r.analysis_date.strftime("%Y-%m-%d") if r.analysis_date else "",
            'GCMS 파일': "O" if r.gcms_file_path else "X",
            '메모': r.notes,
            '식별자': id_str,
            'raw_obj': r,
            'is_detailed': True
        }
        
        # Measurements
        msmts = session_obj.query(FlavorMeasurement).filter(FlavorMeasurement.flavor_analysis_id == r.id).all()
        for m in msmts:
            d_name = code_to_name.get(m.index_code, m.index_code)
            item[d_name] = m.value
            
        unified_data.append(item)
        
    # 2. Process Legacy LOTData (Entry records not yet in FlavorAnalysis initial)
    for l in standard_records:
        if l.id in covered_lots:
            continue
            
        ad_s = l.admission_date.strftime("%Y-%m-%d") if l.admission_date else "입고일미등록"
        pr_s = l.production_date.strftime("%Y-%m-%d") if l.production_date else "분석일미등록"
        id_str = f"입고일 : {ad_s} / LOT : {l.lot_number} / 제품명 : {l.product_name} / 분석일 : {pr_s}"
        
        item = {
            'ID': f"S-{l.id}", # S for Standard (LOTData)
            '구분': '입고검사',
            'LOT': l.lot_number,
            '샘플명': l.product_name,
            '분석일': l.production_date.strftime("%Y-%m-%d") if l.production_date else "",
            'GCMS 파일': "X",
            '메모': l.notes,
            '식별자': id_str,
            'raw_obj': l, 
            'is_detailed': False
        }
        
        l_msmts = session_obj.query(LotMeasurement).filter(LotMeasurement.lot_id == l.id).all()
        for m in l_msmts:
            d_name = code_to_name.get(m.index_code, m.index_code)
            item[d_name] = m.value
            
        unified_data.append(item)
    
    return unified_data, all_indices

unified_records, indices_meta = fetch_unified_data(session)

# ==========================================
# Tab 1: View Results
# ==========================================
with tab_view:
    if unified_records:
        df = pd.DataFrame(unified_records)
        df['분석일_dt'] = pd.to_datetime(df['분석일'], errors='coerce')
        
        # LOT Filtering
        all_lots = sorted(df['LOT'].unique().tolist())
        selected_lots = st.multiselect("🔢 LOT 필터", options=all_lots, help="특정 LOT의 분석 이력을 선택하여 조회합니다.")
        
        if selected_lots:
            df = df[df['LOT'].isin(selected_lots)]
            # If filtered by LOT, sort ascending to show progression
            df = df.sort_values(by='분석일_dt', ascending=True)
        else:
            # Default: descending (most recent first)
            df = df.sort_values(by='분석일_dt', ascending=False)
        
        # Column Ordering
        fixed_cols = ['분석일', '구분', 'LOT', '샘플명']
        meta_cols = ['GCMS 파일', '식별자', '메모']
        internal_cols = ['ID', 'raw_obj', 'is_detailed', '분석일_dt']
        
        other_cols = [c for c in df.columns if c not in fixed_cols and c not in meta_cols and c not in internal_cols]
        
        sorted_dynamic = []
        for idx in indices_meta:
            if idx.name in other_cols:
                sorted_dynamic.append(idx.name)
        remaining = [c for c in other_cols if c not in sorted_dynamic]
        
        final_cols = fixed_cols + sorted_dynamic + remaining + meta_cols
        final_cols = list(dict.fromkeys(final_cols))
        
        st.dataframe(df[final_cols], width='stretch', hide_index=True)
        
        st.divider()
        st.subheader("💾 GCMS 데이터 다운로드")
        downloadable = [d for d in unified_records if d['is_detailed'] and d['GCMS 파일'] == "O"]
        
        if downloadable:
            opts = {d['ID']: f"[{d['분석일']}] {d['구분']} - {d['샘플명']} ({d['LOT'] if d['LOT'] else '타제품'})" for d in downloadable}
            sel_dl = st.selectbox("다운로드할 데이터 선택", options=list(opts.keys()), format_func=lambda x: opts[x], key="dl_select")
            if sel_dl:
                target = next((d for d in downloadable if d['ID'] == sel_dl), None)
                if target and target['raw_obj'].gcms_file_path and os.path.exists(target['raw_obj'].gcms_file_path):
                    with open(target['raw_obj'].gcms_file_path, "rb") as f:
                        st.download_button(f"📥 다운로드", f, file_name=os.path.basename(target['raw_obj'].gcms_file_path), mime="text/csv")
        else:
            st.info("다운로드 가능한 GCMS 파일이 없습니다.")
    else:
        st.info("분석 기록이 없습니다.")

# ==========================================
# Tab 2: Management (Edit/Delete)
# ==========================================
with tab_manage:
    if unified_records:
        st.subheader("✏️ 기록 수정 및 삭제")
        st.warning("경고: 데이터를 삭제하면 복구할 수 없습니다.")
        
        # Sort records for selection
        sorted_records = sorted(unified_records, key=lambda x: x['분석일'] or "", reverse=True)
        record_map = {r['ID']: f"[{r['분석일']}] {r['구분']} - {r['샘플명']} ({r['LOT'] if r['LOT'] else 'N/A'})" for r in sorted_records}
        
        selected_id = st.selectbox("수정/삭제할 기록 선택", options=["선택 안함"] + list(record_map.keys()), format_func=lambda x: record_map[x] if x in record_map else "선택해주세요")
        
        if selected_id != "선택 안함":
            rec = next((r for r in unified_records if r['ID'] == selected_id), None)
            if rec:
                st.write(f"### 📝 정보 수정: {record_map[selected_id]}")
                st.caption(f"시스템 식별자: {rec['식별자']}")
                
                # 1. Basic Info Section
                st.markdown("#### 📦 기본 정보")
                col_e1, col_e2, col_e3 = st.columns(3)
                with col_e1:
                    new_date = st.date_input("🗓️ 분석일 수정", value=pd.to_datetime(rec['분석일']).date() if rec['분석일'] else datetime.now().date())
                with col_e2:
                    current_name = rec['샘플명']
                    new_name = st.text_input("🏷️ 샘플명/제품명 수정", value=current_name)
                    st.caption("※ 제품명 수정 시 원본 LOT 정보도 함께 갱신됩니다.")
                with col_e3:
                    new_notes = st.text_input("📝 메모 수정", value=rec['메모'] or "")
                
                # GCMS File Management (Only for detailed)
                new_gcms_file = None
                if rec['is_detailed']:
                     st.markdown("---")
                     st.markdown("#### 🔬 GCMS 파일 관리")
                     g_c1, g_c2 = st.columns([1, 2])
                     with g_c1:
                         st.write(f"**현재 상태**: {'파일 있음 (O)' if rec['GCMS 파일'] == 'O' else '파일 없음 (X)'}")
                         if rec['GCMS 파일'] == 'O':
                             st.caption(f"파일명: {os.path.basename(rec['raw_obj'].gcms_file_path)}")
                             # Add Download button to check existing file
                             with open(rec['raw_obj'].gcms_file_path, "rb") as f:
                                 st.download_button(
                                     "📥 기존 파일 확인/다운로드",
                                     f,
                                     file_name=os.path.basename(rec['raw_obj'].gcms_file_path),
                                     mime="text/csv",
                                     key=f"dl_existing_{selected_id}"
                                 )
                     with g_c2:
                         new_gcms_file = st.file_uploader("📂 GCMS 파일 교체/추가 (기본값: 기존 파일 유지)", type=['csv'], key=f"edit_gcms_{selected_id}")
                
                st.divider()
                
                # 2. Measurement Values Section
                st.markdown("#### ⚗️ 분석 항목 값 수정")
                st.caption("비어 있는 칸은 None으로 저장됩니다.")
                
                updated_msmts = {}
                
                # Fetch indices by category
                cat_info = [
                    ('basic', '🔬 화학 성분 (Basic Analysis)'),
                    ('sensory', '👅 관능 평가 (Sensory Scores)'),
                    ('flavor_indicator', '📊 향미 관리지표 (Flavor Indicators)')
                ]
                
                for cat_code, cat_label in cat_info:
                    cat_indices = [idx for idx in indices_meta if idx.category == cat_code]
                    if cat_indices:
                        st.markdown(f"**{cat_label}**")
                        for i in range(0, len(cat_indices), 4):
                            cols = st.columns(4)
                            batch = cat_indices[i:i+4]
                            for j, idx in enumerate(batch):
                                with cols[j]:
                                    current_val = rec.get(idx.name)
                                    val_str = st.text_input(
                                        f"{idx.name} ({idx.unit or ''})",
                                        value=str(current_val) if current_val is not None else "",
                                        key=f"edit_{selected_id}_{idx.code}",
                                        placeholder="None"
                                    )
                                    if val_str.strip():
                                        try:
                                            updated_msmts[idx.code] = float(val_str)
                                        except ValueError:
                                            st.error(f"'{idx.name}'에는 숫자만 입력 가능합니다.")
                                    else:
                                        updated_msmts[idx.code] = None
                        st.markdown("<br>", unsafe_allow_html=True)
                                
                st.divider()
                
                c_btn1, c_btn2, _ = st.columns([1, 1, 3])
                
                with c_btn1:
                    if st.button("💾 변경사항 저장", type="primary", width='stretch'):
                        try:
                            obj = rec['raw_obj']
                            # Convert date
                            dt_obj = datetime.combine(new_date, datetime.min.time())
                            
                            if rec['is_detailed']:
                                # Update FlavorAnalysis
                                obj.analysis_date = dt_obj
                                obj.notes = new_notes
                                obj.sample_name = new_name
                                
                                if obj.lot_id:
                                    lot_record = session.query(LOTData).filter(LOTData.id == obj.lot_id).first()
                                    if lot_record:
                                        lot_record.product_name = new_name
                                
                                # Update GCMS File if new one provided
                                if new_gcms_file is not None:
                                    # Delete old file
                                    if obj.gcms_file_path and os.path.exists(obj.gcms_file_path):
                                        try: os.remove(obj.gcms_file_path)
                                        except: pass
                                    
                                    # Save new file
                                    upload_dir = Path("data/gcms_uploads")
                                    upload_dir.mkdir(parents=True, exist_ok=True)
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    safe_name = "".join([c if c.isalnum() else "_" for c in new_name])
                                    file_name = f"{timestamp}_{safe_name}.csv"
                                    new_path = str(upload_dir / file_name)
                                    
                                    with open(new_path, "wb") as f:
                                        f.write(new_gcms_file.getvalue())
                                    obj.gcms_file_path = new_path
                                
                                # Update Measurements (FlavorMeasurement)
                                for code, value in updated_msmts.items():
                                    m_rec = session.query(FlavorMeasurement).filter(
                                        FlavorMeasurement.flavor_analysis_id == obj.id,
                                        FlavorMeasurement.index_code == code
                                    ).first()
                                    if m_rec:
                                        m_rec.value = value
                                    elif value is not None:
                                        # Create new measurement record if it didn't exist
                                        new_m = FlavorMeasurement(flavor_analysis_id=obj.id, index_code=code, value=value)
                                        session.add(new_m)
                            else:
                                # Update LOTData (Legacy/Standard)
                                obj.production_date = dt_obj
                                obj.notes = new_notes
                                obj.product_name = new_name
                                
                                # Update Measurements (LotMeasurement)
                                for code, value in updated_msmts.items():
                                    m_rec = session.query(LotMeasurement).filter(
                                        LotMeasurement.lot_id == obj.id,
                                        LotMeasurement.index_code == code
                                    ).first()
                                    if m_rec:
                                        m_rec.value = value
                                    elif value is not None:
                                        new_m = LotMeasurement(lot_id=obj.id, lot_number=obj.lot_number, index_code=code, value=value)
                                        session.add(new_m)
                            
                            session.commit()
                            st.success("✅ 모든 정보가 성공적으로 업데이트되었습니다.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"저장 실패: {e}")
                            
                with c_btn2:
                    if st.button("🗑️ 기록 삭제", type="secondary", width='stretch'):
                        st.session_state[f"confirm_delete_{selected_id}"] = True
                
                if st.session_state.get(f"confirm_delete_{selected_id}"):
                    st.error("정말로 이 분석 기록을 삭제하시겠습니까? (복구 불가)")
                    if st.button("❗️ 예, 확실히 삭제합니다", key=f"final_del_{selected_id}", width='stretch'):
                        try:
                            obj = rec['raw_obj']
                            if rec['is_detailed']:
                                # Delete GCMS file from disk if exists
                                if obj.gcms_file_path and os.path.exists(obj.gcms_file_path):
                                    try: os.remove(obj.gcms_file_path)
                                    except: pass

                                session.query(FlavorMeasurement).filter(FlavorMeasurement.flavor_analysis_id == obj.id).delete()
                                session.delete(obj)
                            else:
                                session.query(LotMeasurement).filter(LotMeasurement.lot_id == obj.id).delete()
                                session.delete(obj)
                            session.commit()
                            st.success("✅ 삭제 완료되었습니다.")
                            del st.session_state[f"confirm_delete_{selected_id}"]
                            st.rerun()
                        except Exception as e:
                            st.error(f"삭제 실패: {e}")
                            
    else:
        st.info("관리할 기록이 없습니다.")

session.close()
