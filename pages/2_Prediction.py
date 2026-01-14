"""
Prediction Page - Predict sensory scores using ML regression models
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import init_database, get_session, get_all_lots, get_lot_by_number
from src.analysis import SensoryPredictor, generate_correlation_analysis, get_feature_importance

# Initialize database
init_database()

st.set_page_config(page_title="Prediction", page_icon="🎯", layout="wide")

st.title("🎯 Sensory Score Prediction")
st.markdown("Predict sensory scores using machine learning regression models")

# Sidebar for model configuration
st.sidebar.header("Model Configuration")
model_type = st.sidebar.selectbox(
    "Select Model Type",
    ['random_forest', 'gradient_boosting', 'linear', 'ridge', 'lasso'],
    help="Choose the regression algorithm"
)

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🔮 Make Predictions", 
    "🏋️ Train Model", 
    "📊 Model Analysis",
    "🔗 Correlations"
])

# Tab 1: Make Predictions
with tab1:
    st.subheader("Predict Sensory Scores")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Input Method")
        input_method = st.radio(
            "Choose input method:",
            ["Select Existing LOT", "Manual Input"],
            horizontal=True
        )
    
    chemical_data = {}
    
    if input_method == "Select Existing LOT":
        try:
            session = get_session()
            lots = get_all_lots(session)
            
            if lots:
                lot_numbers = [lot.lot_number for lot in lots]
                selected_lot = st.selectbox("Select LOT for Prediction", lot_numbers)
                
                if selected_lot:
                    lot = get_lot_by_number(session, selected_lot)
                    
                    st.info(f"📦 Selected: {lot.product_name} (LOT {lot.lot_number})")
                    
                    chemical_data = {
                        'alcohol_content': lot.alcohol_content,
                        'acidity': lot.acidity,
                        'sugar_content': lot.sugar_content,
                        'tannin_level': lot.tannin_level,
                        'ester_concentration': lot.ester_concentration,
                        'aldehyde_level': lot.aldehyde_level
                    }
                    
                    # Display chemical composition
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Alcohol Content", f"{lot.alcohol_content}% ABV")
                        st.metric("Acidity", f"{lot.acidity} pH")
                    with col_b:
                        st.metric("Sugar Content", f"{lot.sugar_content} g/L")
                        st.metric("Tannin Level", f"{lot.tannin_level} mg/L")
                    with col_c:
                        st.metric("Ester Concentration", f"{lot.ester_concentration} mg/L")
                        st.metric("Aldehyde Level", f"{lot.aldehyde_level} mg/L")
            else:
                st.warning("📭 No LOT data available. Add data in the Data Entry page first.")
            
            session.close()
        except Exception as e:
            st.error(f"❌ Error loading LOTs: {str(e)}")
    
    else:  # Manual Input
        st.markdown("### Enter Chemical Composition")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            chemical_data['alcohol_content'] = st.number_input(
                "Alcohol Content (% ABV)", 
                min_value=0.0, max_value=100.0, value=40.0, step=0.1
            )
            chemical_data['acidity'] = st.number_input(
                "Acidity (pH)", 
                min_value=0.0, max_value=14.0, value=7.0, step=0.1
            )
        
        with col2:
            chemical_data['sugar_content'] = st.number_input(
                "Sugar Content (g/L)", 
                min_value=0.0, value=0.0, step=0.1
            )
            chemical_data['tannin_level'] = st.number_input(
                "Tannin Level (mg/L)", 
                min_value=0.0, value=0.0, step=0.1
            )
        
        with col3:
            chemical_data['ester_concentration'] = st.number_input(
                "Ester Concentration (mg/L)", 
                min_value=0.0, value=0.0, step=0.1
            )
            chemical_data['aldehyde_level'] = st.number_input(
                "Aldehyde Level (mg/L)", 
                min_value=0.0, value=0.0, step=0.1
            )
    
    if st.button("🔮 Predict Sensory Scores", type="primary"):
        try:
            # Check if model exists
            model_path = Path(__file__).resolve().parent.parent / "data" / "models" / f"sensory_predictor_{model_type}.pkl"
            
            if not model_path.exists():
                st.error(f"❌ Model not found! Please train the {model_type} model first in the 'Train Model' tab.")
            else:
                predictor = SensoryPredictor(model_type=model_type)
                predictor.load_models(model_path)
                
                predictions = predictor.predict(chemical_data)
                
                st.success("✅ Predictions generated successfully!")
                
                # Display predictions
                st.markdown("### 🎯 Predicted Sensory Scores")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Aroma Score", f"{predictions['aroma_score']:.1f}/100")
                with col2:
                    st.metric("Taste Score", f"{predictions['taste_score']:.1f}/100")
                with col3:
                    st.metric("Finish Score", f"{predictions['finish_score']:.1f}/100")
                with col4:
                    st.metric("Overall Score", f"{predictions['overall_score']:.1f}/100")
                
                # Radar chart
                categories = ['Aroma', 'Taste', 'Finish', 'Overall']
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
                    name='Predicted Scores'
                ))
                
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=False,
                    title="Sensory Score Profile"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"❌ Prediction error: {str(e)}")

# Tab 2: Train Model
with tab2:
    st.subheader("Train Prediction Model")
    
    st.info("""
    ℹ️ **Training Requirements:**
    - At least 5 LOT records with complete sensory scores
    - Chemical composition data for all LOTs
    - Training will use 80% data for training and 20% for testing
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
        
        st.metric("Available Training Samples", len(complete_lots))
        
        if len(complete_lots) >= 5:
            test_size = st.slider("Test Data Percentage", 10, 40, 20) / 100
            
            if st.button("🏋️ Train Model", type="primary"):
                with st.spinner(f"Training {model_type} model..."):
                    try:
                        predictor = SensoryPredictor(model_type=model_type)
                        metrics = predictor.train(complete_lots, test_size=test_size)
                        
                        # Save the model
                        model_path = predictor.save_models()
                        
                        st.success(f"✅ Model trained and saved successfully to {model_path.name}")
                        
                        # Display metrics
                        st.markdown("### 📊 Model Performance Metrics")
                        
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
                            title="Model Performance Across Targets",
                            xaxis_title="Target Variable",
                            yaxis_title="Score",
                            barmode='group'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"❌ Training error: {str(e)}")
        else:
            st.warning(f"⚠️ Insufficient data for training. Need at least 5 LOTs with complete sensory scores. Currently have {len(complete_lots)}.")
            st.info("💡 Add more LOT data with sensory scores in the Data Entry page.")
        
        session.close()
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Tab 3: Model Analysis
with tab3:
    st.subheader("Model Analysis & Feature Importance")
    
    try:
        model_path = Path(__file__).resolve().parent.parent / "data" / "models" / f"sensory_predictor_{model_type}.pkl"
        
        if model_path.exists():
            predictor = SensoryPredictor(model_type=model_type)
            predictor.load_models(model_path)
            
            st.success(f"✅ Loaded {model_type} model")
            
            # Feature importance (for tree-based models)
            if model_type in ['random_forest', 'gradient_boosting']:
                st.markdown("### 🎯 Feature Importance")
                
                target_select = st.selectbox(
                    "Select Target Variable",
                    predictor.target_names
                )
                
                importance = get_feature_importance(predictor, target_select)
                
                if importance:
                    # Create bar chart
                    fig = px.bar(
                        x=list(importance.values()),
                        y=list(importance.keys()),
                        orientation='h',
                        title=f"Feature Importance for {target_select.replace('_', ' ').title()}",
                        labels={'x': 'Importance', 'y': 'Feature'}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show as table
                    importance_df = pd.DataFrame({
                        'Feature': importance.keys(),
                        'Importance': importance.values()
                    })
                    st.dataframe(importance_df, use_container_width=True)
            else:
                st.info("ℹ️ Feature importance is only available for tree-based models (Random Forest, Gradient Boosting)")
        else:
            st.warning(f"⚠️ No trained model found for {model_type}. Train a model first in the 'Train Model' tab.")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# Tab 4: Correlations
with tab4:
    st.subheader("Chemical-Sensory Correlations")
    
    try:
        session = get_session()
        lots = get_all_lots(session)
        
        if lots and len(lots) >= 3:
            corr_matrix = generate_correlation_analysis(lots)
            
            # Heatmap
            fig = px.imshow(
                corr_matrix,
                labels=dict(color="Correlation"),
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                color_continuous_scale='RdBu_r',
                aspect="auto",
                title="Correlation Matrix: Chemical Features vs Sensory Scores"
            )
            
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show correlation table
            with st.expander("📋 View Correlation Values"):
                st.dataframe(corr_matrix.style.background_gradient(cmap='RdBu_r', axis=None), use_container_width=True)
        else:
            st.warning("⚠️ Need at least 3 LOT records to generate correlation analysis.")
        
        session.close()
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
