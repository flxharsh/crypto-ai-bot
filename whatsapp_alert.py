from twilio.rest import Client
import os

# Load credentials from Replit Secrets or environment variables
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH")
TWILIO_FROM = os.environ.get("TWILIO_FROM")  # e.g. 'whatsapp:+14155238886'
TWILIO_TO = os.environ.get("TWILIO_TO")      # e.g. 'whatsapp:+91xxxxxxxxxx'

client = Client(TWILIO_SID, TWILIO_AUTH)

def send_whatsapp_alert(message):
    try:
        message = client.messages.create(
            from_=TWILIO_FROM,
            to=TWILIO_TO,
            body=message
        )
        print(f"📲 WhatsApp alert sent: SID {message.sid}")
    except Exception as e:
        print(f"❌ WhatsApp alert failed: {e}")
# whatsapp_alert.py

def send_whatsapp_message(message):
    """
    Dummy function to simulate sending WhatsApp alerts.
    This is useful for testing without needing Twilio API.
    """
    print(f"📩 WhatsApp alert sent (dummy): {message}")
