import asyncio
import logging
from app.db.session import AsyncSessionLocal
from app.services.streaming import redis_client, StreamingService
from app.services.threat_detection import ThreatDetectionService
from app.services.anomaly_detection import AnomalyDetectionService
from app.services.correlation_engine import CorrelationEngine
from app.services.risk_scoring import RiskScoringEngine
from app.services.response_engine import ResponseEngine
from app.models.log import LogEvent
from app.models.alert import Alert
from app.models.incident import Incident
from app.schemas.alert import AlertCreate
from sqlalchemy.future import select

logger = logging.getLogger(__name__)

async def process_logs_raw_stream():
    """Consume from logs_raw and run Threat Detection & Anomaly Detection."""
    last_id = "$"
    anomaly_svc = AnomalyDetectionService()
    
    while True:
        try:
            # Read from stream
            messages = await redis_client.xread({"logs_raw": last_id}, count=10, block=5000)
            if not messages:
                continue
                
            async with AsyncSessionLocal() as db:
                detector = ThreatDetectionService(db)
                
                for stream_name, events in messages:
                    for event_id, payload in events:
                        last_id = event_id
                        
                        log_id = payload.get("id")
                        if not log_id:
                            continue
                            
                        # Fetch log from DB
                        result = await db.execute(select(LogEvent).where(LogEvent.id == int(log_id)))
                        db_log = result.scalar_one_or_none()
                        
                        if not db_log:
                            continue
                            
                        # Rule-based detection
                        alert = await detector.detect_threats(db_log)
                        
                        # AI Anomaly detection
                        if not alert:
                            anomaly_alert = anomaly_svc.predict_anomaly({
                                "path": payload.get("path"),
                                "payload": payload.get("payload"),
                                "status_code": payload.get("status_code", 200)
                            })
                            
                            if anomaly_alert and anomaly_alert.get("is_anomaly"):
                                alert_create = AlertCreate(
                                    threat_type=anomaly_alert["threat"],
                                    severity="Medium",
                                    source_ip=payload.get("source_ip", "Unknown"),
                                    tenant_id=payload.get("tenant_id", "default"),
                                    confidence=0.85,
                                    description=f"AI Detection Confidence: {anomaly_alert['confidence']}",
                                    log_id=db_log.id
                                )
                                alert = Alert(**alert_create.model_dump())
                                db.add(alert)
                                await db.commit()
                                await db.refresh(alert)
                                
                        if alert:
                            # Publish to alerts stream
                            alert_dict = {
                                "id": alert.id,
                                "threat_type": alert.threat_type,
                                "source_ip": alert.source_ip
                            }
                            await StreamingService.publish_alert(alert_dict)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error processing logs_raw stream: {e}")
            await asyncio.sleep(1)

async def process_alerts_stream():
    """Consume from alerts and run Correlation Engine."""
    last_id = "$"
    
    while True:
        try:
            messages = await redis_client.xread({"alerts": last_id}, count=10, block=5000)
            if not messages:
                continue
                
            async with AsyncSessionLocal() as db:
                correlator = CorrelationEngine(db)
                
                for stream_name, events in messages:
                    for event_id, payload in events:
                        last_id = event_id
                        
                        alert_id = payload.get("id")
                        if not alert_id:
                            continue
                            
                        result = await db.execute(select(Alert).where(Alert.id == int(alert_id)))
                        db_alert = result.scalar_one_or_none()
                        
                        if db_alert:
                            incident = await correlator.correlate_alerts(db_alert)
                            if incident:
                                incident_dict = {"id": incident.id}
                                await StreamingService.publish_incident(incident_dict)
                                
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error processing alerts stream: {e}")
            await asyncio.sleep(1)

async def process_incidents_stream():
    """Consume from incidents and run Risk Scoring and Response Engine."""
    last_id = "$"
    
    while True:
        try:
            messages = await redis_client.xread({"incidents": last_id}, count=10, block=5000)
            if not messages:
                continue
                
            async with AsyncSessionLocal() as db:
                risk_engine = RiskScoringEngine()
                response_engine = ResponseEngine(db)
                
                for stream_name, events in messages:
                    for event_id, payload in events:
                        last_id = event_id
                        
                        incident_id = payload.get("id")
                        if not incident_id:
                            continue
                            
                        # Fetch incident from DB
                        result = await db.execute(select(Incident).where(Incident.id == int(incident_id)))
                        db_incident = result.scalar_one_or_none()
                        
                        if db_incident:
                            # Calculate risk
                            incident_dict = {
                                "incident_type": db_incident.incident_type,
                                "severity": db_incident.severity,
                                "alert_ids": [1], # dummy for count
                                "source_ips": db_incident.source_ips
                            }
                            enriched = risk_engine.enrich_incident(incident_dict)
                            
                            db_incident.risk_score = enriched["risk_score"]
                            db_incident.risk_level = enriched["risk_level"]
                            db_incident.requires_immediate_action = enriched["requires_immediate_action"]
                            await db.commit()
                            
                            # Run automated response
                            if db_incident.requires_immediate_action and db_incident.source_ips:
                                await response_engine.execute_action(
                                    incident_id=db_incident.id,
                                    action_type="Block IP",
                                    target=db_incident.source_ips[0]
                                )
                            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error processing incidents stream: {e}")
            await asyncio.sleep(1)
