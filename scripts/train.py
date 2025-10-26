#note; will make 3 artiiacts (below): 
'''
1. src/artifacts/model.pkl2
2. src/artifacts/threshold.json
3. reports/metrics.json
'''

import json, joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    average_precision_score, precision_recall_curve,
    classification_report, confusion_matrix
)
from sklearn.calibration import CalibratedClassifierCV
from xgboost import XGBClassifier #just throwing error becasue python interpeeter is diff 

#THIS IS THE BLOCK FOR PATHS 
DATA = "data/creditcard.csv"  #EDIT FOR DATASET 
ART = Path("src/artifacts"); ART.mkdir(parents=True, exist_ok=True)
RPT = Path("reports"); RPT.mkdir(exist_ok=True)

def choose_threshold(proba, y_true, min_precision=0.90):
    prec, rec, thr = precision_recall_curve(y_true, proba)
    best_rec, best_thr = -1, 0.5
    for p, r, t in zip(prec[:-1], rec[:-1], thr):
        if p >= min_precision and r > best_rec:
            best_rec, best_thr = r, t
    return float(best_thr), float(best_rec)

def train_model():
    ################# load data
    df = pd.read_csv(DATA)
    X = df.drop("Class", axis=1).values
    y = df["Class"].values
    ######################
    #SPLIT THE DATA Here
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.15, stratify=y, random_state=42
    )
    #######################

    
    # 3. Define model (XGBoost with imbalance handling)
    model = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=(len(y_tr) - y_tr.sum())/y_tr.sum(),
        eval_metric="logloss",
        use_label_encoder=False
    )

    # 4. Calibrate probabilities
    model.fit(X_tr, y_tr)
    calib = CalibratedClassifierCV(model, method="isotonic", cv=3)
    calib.fit(X_tr, y_tr)

    # 5. Evaluate
    proba = calib.predict_proba(X_te)[:,1]
    pr_auc = average_precision_score(y_te, proba)
    thr, best_rec = choose_threshold(proba, y_te, min_precision=0.90)
    pred = (proba >= thr).astype(int)

    cm = confusion_matrix(y_te, pred).tolist()
    report = classification_report(y_te, pred, digits=4, output_dict=True)

    # 6. Save outputs
    joblib.dump(calib, ART/"model.pkl")
    with open(ART/"threshold.json", "w") as f:
        json.dump({"t": thr}, f)

    metrics = {
        "pr_auc": pr_auc,
        "recall_at_p90": best_rec,
        "threshold": thr,
        "confusion_matrix": cm,
        "classification_report": report
    }
    with open(RPT/"metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    train_model()
