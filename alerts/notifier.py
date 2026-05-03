import os
import platform
import logging
import shlex

# Configure logging to write to alerts/failures.log without hijacking the root logger
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'failures.log')

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

if not logger.handlers:
    file_handler = logging.FileHandler(log_file_path)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.propagate = False

def send_desktop_notification(title, message):
    """
    Placeholder function for sending a Desktop Notification.
    Uses osascript for macOS and notify-send for Linux.
    """
    system = platform.system()
    if system == "Darwin":
        # macOS
        # Safely escape double quotes for AppleScript, then use shlex.quote for Bash
        safe_msg = message.replace('"', '\\"')
        safe_title = title.replace('"', '\\"')
        applescript = f'display notification "{safe_msg}" with title "{safe_title}"'
        os.system(f"osascript -e {shlex.quote(applescript)}")
    elif system == "Linux":
        # Linux
        os.system(f"notify-send {shlex.quote(title)} {shlex.quote(message)}")
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
        # Support both 'status' and 'status_code' to prevent mismatch with engine.py
        status = result.get('status', result.get('status_code'))
        latency = result.get('latency', result.get('latency_ms'))

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
