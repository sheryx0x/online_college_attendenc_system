from django.core.management.base import BaseCommand
from django.core.mail import send_mail

class Command(BaseCommand):
    help = 'Send a test email to verify email settings.'

    def handle(self, *args, **kwargs):
        subject = "Test Email"
        message = "This is a test email to verify that your email settings are working correctly."
        from_email = 'from@example.com'  # Replace with your sender email
        recipient_list = ['recipient@example.com']  # Replace with the recipient's email

        send_mail(subject, message, from_email, recipient_list)
        self.stdout.write(self.style.SUCCESS('Test email sent successfully!'))
