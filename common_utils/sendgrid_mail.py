import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import os
from common_utils.local_logger import logger

# Set your SendGrid API Key
SENDGRID_API_KEY = os.getenv('SENDGRID_MAIL_KEY')
if not SENDGRID_API_KEY:
    logger.error("SENDGRID_API_KEY Not found. Can't send email")
    sg = None
else:
    # Initialize SendGrid client
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)


def send_email(from_email, to_email, subject, content):
    if not sg:
        return
    # Create the email message
    mail = Mail(from_email, to_email, subject, content)

    # Send the email
    try:
        response = sg.send(mail)
        print(f"Email sent successfully. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    # Set up the email components
    from_email = Email("eyalsad70@gmail.com")  # Verified sender email
    to_email = To("eyals11@yahoo.com")  # The recipient's email address
    subject = "route test"
    content = Content("text/plain", "TESTING!!!")
    send_email(from_email, to_email, subject, content)
    


