import pandas as pd
import datetime as dt
## Email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
import smtplib
## Credentials
import config


def parse_release_date_to_date(row):
    date_dict = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7, 'Aug':8, 'Sept':9, 'Oct':10, 'Nov':11, 'Dec':12}
    date_str = row['release_date']

    if "Premiered on" in date_str:
        date_str = date_str[len("Premiered on")+1:]


    splt_date_info = date_str.split(' ')

    print(f"date_str -> {date_str}")
    year = int(splt_date_info[2])
    month = int(date_dict[splt_date_info[1]])
    day = int(splt_date_info[0])

    date = dt.datetime(year, month, day)

    row['birthday'] = date

    return row



def send_mail_birthday(filename, recipients, name, url_list):
    print('Starting email creation...')
    #Creating the SMTP Object and connecting to the server and port
    smtpObj = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    sender = config.email
    pwd = config.password
    smtpObj.login(sender, pwd)
    recipient_email = ', '.join(recipients)
    subject = f"Happy Birthday {name}!"
    songs = '\n'.join(url_list)
    body = f"Here are all NCS Songs that were released on the same date as your birthday! \n\nEnjoy!\n\n"
    # Create a multipart messages
    msg = MIMEMultipart()
    msg ['From'] = sender
    msg['To'] = recipient_email
    msg['Subject'] = subject
    # Add the body to email
    msg.attach(MIMEText(body, 'plain'))

    img_name = "ncs.png"
    msg.attach(MIMEText(f'<img style="width:160px;height:100px;" src="cid:ncs"><br>', 'html'))

    #Attach Image 
    fp = open(img_name, 'rb') #Read image 
    msgImage = MIMEImage(fp.read())
    fp.close()

    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', '<ncs>')
    msg.attach(msgImage)
    
    ## Ending Email
    ender = f"\n\n{songs}\n\n"
    msg.attach(MIMEText(ender, 'plain'))

    # Open file in binary mode using read() method
    attachment = open(filename, 'rb')
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    # Encode file in base64
    encoders.encode_base64(part)
    # Add header to attachment called part
    part.add_header('Content-Disposition',f'attachment; filename= {filename}')
    # Add attachment to msg and convert it to string using the as_string method
    msg.attach(part)
    text = msg.as_string()
    #Send the message over using sendmail() method
    print('Sending email...')
    smtpObj.sendmail(sender, recipients, text)
    #End the SMTP Server connection
    smtpObj.quit()
    print('Email sent... Script ended with SUCCESS state...')




def main():
    df = pd.read_excel("nocopyrightsounds-2023-03-22.xlsx")


    df = df.apply(lambda row: parse_release_date_to_date(row), axis=1)
    date = dt.datetime(2001, 12, 12).date()
    ## emails: iago.ecfto@gmail.com guihperez4@hotmail.com annaluvaladares@gmail.com pedro.handrade2000@gmail.com pgdias020600@gmail.com jpcarvalhoalmeida44@gmail.com
    recipients = ['vitor.carvalho.ufu@gmail.com', 'jpcarvalhoalmeida44@gmail.com']
    name = "Jão"
    filename = f"df_birthday-{date}.xlsx"
    df_birthday = df[(df['birthday'].dt.month == date.month) & (df['birthday'].dt.day == date.day)]
    df_birthday.to_excel(filename, index=False)
    url_list = df_birthday['url'].to_list()

    send_mail_birthday(filename, recipients, name, url_list)

if __name__ == "__main__":
    main()