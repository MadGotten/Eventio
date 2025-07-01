import logging
import threading
from allauth.account.adapter import DefaultAccountAdapter

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        logger.info(f"Sending email to {email}")
        mailing_thread = threading.Thread(
            target=super().send_mail(template_prefix, email, context),
            args=(template_prefix, email, context),
        )
        mailing_thread.start()
