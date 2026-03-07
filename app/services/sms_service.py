import vonage
import structlog
from app.core.config import settings

log = structlog.get_logger()

def send_sos_sms(lat: float, lng: float, people_count: int, message: str = "", has_injured: bool = False, has_children: bool = False):
    try:
        client = vonage.Client(key=settings.vonage_api_key, secret=settings.vonage_api_secret)
        sms = vonage.Sms(client)

        details = []
        if has_injured:
            details.append("INJURED")
        if has_children:
            details.append("CHILDREN")
        detail_str = " | ".join(details) if details else "No special conditions"

        text = (
            f"🆘 SAFEPASSAGE SOS ALERT\n"
            f"Location: {lat:.4f}, {lng:.4f}\n"
            f"People: {people_count}\n"
            f"Conditions: {detail_str}\n"
            f"Message: {message or 'None'}\n"
            f"Maps: https://maps.google.com/?q={lat},{lng}"
        )

        response = sms.send_message({
            "from": settings.vonage_from,
            "to": settings.alert_phone,
            "text": text,
        })

        if response["messages"][0]["status"] == "0":
            log.info("sos_sms_sent", to=settings.alert_phone)
        else:
            log.error("sos_sms_failed", error=response["messages"][0]["error-text"])

    except Exception as e:
        log.error("sos_sms_exception", error=str(e))
