"""
ML utilities for MonEva — all models train on real data from the database.

Minimum data thresholds are enforced: if there is not enough historical data,
functions return safe empty results rather than fabricated predictions.

Classes:
  MLPredictor   — project delay prediction (Random Forest on milestone overdue history)
  AnomalyDetector — financial claim anomaly detection (Isolation Forest)
  ThemeExtractor  — keyword-based inspection theme extraction (no ML required)
"""

import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

# Minimum rows needed before we trust a model
MIN_TRAINING_ROWS = 5
MIN_ANOMALY_ROWS = 10


class MLPredictor:
    """Predicts delay risk for active projects using completed milestone history."""

    @staticmethod
    def predict_delays(projects_data: list[dict]) -> dict:
        """
        Predict estimated delay (days) for each project in projects_data.

        projects_data: list of dicts, each must have keys:
            id, type, duration_days, num_milestones

        Returns: {project_id: predicted_delay_days}
        Returns {} if there is insufficient training data.
        """
        if not projects_data:
            return {}

        # ── Build training set from real milestone history ─────────────────────
        try:
            from projects.models import Milestone
            from django.utils import timezone

            today = timezone.now().date()

            # Completed milestones: due_date is our planned date.
            # We use days overdue (0 if on time or early) as the delay target.
            completed = (
                Milestone.objects
                .filter(status='COMPLETED')
                .select_related('contract__project')
            )

            rows = []
            for m in completed:
                project = m.contract.project
                planned_days = (project.end_date - project.start_date).days
                num_milestones = m.contract.milestones.count()
                # Proxy delay: if milestone due_date was overdue relative to project end
                delay = max(0, (m.due_date - project.end_date).days)
                rows.append({
                    'type': project.project_type or 'INFRASTRUCTURE',
                    'duration_days': max(planned_days, 1),
                    'num_milestones': num_milestones,
                    'delay': delay,
                })

            if len(rows) < MIN_TRAINING_ROWS:
                logger.info(
                    'MLPredictor: only %d training rows (need %d) — skipping predictions',
                    len(rows), MIN_TRAINING_ROWS
                )
                return {row['id']: None for row in projects_data}

            train_df = pd.DataFrame(rows)
            le = LabelEncoder()
            all_types = list(train_df['type'].unique()) + [r.get('type', 'INFRASTRUCTURE') for r in projects_data]
            le.fit(all_types)

            X_train = pd.DataFrame({
                'type_enc': le.transform(train_df['type']),
                'duration_days': train_df['duration_days'],
                'num_milestones': train_df['num_milestones'],
            })
            y_train = train_df['delay'].values

            model = RandomForestRegressor(n_estimators=50, random_state=42)
            model.fit(X_train, y_train)

        except Exception:
            logger.exception('MLPredictor: failed to build training set')
            return {}

        # ── Predict for active projects ────────────────────────────────────────
        results = {}
        for row in projects_data:
            try:
                X_pred = pd.DataFrame([{
                    'type_enc': le.transform([row.get('type', 'INFRASTRUCTURE')])[0],
                    'duration_days': max(row.get('duration_days', 1), 1),
                    'num_milestones': row.get('num_milestones', 0),
                }])
                pred = model.predict(X_pred)[0]
                results[row['id']] = round(float(pred), 1)
            except Exception:
                results[row['id']] = None

        return results


class AnomalyDetector:
    """Detects financially suspicious payment claims using Isolation Forest."""

    @staticmethod
    def detect_claim_anomalies(claims_data: list[dict] | None = None) -> list:
        """
        Detects outlier payment claims.

        claims_data: optional list of dicts with 'id' and 'amount'.
                     If None, queries the database directly.

        Returns: list of claim IDs flagged as anomalies.
        Returns [] if insufficient data.
        """
        try:
            if claims_data is None:
                from finance.models import PaymentClaim
                qs = PaymentClaim.objects.values('id', 'amount')
                claims_data = [{'id': str(c['id']), 'amount': float(c['amount'])} for c in qs]

            if len(claims_data) < MIN_ANOMALY_ROWS:
                logger.info(
                    'AnomalyDetector: only %d claims (need %d) — skipping',
                    len(claims_data), MIN_ANOMALY_ROWS
                )
                return []

            df = pd.DataFrame(claims_data)
            X = df[['amount']].values

            iso = IsolationForest(contamination=0.1, random_state=42)
            preds = iso.fit_predict(X)

            anomalies = df[preds == -1]['id'].tolist()
            return anomalies

        except Exception:
            logger.exception('AnomalyDetector: failed')
            return []


class ThemeExtractor:
    """Keyword-based inspection theme extraction — no ML model required."""

    THEME_KEYWORDS = {
        'Safety': ['safety', 'protective', 'ppe', 'hazard', 'risk', 'accident'],
        'Quality': ['crack', 'finish', 'standard', 'spec', 'quality', 'leak'],
        'Logistics': ['delay', 'material', 'supply', 'delivery', 'transport'],
        'Compliance': ['permit', 'regulation', 'audit', 'sign-off', 'license'],
    }

    @staticmethod
    def extract_themes(notes_list: list[str]) -> list[list[str]]:
        """
        Extract key themes from inspection text notes.

        Returns: list of theme lists, one per note.
        """
        results = []
        for note in notes_list:
            note_lower = (note or '').lower()
            found = [
                theme for theme, keywords in ThemeExtractor.THEME_KEYWORDS.items()
                if any(kw in note_lower for kw in keywords)
            ]
            results.append(found if found else ['General'])
        return results
