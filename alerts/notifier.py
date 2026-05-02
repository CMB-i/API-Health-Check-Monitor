import os
import platform
import logging

# Configure logging to write to alerts/failures.log
log_file_path = os.path.join(os.path.dirname(__file__), 'failures.log')

logging.basicConfig(
    filename=log_file_path,
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def send_desktop_notification(title, message):
    """
    Placeholder function for sending a Desktop Notification.
    Uses osascript for macOS and notify-send for Linux.
    """
    system = platform.system()
    if system == "Darwin":
        # macOS
        safe_title = title.replace('"', '\\"')
        safe_message = message.replace('"', '\\"')
        os.system(f'osascript -e \'display notification "{safe_message}" with title "{safe_title}"\'')
    elif system == "Linux":
        # Linux
        safe_title = title.replace('"', '\\"')
        safe_message = message.replace('"', '\\"')
        os.system(f'notify-send "{safe_title}" "{safe_message}"')
    else:
        # Windows or other systems
        logger.info(f"Desktop notifications not implemented for OS: {system}")

def process_alerts(results, latency_threshold_ms=500):
    """
    Processes a list of API health check results.
    Results are expected to be a list of dicts: [{'name': '...', 'status': ..., 'latency': ...}, ...]
    Logs an incident and sends a desktop notification if status != 200 or latency > latency_threshold_ms.
    """
    if not results:
        return

    for result in results:
        name = result.get('name', 'Unknown API')
        status = result.get('status')
        latency = result.get('latency')

        is_failure = False
        incident_reasons = []

        if status != 200:
            is_failure = True
            incident_reasons.append(f"HTTP Status {status}")
        
        if latency is not None and latency > latency_threshold_ms:
            is_failure = True
            incident_reasons.append(f"High Latency ({latency}ms > {latency_threshold_ms}ms)")

        if is_failure:
            reason_str = ", ".join(incident_reasons)
            log_message = f"Incident detected for {name}: {reason_str}"
            
            # Log the incident to failures.log using the logging library
            logger.warning(log_message)
            
            # Trigger scalable desktop notification
            send_desktop_notification("API Health Monitor Alert", log_message)
