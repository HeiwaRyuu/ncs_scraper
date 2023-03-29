## Email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib
## Credentials
import config


def send_mail(filename, recipients, channel_name, date):
    print('Starting email creation...')
    #Creating the SMTP Object and connecting to the server and port
    smtpObj = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    sender = config.email
    pwd = config.password
    smtpObj.login(sender, pwd)
    recipient_email = ', '.join(recipients)
    subject = f"{channel_name} - {date}"
    body = f"Feteched informartion from {channel_name}..."
    # Create a multipart messages
    msg = MIMEMultipart()
    msg ['From'] = sender
    msg['To'] = recipient_email
    msg['Subject'] = subject
    # Add the body to email
    msg.attach(MIMEText(body, 'plain'))
    # Open file in binary mode using read() method
    attachment = open(filename, 'rb')
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    # Encode file in base64
    encoders.encode_base64(part)
    # Add header to attachment called part
    part.add_header('Content-Disposition',f'attachment; filename= {filename}',)
    # Add attachment to msg and convert it to string using the as_string method
    msg.attach(part)
    text = msg.as_string()
    #Send the message over using sendmail() method
    print('Sending email...')
    smtpObj.sendmail(sender, recipients, text)
    #End the SMTP Server connection
    smtpObj.quit()
    print('Email sent... Script ended with SUCCESS state...')