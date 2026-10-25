import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from transactions.models import Invoice, Payment, EmployeeExpense

def train_and_predict_isolation_forest():
    """
    Fits Isolation Forest anomaly detection model on financial transactions dataset.
    Returns dictionary mapping transaction IDs to ML anomaly scores (0.0 to 1.0).
    """
    invoices = list(Invoice.objects.all().values('invoice_id', 'amount', 'vendor_id'))
    if not invoices:
        return {}

    df = pd.DataFrame(invoices)
    df['amount'] = df['amount'].astype(float)
    
    # Feature Engineering
    vendor_counts = df['vendor_id'].value_counts().to_dict()
    vendor_means = df.groupby('vendor_id')['amount'].mean().to_dict()
    vendor_stds = df.groupby('vendor_id')['amount'].std().fillna(1.0).to_dict()

    df['vendor_tx_count'] = df['vendor_id'].map(vendor_counts)
    df['vendor_mean'] = df['vendor_id'].map(vendor_means)
    df['vendor_std'] = df['vendor_id'].map(vendor_stds)
    df['z_score'] = (df['amount'] - df['vendor_mean']) / (df['vendor_std'] + 1e-5)
    
    features = ['amount', 'vendor_tx_count', 'z_score']
    X = df[features].fillna(0.0)

    # Scikit-learn Isolation Forest
    clf = IsolationForest(contamination=0.08, random_state=42)
    clf.fit(X)

    # Decision function returns anomaly raw score (lower = more abnormal)
    raw_scores = clf.decision_function(X)
    
    # Normalize score between 0.0 (normal) and 1.0 (extreme anomaly)
    min_score, max_score = raw_scores.min(), raw_scores.max()
    if max_score > min_score:
        norm_scores = 1.0 - ((raw_scores - min_score) / (max_score - min_score))
    else:
        norm_scores = np.zeros_like(raw_scores)

    results = {}
    for idx, row in df.iterrows():
        results[row['invoice_id']] = round(float(norm_scores[idx]), 3)

    return results
