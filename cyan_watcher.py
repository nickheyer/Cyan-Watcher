from bs4 import BeautifulSoup
from subprocess import call
import time
import os
import requests
import smtplib
from apscheduler.schedulers.background import BackgroundScheduler
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from cryptography.fernet import Fernet
import ast
from time import sleep
import sys

email_creds_path = os.path.join(os.path.dirname(__file__), 'emailcreds.json')
crypt_key_path = os.path.join(os.path.dirname(__file__), 'key.key')

print("Bot initiating...")
check_interval = input("How often would you like to check Cyan's website for new job listings? (In hours): ")
en_email = input("Would you like to enable email notifications? (yes or no): ")
if en_email.lower().strip() == "yes":
    try:
        file = open(crypt_key_path, "rb")
        key = file.read()
        file.close()
    except:
        key = Fernet.generate_key()
        file = open(crypt_key_path,'wb')
        file.write(key)
        file.close()
    fernet = Fernet(key)
    try:
        with open(email_creds_path, "r") as emailcreds_r:
            encrypted = emailcreds_r.read()
        encrypted_bytes = encrypted.encode('utf-8')
        emailcreds = fernet.decrypt(encrypted_bytes)
        emailcreds = ast.literal_eval(emailcreds.decode('utf-8'))
        server = smtplib.SMTP(host = emailcreds["smtp_host"], port = int(emailcreds["smtp_port"]))
    except:
        while True:
            emailcreds = {}
            emailcreds["smtp_address"] = input("Please input your outgoing email address: ").strip()
            emailcreds["smtp_host"] = input("Please input your outgoing email providor's smtp server (ie: 'smtp.gmail.com'): ").strip()
            emailcreds["password"] = input(f"Please input the outgoing email password for '{emailcreds['smtp_address']}': ").strip()
            if emailcreds["smtp_host"] == 'smtp.gmail.com':
                print("Since you are using a google email, you must enable 'less-secure-apps' via https://www.google.com/settings/security/lesssecureapps")
            emailcreds["smtp_port"] = input("Please input your email providor's smtp port (ie: '587'): ").strip()
            emailcreds["dest_email"] = input("Please input what email you'd like to send notifications to: ").strip()
            try:
                server = smtplib.SMTP(host = emailcreds["smtp_host"], port = int(emailcreds["smtp_port"]))
                encoded_creds = json.dumps(emailcreds).encode('utf-8')
                encrypted= fernet.encrypt(encoded_creds)
                with open(email_creds_path, "wb") as emailcreds_w:
                    emailcreds_w.write(encrypted)
                break
            except:
                print("There seems to be an error regarding your email credentials, try inputting them again.")
                pass
      
def job():
    source = requests.get("https://cyan.com/company/careers/").text
    soup = BeautifulSoup(source, "lxml")
    section_1  = soup.select_one('#sp-ea-474')
    sub_1 = section_1.div.div.h3.text
    if en_email.lower().strip() == "yes" and sub_1 != "Check back later!":
        msg = MIMEMultipart()
        password = emailcreds["password"]
        msg['From'] = emailcreds["smtp_address"] 
        msg['To'] = emailcreds["dest_email"]
        msg['Subject'] = "BIG UPDATE: CYAN IS NOW HIRING"
        msg_body = (f'CYAN has updated their "Careers" page: "https://cyan.com/company/careers/"\n"{sub_1}"')
        msg.attach(MIMEText(msg_body, 'plain'))
        server.connect(emailcreds["smtp_host"], emailcreds["smtp_port"])
        server.starttls()
        server.login(msg['From'], password)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
scheduler = BackgroundScheduler()
scheduler.configure()
scheduler.add_job(job, 'interval', hours = int(check_interval))
scheduler.start()
os.system('cls' if os.name == 'nt' else 'clear')
print('Bot is running, press Ctrl+C to stop and exit')
try:
    while True:
        time.sleep(5)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
    print("Quitting Cyan_Watcher, good luck!") ; sleep(4)
    sys.exit()