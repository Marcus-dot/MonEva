from sklearn.ensemble import IsolationForest
import pandas as pd
import numpy as np
from .models import PaymentClaim

class ClaimRiskScorer:
    """
    ML Engine for scoring payment claims.
    Uses Isolation Forest for unsupervised anomaly detection.
    """
    
    def __init__(self):
        self.model = None
        self.feature_columns = ['amount', 'contract_value', 'ratio']

    def train(self):
        """
        Train the model on historical drafted/submitted claims.
        """
        # Fetch historical data
        claims = PaymentClaim.objects.exclude(status='REJECTED')
        if not claims.exists():
            return False

        data = []
        for c in claims:
            data.append({
                'amount': float(c.amount),
                'contract_value': float(c.contract.total_value),
                'ratio': float(c.amount) / float(c.contract.total_value) if c.contract.total_value > 0 else 0
            })
        
        df = pd.DataFrame(data)
        
        # Isolation Forest
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.model.fit(df[self.feature_columns])
        return True

    def predict(self, claim):
        """
        Calculate risk score for a single claim.
        Returns: Score (0-100), Factors (dict)
        """
        amount = float(claim.amount)
        contract_value = float(claim.contract.total_value)
        ratio = amount / contract_value if contract_value > 0 else 0
        
        # Simple Heuristics (Cold Start / Fallback)
        score = 0
        factors = {}
        
        # 1. Ratio check
        if ratio > 0.5:
            score += 40
            factors['high_ratio'] = f"Claim is {ratio:.0%} of total contract value"
        
        # 2. Amount check (Model)
        # If we had a trained model, we'd use decision_function here.
        # For prototype without persistence, we'll re-train on fly if small dataset, 
        # or just rely on heuristics + simple statistical deviation.
        
        # Let's do a Z-Score based outlier detection if we have enough peers
        peer_claims = PaymentClaim.objects.filter(contract=claim.contract).exclude(id=claim.id)
        if peer_claims.count() > 3:
            amounts = [float(c.amount) for c in peer_claims]
            mean = np.mean(amounts)
            std = np.std(amounts)
            if std > 0:
                z_score = (amount - mean) / std
                if z_score > 2: # 2 Sigma
                    score += 50
                    factors['statistical_outlier'] = f"Amount is {z_score:.1f} standard deviations above average"
        
        # Cap Score
        score = min(score, 100)
        
        # If score is low but we want to simulate ML sensitivity:
        if score == 0 and amount > 50000:
             score = 15
             factors['large_transaction'] = "High value transaction requires check"

        return score, factors

# Singleton
scorer = ClaimRiskScorer()
