import numpy as np
import pandas as pd
import joblib
import os
import logging
from app.core.config import settings


class AnomalyDetectionService:
    """
    AI Threat Detection module using XGBoost.
    Detects specific network attacks based on the CIC-IDS-2017 dataset features.
    """

    def __init__(self):
        model_path = settings.model_path
        self.model = None
        self.encoder = None
        self.features = [
            'Destination Port',
            'Flow Duration',
            'Total Fwd Packets',
            'Total Backward Packets',
            'Fwd Packet Length Max',
            'Flow Bytes/s',
            'Flow Packets/s',
            'SYN Flag Count',
            'RST Flag Count',
            'PSH Flag Count',
            'Average Packet Size'
        ]
        
        if os.path.exists(model_path):
            try:
                artifact = joblib.load(model_path)
                
                # Check if it's the old IsolationForest or new XGBoost artifact
                if isinstance(artifact, dict) and "model" in artifact:
                    self.model = artifact["model"]
                    self.encoder = artifact["encoder"]
                    self.features = artifact.get("features", self.features)
                    logging.info(f"[AnomalyDetection] Loaded XGBoost model from '{model_path}'")
                else:
                    logging.warning(f"[AnomalyDetection] Expected dict artifact, found {type(artifact)}. Retrain model.")
            except Exception as e:
                logging.error(f"[AnomalyDetection] Failed to load model: {e}")
        else:
            logging.warning("[AnomalyDetection] model file not found.")

    def _extract_features(self, log: dict) -> list[float]:
        """
        Maps the incoming log dict to the 11 CICIDS features.
        If standard web log fields are sent instead of NetFlow, 
        defaults to benign network statistics to prevent false positives.
        """
        # Try to pull exact features (e.g. from Vector) or fallback to mapping web logs
        return [
            float(log.get("Destination Port", log.get("destination_port", 80))),
            float(log.get("Flow Duration", log.get("flow_duration", 1000.0))),
            float(log.get("Total Fwd Packets", log.get("total_fwd_packets", 5))),
            float(log.get("Total Backward Packets", log.get("total_bwd_packets", 5))),
            
            # Map payload length to packet length if available
            float(log.get("Fwd Packet Length Max", len(log.get("payload", "")) if log.get("payload") else 100)),
            
            float(log.get("Flow Bytes/s", 500.0)),
            float(log.get("Flow Packets/s", 10.0)),
            float(log.get("SYN Flag Count", log.get("syn_flag_count", 0))),
            float(log.get("RST Flag Count", log.get("rst_flag_count", 0))),
            float(log.get("PSH Flag Count", log.get("psh_flag_count", 1))),
            float(log.get("Average Packet Size", 100.0))
        ]

    def predict_anomaly(self, log: dict) -> dict:
        """
        Returns:
          {
            "is_anomaly": bool,
            "threat": str,
            "confidence": float
          }
        """
        if not self.model or not self.encoder:
            return {"is_anomaly": False, "threat": None, "confidence": 0.0}

        features = self._extract_features(log)
        
        try:
            # XGBoost requires column names to match exactly if trained with them
            df = pd.DataFrame([features], columns=self.features)
            
            probs = self.model.predict_proba(df)[0]
            pred_idx = np.argmax(probs)
            confidence = float(probs[pred_idx])
            
            predicted_class = self.encoder.inverse_transform([pred_idx])[0]
            
            # If the model predicts an attack with high confidence
            if predicted_class != "BENIGN" and confidence > 0.60:
                logging.warning(f"AI Detection flagged '{predicted_class}' with {confidence*100:.1f}% confidence.")
                return {
                    "is_anomaly": True,
                    "threat": str(predicted_class),
                    "confidence": round(confidence, 4),
                }
        except Exception as e:
            logging.error(f"Prediction error: {e}")

        return {"is_anomaly": False, "threat": None, "confidence": 0.0}
