import streamlit as st
import pandas as pd
import sys
import os
import uuid
from pathlib import Path

# src 모듈 경로 추가
root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from src.analysis import FlavorAnalyzer
from src.database import init_database, get_session, get_all_indices, add_analysis_index, update_analysis_index, delete_analysis_index
from src.chem_utils import lookup_compound, get_molecule_image, get_rdkit_properties, FUNCTIONAL_GROUP_PATTERNS

# Initialize database
init_database()

st.set_page_config(page_title="Flavor Master Manager", page_icon="👃", layout="wide")

st.title("👃 Flavor Knowledge Base Management")
st.markdown("향미 마스터 DB와 화학 라이브러리를 통합 관리합니다.")

# 분석 엔진 초기화
analyzer = FlavorAnalyzer()

# 추천 태그 추출 함수
def get_all_tags(df, column):
    if df.empty or column not in df.columns:
        return []
    # NaN을 빈 문자열로 처리하고 쉼표로 합침
    all_text = ",".join(df[column].fillna("").astype(str))
    # 쉼표 분리 후 공백 제거, 'nan', 'NaN' 및 빈 문자열 제외
    tags = [t.strip() for t in all_text.split(",") if t.strip() and t.strip().lower() != 'nan']
    return sorted(list(set(tags)))

# 한글 묘사 추천 태그
KO_TAGS_BASE = ['과일향', '바나나', '달콤함', '꼬리한', '알코올', '꽃향', '시트러스', 
                '견과', '풀취', '고량주', '식초', '곡물', '누룽지', '황취', '화학취']
EN_TAGS_BASE = ['fruity', 'sweet', 'banana', 'floral', 'citrus', 'green', 'ethereal', 
                'fatty', 'nutty', 'roasted', 'sulfurous', 'medicinal', 'alcoholic']
GROUPS_BASE = ['Alcohol', 'Aldehyde', 'Ester', 'Ketone', 'Carboxylic Acid', 'Ether', 
               'Phenol', 'Amine', 'Amide', 'Thiol', 'Alkene', 'Alkyne', 'Aromatic']

# 폼 필드 가젯 (NaN 방지 헬퍼)
def get_safe_str(val):
    if pd.isna(val) or str(val).lower() == 'nan':
        return ""
    return str(val).strip()

def get_safe_tags(val):
    s = get_safe_str(val)
    if not s:
        return []
    return [t.strip() for t in s.split(",") if t.strip() and t.strip().lower() != 'nan']

# 동적 태그 리스트 생성
all_ko_tags = sorted(list(set(KO_TAGS_BASE + get_all_tags(analyzer.df, 'Desc_Korean'))))
all_en_tags = sorted(list(set(EN_TAGS_BASE + get_all_tags(analyzer.df, 'Desc_English'))))
all_groups_tags = sorted(list(set(GROUPS_BASE + get_all_tags(analyzer.df, 'Groups'))))

# ----------------------------------------------------
# 1. 상단: 데이터 테이블 조회 (View Only)
# ----------------------------------------------------
with st.expander("📋 등록된 전체 성분 조회 (Read-only View)", expanded=False):
    if analyzer.df.empty:
        st.info("등록된 성분이 없습니다.")
    else:
        # 데이터프레임 표시 시에도 NaN을 빈칸으로 보이게 함
        display_df = analyzer.df.fillna("")
        st.dataframe(
            display_df,
            column_config={
                "CAS": "CAS No",
                "Name_Common": "성분명",
                "Desc_Korean": "한글 묘사",
                "Threshold": st.column_config.NumberColumn("역치 (ppm)", format="%.4f"),
                "Is_AAC": "AAC",
                "Groups": "화학 그룹",
                "Desc_English": "영어 묘사",
                "MW": "MW",
                "LogP": "LogP"
            },
            width='stretch',
            hide_index=True
        )

st.divider()

# ----------------------------------------------------
# 2. 하단: 물질 상세 관리 (Search, Register, Edit)
# ----------------------------------------------------
col_search, col_form = st.columns([1, 1], gap="large")

# 세션 스테이트 초기화 (검색 결과용)
if 'current_entry' not in st.session_state:
    st.session_state['current_entry'] = {}
if 'data_sources' not in st.session_state:
    st.session_state['data_sources'] = {}

