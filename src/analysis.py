"""
Analysis module for ML-based sensory score prediction using scikit-learn and pandas
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import pickle
from pathlib import Path

# Model storage path
MODEL_DIR = Path(__file__).resolve().parent.parent / "data" / "models"
MODEL_DIR.mkdir(exist_ok=True, parents=True)


class SensoryPredictor:
    """
    Machine learning predictor for sensory scores based on chemical composition
    """
    
    def __init__(self, model_type='random_forest'):
        """
        Initialize the predictor with a specific model type
        
        Args:
            model_type: Type of regression model to use
                       ('random_forest', 'gradient_boosting', 'linear', 'ridge', 'lasso')
        """
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
        
        # Initialize models for each target
        for target in self.target_names:
            self.models[target] = self._get_model(model_type)
            self.scalers[target] = StandardScaler()
    
    def _get_model(self, model_type):
        """Get model instance based on type"""
        models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'linear': LinearRegression(),
            'ridge': Ridge(alpha=1.0),
            'lasso': Lasso(alpha=1.0)
        }
        return models.get(model_type, RandomForestRegressor(n_estimators=100, random_state=42))
    
    def prepare_data(self, lot_data_list):
        """
        Prepare data from LOT records for training or prediction
        
        Args:
            lot_data_list: List of LOTData objects or dictionaries
        
        Returns:
            Tuple of (features_df, targets_df)
        """
        data = []
        for lot in lot_data_list:
            if isinstance(lot, dict):
                data.append(lot)
            else:
                # Convert SQLAlchemy object to dict
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
        
        # Handle missing values
        df = df.fillna(df.mean())
        
        features = df[self.feature_names]
        targets = df[self.target_names] if all(t in df.columns for t in self.target_names) else None
        
        return features, targets
    
    def train(self, lot_data_list, test_size=0.2):
        """
        Train the prediction models
        
        Args:
            lot_data_list: List of LOTData objects with complete sensory scores
            test_size: Fraction of data to use for testing
        
        Returns:
            Dictionary containing training metrics
        """
        features, targets = self.prepare_data(lot_data_list)
        
        if targets is None or len(features) < 5:
            raise ValueError("Insufficient data for training. Need at least 5 samples with sensory scores.")
        
        metrics = {}
        
        for target_name in self.target_names:
            y = targets[target_name]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, y, test_size=test_size, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scalers[target_name].fit_transform(X_train)
            X_test_scaled = self.scalers[target_name].transform(X_test)
            
            # Train model
            self.models[target_name].fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.models[target_name].predict(X_test_scaled)
            
            metrics[target_name] = {
                'r2': r2_score(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'mae': mean_absolute_error(y_test, y_pred)
            }
        
        return metrics
    
    def predict(self, chemical_data):
        """
        Predict sensory scores from chemical composition
        
        Args:
            chemical_data: Dictionary or DataFrame with chemical features
        
        Returns:
            Dictionary with predicted scores
        """
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
        """Save trained models and scalers to disk"""
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
        """Load trained models and scalers from disk"""
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
        
        self.models = data['models']
        self.scalers = data['scalers']
        self.model_type = data['model_type']
        self.feature_names = data['feature_names']
        self.target_names = data['target_names']


def generate_correlation_analysis(lot_data_list):
    """
    Generate correlation analysis between chemical features and sensory scores
    
    Args:
        lot_data_list: List of LOTData objects
    
    Returns:
        Pandas DataFrame with correlation matrix
    """
    predictor = SensoryPredictor()
    features, targets = predictor.prepare_data(lot_data_list)
    
    if targets is not None:
        combined = pd.concat([features, targets], axis=1)
        return combined.corr()
    else:
        return features.corr()


def get_feature_importance(predictor, target_name):
    """
    Get feature importance for tree-based models
    
    Args:
        predictor: Trained SensoryPredictor instance
        target_name: Target variable name
    
    Returns:
        Dictionary of feature importances
    """
    model = predictor.models[target_name]
    
    if hasattr(model, 'feature_importances_'):
        importance = dict(zip(predictor.feature_names, model.feature_importances_))
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    else:
        return None
