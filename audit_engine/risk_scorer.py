def calculate_explainable_risk_score(rule_severity, amount, ml_anomaly_score=0.0, is_conflict_of_interest=False):
    """
    Computes an explainable 0-100 Risk Score combining:
    1. Base Rule Severity Weight (Low: 25, Medium: 50, High: 75, Critical: 90)
    2. Financial Value Magnitude Scaling — INR scale (+0 to +20)
       >₹1 Crore → +20, >₹50 Lakhs → +15, >₹10 Lakhs → +10, else → +5
    3. ML Anomaly Score Contribution (+0 to +15)
    4. Conflict of Interest Multiplier (+20)
    Normalised to 0-100 range.
    """
    severity_base = {
        'LOW': 25,
        'MEDIUM': 50,
        'HIGH': 75,
        'CRITICAL': 90
    }.get(rule_severity.upper(), 40)

    # Value magnitude component — INR scale
    amount_float = float(amount or 0.0)
    if amount_float > 10000000:      # ₹1 Crore+
        val_weight = 20
    elif amount_float > 5000000:     # ₹50 Lakhs+
        val_weight = 15
    elif amount_float > 1000000:     # ₹10 Lakhs+
        val_weight = 10
    else:
        val_weight = 5

    # ML component
    ml_weight = int(ml_anomaly_score * 15)

    # Conflict of Interest penalty
    coi_penalty = 20 if is_conflict_of_interest else 0

    total_score = severity_base + val_weight + ml_weight + coi_penalty
    total_score = min(100, max(0, total_score))

    if total_score <= 30:
        category = 'LOW'
    elif total_score <= 60:
        category = 'MEDIUM'
    elif total_score <= 80:
        category = 'HIGH'
    else:
        category = 'CRITICAL'

    return total_score, category
