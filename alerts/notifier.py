import os
import platform
import logging
import shlex
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging to write to alerts/failures.log without hijacking root logger
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "failures.log")

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

if not logger.handlers:
    file_handler = logging.FileHandler(log_file_path)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.propagate = False


def send_desktop_notification(title, message):
    """
    Desktop notification:
    - macOS: osascript
    - Linux: notify-send
    """
    system = platform.system()
    if system == "Darwin":
        safe_msg = message.replace('"', '\\"')
        safe_title = title.replace('"', '\\"')
        applescript = f'display notification "{safe_msg}" with title "{safe_title}"'
        os.system(f"osascript -e {shlex.quote(applescript)}")
    elif system == "Linux":
        os.system(f"notify-send {shlex.quote(title)} {shlex.quote(message)}")
    else:
        logger.info(f"Desktop notifications not implemented for OS: {system}")


def send_email_notification(subject, message, email_config):
    """
    Send email alert using SMTP configuration from config.yaml.
    """
    if not email_config or not email_config.get("enabled", False):
        return

    smtp_host = email_config.get("smtp_host")
    smtp_port = email_config.get("smtp_port", 587)
    username = email_config.get("username")
    password = email_config.get("password")
    from_email = email_config.get("from_email")
    to_emails = email_config.get("to_emails", [])

    if not all([smtp_host, smtp_port, username, password, from_email]) or not to_emails:
        logger.warning("Email alert skipped: incomplete email configuration.")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(from_email, to_emails, msg.as_string())

    except Exception as exc:
        logger.warning(f"Email alert failed: {exc}")


def process_alerts(results, latency_threshold_ms=500, email_config=None):
    """
    Process API check results and trigger alerts for:
    - status != 200
    - latency > threshold
    - invalid response content
    """
    if not results:
        return

    for result in results:
        name = result.get("name", "Unknown API")
        status = result.get("status", result.get("status_code"))
        latency = result.get("latency", result.get("latency_ms"))
        content_valid = result.get("content_valid", True)
        validation_error = result.get("validation_error")
        error = result.get("error")

        is_failure = False
        incident_reasons = []

        if status != 200:
            is_failure = True
            incident_reasons.append(f"HTTP Status {status}")

        if latency is not None and latency > latency_threshold_ms:
            is_failure = True
            incident_reasons.append(f"High Latency ({latency}ms > {latency_threshold_ms}ms)")

        if content_valid is False:
            is_failure = True
            reason = validation_error or "validation failed"
            incident_reasons.append(f"Invalid Response Content ({reason})")

        if error:
            is_failure = True
            incident_reasons.append(f"Error ({error})")

        if is_failure:
            reason_str = ", ".join(incident_reasons)
            log_message = f"Incident detected for {name}: {reason_str}"

            logger.warning(log_message)
            send_desktop_notification("API Health Monitor Alert", log_message)
            send_email_notification(
                subject=f"[API Alert] {name}",
                message=log_message,
                email_config=email_config,
            )