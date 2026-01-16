"""
Report Page - Generate comprehensive flavor reports using Google Gemini AI
"""

import streamlit as st
import sys
from pathlib import Path
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import init_database, get_session, get_all_lots, get_lot_by_number, get_sensory_profiles_by_lot
from src.llm import GeminiFlavorReporter, test_gemini_connection
from src.analysis import SensoryPredictor

# Initialize database
init_database()

st.set_page_config(page_title="AI 리포트", page_icon="📝", layout="wide")

st.title("📝 AI 기반 향미 리포트")
st.markdown("Google Gemini AI를 사용하여 종합적인 향미 리포트를 생성합니다")

# Check API key configuration
api_key_configured = os.getenv('GEMINI_API_KEY') is not None

if not api_key_configured:
    st.warning("⚠️ **Gemini API 키가 설정되지 않았습니다**")
    st.info("""
    AI 기반 리포트를 사용하려면 Google Gemini API 키를 설정해야 합니다:
    
    1. [Google AI Studio](https://makersuite.google.com/app/apikey)에서 API 키를 발급받으세요.
    2. 프로젝트 루트에 `.env` 파일을 생성하거나 환경 변수를 설정하세요.
    3. 다음을 추가하세요: `GEMINI_API_KEY=your_api_key_here`
    
    또는 아래에 API 키를 입력하여 이 세션에서 사용할 수 있습니다:
    """)
    
    temp_api_key = st.text_input("Gemini API 키 입력 (임시)", type="password")
    
    if temp_api_key:
        os.environ['GEMINI_API_KEY'] = temp_api_key
        if st.button("연결 테스트"):
            if test_gemini_connection(temp_api_key):
                st.success("✅ API 키가 유효합니다! 이제 리포트를 생성할 수 있습니다.")
                api_key_configured = True
            else:
                st.error("❌ 유효하지 않은 API 키거나 연결에 실패했습니다.")

