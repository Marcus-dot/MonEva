import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import LabelEncoder
import datetime

class MLPredictor:
    """Helper for delay predictions and risk analysis"""
    
    @staticmethod
    def predict_delays(projects_data):
        """
        Predicts days of potential delay for active projects.
        projects_data: List of dicts with project features.
        """
        if not projects_data or len(projects_data) < 2:
            return {}

        df = pd.DataFrame(projects_data)
        
        # Simple feature engineering for demo
        le_type = LabelEncoder()
        df['type_encoded'] = le_type.fit_transform(df['type'])
        
        # Features: type, duration_days, budget (mocked for now), num_milestones
        # Target: past_delays (mocked from history for training)
        
        # Training (Mocked with small noise for dynamic feel)
        X = df[['type_encoded', 'duration_days', 'num_milestones']]
        y = np.array([5, 0, 15, 2])[:len(df)] # Mock historic targets
        
        if len(y) < len(df):
            y = np.pad(y, (0, len(df) - len(y)), 'edge')

        model = RandomForestRegressor(n_estimators=10)
        model.fit(X, y)
        
        predictions = model.predict(X)
        return {row['id']: round(pred, 1) for row, pred in zip(projects_data, predictions)}

class AnomalyDetector:
    """Detects suspicious financial claims"""
    
    @staticmethod
    def detect_claim_anomalies(claims_data):
        """
        Detects outliers in payment claims.
        claims_data: List of amounts and historical context.
        """
        if not claims_data or len(claims_data) < 3:
            return []

        df = pd.DataFrame(claims_data)
        X = df[['amount']].values
        
        # Isolation Forest for outlier detection
        iso = IsolationForest(contamination=0.1, random_state=42)
        preds = iso.fit_predict(X)
        
        # -1 indicates an anomaly
        anomalies = df[preds == -1]['id'].tolist()
        return anomalies

class ThemeExtractor:
    """NLP utility for extracting themes from inspection notes"""
    
    @staticmethod
    def extract_themes(notes_list):
        """
        Extracts key themes from inspection text notes.
        notes_list: List of strings.
        """
        # Dictionary of keyword mappings for simplified NLP
        THEME_KEYWORDS = {
            'Safety': ['safety', 'protective', 'ppe', 'hazard', 'risk', 'accident'],
            'Quality': ['crack', 'finish', 'standard', 'spec', 'quality', 'leak'],
            'Logistics': ['delay', 'material', 'supply', 'delivery', 'transport'],
            'Compliance': ['permit', 'regulation', 'audit', 'sign-off', 'license']
        }
        
        results = []
        for note in notes_list:
            found_themes = []
            note_lower = note.lower()
            for theme, keywords in THEME_KEYWORDS.items():
                if any(kw in note_lower for kw in keywords):
                    found_themes.append(theme)
            results.append(found_themes if found_themes else ['General'])
            
        return results
