import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, From, Content
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

from_email_str = os.getenv('SENDER_EMAIL')
if not from_email_str:
    logger.error("email sender not defined")
    sg = None
    
default_to_email_str = os.getenv('RECEIVER_EMAIL')


def send_email(to_email_str, subject_str, content_str):
    if not sg or not to_email_str:
        return 
    
    from_email = Email(from_email_str)
    
    email_list = to_email_str.split(";")  # Convert to list
    # Convert list of emails into a list of `To` objects
    to_email_list = [To(email) for email in email_list]

    #to_email = To(to_email_str)
    content = Content("text/plain", content_str)
    
    # Create the email message
    message = Mail(from_email, to_email_list, subject_str, content)
    # message = Mail(
    #     from_email=from_email_str,
    #     to_emails=to_email_str,
    #     subject=subject_str,
    #     plain_text_content=content_str)
    
    # Send the email
    try:
        response = sg.send(message)
        logger.info(f"Email sent successfully to {to_email_str} subject {subject_str}. Status code: {response.status_code}")
        logger.debug(f"Response Headers: {response.headers}")
    except Exception as e:
        logger.error(f"send_email to {to_email_str} subject {subject_str} ; Error: {str(e)}")


# def test():
#     if from_email_str and default_to_email_str:
#         from_email = Email(from_email_str)  # Verified sender email
#         to_email = To(default_to_email_str)  # The recipient's email address
#         subject = "route test"
#         content = Content("text/plain", "TESTING!!!")
#         # Create the email message
#         mail = Mail(from_email, to_email, subject, content)
#         response = sg.send(mail)

if __name__ == "__main__":
    # Set up the email components
    to_email = default_to_email_str  # The recipient's email address
    subject = "route test 101"
    content = "TESTING!!! dssdsdsdsd"
    send_email(to_email, subject, content)
    #test()
    


