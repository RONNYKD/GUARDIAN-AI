"""
GuardianAI Telemetry Processor - Cloud Function Entry Point

Processes telemetry data from Pub/Sub, runs threat detection,
anomaly detection, and quality analysis pipeline.
"""

import os
import json
import logging
from typing import Dict, Any
from google.cloud import firestore
from datadog import api as dd_api, initialize as dd_initialize

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Datadog
dd_initialize(
    api_key=os.getenv('DD_API_KEY'),
    app_key=os.getenv('DD_APP_KEY'),
    host_name=os.getenv('DD_SITE', 'datadoghq.com')
)

# Initialize Firestore
db = firestore.Client()

# Import pipeline components
from threat_detector import ThreatDetector
from anomaly_detector import AnomalyDetector
from quality_analyzer import QualityAnalyzer
from alert_manager import AlertManager

# Initialize pipeline components
threat_detector = ThreatDetector()
anomaly_detector = AnomalyDetector()
quality_analyzer = QualityAnalyzer()
alert_manager = AlertManager()


def process_telemetry(event: Dict[str, Any], context: Any) -> None:
    """
    Cloud Function entry point for Pub/Sub trigger.
    
    Args:
        event: Pub/Sub message event
        context: Cloud Function context
    """
    try:
        # Decode Pub/Sub message
        import base64
        if 'data' in event:
            message_data = base64.b64decode(event['data']).decode('utf-8')
            telemetry = json.loads(message_data)
        else:
            logger.error("No data in event")
            return

        logger.info(f"Processing telemetry for trace_id: {telemetry.get('trace_id')}")

        # Step 1: Threat Detection
        threats = threat_detector.analyze(
            prompt=telemetry.get('prompt', ''),
            response=telemetry.get('response', ''),
            trace_id=telemetry.get('trace_id')
        )

        # Store threats in Firestore
        if threats:
            for threat in threats:
                db.collection('threats').add(threat)
                logger.info(f"Detected threat: {threat['type']} - {threat['severity']}")

        # Step 2: Anomaly Detection
        anomalies = []
        
        # Check cost anomaly
        if anomaly_detector.check_cost_anomaly(
            telemetry.get('input_tokens', 0) + telemetry.get('output_tokens', 0)
        ):
            anomalies.append({
                'type': 'cost_anomaly',
                'value': telemetry.get('cost_usd'),
                'threshold': 400000,
                'severity': 'high'
            })

        # Check latency anomaly
        if anomaly_detector.check_latency_anomaly(telemetry.get('latency_ms', 0)):
            anomalies.append({
                'type': 'latency_spike',
                'value': telemetry.get('latency_ms'),
                'threshold': 5000,
                'severity': 'medium'
            })

        # Check quality anomaly
        if anomaly_detector.check_quality_anomaly(telemetry.get('quality_score', 1.0)):
            anomalies.append({
                'type': 'quality_degradation',
                'value': telemetry.get('quality_score'),
                'threshold': 0.7,
                'severity': 'medium'
            })

        if anomalies:
            logger.info(f"Detected {len(anomalies)} anomalies")

        # Step 3: Quality Analysis
        quality_result = quality_analyzer.analyze(
            prompt=telemetry.get('prompt', ''),
            response=telemetry.get('response', '')
        )
        
        # Update telemetry with quality score
        db.collection('telemetry').document(telemetry['trace_id']).update({
            'quality_score': quality_result['overall_score'],
            'quality_details': quality_result
        })

        # Step 4: Create Incidents and Alerts
        if threats or anomalies:
            # Create incident
            incident = {
                'title': f"Security/Performance Issue - {telemetry.get('trace_id', '')[:8]}",
                'description': f"Detected {len(threats)} threats and {len(anomalies)} anomalies",
                'severity': 'critical' if any(t.get('severity') == 'critical' for t in threats) else 'high',
                'status': 'open',
                'threat_ids': [t.get('id') for t in threats if t.get('id')],
                'anomalies': anomalies,
                'trace_id': telemetry.get('trace_id'),
                'created_at': firestore.SERVER_TIMESTAMP,
                'auto_remediated': False
            }
            
            incident_ref = db.collection('incidents').add(incident)
            logger.info(f"Created incident: {incident_ref[1].id}")

            # Send alerts to Datadog
            for threat in threats:
                alert_manager.create_threat_alert(threat, telemetry)
            
            for anomaly in anomalies:
                alert_manager.create_anomaly_alert(anomaly, telemetry)

        logger.info(f"Successfully processed telemetry for trace_id: {telemetry.get('trace_id')}")

    except Exception as e:
        logger.error(f"Error processing telemetry: {str(e)}", exc_info=True)
        raise


def process_http(request) -> tuple:
    """
    HTTP Cloud Function entry point for testing.
    
    Args:
        request: Flask request object
        
    Returns:
        Tuple of (response, status_code)
    """
    try:
        telemetry = request.get_json()
        
        # Create mock Pub/Sub event
        import base64
        event = {
            'data': base64.b64encode(json.dumps(telemetry).encode('utf-8'))
        }
        
        # Process
        process_telemetry(event, None)
        
        return {'status': 'success', 'message': 'Telemetry processed'}, 200
        
    except Exception as e:
        logger.error(f"Error in HTTP handler: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 500
