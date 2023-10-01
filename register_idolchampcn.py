from dotenv import load_dotenv
load_dotenv()
from common_util import IdolchampUtility

import requests
import json
import random
import pyperclip
import logging
# Set the logging level (you can change this as needed)
logging.basicConfig(level=logging.INFO)
# Create a logger instance
logger = logging.getLogger()
# Define a format for log messages
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# Create a handler for the log file (saves log messages to a file)
file_handler = logging.FileHandler('register.log')
file_handler.setFormatter(formatter)
# Add the handlers to the logger
logger.addHandler(file_handler)

import configparser
config = configparser.ConfigParser()
config.read('config.ini')

USER_AGENT = None
DEFAULT_PHONECODE = config.get('settings', 'DEFAULT_PHONECODE')
USE_PROXY = config.getboolean('settings', 'USE_PROXY')
DELAY_MAX = config.getint('settings', 'DELAY_MAX')
TEST_URL = config.get('settings', 'TEST_URL')
OTP_URL = config.get('settings', 'OTP_URL')
LOGIN_URL = config.get('settings', 'LOGIN_URL')
PASSWORD_URL = config.get('settings', 'PASSWORD_URL')
GET_IDOL_URL = config.get('settings', 'GET_IDOL_URL')
SET_IDOL_URL = config.get('settings', 'SET_IDOL_URL')
VIEW_IDOL_URL = config.get('settings', 'VIEW_IDOL_URL')
PARAM_URL = config.get('settings', 'PARAM_URL')

def generate_otp(phone_code, phone, session):
    url = OTP_URL
    headers = IdolchampUtility.generate_headers(USER_AGENT)
    data = {
        "phoneCode": phone_code,
        "phone": phone,
        "position": 1
    }

    response = session.post(url, headers=headers, data=json.dumps(data))
    response_json = response.json()

    if response.status_code == 200:
        if "isExistPhone" in response_json.get("data", {}):
            phoneExist = response_json["data"]["isExistPhone"]
            logger.info(f"OTP generated successfully. Exist: {phoneExist}") 
        else:
            logger.info("OTP generated successfully.")
        return True
    else:
        logger.info(f"Error generating OTP. Status code: {response.status_code}")
        return False

def login_with_otp(phone_code, phone, otp, session):
    url = LOGIN_URL
    headers = IdolchampUtility.generate_headers(USER_AGENT)
    data = {
        "phoneCode": phone_code,
        "phone": phone,
        "verificationCode": otp,
        "position": 1,
        "device": "ANDROID"
    }

    response = session.post(url, headers=headers, data=json.dumps(data))
    response_json = response.json()

    if response.status_code == 200:
        if "token" in response_json.get("data", {}):
            return response_json["data"]  # Return data if it contains a token
        else:
            logger.info("Login successful, but token not found in response.")
    else:
        logger.info(f"Login failed. Status code: {response.status_code}")
    return None

def change_password(token, new_password, session):
    url = PASSWORD_URL
    headers = IdolchampUtility.generate_headers(USER_AGENT, token)
    data = {
        "password": new_password
    }

    response = session.post(url, headers=headers, data=json.dumps(data))
    response_json = response.json()

    if response.status_code == 200:
        logger.info(f"Password change successful. [{new_password}]")
    else:
        logger.info(f"Password change failed. Status code: {response.status_code}")

def get_idol_list(token, session):
    url = GET_IDOL_URL
    headers = IdolchampUtility.generate_headers(USER_AGENT, token)
    
    response = session.get(url, headers=headers)
    response_json = response.json()
    
    if response.status_code == 200:
        idol_list = response_json.get("data", {}).get("idolList", [])
        if idol_list:
            random_idol = random.choice(idol_list)
            idol_id = random_idol.get("id")
            name_en = random_idol.get("nameEn")
            logger.info(f"Random Idol: ID - {idol_id}, NameEn - {name_en}")
            IdolchampUtility.random_sleep(DELAY_MAX, False)
            set_idol(token, idol_id, session)
        else:
            logger.info("No idols found in the response.")
    else:
        logger.info(f"Failed to retrieve idol list. Status code: {response.status_code}")