# --- LEFT: Search & Logic Section ---
with col_search:
    st.subheader("🔍 물질 찾기 및 정보 조회")
    
    # 2-1. 기존 데이터에서 선택
    all_items = []
    if not analyzer.df.empty:
        all_items = analyzer.df.apply(lambda r: f"{get_safe_str(r['CAS'])} | {get_safe_str(r['Name_Common'])}", axis=1).tolist()
    
    new_reg_option = "--- 신규 등록(아래에 CAS 번호를 검색하세요.) ---"
    selected_item = st.selectbox("마스터 DB에서 선택 (수정용)", options=[new_reg_option] + all_items)
    
    if selected_item != new_reg_option:
        sel_cas = selected_item.split(" | ")[0]
        # 선택 시 검색 입력창에 CAS 번호 자동 채우기
        st.session_state['search_query_sync'] = sel_cas
        
        if st.session_state.get('last_selected') != sel_cas:
            row = analyzer.df[analyzer.df['CAS'].astype(str) == sel_cas].iloc[0]
            st.session_state['current_entry'] = row.to_dict()
            st.session_state['last_selected'] = sel_cas
            st.session_state['data_sources'] = {k: "Master DB" for k in row.keys()}
    else:
        if st.session_state.get('last_selected') is not None:
            st.session_state['current_entry'] = {}
            st.session_state['last_selected'] = None
            st.session_state['search_query_sync'] = ""

    st.markdown("---")
    
    # 2-2. 외부 DB 조회
    search_query = st.text_input(
        "CAS 번호 혹은 영문명으로 외부 조회", 
        value=st.session_state.get('search_query_sync', ""),
        help="PubChem/RDKit 정보를 가져옵니다."
    )
    if st.button("🔎 정보 가져오기 (Fetch Info)"):
        if search_query:
            with st.spinner("정보 조회 중..."):
                info = lookup_compound(search_query)
                if info and not info.get('error'):
                    props = get_rdkit_properties(info['smiles']) if info.get('smiles') else {}
                    
                    found_cas = info.get('cas_number', search_query)
                    sources = {
                        'CAS': 'PubChem', 'Name_Common': 'PubChem',
                        'MW': 'PubChem/RDKit', 'LogP': 'RDKit', 'SMILES': 'PubChem',
                        'Groups': 'RDKit (Patterns)'
                    }
                    
                    # 1. 우선순위: 기존 마스터 DB 확인
                    db_match = analyzer.df[analyzer.df['CAS'].astype(str) == str(found_cas)]
                    db_threshold = 0.0
                    db_desc_ko = ""
                    db_desc_en = ""
                    db_is_aac = False
                    
                    if not db_match.empty:
                        matched_row = db_match.iloc[0]
                        db_threshold = float(matched_row.get('Threshold', 0.0)) if not pd.isna(matched_row.get('Threshold')) else 0.0
                        db_desc_ko = get_safe_str(matched_row.get('Desc_Korean', ''))
                        db_desc_en = get_safe_str(matched_row.get('Desc_English', ''))
                        db_is_aac = bool(matched_row.get('Is_AAC', False))

                    # 2. 역치/묘사가 없거나 0이면 로컬 데이터 사이언스 기반 예측
                    threshold = db_threshold
                    desc_ko = db_desc_ko
                    desc_en = db_desc_en
                    is_aac = db_is_aac
                    sources['Threshold'] = 'Master DB' if db_threshold > 0 else 'Local Similarity (Data-Driven)'
                    sources['Desc_Korean'] = 'Master DB' if db_desc_ko else 'Local Similarity (Data-Driven)'
                    sources['Desc_English'] = 'Master DB' if db_desc_en else 'Local Similarity (Data-Driven)'
                    
                    if threshold <= 0 or not desc_ko or not desc_en:
                        try:
                            # 로컬 데이터 사이언스 기반 예측 실행
                            local_preds = analyzer.predict_compound_info_local(
                                mw=info.get('molecular_weight', props.get('molecular_weight', 0.0)),
                                logp=props.get('log_p', 0.0),
                                groups=props.get('functional_groups', '')
                            )
                            
                            if threshold <= 0:
                                threshold = local_preds.get('threshold', 0.0)
                            
                            if not desc_ko:
                                desc_ko = local_preds.get('desc_ko', '')
                            if not desc_en:
                                desc_en = local_preds.get('desc_en', '')
                            
                            if local_preds.get('justification'):
                                st.info(f"📊 **데이터 분석 의견:** {local_preds['justification']}")
                        except Exception as e:
                            st.warning(f"예측 도중 오류가 발생했습니다: {e}")

                    st.session_state['data_sources'] = sources
                    st.session_state['current_entry'] = {
                        'CAS': found_cas,
                        'Name_Common': info.get('name', ''),
                        'Desc_Korean': desc_ko,
                        'Threshold': threshold,
                        'Is_AAC': is_aac,
                        'Groups': props.get('functional_groups', ''),
                        'Desc_English': desc_en,
                        'MW': info.get('molecular_weight', props.get('molecular_weight', 0.0)),
                        'LogP': props.get('log_p', 0.0),
                        'SMILES': info.get('smiles', '')
                    }
                    st.success("데이터를 성공적으로 가져왔습니다.")
                else:
                    st.error("정보를 찾을 수 없습니다.")

    # 구조 이미지
    curr = st.session_state['current_entry']
    if curr.get('SMILES'):
        img = get_molecule_image(curr['SMILES'])
        if img:
            st.image(img, caption=curr.get('Name_Common', 'Structure'), width=250)

