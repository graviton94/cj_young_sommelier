"""
Sensory Page - Analyze and visualize sensory characteristics
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from src.database import (
    init_database, get_session, get_lot_by_number, get_all_lots,
    add_sensory_profile, get_sensory_profiles_by_lot
)

# Initialize database
init_database()

st.set_page_config(page_title="관능 분석", page_icon="👃", layout="wide")

st.title("👃 관능 분석 및 프로파일링")
st.markdown("주류 LOT의 관능 특성을 분석하고 시각화합니다")

# Tabs
tab1, tab2, tab3 = st.tabs([
    "📝 관능 프로파일 추가", 
    "📊 관능 데이터 보기",
    "🔍 LOT 비교"
])

# Tab 1: Add Sensory Profile
with tab1:
    st.subheader("상세 관능 프로파일 작성")
    
    try:
        session = get_session()
        lots = get_all_lots(session)
        
        if lots:
            lot_numbers = [lot.lot_number for lot in lots]
            selected_lot = st.selectbox("LOT 선택", lot_numbers)
            
            if selected_lot:
                lot = get_lot_by_number(session, selected_lot)
                st.info(f"📦 관능 프로파일 작성 대상: {lot.product_name} (LOT {lot.lot_number})")
                
                with st.form("sensory_profile_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 시각 및 향")
                        color_description = st.text_input(
                            "색상 설명",
                            placeholder="예: 깊은 호박색, 투명한"
                        )
                        
                        aroma_notes = st.text_area(
                            "향 특징",
                            placeholder="예: 바닐라, 오크, 카라멜, 과일",
                            help="쉼표로 구분하여 설명"
                        )
                        
                        st.markdown("### 맛 및 질감")
                        flavor_notes = st.text_area(
                            "향미 특징",
                            placeholder="예: 향신료, 꾸, 감귀류, 초콜릿",
                            help="쉼표로 구분하여 설명"
                        )
                        
                        mouthfeel = st.text_input(
                            "입안감",
                            placeholder="예: 부드러운, 풍부한 바디감, 크리미한"
                        )
                    
                    with col2:
                        st.markdown("### 여운 및 종합")
                        finish_description = st.text_area(
                            "여운 설명",
                            placeholder="잔향과 지속되는 향미를 설명하세요"
                        )
                        
                        st.markdown("### 시음 정보")
                        taster_name = st.text_input(
                            "시음자 이름",
                            placeholder="이름 또는 ID"
                        )
                        
                        tasting_date = st.date_input(
                            "시음일",
                            value=datetime.now()
                        )
                    
                    submitted = st.form_submit_button("💾 관능 프로파일 저장")
                    
                    if submitted:
                        if not taster_name:
                            st.error("❌ 시음자 이름은 필수 항목입니다!")
                        else:
                            try:
                                profile_data = {
                                    'lot_number': selected_lot,
                                    'color_description': color_description,
                                    'aroma_notes': aroma_notes,
                                    'flavor_notes': flavor_notes,
                                    'mouthfeel': mouthfeel,
                                    'finish_description': finish_description,
                                    'taster_name': taster_name,
                                    'tasting_date': datetime.combine(tasting_date, datetime.min.time())
                                }
                                
                                add_sensory_profile(session, profile_data)
                                st.success(f"✅ LOT {selected_lot}에 대한 관능 프로파일이 저장되었습니다!")
                                st.balloons()
                            except Exception as e:
                                st.error(f"❌ 프로파일 저장 오류: {str(e)}")
        else:
            st.warning("📭 LOT 데이터가 없습니다. 먼저 데이터 입력 페이지에서 LOT을 추가하세요.")
        
        session.close()
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Tab 2: View Sensory Data
with tab2:
    st.subheader("관능 프로파일 및 점수")
    
    try:
        session = get_session()
        lots = get_all_lots(session)
        
        if lots:
            # LOT selector
            lot_numbers = ['전체 LOT'] + [lot.lot_number for lot in lots]
            view_lot = st.selectbox("조회할 LOT 선택", lot_numbers)
            
            if view_lot == '전체 LOT':
                # Show all LOTs with sensory scores
                st.markdown("### 전체 LOT 관능 점수")
                
                data = []
                for lot in lots:
                    if lot.aroma_score or lot.taste_score or lot.finish_score or lot.overall_score:
                        data.append({
                            'LOT 번호': lot.lot_number,
                            '제품명': lot.product_name,
                            '향': lot.aroma_score or 0,
                            '맛': lot.taste_score or 0,
                            '여운': lot.finish_score or 0,
                            '종합': lot.overall_score or 0
                        })
                
                if data:
                    df = pd.DataFrame(data)
                    
                    # Display table
                    st.dataframe(df, use_container_width=True)
                    
                    # Visualization
                    fig = go.Figure()
                    
                    for category in ['향', '맛', '여운', '종합']:
                        fig.add_trace(go.Bar(
                            name=category,
                            x=df['LOT 번호'],
                            y=df[category]
                        ))
                    
                    fig.update_layout(
                        title="LOT별 관능 점수",
                        xaxis_title="LOT 번호",
                        yaxis_title="점수 (0-100)",
                        barmode='group',
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("ℹ️ 아직 기록된 관능 점수가 없습니다.")
            
            else:
                # Show specific LOT details
                lot = get_lot_by_number(session, view_lot)
                
                if lot:
                    st.markdown(f"### {lot.product_name} (LOT {lot.lot_number})")
                    
                    # Chemical composition
                    with st.expander("🧪 화학 성분 구성", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("알코올 도수", f"{lot.alcohol_content}% ABV")
                            st.metric("산도", f"{lot.acidity} pH")
                        with col2:
                            st.metric("당 함량", f"{lot.sugar_content} g/L")
                            st.metric("타닌 수치", f"{lot.tannin_level} mg/L")
                        with col3:
                            st.metric("에스터 농도", f"{lot.ester_concentration} mg/L")
                            st.metric("알데히드 수치", f"{lot.aldehyde_level} mg/L")
                    
                    # Sensory scores
                    if lot.aroma_score or lot.taste_score:
                        with st.expander("🎯 관능 점수", expanded=True):
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("향", f"{lot.aroma_score or 0:.1f}/100")
                            with col2:
                                st.metric("맛", f"{lot.taste_score or 0:.1f}/100")
                            with col3:
                                st.metric("여운", f"{lot.finish_score or 0:.1f}/100")
                            with col4:
                                st.metric("종합", f"{lot.overall_score or 0:.1f}/100")
                            
                            # Radar chart
                            categories = ['향', '맛', '여운', '종합']
                            values = [
                                lot.aroma_score or 0,
                                lot.taste_score or 0,
                                lot.finish_score or 0,
                                lot.overall_score or 0
                            ]
                            
                            fig = go.Figure()
                            fig.add_trace(go.Scatterpolar(
                                r=values,
                                theta=categories,
                                fill='toself'
                            ))
                            
                            fig.update_layout(
                                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                                showlegend=False,
                                title="관능 프로파일"
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Sensory profiles
                    profiles = get_sensory_profiles_by_lot(session, view_lot)
                    
                    if profiles:
                        with st.expander("📝 시음 노트", expanded=True):
                            for i, profile in enumerate(profiles, 1):
                                st.markdown(f"**시음 #{i}** - 시음자: {profile.taster_name}, 일자: {profile.tasting_date.strftime('%Y-%m-%d') if profile.tasting_date else 'N/A'}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if profile.color_description:
                                        st.write(f"**색상:** {profile.color_description}")
                                    if profile.aroma_notes:
                                        st.write(f"**향:** {profile.aroma_notes}")
                                    if profile.flavor_notes:
                                        st.write(f"**향미:** {profile.flavor_notes}")
                                
                                with col2:
                                    if profile.mouthfeel:
                                        st.write(f"**입안감:** {profile.mouthfeel}")
                                    if profile.finish_description:
                                        st.write(f"**여운:** {profile.finish_description}")
                                
                                st.divider()
                    
                    # Notes
                    if lot.notes:
                        with st.expander("📋 추가 메모"):
                            st.write(lot.notes)
        
        session.close()
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Tab 3: Compare LOTs
with tab3:
    st.subheader("다중 LOT 비교")
    
    try:
        session = get_session()
        lots = get_all_lots(session)
        
        if lots and len(lots) >= 2:
            lot_numbers = [lot.lot_number for lot in lots]
            
            selected_lots = st.multiselect(
                "비교할 LOT 선택 (2-5개)",
                lot_numbers,
                max_selections=5
            )
            
            if len(selected_lots) >= 2:
                comparison_data = []
                
                for lot_num in selected_lots:
                    lot = get_lot_by_number(session, lot_num)
                    comparison_data.append({
                        'LOT': lot.lot_number,
                        '제품명': lot.product_name,
                        '알코올 도수 (%)': lot.alcohol_content,
                        '산도 (pH)': lot.acidity,
                        '당 함량': lot.sugar_content,
                        '타닌': lot.tannin_level,
                        '에스터': lot.ester_concentration,
                        '알데히드': lot.aldehyde_level,
                        '향 점수': lot.aroma_score or 0,
                        '맛 점수': lot.taste_score or 0,
                        '여운 점수': lot.finish_score or 0,
                        '종합 점수': lot.overall_score or 0
                    })
                
                df = pd.DataFrame(comparison_data)
                
                # Display comparison table
                st.markdown("### 📊 비교 표")
                st.dataframe(df, use_container_width=True)
                
                # Chemical composition comparison
                st.markdown("### 🧪 화학 성분 비교")
                
                chemical_features = ['알코올 도수 (%)', '산도 (pH)', '당 함량', '타닌', '에스터', '알데히드']
                
                fig = go.Figure()
                
                for lot_num in selected_lots:
                    lot_data = df[df['LOT'] == lot_num].iloc[0]
                    values = [lot_data[feat] for feat in chemical_features]
                    
                    fig.add_trace(go.Bar(
                        name=f"LOT {lot_num}",
                        x=chemical_features,
                        y=values
                    ))
                
                fig.update_layout(
                    title="화학 성분 비교",
                    xaxis_title="화학 성분",
                    yaxis_title="값",
                    barmode='group',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Sensory scores comparison
                st.markdown("### 🎯 관능 점수 비교")
                
                sensory_features = ['향 점수', '맛 점수', '여운 점수', '종합 점수']
                
                fig2 = go.Figure()
                
                for lot_num in selected_lots:
                    lot_data = df[df['LOT'] == lot_num].iloc[0]
                    values = [lot_data[feat] for feat in sensory_features]
                    
                    fig2.add_trace(go.Scatterpolar(
                        r=values,
                        theta=[s.replace(' 점수', '') for s in sensory_features],
                        fill='toself',
                        name=f"LOT {lot_num}"
                    ))
                
                fig2.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    title="관능 점수 레이더 비교"
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            
            elif len(selected_lots) == 1:
                st.info("ℹ️ 비교하려면 최소 2개의 LOT을 선택하세요")
        else:
            st.warning("⚠️ 비교 기능을 사용하려면 최소 2개의 LOT 기록이 필요합니다.")
        
        session.close()
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