# Main functionality (only if API key is configured)
if api_key_configured or os.getenv('GEMINI_API_KEY'):
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 향미 리포트",
        "🔬 화학 성분 분석",
        "⚖️ 비교 리포트",
        "🏷️ 관능 묘사어"
    ])
    
    # Tab 1: Generate Flavor Report
    with tab1:
        st.subheader("종합 향미 리포트 생성")
        
        try:
            session = get_session()
            lots = get_all_lots(session)
            
            if lots:
                lot_numbers = [lot.lot_number for lot in lots]
                selected_lot = st.selectbox("리포트 생성할 LOT 선택", lot_numbers)
                
                if selected_lot:
                    lot = get_lot_by_number(session, selected_lot)
                    
                    st.info(f"📦 리포트 생성 중: {lot.product_name} (LOT {lot.lot_number})")
                    
                    # Display current data
                    with st.expander("📊 LOT 데이터 보기"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**화학 성분:**")
                            st.write(f"- 알코올 도수: {lot.alcohol_content}% ABV")
                            st.write(f"- 산도: {lot.acidity} pH")
                            st.write(f"- 당 함량: {lot.sugar_content} g/L")
                            st.write(f"- 타닌 수치: {lot.tannin_level} mg/L")
                            st.write(f"- 에스터 농도: {lot.ester_concentration} mg/L")
                            st.write(f"- 알데히드 수치: {lot.aldehyde_level} mg/L")
                        
                        with col2:
                            if lot.aroma_score:
                                st.markdown("**관능 점수:**")
                                st.write(f"- 향: {lot.aroma_score}/100")
                                st.write(f"- 맛: {lot.taste_score}/100")
                                st.write(f"- 여운: {lot.finish_score}/100")
                                st.write(f"- 종합: {lot.overall_score}/100")
                    
                    # Option to include predicted scores
                    use_predictions = False
                    if not lot.aroma_score:
                        st.info("ℹ️ 기록된 관능 점수가 없습니다. AI 예측 값을 리포트에 포함할 수 있습니다.")
                        use_predictions = st.checkbox("예측 관능 점수 포함", value=True)
                    
                    if st.button("🤖 AI 향미 리포트 생성", type="primary"):
                        with st.spinner("Gemini AI로 리포트 생성 중..."):
                            try:
                                reporter = GeminiFlavorReporter()
                                
                                # Prepare chemical data
                                chemical_data = {
                                    'alcohol_content': lot.alcohol_content,
                                    'acidity': lot.acidity,
                                    'sugar_content': lot.sugar_content,
                                    'tannin_level': lot.tannin_level,
                                    'ester_concentration': lot.ester_concentration,
                                    'aldehyde_level': lot.aldehyde_level
                                }
                                
                                # Prepare sensory scores
                                sensory_scores = None
                                if lot.aroma_score:
                                    sensory_scores = {
                                        'aroma_score': lot.aroma_score,
                                        'taste_score': lot.taste_score,
                                        'finish_score': lot.finish_score,
                                        'overall_score': lot.overall_score
                                    }
                                elif use_predictions:
                                    # Try to load model and predict
                                    try:
                                        model_path = Path(__file__).resolve().parent.parent / "data" / "models" / "sensory_predictor_random_forest.pkl"
                                        if model_path.exists():
                                            predictor = SensoryPredictor(model_type='random_forest')
                                            predictor.load_models(model_path)
                                            sensory_scores = predictor.predict(chemical_data)
                                            st.info("📊 ML 예측 관능 점수 사용")
                                    except:
                                        pass
                                
                                # Get sensory notes if available
                                sensory_notes = None
                                profiles = get_sensory_profiles_by_lot(session, selected_lot)
                                if profiles:
                                    profile = profiles[0]  # Use most recent
                                    sensory_notes = {
                                        'color': profile.color_description,
                                        'aroma_notes': profile.aroma_notes,
                                        'flavor_notes': profile.flavor_notes,
                                        'mouthfeel': profile.mouthfeel,
                                        'finish': profile.finish_description
                                    }
                                
                                # Generate report
                                report = reporter.generate_flavor_report(
                                    chemical_data,
                                    sensory_scores,
                                    sensory_notes
                                )
                                
                                st.success("✅ 리포트가 성공적으로 생성되었습니다!")
                                
                                # Display report
                                st.markdown("---")
                                st.markdown("## 🍷 향미 리포트")
                                st.markdown(f"**제품명:** {lot.product_name}")
                                st.markdown(f"**LOT:** {lot.lot_number}")
                                st.markdown("---")
                                st.markdown(report)
                                
                                # Download option
                                st.download_button(
                                    label="📥 리포트 다운로드",
                                    data=report,
                                    file_name=f"flavor_report_{selected_lot}.txt",
                                    mime="text/plain"
                                )
                                
                            except Exception as e:
                                st.error(f"❌ 리포트 생성 오류: {str(e)}")
            else:
                st.warning("📭 LOT 데이터가 없습니다. 데이터 입력 페이지에서 먼저 데이터를 추가하세요.")
            
            session.close()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # Tab 2: Chemical Insights
    with tab2:
        st.subheader("화학 성분 인사이트")
        
        try:
            session = get_session()
            lots = get_all_lots(session)
            
            if lots:
                lot_numbers = [lot.lot_number for lot in lots]
                selected_lot = st.selectbox("화학 분석할 LOT 선택", lot_numbers, key="chem_insights")
                
                if selected_lot:
                    lot = get_lot_by_number(session, selected_lot)
                    
                    if st.button("🔬 화학 인사이트 생성", type="primary"):
                        with st.spinner("화학 성분 분석 중..."):
                            try:
                                reporter = GeminiFlavorReporter()
                                
                                chemical_data = {
                                    'alcohol_content': lot.alcohol_content,
                                    'acidity': lot.acidity,
                                    'sugar_content': lot.sugar_content,
                                    'tannin_level': lot.tannin_level,
                                    'ester_concentration': lot.ester_concentration,
                                    'aldehyde_level': lot.aldehyde_level,
                                    'product_name': lot.product_name,
                                    'lot_number': lot.lot_number
                                }
                                
                                insights = reporter.generate_chemical_insights(chemical_data)
                                
                                st.success("✅ 인사이트가 생성되었습니다!")
                                st.markdown("---")
                                st.markdown(insights)
                                
                                st.download_button(
                                    label="📥 인사이트 다운로드",
                                    data=insights,
                                    file_name=f"chemical_insights_{selected_lot}.txt",
                                    mime="text/plain"
                                )
                            except Exception as e:
                                st.error(f"❌ 오류: {str(e)}")
            else:
                st.warning("📭 LOT 데이터가 없습니다.")
            
            session.close()
        except Exception as e:
            st.error(f"❌ 오류: {str(e)}")
    
    # Tab 3: Comparison Report
    with tab3:
        st.subheader("AI 기반 LOT 비교")
        
        try:
            session = get_session()
            lots = get_all_lots(session)
            
            if lots and len(lots) >= 2:
                lot_numbers = [lot.lot_number for lot in lots]
                
                selected_lots = st.multiselect(
                    "비교할 LOT 선택 (2-5개)",
                    lot_numbers,
                    max_selections=5,
                    key="compare_lots"
                )
                
                if len(selected_lots) >= 2:
                    focus_lot = st.selectbox("기준 LOT (비교 주체)", selected_lots)
                    
                    if st.button("⚖️ 비교 리포트 생성", type="primary"):
                        with st.spinner("비교 리포트 생성 중..."):
                            try:
                                reporter = GeminiFlavorReporter()
                                
                                lot_data_list = []
                                for lot_num in selected_lots:
                                    lot = get_lot_by_number(session, lot_num)
                                    lot_data_list.append({
                                        'lot_number': lot.lot_number,
                                        'product_name': lot.product_name,
                                        'alcohol_content': lot.alcohol_content,
                                        'acidity': lot.acidity,
                                        'sugar_content': lot.sugar_content,
                                        'tannin_level': lot.tannin_level,
                                        'ester_concentration': lot.ester_concentration,
                                        'aldehyde_level': lot.aldehyde_level,
                                        'aroma_score': lot.aroma_score,
                                        'taste_score': lot.taste_score,
                                        'finish_score': lot.finish_score,
                                        'overall_score': lot.overall_score
                                    })
                                
                                report = reporter.generate_comparison_report(lot_data_list, focus_lot)
                                
                                st.success("✅ 비교 리포트가 생성되었습니다!")
                                st.markdown("---")
                                st.markdown(report)
                                
                                st.download_button(
                                    label="📥 비교 리포트 다운로드",
                                    data=report,
                                    file_name=f"comparison_report_{focus_lot}.txt",
                                    mime="text/plain"
                                )
                            except Exception as e:
                                st.error(f"❌ 오류: {str(e)}")
                else:
                    st.info("ℹ️ 비교하려면 최소 2개의 LOT을 선택하세요")
            else:
                st.warning("⚠️ 비교를 위해 최소 2개의 LOT 기록이 필요합니다.")
            
            session.close()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # Tab 4: Sensory Descriptors
    with tab4:
        st.subheader("관능 묘사어 생성")
        
        st.info("💡 화학 성분과 예측 점수를 기반으로 AI 관능 묘사어를 생성합니다")
        
        try:
            session = get_session()
            lots = get_all_lots(session)
            
            if lots:
                lot_numbers = [lot.lot_number for lot in lots]
                selected_lot = st.selectbox("LOT 선택", lot_numbers, key="descriptors")
                
                if selected_lot:
                    lot = get_lot_by_number(session, selected_lot)
                    
                    if st.button("🏷️ 묘사어 생성", type="primary"):
                        with st.spinner("관능 묘사어 생성 중..."):
                            try:
                                reporter = GeminiFlavorReporter()
                                
                                chemical_data = {
                                    'alcohol_content': lot.alcohol_content,
                                    'acidity': lot.acidity,
                                    'sugar_content': lot.sugar_content,
                                    'tannin_level': lot.tannin_level,
                                    'ester_concentration': lot.ester_concentration,
                                    'aldehyde_level': lot.aldehyde_level
                                }
                                
                                # Get or predict sensory scores
                                predicted_scores = {
                                    'aroma_score': lot.aroma_score or 75,
                                    'taste_score': lot.taste_score or 75,
                                    'finish_score': lot.finish_score or 75,
                                    'overall_score': lot.overall_score or 75
                                }
                                
                                descriptors = reporter.generate_sensory_descriptors(
                                    chemical_data,
                                    predicted_scores
                                )
                                
                                st.success("✅ 묘사어가 생성되었습니다!")
                                
                                # Display in columns
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("### 👃 향 묘사어")
                                    for desc in descriptors.get('aroma', []):
                                        if desc:
                                            st.markdown(f"- {desc}")
                                    
                                    st.markdown("### 👅 향미 묘사어")
                                    for desc in descriptors.get('flavor', []):
                                        if desc:
                                            st.markdown(f"- {desc}")
                                
                                with col2:
                                    st.markdown("### 🥃 입안감 묘사어")
                                    for desc in descriptors.get('mouthfeel', []):
                                        if desc:
                                            st.markdown(f"- {desc}")
                                    
                                    st.markdown("### ✨ 여운 묘사어")
                                    for desc in descriptors.get('finish', []):
                                        if desc:
                                            st.markdown(f"- {desc}")
                                
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("📭 LOT 데이터가 없습니다.")
            
            session.close()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

else:
    st.warning("⚠️ 이 기능을 사용하려면 Gemini API 키를 설정하세요.")
