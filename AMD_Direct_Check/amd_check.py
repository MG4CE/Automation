import logging
import time
import random
import requests 
import os

from datetime import datetime
from pytz import timezone

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

TIMEZONE = 'US/Eastern'
SMPT_SERVER = "smtp.gmail.com"
SMPT_PORT = 587
URL = "https://www.amd.com/en/direct-buy/ca"
SELECTOR = "#block-amd-content > div > div > div > div > div"
NAME_SELECTOR = "div.shop-content > div.direct-buy > div.shop-title"
BUTTON_SELECTOR = "div.shop-content > div.direct-buy > div.shop-links > button"
BUTTON_EXPECTED_TEXT = "Add to cart"

# Logging Config
logging.basicConfig(filename='tracker.log', filemode='w', format='%(asctime)s - %(message)s', level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())

# Set Paramaters
sender_email = os.environ.get('S_EMAIL')
password = os.environ.get('E_PASS') 
target_email = os.environ.get('T_EMAIL')

if target_email == None or sender_email == None or password == None:
    logging.error("Failed to fetch required environment variables!")
    quit()

def send_msg(message):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = target_email
        msg['Subject'] = "AMD Notify"
        message = message
        msg.attach(MIMEText(message))

        server = smtplib.SMTP(SMPT_SERVER, SMPT_PORT)

        # identify ourselves to smtp gmail client
        server.ehlo()
        # secure our email with tls encryption
        server.starttls()
        # re-identify ourselves as an encrypted connection
        server.ehlo()

        server.login(sender_email,password)
        server.sendmail(sender_email, target_email, msg.as_string())
        server.quit()
        
        logging.info("Message sent!")
    except Exception as err:
        logging.error("Failed to send message: " + str(err))

def start_chrome_driver():
    logging.info("Starting ChromeDriver.....")
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument('start-maximized')
    options.add_argument('disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75")
    options.add_experimental_option( "prefs",{'profile.managed_default_content_settings.javascript': 2})
    options.add_experimental_option( "prefs",{'profile.managed_default_content_settings.images': 2})
    options.add_argument('--disable-dev-shm-usage')
    wd = webdriver.Chrome("/usr/bin/chromedriver",options=options)
    logging.info("ChromeDriver Started!")
    return wd

if __name__ == "__main__":
    wd = start_chrome_driver()
    logging.info("Sending start message!")
    send_msg("Chrome Driver Started")

    product_info = []

    while True:
        now_time = datetime.now(timezone(TIMEZONE))
        message = ""
        trigger_send = False

        if now_time.hour == 0 and now_time.minute == 0:
            send_msg("Script still running!")
            time.sleep(60)

        if now_time.hour >= 8 and now_time.hour <= 18:            
            try:
                wd.get(URL)
            except Exception as err:
                logging.warning(err)
                continue
                    
            # TODO add status code check
                    
            try:
                elements = wd.find_elements(By.CSS_SELECTOR, SELECTOR)
            except Exception as err:
                logging.warning(err)
                continue
                        
            for elem in elements:
                try:
                    item = elem.find_element(By.CSS_SELECTOR, NAME_SELECTOR)
                    prod_name = item.text.strip()

                    if [prod_name, False or True] not in product_info:
                        product_info.append([prod_name, False]) 
                    
                    index = 0
                    for i in range(0, len(product_info)):
                        if product_info[i][0] == prod_name:
                            index = i
                            break
                        if i == len(product_info) - 1:
                            logging.error("Product not found in list, quitting!")
                            quit()
                    
                    try:
                        stock_check = elem.find_element(By.CSS_SELECTOR, BUTTON_SELECTOR)
                        if not product_info[index][1]:
                            product_info[index][1] = True
                            trigger_send = True
                            message += product_info[index][0] + "\nIn Stock!\n"
                        logging.info(product_info[index][0] + " In Stock!")

                    except Exception as err:
                        product_info[index][1] = False
                        logging.info(product_info[index][0] + " Out of Stock!")
                
                except Exception as err:
                    logging.warning(err)

            if trigger_send:
                send_msg(URL + " \n" + message)

        timeout = random.randint(5, 10)
        logging.info("Sleep for " + str(timeout) + "s")
        time.sleep(timeout) 
