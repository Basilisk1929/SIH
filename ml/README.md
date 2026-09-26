# Financial Transaction Risk Engine

## Overview
The Financial Transaction Risk Engine is a production-grade machine learning subsystem designed to detect high-risk and mule-pattern transactions in real-time. It uses an **XGBoost** gradient-boosted decision tree model trained on synthetic financial data, computing 12 temporal, behavioral, network graph, and geographic features with zero lookahead bias.

```
Raw Transaction Stream / CSV
             │
             ▼
[Transaction Preprocessor] ──> Validation, chronological ordering, timestamp parsing
             │
             ▼
[Feature Engineering]      ──> 12 behavioral, temporal, graph & spatial features
             │
             ▼
[Time-Aware Splitter]     ──> 70% Train / 15% Val / 15% Test (Strict chronological boundary)
             │
             ▼
[Model Trainer]           ──> XGBoost (scale_pos_weight, early stopping on validation PR-AUC)
             │
             ▼
[Model Evaluator]         ──> ROC-AUC (0.967), PR-AUC (0.827), F1 (0.794), Precision, Recall
             │
             ▼
[Model Serialization]     ──> risk_model_xgb.json & feature_config.json
             │
             ▼
[Inference Service]       ──> POST /risk/predict (0-100 score, risk band, feature explanations)
```

---

## 1. Feature Specifications (12 Features)

All 12 features are computed dynamically with **strict time-awareness** (evaluating only events strictly prior to `event_timestamp` to prevent lookahead data leakage):

| # | Feature Name | Type | Description | Leakage Prevention Strategy |
|---|---|---|---|---|
| 1 | `transaction_amount` | Float | Transaction amount in INR | Current event payload |
| 2 | `transaction_frequency` | Float | Lifetime transaction count of the originating account up to this moment | Point-in-time account state accumulator |
| 3 | `transactions_last_1h` | Integer | Count of transactions from this account in the rolling 60-minute window | Windowed timestamp filter (`t - 1h <= t_prev < t`) |
| 4 | `transactions_last_24h` | Integer | Count of transactions from this account in the rolling 24-hour window | Windowed timestamp filter (`t - 24h <= t_prev < t`) |
| 5 | `unique_receivers` | Integer | Number of distinct beneficiary accounts transacted with in the last 24h | Point-in-time sliding window distinct set |
| 6 | `unique_senders` | Integer | Number of distinct sending accounts transferring to this account in the last 24h | Point-in-time sliding window distinct set |
| 7 | `cashout_ratio` | Float | Cumulative `CASH_OUT` amount divided by cumulative total volume (`[0.0, 1.0]`) | Historical ratio strictly before current transaction |
| 8 | `account_age` | Float | Account age in days from creation date to current transaction | Fixed immutable reference point (`t_tx - t_created`) |
| 9 | `graph_degree` | Integer | Total in-degree + out-degree in the point-in-time transaction graph | Dynamic multigraph degree excluding future transactions |
| 10 | `graph_centrality` | Float | Normalized point-in-time degree centrality in the active account graph | Degree centrality recomputed dynamically |
| 11 | `complaint_link_count` | Integer | Number of prior cybercrime complaints filed naming this account as suspect | Citizen reports strictly before `event_timestamp` |
| 12 | `geographic_distance` | Float | Great-circle Haversine distance (km) between origin account and counterparty/ATM | Physical location coordinate computation |

---

## 2. Model Architecture & Training

- **Algorithm**: `XGBoostClassifier` (native C++ tree ensemble with Python API).
- **Alternative Algorithm Supported**: `LGBMClassifier` (LightGBM).
- **Objective**: `binary:logistic`.
- **Class Imbalance Strategy**: `scale_pos_weight = N_neg / N_pos` (~18.0) calculated strictly on the training partition.
- **Hyperparameters**:
  - `max_depth`: 6
  - `learning_rate`: 0.05
  - `n_estimators`: 300
  - `subsample`: 0.8
  - `colsample_bytree`: 0.8
  - `eval_metric`: `["logloss", "aucpr"]`
  - `early_stopping_rounds`: 25 on the validation split.

---

## 3. Data Leakage Prevention & Time-Aware Splitting

### Why Standard Random K-Fold Split Fails
In financial fraud and cybercrime investigation, random cross-validation leaks future patterns into the past. An account's future mule burst would leak into earlier transactions of the same cluster, artificially inflating model metrics to 0.999 while failing in production.

### Time-Aware Splitting Implementation (`TimeAwareSplitter`)
1. Data is sorted strictly chronologically by `timestamp`.
2. The partition boundaries are timestamp-indexed:
   - **Train Set (70%)**: $T_0 \le t < T_{\text{val}}$ (23,165 transactions)
   - **Validation Set (15%)**: $T_{\text{val}} \le t < T_{\text{test}}$ (4,964 transactions)
   - **Test Set (15%)**: $T_{\text{test}} \le t \le T_{\text{max}}$ (4,965 transactions)
3. Evaluated on genuine unseen future transactions.

