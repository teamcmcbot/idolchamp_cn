from dotenv import load_dotenv
load_dotenv()
import random
import string
import time
import csv
import os
import configparser
import pyperclip
import requests
import logging
class IdolchampUtility:
    config = configparser.ConfigParser()
    config.read('config.ini')
    user_agents = []
    proxy_list = []
    proxy_username = os.environ.get("PROXY_USERNAME")
    proxy_password = os.environ.get("PROXY_PASSWORD")
    proxy_resident_username = os.environ.get("PROXY_RESIDENT_USERNAME")
    proxy_resident_password = os.environ.get("PROXY_RESIDENT_PASSWORD")
    # Define the path to your data.csv file
    data_file = "data.csv"
    ORIGIN = config.get('settings', 'ORIGIN')
    REFERER = config.get('settings', 'REFERER')
    pushover_url = config.get('settings', 'PUSHOVER_URL')
    TEST_URL = config.get('settings', 'TEST_URL')
    
    @staticmethod
    def initialize():
        with open('user_agents.csv', 'r') as file:
            IdolchampUtility.user_agents = file.read().splitlines()
        # Read proxy configurations from data.csv
        with open(IdolchampUtility.data_file, mode='r') as file:
            csv_reader = csv.reader(file, delimiter=':')
            for row in csv_reader:
                host = row[0]
                port = row[1]
                # Set password based on the host prefix
                if host.startswith("dc."):
                    username = IdolchampUtility.proxy_username
                    password = IdolchampUtility.proxy_password
                else:
                    username = IdolchampUtility.proxy_resident_username
                    password = IdolchampUtility.proxy_resident_password
                if len(row) == 2:  # Ensure each row has four elements
                    IdolchampUtility.proxy_list.append({
                        'host': host,
                        'port': port,
                        'username': username,
                        'password': password
                    })

    @staticmethod
    def generate_headers(user_agent, token=None):
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-GB,en;q=0.9",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": IdolchampUtility.ORIGIN,
            "Referer": IdolchampUtility.REFERER,
            "Sec-Ch-Ua": '"Not A;Brand";v="99", "Chromium";v="116", "Google Chrome";v="116"',
            "Sec-Ch-Ua-Mobile": "?1",
            "Sec-Ch-Ua-Platform": "Android",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": user_agent
        }

        if token:
            headers["Token"] = token

        return headers
    @staticmethod
    def generate_user_agent():
        if not IdolchampUtility.user_agents:
            # Initialize user agents if the list is empty
            IdolchampUtility.initialize()
        return random.choice(IdolchampUtility.user_agents)
    @staticmethod
    def set_random_proxy():
        if not IdolchampUtility.proxy_list:
            IdolchampUtility.initialize()

        # Select a random proxy configuration
        random_proxy = random.choice(IdolchampUtility.proxy_list)
        #print(f"random_proxy: {random_proxy}")
        
        # Set the proxy for your requests
        proxies = {
            'http': f"http://{random_proxy['username']}:{random_proxy['password']}@{random_proxy['host']}:{random_proxy['port']}",
            'https': f"http://{random_proxy['username']}:{random_proxy['password']}@{random_proxy['host']}:{random_proxy['port']}"
        }
        
        return proxies
    @staticmethod
    def generate_random_password():
        # Define character sets
        uppercase_letters = string.ascii_uppercase
        lowercase_letters = string.ascii_lowercase
        digits = string.digits

        # Combine character sets
        all_characters = uppercase_letters + lowercase_letters + digits

        # Ensure at least one character from each set
        password = random.choice(uppercase_letters) + \
                random.choice(lowercase_letters) + \
                random.choice(digits)

        # Generate the remaining characters
        remaining_length = 12 - len(password)
        for _ in range(remaining_length):
            password += random.choice(all_characters)

        # Shuffle the password to randomize character order
        password_list = list(password)
        random.shuffle(password_list)
        password = ''.join(password_list)
        #print(password)
        return password
    @staticmethod
    def random_sleep(max_delay, show_delay):
        logger = logging.getLogger(__name__)
        sleep_time = round(random.uniform(0, max_delay), 2)  # Generates a random float and rounds it to 2 decimal places
        if show_delay:
            logger.info(f"Waiting for {sleep_time} seconds.")
        time.sleep(sleep_time)
    @staticmethod
    def copy_to_clipboard(text):
        try:
            pyperclip.copy(text)
            print("Text copied to clipboard successfully.")
        except pyperclip.PyperclipException:
            print("Unable to copy text to clipboard. You can manually paste the text.")
            print(text)
    @staticmethod
    def send_message(URL, message):
        try:
            response = requests.post(
                URL,
                data=message,
                headers={
                    "Markdown": "yes",
                    "Tags": "chart_with_upwards_trend"
                },
                timeout=5
            )
            return response.text
        except requests.exceptions.Timeout:
            return "Error sending message: Request Timeout"
    @staticmethod
    def send_push(message, title=None):
        URL = IdolchampUtility.pushover_url
        print(f"URL: {URL}")
        try:
            response = requests.post(
                URL,
                json={ 
                    "title" : title, 
                    "message": message 
                },
                headers={
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            return response.text
        except requests.exceptions.Timeout:
            return "Error sending message: Request Timeout"
    @staticmethod
    def test_proxy(proxies):
        with requests.Session() as session:
            session.proxies = proxies
            result = session.get(IdolchampUtility.TEST_URL)
            logger.info(result.text)  
            print(f"Reponse time: {result.elapsed.total_seconds()}")  
            result = session.get(IdolchampUtility.TEST_URL)
            logger.info(result.text)  
            print(f"Reponse time: {result.elapsed.total_seconds()}")  
            result = session.get(IdolchampUtility.TEST_URL)
            logger.info(result.text)  
            print(f"Reponse time: {result.elapsed.total_seconds()}")
    @staticmethod
    def generate_device_id():
        epoch = int(time.time() * 1000)  # Convert time to milliseconds, similar to JavaScript's getTime()
        device_id = f"device-{epoch}"
        #logger.info(f"deviceId: {device_id}")
        return device_id  
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler('common_util.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    # user_agent = IdolchampUtility.generate_user_agent()
    # print(f"user_agent: {user_agent}\n")
    # headers = IdolchampUtility.generate_headers(user_agent)
    # print(f"headers: {headers}\n")
    # headers_with_token = IdolchampUtility.generate_headers(user_agent, "1234567890")
    # print(f"headers_with_token: {headers_with_token}\n")
    # password = IdolchampUtility.generate_random_password()
    # print(f"Password: {password}")
    # IdolchampUtility.random_sleep(5, True)
    proxy = IdolchampUtility.set_random_proxy()
    print(f"Proxy: {proxy}")
    IdolchampUtility.test_proxy(proxy)
    #message = "# updates \n_____\nStart Time: 00:01\nEnd Time: 00:35\nAccount Used: 1\n**Votes Casted: 500**"
    #print(IdolchampUtility.send_push("", message))
    #message = "An error has occured 2"
    #title = "Error Occurred 2"
    #print(IdolchampUtility.notify_error(message, title))
    #IdolchampUtility.random_sleep(5, True)
