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
class IdolchampUtility:
    config = configparser.ConfigParser()
    config.read('config.ini')
    user_agents = []
    proxy_list = []
    proxy_username = os.environ.get("PROXY_USERNAME")
    proxy_password = os.environ.get("PROXY_PASSWORD")
    # Define the path to your data.csv file
    data_file = "data.csv"
    ORIGIN = config.get('settings', 'ORIGIN')
    REFERER = config.get('settings', 'REFERER')
    
    @staticmethod
    def initialize():
        with open('user_agents.csv', 'r') as file:
            IdolchampUtility.user_agents = file.read().splitlines()
        # Read proxy configurations from data.csv
        with open(IdolchampUtility.data_file, mode='r') as file:
            csv_reader = csv.reader(file, delimiter=':')
            for row in csv_reader:
                if len(row) == 2:  # Ensure each row has four elements
                    IdolchampUtility.proxy_list.append({
                        'host': row[0],
                        'port': row[1],
                        'username': IdolchampUtility.proxy_username,
                        'password': IdolchampUtility.proxy_password
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
        sleep_time = round(random.uniform(0, max_delay), 2)  # Generates a random float and rounds it to 2 decimal places
        if show_delay:
            print(f"Waiting for {sleep_time} seconds.")
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
        url = URL
        response = requests.post(url, data=message, headers={ 
            
            "Markdown": "yes",
            "Tags": "chart_with_upwards_trend" 
            })
        return response.text

if __name__ == "__main__":
    # user_agent = IdolchampUtility.generate_user_agent()
    # print(f"user_agent: {user_agent}\n")
    # headers = IdolchampUtility.generate_headers(user_agent)
    # print(f"headers: {headers}\n")
    # headers_with_token = IdolchampUtility.generate_headers(user_agent, "1234567890")
    # print(f"headers_with_token: {headers_with_token}\n")
    # password = IdolchampUtility.generate_random_password()
    # print(f"Password: {password}")
    # IdolchampUtility.random_sleep(5, True)
    #proxy = IdolchampUtility.set_random_proxy()
    #print(f"Proxy: {proxy}")
    message = "# updates \n_____\nStart Time: 00:01\nEnd Time: 00:35\nAccount Used: 1\n**Votes Casted: 500**"
    IdolchampUtility.send_message("http://ec2-54-169-109-225.ap-southeast-1.compute.amazonaws.com:7777/tempest-8347820", message)