---

## 4. Evaluation Results on Unseen Holdout Test Split

The model was evaluated on the unseen 15% future holdout set (4,965 transactions, 176 fraud cases):

| Metric | Score | Evaluation Context |
|---|---|---|
| **ROC-AUC** | **96.74%** (`0.9674`) | Outstanding class separation across discrimination thresholds |
| **PR-AUC (Average Precision)** | **82.68%** (`0.8268`) | Strong precision retention across recall curve on imbalanced data |
| **Precision** | **86.58%** (`0.8658`) | Very low false-positive investigation load (only 20 false alarms) |
| **Recall** | **73.30%** (`0.7330`) | Catches 129 out of 176 unseen future fraud transactions |
| **F1 Score** | **79.38%** (`0.7938`) | Balanced harmonic mean |

### Confusion Matrix
```
                    Predicted Normal    Predicted Suspicious
Actual Normal            4,769                    20
Actual Suspicious           47                   129
```

---

## 5. Risk Scoring, Bands & Explainability

### Calibration to Risk Score (0–100)
The raw sigmoid posterior probability $P(Y=1 \mid X)$ is mapped to an integer risk score:
$$\text{risk\_score} = \text{round}(P \times 100)$$

### Risk Bands
- **`LOW`** (0 – 29.99): Normal routine transacting behavior.
- **`MEDIUM`** (30 – 59.99): Mild deviations (e.g. slight velocity increase).
- **`HIGH`** (60 – 84.99): Significant anomalies (e.g. rapid fan-in/fan-out, high cashout ratio).
- **`CRITICAL`** (85 – 100): Extreme risk markers (e.g. named in prior NCRP complaints, massive burst velocity, high graph centrality).

### Forensic Feature Explanations (`RiskFeatureExplainer`)
Every prediction generates human-readable forensic drivers explaining why the score was assigned, comparing feature values against baseline distributions:
- `Rapid transaction burst in last 1 hour (N transactions)`
- `Rapid transaction burst in last 24 hours (N transactions)`
- `Account named in N prior cybercrime complaints`
- `High cashout ratio (X% of cumulative funds withdrawn via ATM/cash)`
- `High transaction amount (₹X vs median ₹Y)`
- `Elevated connectivity in transaction network (degree: N)`
- `High geographic distance (X km between transacting parties)`

---

## 6. REST API Inference Service

Start the risk inference microservice:
```bash
uvicorn ml.api.service:app --host 127.0.0.1 --port 8004
```

### Endpoints

#### 1. `POST /risk/predict`
Calculates real-time risk score, risk band, and feature explanations.

**Request:**
```bash
curl -X POST "http://127.0.0.1:8004/risk/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_amount": 185000.0,
    "transaction_frequency": 42.0,
    "transactions_last_1h": 8,
    "transactions_last_24h": 26,
    "unique_receivers": 12,
    "unique_senders": 1,
    "cashout_ratio": 0.88,
    "account_age": 14.5,
    "graph_degree": 28,
    "graph_centrality": 0.045,
    "complaint_link_count": 2,
    "geographic_distance": 1420.5
  }'
```

**Response:**
```json
{
  "risk_score": 92.4,
  "risk_band": "CRITICAL",
  "feature_explanations": [
    "Account named in 2 prior cybercrime complaints",
    "Rapid transaction burst in last 1 hour (8 transactions)",
    "Rapid transaction burst in last 24 hours (26 transactions)",
    "High cashout ratio (88.0% of cumulative funds withdrawn)",
    "Elevated connectivity in transaction network (degree: 28)",
    "High transaction amount (₹185,000.00 vs baseline median ₹5,528.00)"
  ],
  "feature_importance_contributions": {
    "complaint_link_count": 0.428,
    "cashout_ratio": 0.215,
    "transactions_last_1h": 0.162,
    "graph_degree": 0.094,
    "transaction_amount": 0.058,
    "geographic_distance": 0.043
  },
  "model_version": "1.0.0",
  "disclaimer": "Do not claim that a risk score proves criminal activity. It represents a model-generated risk signal for investigation."
}
```

#### 2. `GET /risk/model-info`
Returns loaded model architecture, training metrics, and feature list.

#### 3. `GET /risk/health`
Health check verifying model artifact availability.

---

## 7. Mandatory Legal & Investigative Disclaimer

> [!IMPORTANT]
> **Regulatory and Evidentiary Notice**:
> *"Do not claim that a risk score proves criminal activity. It represents a model-generated risk signal for investigation."*
> 
> Risk scores emitted by this engine provide automated prioritization for cybercrime analysts, Law Enforcement Officers (LEOs), and fraud monitoring cells. They do not constitute prima facie proof of guilt, statutory crime, or penal liability without independent judicial evidence, KYC corroboration, and Section 91 CrPC bank records.

---

## 8. Running the Pipeline & Tests

### Retrain the Model
```bash
python -m ml.pipeline.trainer
```

### Run Tests
```bash
pytest tests/ml/ -v
```
