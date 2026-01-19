"""
Analysis module for ML-based sensory score prediction and Flavor Master DB management.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import pickle
import os
from pathlib import Path

# Project root and data paths
project_root = Path(__file__).resolve().parent.parent
MODEL_DIR = project_root / "data" / "models"
MODEL_DIR.mkdir(exist_ok=True, parents=True)

MASTER_DB_PATH = project_root / "data" / "master_flavor_db.csv"


class SensoryPredictor:
    """
    Machine learning predictor for sensory scores based on chemical composition
    """
    
    def __init__(self, model_type='random_forest'):
        self.model_type = model_type
        self.models = {}
        self.scalers = {}
        self.feature_names = [
            'alcohol_content',
            'acidity',
            'sugar_content',
            'tannin_level',
            'ester_concentration',
            'aldehyde_level'
        ]
        self.target_names = [
            'aroma_score',
            'taste_score',
            'finish_score',
            'overall_score'
        ]
        
        for target in self.target_names:
            self.models[target] = self._get_model(model_type)
            self.scalers[target] = StandardScaler()
    
    def _get_model(self, model_type):
        models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'linear': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'lasso': Lasso(alpha=1.0)
        }
        return models.get(model_type, RandomForestRegressor(n_estimators=100, random_state=42))
    
    def prepare_data(self, lot_data_list):
        data = []
        for lot in lot_data_list:
            if isinstance(lot, dict):
                data.append(lot)
            else:
                data.append({
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
        
        df = pd.DataFrame(data)
        for col in self.feature_names:
            if col in df.columns and df[col].isnull().any():
                median_val = df[col].median()
                if pd.isna(median_val):
                    median_val = 0.0
                df[col] = df[col].fillna(median_val)
        
        features = df[self.feature_names]
        targets = df[self.target_names] if all(t in df.columns for t in self.target_names) else None
        return features, targets
    
    def train(self, lot_data_list, test_size=0.2):
        features, targets = self.prepare_data(lot_data_list)
        if targets is None or len(features) < 5:
            raise ValueError("Insufficient data for training. Need at least 5 samples with sensory scores.")
        
        metrics = {}
        for target_name in self.target_names:
            y = targets[target_name]
            X_train, X_test, y_train, y_test = train_test_split(features, y, test_size=test_size, random_state=42)
            X_train_scaled = self.scalers[target_name].fit_transform(X_train)
            X_test_scaled = self.scalers[target_name].transform(X_test)
            self.models[target_name].fit(X_train_scaled, y_train)
            y_pred = self.models[target_name].predict(X_test_scaled)
            metrics[target_name] = {
                'r2': r2_score(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'mae': mean_absolute_error(y_test, y_pred)
            }
        return metrics
    
    def predict(self, chemical_data):
        if isinstance(chemical_data, dict):
            features = pd.DataFrame([chemical_data])[self.feature_names]
        else:
            features = chemical_data[self.feature_names]
        
        predictions = {}
        for target_name in self.target_names:
            features_scaled = self.scalers[target_name].transform(features)
            pred = self.models[target_name].predict(features_scaled)
            predictions[target_name] = float(pred[0])
        return predictions
    
    def save_models(self, prefix='sensory_predictor'):
        model_path = MODEL_DIR / f"{prefix}_{self.model_type}.pkl"
        data_to_save = {
            'models': self.models,
            'scalers': self.scalers,
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'target_names': self.target_names
        }
        with open(model_path, 'wb') as f:
            pickle.dump(data_to_save, f)
        return model_path
    
    def load_models(self, model_path):
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
        self.models = data['models']
        self.scalers = data['scalers']
        self.model_type = data['model_type']
        self.feature_names = data['feature_names']
        self.target_names = data['target_names']


def generate_correlation_analysis(lot_data_list):
    predictor = SensoryPredictor()
    features, targets = predictor.prepare_data(lot_data_list)
    if targets is not None:
        combined = pd.concat([features, targets], axis=1)
        return combined.corr()
    else:
        return features.corr()


def get_feature_importance(predictor, target_name):
    model = predictor.models[target_name]
    if hasattr(model, 'feature_importances_'):
        importance = dict(zip(predictor.feature_names, model.feature_importances_))
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    else:
        return None


class FlavorAnalyzer:
    """
    Manager for the Flavor Master DB and ETL of GCMS data using CSV format.
    """
    def __init__(self):
        self.df = pd.DataFrame()
        self.db_path = MASTER_DB_PATH
        self._load_db()

    def _load_db(self):
        if self.db_path.exists():
            try:
                self.df = pd.read_csv(self.db_path)
                # Ensure Threshold is numeric to avoid Arrow/Parquet type issues
                if 'Threshold' in self.df.columns:
                    self.df['Threshold'] = pd.to_numeric(self.df['Threshold'], errors='coerce').fillna(0.0)
            except Exception as e:
                print(f"Error loading Master DB CSV: {e}")
                self.df = pd.DataFrame()

    def _save_db(self):
        try:
            self.df.to_csv(self.db_path, index=False, encoding='utf-8-sig')
        except Exception as e:
            print(f"Error saving Master DB CSV: {e}")

    def predict_compound_info_local(self, mw, logp, groups):
        """
        Predict compound info (threshold, descriptions) based on local similarity.
        Returns a dictionary with predicted values and justification.
        """
        if self.df.empty:
            return {'threshold': 0.0, 'desc_ko': '', 'desc_en': '', 'justification': 'DB가 비어 있습니다.'}

        try:
            target_mw = float(mw) if mw else 0.0
            target_logp = float(logp) if logp else 0.0
        except (ValueError, TypeError):
            return {'threshold': 0.0, 'desc_ko': '', 'desc_en': '', 'justification': '부적절한 물리적 속성 값'}

        target_groups = set([g.strip().lower() for g in str(groups).replace(',', ' ').split() if g.strip()])

        # 비교 대상 데이터 준비
        valid_df = self.df.copy()
        valid_df['MW'] = pd.to_numeric(valid_df.get('MW'), errors='coerce')
        valid_df['LogP'] = pd.to_numeric(valid_df.get('LogP'), errors='coerce')
        valid_df['Threshold'] = pd.to_numeric(valid_df.get('Threshold'), errors='coerce')
        
        # 물리적 속성이 있는 항목들 (역치는 나중에 처리)
        valid_df = valid_df.dropna(subset=['MW', 'LogP'])
        
        if valid_df.empty:
            return {'threshold': 0.0, 'desc_ko': '', 'desc_en': '', 'justification': '비교 가능한 데이터가 없습니다.'}

        def calc_similarity(row):
            # 정규화 거리 (MW: 0-500, LogP: -5~10 가정)
            mw_dist = abs(row['MW'] - target_mw) / 300.0
            logp_dist = abs(row['LogP'] - target_logp) / 10.0
            
            # 작용기 유사도 (Jaccard)
            row_groups = set([g.strip().lower() for g in str(row.get('Groups', '')).replace(',', ' ').split() if g.strip()])
            if not target_groups and not row_groups:
                group_penalty = 0.0
            elif not target_groups or not row_groups:
                group_penalty = 0.8
            else:
                intersection = len(target_groups.intersection(row_groups))
                union = len(target_groups.union(row_groups))
                group_penalty = 1.0 - (intersection / union)
            
            return (mw_dist * 0.3) + (logp_dist * 0.3) + (group_penalty * 0.4)

        valid_df['distance'] = valid_df.apply(calc_similarity, axis=1)
        neighbors = valid_df.sort_values('distance').head(5)

        # 1. 역치 예측 (역치가 있는 인접 항목들만 사용)
        thr_neighbors = neighbors[neighbors['Threshold'] > 0]
        predicted_threshold = 0.0
        if not thr_neighbors.empty:
            weights = 1.0 / (thr_neighbors['distance'] + 0.01)
            predicted_threshold = round(float(np.average(thr_neighbors['Threshold'], weights=weights)), 6)

        # 2. 묘사 예측 (태그 빈도 기반)
        def get_top_tags(df, col):
            tags = []
            for val in df[col].dropna():
                # Split by comma, strip, and ignore 'nan' strings
                parts = [t.strip() for t in str(val).split(',') if t.strip() and str(t).lower() != 'nan']
                tags.extend(parts)
            if not tags: return ""
            
            # value_counts().index can be non-string if tags are somehow weird
            top_tags = pd.Series(tags).value_counts().head(3).index.tolist()
            return ", ".join([str(t) for t in top_tags])

        desc_ko = get_top_tags(neighbors, 'Desc_Korean')
        desc_en = get_top_tags(neighbors, 'Desc_English')

        # 3. 근거 요약 (null 또는 'nan' 필사)
        valid_names = [str(n) for n in neighbors['Name_Common'].dropna().tolist() if str(n).strip() and str(n).lower() != 'nan']
        neighbor_names = ", ".join(valid_names[:3])
        justification = f"가장 유사한 성분({neighbor_names} 등)의 데이터를 기반으로 추정한 결과입니다." if neighbor_names else "유사한 성분들의 데이터를 기반으로 추정한 결과입니다."

        return {
            'threshold': predicted_threshold,
            'desc_ko': desc_ko,
            'desc_en': desc_en,
            'justification': justification
        }