def set_idol(token, idol_id, session):
    url = SET_IDOL_URL
    headers = IdolchampUtility.generate_headers(USER_AGENT, token)
    data = {
        "list": [idol_id]
    }

    response = session.post(url, headers=headers, data=json.dumps(data))
    response_json = response.json()

    if response.status_code == 200:
        logger.info(f"Idol with ID {idol_id} set successfully.")
        IdolchampUtility.random_sleep(DELAY_MAX, False)
        view_idol(idol_id,token, session)
    else:
        logger.info(f"Failed to set idol with ID {idol_id}. Status code: {response.status_code}")

def view_idol(idol_id, token, session):
    url = VIEW_IDOL_URL + str(idol_id)
    headers = IdolchampUtility.generate_headers(USER_AGENT, token)
    
    response = session.get(url, headers=headers)
    response_json = response.json()
    
    if response.status_code == 200:
        logger.info(f"Viewing idol: {idol_id}")
        IdolchampUtility.random_sleep(DELAY_MAX, False)
        complete_registration(token, session)
    else:
        logger.info(f"Failed to view idol. Status code: {response.status_code}")
def complete_registration(token, session):
    url = PARAM_URL
    headers = IdolchampUtility.generate_headers(USER_AGENT, token)
    
    response = session.get(url, headers=headers)
    response_json = response.json()
    
    if response.status_code == 200:
        logger.info("Account registered: "+token)
    else:
        logger.info(f"Failed to proceed. Status code: {response.status_code}")

def main():
    USER_AGENT = IdolchampUtility.generate_user_agent()
    logger.info(f"User-Agent: {USER_AGENT}")
    proxies = IdolchampUtility.set_random_proxy()
    with requests.Session() as session:
        # Set the proxies for the session
        if USE_PROXY:
            session.proxies = proxies
        try:
            result = session.get(TEST_URL, timeout=(5, 5))
            logger.info(result.text)
            logger.info(f"Response time: {result.elapsed.total_seconds()} seconds")
        except (requests.Timeout, requests.exceptions.ProxyError):
            logger.info("Request timed out!")
            # Disable the proxies for the session and retry the request
            session.proxies = {}
            result = session.get(TEST_URL, timeout=(5, 5))
            logger.info(result.text)
            logger.info(f"Response time: {result.elapsed.total_seconds()} seconds")

        phone_code = input(f"Enter phone code [{DEFAULT_PHONECODE}]: ")
        if not phone_code:
            phone_code = DEFAULT_PHONECODE
        default_phone = None
        if phone_code.startswith(DEFAULT_PHONECODE) and len(phone_code) > len(DEFAULT_PHONECODE):
            default_phone = phone_code[len(DEFAULT_PHONECODE):]
            phone_code = DEFAULT_PHONECODE
        logger.info(f"Enter phone code [{DEFAULT_PHONECODE}]: {phone_code}")
        phone = input(f"Enter phone number [{default_phone}]: ") or default_phone
        logger.info(f"Enter phone number [{default_phone}]: {phone}")
        # Check if phone is empty
        if not phone:
            logger.info("Empty phone entered. Exiting.")
            return

        while True:  # Loop to keep asking for OTP or retriggering its generation
            if generate_otp(phone_code, phone, session):
                otp = input("Enter OTP received on your phone: ")

                # Check if OTP is empty
                if not otp:
                    logger.info("Empty OTP entered. Exiting.")
                    return

                # Check if OTP is "R" or "r" to retrigger generate_otp flow
                elif otp.upper() == "R":
                    logger.info("Retriggering OTP generation.")
                    continue

                # Check if OTP contains only numeric values
                elif not otp.isdigit():
                    logger.info("Invalid OTP format. OTP should be numeric. Exiting.")
                    return

                login_data = login_with_otp(phone_code, phone, otp, session)

                if login_data and "token" in login_data:
                    new_password = IdolchampUtility.generate_random_password()
                    token = login_data["token"]
                    IdolchampUtility.random_sleep(DELAY_MAX, False)
                    change_password(token, new_password, session)
                    IdolchampUtility.random_sleep(DELAY_MAX, False)
                    get_idol_list(token, session)
                    copytext = f"{phone_code}\t{phone}\t{new_password}"
                    pyperclip.copy(copytext)
                    logger.info("Copied to clipboard.")
                    # result = session.get(TEST_URL, timeout=(5, 5))
                    # logger.info(result.text)
                    # logger.info(f"Response time: {result.elapsed.total_seconds()} seconds")
                    break
                else:
                    logger.info("Login data does not contain a valid token. Password change aborted.")
                    break
    # Close the file handler when done
    file_handler.close()
    return
if __name__ == "__main__":
    main()