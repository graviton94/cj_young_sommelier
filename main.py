"""
CJ Young Sommelier - AI-driven Liquor Analytics Platform

Main Streamlit application entry point for tracking LOT-specific chemical changes,
predicting sensory scores, and generating flavor reports.
"""

import streamlit as st
from pathlib import Path
import sys

# SQLite fix for Streamlit Cloud (Linux)
# Streamlit Cloud's system sqlite3 is often outdated; we swap it with pysqlite3
try:
    import platform
    if platform.system() == 'Linux':
        __import__('pysqlite3')
        import sys
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

# Page configuration
st.set_page_config(
    page_title="CJ Young Sommelier",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application landing page"""
    
    st.title("🍷 CJ Young Sommelier")
    st.subheader("AI 기반 주류 분석 및 향미 예측 플랫폼")
    
    st.markdown("""
    CJ Young Sommelier 플랫폼에 오신 것을 환영합니다! 이 애플리케이션은 다음과 같은 기능을 제공합니다:
    
    - **LOT별 화학 성분 변화 추적** - 주류 재고의 화학적 변화를 관리합니다
    - **관능 점수 예측** - 머신러닝 회귀 모델을 사용하여 관능 점수를 예측합니다
    - **향미 리포트 생성** - Google Gemini AI로 포괄적인 향미 리포트를 생성합니다
    
    ### 시작하기
    
    왼쪽 메뉴(Sidebar)를 사용하여 다양한 기능에 접근하세요:
    
    1. **📊 데이터 입력** - 신규 LOT 등록 및 기본 화학 성분 입력
    2. **🧪 향미 상세 분석** - 시제품 및 LOT의 향미/성능 정밀 분석 기록
    3. **📋 전체 분석 결과** - 모든 분석 이력 통합 조회 및 데이터 관리(수정/삭제)
    4. **🎯 예측** - 머신러닝 기반 관능 점수 예측 (🚧 개발 중 🚧)
    5. **👃 관능 분석** - 관능 평가 시각화 및 비교 분석
    6. **📝 AI 리포트** - Google Gemini를 활용한 종합 향미 보고서 생성 (🚧 개발 중 🚧)
    7. **⚙️ 시스템 설정** - 분석 항목, 단위, GCMS 물질 라이브러리 관리
    
    ### 플랫폼 소개
    
    이 플랫폼은 화학 분석과 머신러닝, AI를 결합하여 주류 품질 평가 및 향미 프로파일링을 위한
    실용적인 인사이트를 제공합니다.
    """)
    
    # Display system status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("데이터베이스", "준비됨", delta="SQLite")
    
    with col2:
        st.metric("머신러닝 모델", "(🚧 개발 중 🚧)", delta="sklearn")
    
    with col3:
        st.metric("AI 엔진", "(🚧 개발 중 🚧)", delta="Gemini")
    
    # Information section
    with st.expander("ℹ️ 시스템 정보"):
        st.info("""
        **기술 스택:**
        - 프론트엔드: Streamlit
        - 데이터베이스: SQLite with SQLAlchemy
        - 머신러닝: scikit-learn, pandas
        - AI: Google Gemini
        
        **데이터 저장:**
        - 화학 데이터는 로컬 SQLite 데이터베이스에 저장
        - 참조 자료를 위한 지식 베이스
        """)

if __name__ == "__main__":
    main()
