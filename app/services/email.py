import logging
import requests

from config import DEFAULT_EMAIL_FROM_ADDRESS, MAILGUN_API_KEY, DEBUG


def send_email(to, subject, text):
    logging.warning("Sending email to %s: %s", to, text)
    if not DEBUG:
        resp = requests.post(
            'https://api.mailgun.net/v3/sandboxe0838290622c4d74910c2ed42364999c.mailgun.org/messages',
            auth=('api', MAILGUN_API_KEY),
            data={
                'from': DEFAULT_EMAIL_FROM_ADDRESS,
                'to': to,
                'subject': subject,
                'text': text
            }
        )
