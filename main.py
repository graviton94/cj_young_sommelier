"""
CJ Young Sommelier - AI-driven Liquor Analytics Platform

Main Streamlit application entry point for tracking LOT-specific chemical changes,
predicting sensory scores, and generating flavor reports.
"""

import streamlit as st
from pathlib import Path

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
    
    왼쪽 메뉴를 사용하여 다양한 기능에 접근하세요:
    
    1. **📊 데이터 입력** - LOT 화학 성분 데이터를 입력하고 관리합니다
    2. **🧪 향미 상세 분석** - 시제품 및 LOT의 상세 향미/성분 분석 데이터를 기록합니다
    3. **🎯 예측** - 화학 프로파일을 기반으로 관능 점수를 예측합니다
    4. **👃 관능 분석** - 관능 특성을 분석하고 시각화합니다
    5. **📝 리포트** - AI를 활용한 포괄적인 향미 리포트를 생성합니다
    
    ### 플랫폼 소개
    
    이 플랫폼은 화학 분석과 머신러닝, AI를 결합하여 주류 품질 평가 및 향미 프로파일링을 위한
    실용적인 인사이트를 제공합니다.
    """)
    
    # Display system status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("데이터베이스", "준비됨", delta="SQLite")
    
    with col2:
        st.metric("머신러닝 모델", "준비됨", delta="sklearn")
    
    with col3:
        st.metric("AI 엔진", "준비됨", delta="Gemini")
    
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
