"""
Run this script to train the AI Detection engine using CIC-IDS-2017 Dataset.

Usage:
    python train_model.py
"""
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
import os
import glob
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MODEL_DIR = "data"
MODEL_PATH = os.path.join(MODEL_DIR, "model.joblib")
DATA_DIR = os.path.join(MODEL_DIR, "MachineLearningCVE")

# Top features identified for NIDS
FEATURES = [
    ' Destination Port',
    ' Flow Duration',
    ' Total Fwd Packets',
    ' Total Backward Packets',
    ' Fwd Packet Length Max',
    'Flow Bytes/s',
    ' Flow Packets/s',
    ' SYN Flag Count',
    ' RST Flag Count',
    ' PSH Flag Count',
    ' Average Packet Size'
]

def load_data():
    logging.info(f"Scanning for CSV datasets in {DATA_DIR}...")
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    
    if not csv_files:
        logging.warning("No CSV files found! Generating dummy dataset...")
        clean_features = [f.strip() for f in FEATURES]
        return pd.DataFrame(np.random.rand(1000, len(FEATURES)), columns=clean_features), pd.Series(['BENIGN'] * 500 + ['DDoS'] * 500)
        
    dfs = []
    for f in csv_files:
        logging.info(f"Sampling {os.path.basename(f)}...")
        try:
            # Load a sample to prevent out-of-memory errors on local dev
            df = pd.read_csv(f, usecols=FEATURES + [' Label'])
            
            # Sample up to 20k rows per file to keep training fast
            if len(df) > 20000:
                df = df.sample(n=20000, random_state=42)
                
            dfs.append(df)
        except Exception as e:
            logging.error(f"Error loading {f}: {e}")
            
    if not dfs:
        raise ValueError("Could not load any data from CSVs!")
        
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Clean column names
    combined_df.columns = combined_df.columns.str.strip()
    clean_features = [f.strip() for f in FEATURES]
    
    # Handle NaNs and Infinity
    combined_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    combined_df.fillna(0, inplace=True)
    
    X = combined_df[clean_features]
    y = combined_df['Label']
    return X, y

def train_and_save():
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    X, y = load_data()
    
    logging.info(f"Training XGBoost on {len(X)} samples.")
    logging.info(f"Class distribution: \n{y.value_counts()}")
    
    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
    
    # Initialize XGBoost
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        eval_metric='mlogloss',
        n_jobs=-1
    )
    
    logging.info("Fitting model...")
    model.fit(X_train, y_train)
    
    score = model.score(X_test, y_test)
    logging.info(f"Model Accuracy: {score * 100:.2f}%")
    
    # Save the model and label encoder together
    artifact = {
        "model": model,
        "encoder": le,
        "features": X.columns.tolist()
    }
    
    joblib.dump(artifact, MODEL_PATH)
    logging.info(f"Model artifact saved to {MODEL_PATH} ({os.path.getsize(MODEL_PATH)} bytes)")

if __name__ == "__main__":
    train_and_save()
