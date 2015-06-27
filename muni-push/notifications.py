"""
Contains various notification strategies.
"""
from twilio.rest import TwilioRestClient


twilio_account_sid = "AC302262767f8c31ae58f6ad3654bb3bdf"
twilio_auth_token = "ed1bc9400ba310b78713b37b80adc8d0"


def notify(notification_settings, departures):
    for notification_type, settings in notification_settings.iteritems():
        if notification_type == "sms":
            print settings
            sms(settings['number'], departures)


def sms(number, departures):
    client = TwilioRestClient(twilio_account_sid, twilio_auth_token)
    message_text = ""
    message = client.messages.create(body=message_text, to=number, from_="+16787716864")