# --- RIGHT: Main Form Section ---
with col_form:
    st.subheader("📝 물질 정보 입력 및 수정")
    
    with st.form("main_entry_form", clear_on_submit=False):
        f_cas = st.text_input("CAS No*", value=get_safe_str(curr.get('CAS', '')))
        f_name = st.text_input("성분명*", value=get_safe_str(curr.get('Name_Common', '')))
        
        # 묘사 (Dual Multi-select Pill UI)
        c_desc_ko, c_desc_en = st.columns(2)
        
        with c_desc_ko:
            existing_ko = get_safe_tags(curr.get('Desc_Korean', ''))
            # 선택된 태그가 options에 없는 경우를 대비해 options를 동적으로 합침
            ko_options = sorted(list(set(all_ko_tags + existing_ko)))
            f_tags_ko = st.multiselect("한글 묘사 (Pills)", options=ko_options, default=existing_ko)
            
        with c_desc_en:
            existing_en = get_safe_tags(curr.get('Desc_English', ''))
            en_options = sorted(list(set(all_en_tags + existing_en)))
            f_tags_en = st.multiselect("영어 묘사 (Pills)", options=en_options, default=existing_en)
            
        c1, c2 = st.columns(2)
        f_thr = c1.number_input("역치 (ppm)", value=float(curr.get('Threshold', 0.0)) if not pd.isna(curr.get('Threshold')) else 0.0, format="%.6f")
        f_aac = c2.checkbox("AAC 핵심성분", value=bool(curr.get('Is_AAC', False)) if not pd.isna(curr.get('Is_AAC')) else False)
        
        # Groups (Multi-select Pill UI)
        existing_groups = get_safe_tags(curr.get('Groups', ''))
        g_options = sorted(list(set(all_groups_tags + existing_groups)))
        f_groups_tags = st.multiselect("Groups (화학 그룹)", options=g_options, default=existing_groups)
        
        c3, c4 = st.columns(2)
        f_mw = c3.number_input("분자량 (MW)", value=float(curr.get('MW', 0.0)) if not pd.isna(curr.get('MW')) else 0.0)
        f_logp = c4.number_input("LogP", value=float(curr.get('LogP', 0.0)) if not pd.isna(curr.get('LogP')) else 0.0)
        
        f_smiles = st.text_input("SMILES 구조식", value=get_safe_str(curr.get('SMILES', '')))

        # --- 데이터 출처 정보 표시 ---
        sources = st.session_state.get('data_sources', {})
        if sources:
            with st.expander("ℹ️ 데이터 출처 정보 (Data Sources)", expanded=True):
                src_data = []
                for k, v in sources.items():
                    # 한글 키로 변환 (UI용)
                    label = {
                        'CAS': 'CAS No', 'Name_Common': '성분명', 'MW': '분자량', 
                        'LogP': 'LogP', 'SMILES': '구조식', 'Groups': '화학 그룹',
                        'Threshold': '역치', 'Desc_Korean': '한글 묘사', 'Desc_English': '영어 묘사'
                    }.get(k, k)
                    src_data.append({"항목": label, "출처": v})
                st.table(pd.DataFrame(src_data))

        # 버튼 영역 (레이아웃 개선)
        is_edit = selected_item != new_reg_option
        
        # Streamlit의 columns는 기본적으로 균등 분할이지만, 중간에 빈 컬럼을 두어 양 끝 정렬 효과를 냄
        # 비율: [저장버튼, 빈공간, 삭제버튼]
        if is_edit:
            col_save, col_space, col_del = st.columns([1, 2, 1])
        else:
            col_save, col_space = st.columns([1, 3]) # 신규 등록 시 삭제 버튼 불필요

        with col_save:
            # use_container_width=True로 버튼을 컬럼 너비에 꽉 차게 만듦
            if st.form_submit_button("💾 정보 저장 (Save)", type="primary", use_container_width=True):
                # ... (저장 로직 동일) ...
                if not f_cas or not f_name:
                    st.error("CAS 번호와 성분명은 필수입니다.")
                else:
                    new_rec = {
                        'CAS': f_cas, 'Name_Common': f_name, 
                        'Desc_Korean': ", ".join(f_tags_ko), 'Desc_English': ", ".join(f_tags_en),
                        'Threshold': f_thr, 'Is_AAC': f_aac, 'Groups': ", ".join(f_groups_tags),
                        'MW': f_mw, 'LogP': f_logp, 'SMILES': f_smiles
                    }
                    
                    if is_edit:
                        idx = analyzer.df[analyzer.df['CAS'] == f_cas].index
                        for k, v in new_rec.items():
                            analyzer.df.loc[idx, k] = v
                    else:
                        if f_cas in analyzer.df['CAS'].astype(str).values:
                            st.warning("이미 존재하는 CAS 번호입니다. 기존 항목 선택 후 수정하세요.")
                        else:
                            analyzer.df = pd.concat([analyzer.df, pd.DataFrame([new_rec])], ignore_index=True)
                    
                    analyzer._save_db()
                    st.success(f"✅ {f_name} 저장 완료!")
                    st.rerun()

        if is_edit:
            with col_del:
                # use_container_width=True로 버튼을 컬럼 너비에 꽉 차게 만듦
                if st.form_submit_button("🗑️ 항목 삭제 (Delete)", use_container_width=True):
                    analyzer.df = analyzer.df[analyzer.df['CAS'] != f_cas]
                    analyzer._save_db()
                    st.success("삭제되었습니다.")
                    st.rerun()