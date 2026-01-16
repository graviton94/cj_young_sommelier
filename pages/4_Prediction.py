"""
Prediction Page - Predict sensory scores using ML regression models
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
import os
from pathlib import Path

# Add project root to path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from src.database import init_database, get_session, get_all_lots, get_lot_by_number, get_all_indices
from src.analysis import SensoryPredictor, generate_correlation_analysis, get_feature_importance

# Initialize database
init_database()

st.set_page_config(page_title="예측", page_icon="🎯", layout="wide")

st.title("🎯 관능 점수 예측")
st.markdown("머신러닝 회귀 모델을 사용하여 관능 점수를 예측합니다")

# Cache indices for performance
@st.cache_data
def load_indices_config():
    session = get_session()
    indices = get_all_indices(session, basic_only=True)
    session.close()
    return indices

try:
    indices = load_indices_config()
    idx_map = {i.code: i for i in indices}
except:
    st.error("설정 로드 실패")
    idx_map = {}

# Sidebar for model configuration
st.sidebar.header("모델 설정")
model_type = st.sidebar.selectbox(
    "모델 유형 선택",
    ['random_forest', 'gradient_boosting', 'linear', 'ridge', 'lasso'],
    help="회귀 알고리즘을 선택하세요"
)

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🔮 예측 수행", 
    "🏋️ 모델 훈련", 
    "📊 모델 분석",
    "🔗 상관관계"
])

# Tab 1: Make Predictions
with tab1:
    st.subheader("관능 점수 예측")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 입력 방법")
        input_method = st.radio(
            "입력 방법 선택:",
            ["기존 LOT 선택", "수동 입력"],
            horizontal=True
        )
    
    chemical_data = {}
    
    if input_method == "기존 LOT 선택":
        try:
            session = get_session()
            # Get unique LOT numbers
            unique_lots = sorted(list(set([l.lot_number for l in get_all_lots(session)])))
            
            selected_lot_num = st.selectbox("예측할 LOT 선택", unique_lots)
            
            if selected_lot_num:
                # Fetch history for this LOT
                history = get_all_lots(session, lot_number=selected_lot_num)
                
                # Select specific analysis record
                selected_id = st.selectbox(
                    "분석 데이터 선택 (날짜)",
                    options=[h.id for h in history],
                    format_func=lambda x: next((f"{h.production_date.strftime('%Y-%m-%d')} ({h.id})" for h in history if h.id == x), str(x))
                )
                
                target_lot = next((h for h in history if h.id == selected_id), None)
                
                if target_lot:
                    st.info(f"📦 선택됨: {target_lot.product_name} (LOT {target_lot.lot_number}) - {target_lot.production_date.strftime('%Y-%m-%d')}")
                    
                    # Construct chemical data dynamically
                    # 1. Standard fields (if any fallback needed, but we rely on dyanmic mostly now?)
                    # Actually standard fields in LOTData are still Alcohol, Acidity... 
                    # But we want to use dynamic values if possible or mixed? 
                    # Currently LOTData has columns.
                    for idx in indices:
                        if hasattr(target_lot, idx.code):
                             chemical_data[idx.code] = getattr(target_lot, idx.code)
                    
                    # 2. Dynamic LotMeasurements
                    from src.database import LotMeasurement
                    msmts = session.query(LotMeasurement).filter(LotMeasurement.lot_id == target_lot.id).all()
                    for m in msmts:
                        chemical_data[m.index_code] = m.value

                    # Display chemical composition dynamically
                    st.markdown("### 🧪 화학 성분 프로파일")
                    cols = st.columns(3)
                    for i, idx in enumerate(indices):
                        with cols[i % 3]:
                            val = chemical_data.get(idx.code)
                            st.metric(f"{idx.name}", f"{val} {idx.unit}")
                            
            else:
                st.warning("📭 LOT 데이터가 없습니다. 먼저 데이터 입력 페이지에서 데이터를 추가하세요.")
            
            session.close()
        except Exception as e:
            st.error(f"❌ LOT 불러오기 오류: {str(e)}")
    
    else:  # Manual Input
        st.markdown("### 화학 성분 입력")
        
        cols = st.columns(3)
        for i, idx in enumerate(indices):
            with cols[i % 3]:
                val = st.number_input(
                    f"{idx.name} ({idx.unit})",
                    min_value=float(idx.min_value) if idx.min_value is not None else 0.0,
                    max_value=float(idx.max_value) if idx.max_value is not None else None,
                    value=float(idx.min_value) if idx.max_value and idx.min_value else 0.0,
                    step=float(idx.step) if idx.step else 0.1,
                    key=f"predict_input_{idx.code}"
                )
                chemical_data[idx.code] = val
    
    st.divider()
    
    if st.button("🔮 관능 점수 예측", type="primary"):
        # Check if we have all necessary features
        # Just passing chemical_data to predictor
        # Predictor needs to handle missing keys or keys mismatch if settings changed
        
        try:
            # Check if model exists
            model_path = Path(__file__).resolve().parent.parent / "data" / "models" / f"sensory_predictor_{model_type}.pkl"
            
            if not model_path.exists():
                st.error(f"❌ 모델을 찾을 수 없습니다! '모델 훈련' 탭에서 먼저 {model_type} 모델을 훈련하세요.")
            else:
                predictor = SensoryPredictor(model_type=model_type)
                predictor.load_models(model_path)
                
                predictions = predictor.predict(chemical_data)
                
                st.success("✅ 예측이 성공적으로 생성되었습니다!")
                
                # Display predictions
                st.markdown("### 🎯 예측된 관능 점수")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("향 점수", f"{predictions['aroma_score']:.1f}/100")
                with col2:
                    st.metric("맛 점수", f"{predictions['taste_score']:.1f}/100")
                with col3:
                    st.metric("여운 점수", f"{predictions['finish_score']:.1f}/100")
                with col4:
                    st.metric("종합 점수", f"{predictions['overall_score']:.1f}/100")
                
                # Radar chart
                categories = ['향', '맛', '여운', '종합']
                values = [
                    predictions['aroma_score'],
                    predictions['taste_score'],
                    predictions['finish_score'],
                    predictions['overall_score']
                ]
                
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name='예측 점수'
                ))
                
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=False,
                    title="관능 점수 프로파일"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"❌ 예측 오류: {str(e)}")

# Tab 2: Train Model
with tab2:
    st.subheader("예측 모델 훈련")
    
    st.info("""
    ℹ️ **훈련 요구사항:**
    - 완전한 관능 점수가 있는 LOT 기록이 최소 5개 필요
    - 모든 LOT에 대한 화학 성분 데이터
    - 훈련은 데이터의 80%를 훈련에, 20%를 테스트에 사용합니다
    """)
    
    try:
        session = get_session()
        lots = get_all_lots(session)
        
        # Filter LOTs with complete sensory scores
        complete_lots = [
            lot for lot in lots 
            if all([
                lot.aroma_score, lot.taste_score, 
                lot.finish_score, lot.overall_score
            ])
        ]
        
        st.metric("사용 가능한 훈련 샘플", len(complete_lots))
        
        if len(complete_lots) >= 5:
            test_size = st.slider("테스트 데이터 비율", 10, 40, 20) / 100
            
            if st.button("🏋️ 모델 훈련", type="primary"):
                with st.spinner(f"{model_type} 모델 훈련 중..."):
                    try:
                        predictor = SensoryPredictor(model_type=model_type)
                        metrics = predictor.train(complete_lots, test_size=test_size)
                        
                        # Save the model
                        model_path = predictor.save_models()
                        
                        st.success(f"✅ 모델이 훈련되어 {model_path.name}에 저장되었습니다")
                        
                        # Display metrics
                        st.markdown("### 📊 모델 성능 메트릭")
                        
                        metrics_df = pd.DataFrame(metrics).T
                        st.dataframe(metrics_df.style.format("{:.4f}"), use_container_width=True)
                        
                        # Visualize metrics
                        fig = go.Figure()
                        
                        for metric in ['r2', 'rmse', 'mae']:
                            values = [metrics[target][metric] for target in metrics.keys()]
                            fig.add_trace(go.Bar(
                                name=metric.upper(),
                                x=list(metrics.keys()),
                                y=values
                            ))
                        
                        fig.update_layout(
                            title="목표별 모델 성능",
                            xaxis_title="목표 변수",
                            yaxis_title="점수",
                            barmode='group'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"❌ 훈련 오류: {str(e)}")
        else:
            st.warning(f"⚠️ 훈련에 충분한 데이터가 없습니다. 완전한 관능 점수가 있는 LOT이 최소 5개 필요합니다. 현재 {len(complete_lots)}개입니다.")
            st.info("💡 데이터 입력 페이지에서 관능 점수가 있는 LOT 데이터를 추가하세요.")
        
        session.close()
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Tab 3: Model Analysis
with tab3:
    st.subheader("모델 분석 및 특성 중요도")
    
    try:
        model_path = Path(__file__).resolve().parent.parent / "data" / "models" / f"sensory_predictor_{model_type}.pkl"
        
        if model_path.exists():
            predictor = SensoryPredictor(model_type=model_type)
            predictor.load_models(model_path)
            
            st.success(f"✅ {model_type} 모델이 로드되었습니다")
            
            # Feature importance (for tree-based models)
            if model_type in ['random_forest', 'gradient_boosting']:
                st.markdown("### 🎯 특성 중요도")
                
                target_select = st.selectbox(
                    "목표 변수 선택",
                    predictor.target_names
                )
                
                importance = get_feature_importance(predictor, target_select)
                
                if importance:
                    # Map codes to names if possible
                    formatted_importance = {}
                    for k, v in importance.items():
                        name = idx_map[k].name if k in idx_map else k
                        formatted_importance[name] = v
                        
                    # Create bar chart
                    fig = px.bar(
                        x=list(formatted_importance.values()),
                        y=list(formatted_importance.keys()),
                        orientation='h',
                        title=f"{target_select.replace('_', ' ').title()}에 대한 특성 중요도",
                        labels={'x': '중요도', 'y': '특성'}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show as table
                    importance_df = pd.DataFrame({
                        '특성': formatted_importance.keys(),
                        '중요도': formatted_importance.values()
                    })
                    st.dataframe(importance_df, use_container_width=True)
            else:
                st.info("ℹ️ 특성 중요도는 트리 기반 모델(Random Forest, Gradient Boosting)에서만 사용할 수 있습니다")
        else:
            st.warning(f"⚠️ {model_type}에 대한 훈련된 모델을 찾을 수 없습니다. '모델 훈련' 탭에서 먼저 모델을 훈련하세요.")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Tab 4: Correlations
with tab4:
    st.subheader("화학-관능 상관관계")
    
    try:
        session = get_session()
        lots = get_all_lots(session)
        
        if lots and len(lots) >= 3:
            corr_matrix = generate_correlation_analysis(lots)
            
            # Translate index using idx_map
            new_index = []
            for idx in corr_matrix.index:
                if idx in idx_map:
                    new_index.append(idx_map[idx].name)
                else:
                    # Fallback translations for scores
                    trans = {
                        'aroma_score': '향 점수', 'taste_score': '맛 점수', 
                        'finish_score': '여운 점수', 'overall_score': '종합 점수'
                    }
                    new_index.append(trans.get(idx, idx))
            
            corr_matrix.index = new_index
            corr_matrix.columns = new_index
            
            # Heatmap
            fig = px.imshow(
                corr_matrix,
                labels=dict(color="상관관계"),
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                color_continuous_scale='RdBu_r',
                aspect="auto",
                title="상관관계 행렬: 화학 특성 vs 관능 점수"
            )
            
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show correlation table
            with st.expander("📋 상관관계 값 보기"):
                st.dataframe(corr_matrix.style.background_gradient(cmap='RdBu_r', axis=None), use_container_width=True)
        else:
            st.warning("⚠️ 상관관계 분석을 위해서는 최소 3개의 LOT 기록이 필요합니다.")
        
        session.close()
    except Exception as e:
        st.error(f"❌ 오류: {str(e)}")
