from dotenv import load_dotenv
load_dotenv()
from common_util import IdolchampUtility

from enum import Enum, auto
class QueryMode(Enum):
    EQUAL = auto()
    GREATER_THAN_EQUAL = auto()
    LESS_THAN_EQUAL = auto()
class VoteMode(Enum):
    EXACT = auto()
    MAX = auto()

import os
import requests
import time
from datetime import datetime
import logging
# Set the logging level (you can change this as needed)
logging.basicConfig(level=logging.INFO)
# Create a logger instance
logger = logging.getLogger()
# Define a format for log messages
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# Create a handler for the log file (saves log messages to a file)
file_handler = logging.FileHandler('vote.log')
file_handler.setFormatter(formatter)
# Add the handlers to the logger
logger.addHandler(file_handler)

import configparser
config = configparser.ConfigParser()
config.read('config.ini')

TIMEOUT_GET = config.getint('settings', 'TIMEOUT_GET')
TIMEOUT_POST = config.getint('settings', 'TIMEOUT_POST')
MAX_RETRIES = config.getint('settings', 'MAX_RETRIES')
DELAY_BETWEEN_RETRIES = config.getint('settings', 'DELAY_BETWEEN_RETRIES')
VOTE_DELAY_MAX = config.getint('settings', 'VOTE_DELAY_MAX')
ACCOUNT_SWITCH_DELAY = config.getint('settings', 'ACCOUNT_SWITCH_DELAY')
USE_PROXY = config.getboolean('settings', 'USE_PROXY_VOTE')
VOTE_DETAIL_URL = config.get('settings', 'VOTE_DETAIL_URL')
VOTE_URL = config.get('settings', 'VOTE_URL')
MY_URL = config.get('settings', 'MY_URL')
TEST_URL = config.get('settings', 'TEST_URL')
UPDATE_PROGRESS = config.getint('settings', 'UPDATE_PROGRESS')

# Vote Config
total_votes = config.getint('settings', 'total_votes')
votes_per_account = config.getint('settings', 'votes_per_account')
votes_to_query = config.getint('settings', 'votes_to_query')
vote_id = config.getint('settings', 'vote_id')
vote_item_id = config.getint('settings', 'vote_item_id')
SHOWCHAMPION_HEARTS_PER_VOTE = config.getint('settings', 'SHOWCHAMPION_HEARTS_PER_VOTE')
total_time = 0
account_time = 0
account_vote_count = 0
error504_count = 0
# Get the query mode from the configuration
query_mode_str = config.get('settings', 'QUERY_MODE')
query_mode_enum = QueryMode[query_mode_str]
# Get the vote mode from the configuration
vote_mode_str = config.get('settings', 'VOTE_MODE')
vote_mode_enum = VoteMode[vote_mode_str]

# NTFY Config
NTFY_HOST=config.get('settings', 'NTFY_HOST')
NTFY_TOPIC=config.get('settings', 'NTFY_TOPIC')
NTFY_URL = f"{NTFY_HOST}{NTFY_TOPIC}"

# DB Config
IDC_TABLE = config.get('settings', 'IDC_TABLE')
IDC_SELECT = config.get('settings', 'IDC_SELECT')
IDC_COL_VOTES_LEFT = config.get('settings', 'IDC_COL_VOTES_LEFT')
IDC_COL_LAST_UPDATE = config.get('settings', 'IDC_COL_LAST_UPDATE')
IDC_COL_MAX_VOTES = config.get('settings', 'IDC_COL_MAX_VOTES')
IDC_COL_BLUE_HEART = config.get('settings', 'IDC_COL_BLUE_HEART')
IDC_COL_ID = config.get('settings', 'IDC_COL_ID')
IDC_COL_TOKEN = config.get('settings', 'IDC_COL_TOKEN')
IDC_COL_PASSWORD = config.get('settings', 'IDC_COL_PASSWORD')

from supabase import create_client, Client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def lambda_handler(event, context):
    total_accounts = 0
    total_votes_casted = 0

    # Initialize the query builder
    query = (
        supabase.table(IDC_TABLE)
        .select(IDC_SELECT)
    )
    # Use the corresponding query method based on QUERY_MODE
    if votes_to_query:
        if query_mode_enum == QueryMode.EQUAL:
            query.eq(IDC_COL_VOTES_LEFT, votes_to_query)
        elif query_mode_enum == QueryMode.GREATER_THAN_EQUAL:
            query.gte(IDC_COL_VOTES_LEFT, votes_to_query)
        elif query_mode_enum == QueryMode.LESS_THAN_EQUAL:
            query.lte(IDC_COL_VOTES_LEFT, votes_to_query)
    query.order(IDC_COL_VOTES_LEFT, desc=True)
    query.order(IDC_COL_LAST_UPDATE, desc=False)
    response = query.execute()
    logger.info(f"Found {len(response.data)} accounts with {query_mode_str} {votes_to_query} votes")
    logger.info(f"Target: {total_votes} votes.")
    start_time = datetime.now()
    for row in response.data:
        votes_left = row[IDC_COL_VOTES_LEFT]
        votes_casted = 0
        global account_time
        global account_vote_count
        account_time = 0
        account_vote_count = 0
        device_id = generate_device_id()
        token = row[IDC_COL_TOKEN]
        user_agent = IdolchampUtility.generate_user_agent()
        headers = IdolchampUtility.generate_headers(user_agent, token)
        logger.info(f"User-Agent: {user_agent}")
        proxies = IdolchampUtility.set_random_proxy()
        #logger.info(f"proxy: {proxies}")
        account_id = row[IDC_COL_ID]
        vote_amount = votes_per_account
        with requests.Session() as session:
            session_start = datetime.now()
            logger.info(f"Start session: {session_start}")
            # Set the proxies for the session
            if USE_PROXY:
                session.proxies = proxies
                # Disable SSL certificate verification for the session
                session.verify = False
            result = session.get(TEST_URL)
            logger.info(result.text)
            love_count = 0
            vote_details = checkVoteDetails(token, vote_id, vote_item_id, headers, session)
            if not verify_vote_details(vote_details):
                if vote_details["state"]!=2 and vote_details["state"]!=0:
                    break
                continue
            love_count = vote_details["love_count"]
            vote_remaining = vote_details["vote_remaining"]

            blue_hearts = checkAccount(token, headers, session)
            vote_amount = get_max_vote_amount(vote_remaining, love_count, blue_hearts, total_votes, total_votes_casted)
            if vote_amount < 1:
                logger.info(f"Account ({account_id}) has not enough votes!")
                update_account(account_id,token,votes_casted, headers, session)
                continue
            logger.info(f"Voting in progress: {total_votes_casted} / {total_votes}")
            for i in range(vote_amount):
                # Call function to cast vote
                vote_success = cast_vote(token, vote_item_id, device_id, headers, session)
                if not vote_success:
                    logger.info(f"Error casting votes for ({account_id}, votes casted: {votes_casted})")
                    break
                #logger.info(f"Casting vote using {row[IDC_COL_TOKEN]} : {i+1}")
                votes_left -= 1
                votes_casted += 1
            # result2 = session.get(TEST_URL)
            # logger.info(result2.text)   
            if votes_casted > 0 : 
                logger.info(f"Average Response Time: {account_time/account_vote_count}") 
                update_account(account_id,token,votes_casted, headers, session)
                total_accounts += 1
                total_votes_casted += votes_casted
                if(total_accounts % UPDATE_PROGRESS == 0):
                    message = f"Current Progress: {total_votes_casted} / {total_votes}"
                    if NTFY_HOST and NTFY_TOPIC:
                        IdolchampUtility.send_message(NTFY_URL, message)
                    IdolchampUtility.send_push(message, "Voting Updates")
                if total_votes_casted >= total_votes:
                    break

            IdolchampUtility.random_sleep(ACCOUNT_SWITCH_DELAY, True)
    # End of for loop of accounts
    logger.info(f"Voting completed! Total Votes Casted: {total_votes_casted}, Accounts used: {total_accounts}")
    end_time = datetime.now()
    if total_votes_casted > 0:
        global total_time
        logger.info(f"total_time: {total_time}, average: {total_time/total_votes_casted}")
    json_response = {
        "total_votes": f"{total_votes}",
        "vote_id": f"{vote_id}",
        "vote_item_id": f"{vote_item_id}",
        "total_accounts": f"{total_accounts}",
        "total_votes_casted": f"{total_votes_casted}",
        "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),  # Format the datetime as a string
        "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S')  # Format the datetime as a string
    }
    if NTFY_HOST and NTFY_TOPIC:
        #NTFY_URL = f"{NTFY_HOST}{NTFY_TOPIC}"
        message = f"# updates \n_____\n*{start_time.strftime('%Y-%m-%d %H:%M:%S')}* to *{end_time.strftime('%Y-%m-%d %H:%M:%S')}*\nAccounts used: {total_accounts}\n**Votes Casted: {total_votes_casted}**"
        #logger.info(f"Sending message to {NTFY_URL}: {message}")
        logger.info(IdolchampUtility.send_message(NTFY_URL, message))
    IdolchampUtility.send_push(json_response, "Voting Completed")    
    return json_response
def cast_vote(token, vote_item_id, device_id, headers, session):
    url = VOTE_URL
    # Payload with voteItemId and deviceId
    data = {
        "voteItemId": vote_item_id,
        "device": "ANDROID",
        "deviceId": device_id
    }
    for attempt in range(MAX_RETRIES):
        try:
            vote_response = session.post(url, json=data, headers=headers, timeout=TIMEOUT_POST)  # Send data as JSON
            vote_response.raise_for_status()  # Will raise an exception for HTTP error responses
            # Print the response time in seconds
            #logger.info(f"Response time: {vote_response.elapsed.total_seconds()} seconds")
            global total_time
            total_time += vote_response.elapsed.total_seconds()
            global account_time
            account_time += vote_response.elapsed.total_seconds()
            global account_vote_count
            account_vote_count += 1
            IdolchampUtility.random_sleep(VOTE_DELAY_MAX, False)
            return True
        except requests.Timeout:
            logger.error(f"Timeout error while casting vote using token: {token}")
        except requests.HTTPError as e:
            if vote_response.status_code == 504:
                global error504_count
                error504_count += 1
                logger.error(f"Received a 504 error. Count: {error504_count}")
                if error504_count >= 10:
                    return False
            logger.error(f"HTTP Error {e} occurred while casting vote using token: {token}")
        except requests.RequestException as e:
            logger.error(f"Error {e} occurred while casting vote using token: {token}")
        # If this isn't the last attempt, sleep before trying again
        if attempt < MAX_RETRIES - 1:
            time.sleep(DELAY_BETWEEN_RETRIES)
    return False

def update_account(id, token, votes_casted, headers, session):
    blue_hearts_after = checkAccount(token, headers, session)
    if blue_hearts_after is not None:
        logger.info(f"Blue Hearts after voting: {blue_hearts_after}")
        votes_left_after = blue_hearts_after//SHOWCHAMPION_HEARTS_PER_VOTE
        max_votes_left_after = 100 if votes_left_after > 100 else votes_left_after
        logger.info(f"Updating account id: {id}, votes casted: {votes_casted}, votes left: {votes_left_after}")
        db_update = supabase.table(IDC_TABLE).update({
            IDC_COL_BLUE_HEART: blue_hearts_after,
            IDC_COL_VOTES_LEFT: votes_left_after,
            IDC_COL_MAX_VOTES: max_votes_left_after
        }).eq(IDC_COL_ID, id).execute()
        #logger.info(db_update)
        if not db_update.data:
            logger.info(f"Error: Update ({id}) was unsuccessful!")
        #else:
            #logger.info(f"Update ({id}) successful!")


def checkAccount(token, headers, session):
    url = MY_URL
    
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, headers=headers,timeout=TIMEOUT_GET)
            response.raise_for_status()  # This will raise an exception for HTTP error responses
            
            data = response.json()
            if 'data' in data and 'loveTimeNum' in data['data']:
                return data['data']['loveTimeNum']
            else:
                logger.info("The response does not contain the expected data.")
                return 0
                
        except (requests.RequestException, ValueError) as e:
            logger.info(f"Attempt {attempt + 1} failed due to: {e}")
            if attempt == MAX_RETRIES - 1:  # If this was the last attempt
                logger.info("Max retries reached. Exiting.")
                return 0


def generate_device_id():
    epoch = int(time.time() * 1000)  # Convert time to milliseconds, similar to JavaScript's getTime()
    device_id = f"device-{epoch}"
    #logger.info(f"deviceId: {device_id}")
    return device_id
def checkVoteDetails(token, voteId, voteItemId, headers, session):
    # Construct the URL
    url = f"{VOTE_DETAIL_URL}{voteId}"
    vote_remaining = 0
    vote_times = 0
    love_count = 0
    state = 0
    vote_details = {
        "vote_remaining": vote_remaining,
        "vote_times": vote_times,
        "love_count": love_count,
        "state": state,
        "title": "",
        "titleMain": ""
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            # Make the GET request
            response = session.get(url, headers=headers, timeout=TIMEOUT_GET)
            
            # Check for successful response
            if response.status_code == 200:
                result = check_vote_item_id_in_list(response.json(), voteItemId)
                if not result:
                    logger.info(f"Vote Item Id {voteItemId} not found! token: {token}")
                    vote_details["vote_remaining"] = -1
                    return vote_details
                data = response.json().get('data', {})
                vote_remaining = data.get('remainVoteTimes')
                logger.info(f"remainVoteTimes: {vote_remaining}")
                # Access voteTimes, loveCount, and state
                vote_times = data.get('voteDetail', {}).get('voteTimes')
                love_count = data.get('voteDetail', {}).get('loveCount')
                state = data.get('voteDetail', {}).get('state')
                title = data.get('voteDetail', {}).get('title')
                titleMain = data.get('voteDetail', {}).get('titleMain')

                vote_details["vote_remaining"] = vote_remaining
                vote_details["vote_times"] = vote_times
                vote_details["love_count"] = love_count
                vote_details["state"] = state
                vote_details["title"] = title
                vote_details["titleMain"] = titleMain
                return vote_details
                
            else:
                logger.info(f"Error on attempt {attempt + 1}: {response.status_code}")
                if attempt < MAX_RETRIES - 1:  # i.e. not on the last attempt
                    time.sleep(DELAY_BETWEEN_RETRIES)
                else:
                    vote_details["vote_remaining"] = -1
                    return vote_details
        except requests.RequestException as e:
            logger.info(f"An error occurred on attempt {attempt + 1}: {e}")
            if attempt < MAX_RETRIES - 1:  # i.e. not on the last attempt
                time.sleep(DELAY_BETWEEN_RETRIES)
            else:
                vote_details["vote_remaining"] = -1
                return vote_details
def check_vote_item_id_in_list(response, voteItemId):
    # Extract the voteItemList from the response
    voteItemList = response.get('data', {}).get('voteItemList', [])
    voteDetail = response.get('data', {}).get('voteDetail', {})

    # Get love_count and ensure it's a valid integer
    love_count = voteDetail.get('loveCount')
    
    # Loop through the voteItemList and check for record with specified voteItemId
    for item in voteItemList:
        if item.get('id') == voteItemId:
            name = item.get('titleSub')
            song = item.get('title')
            score = item.get('score')
            if love_count is not None and isinstance(love_count, int) and love_count!=0:
                score = score // love_count
            logger.info(f"Vote Item Id {voteItemId} found: {name} - {song} ({score} votes)")
            return True
            
    return False
def verify_vote_details(vote_details):
    to_vote = True
    vote_remaining = vote_details["vote_remaining"]
    state =  vote_details["state"]
    title =  vote_details["title"]
    titleMain =  vote_details["titleMain"]
    # logger.info(f"title: {title}")
    # logger.info(f"titleMain: {titleMain}")
    # logger.info(f"state: {state}")
    
    if vote_remaining < 0:
        # Handle the case when vote_remaining is less than 0
        to_vote = False
    elif vote_remaining == 0:
        # Handle the case when vote_remaining is equal to 0
        logger.info("Votes completed for today.")
        to_vote = False
    if state != 2: 
        logger.info(f"Vote is not ongoing. state: {state}")
        to_vote = False
    return to_vote
def get_max_vote_amount(vote_remaining, love_count, blue_hearts, total_votes, total_votes_casted):
    amount_to_vote = 0 
    votes_left = total_votes - total_votes_casted
    logger.info(f"total_votes: {total_votes}, total_votes_casted: {total_votes_casted}, votes_left: {votes_left}, blue_hearts: {blue_hearts}")
    if love_count == 0:
        return vote_remaining # doesnt cost hearts to vote.
    account_max_votes = blue_hearts // love_count
    amount_to_vote = account_max_votes
    if account_max_votes > vote_remaining:
        amount_to_vote =  vote_remaining
    if amount_to_vote > votes_left:
        amount_to_vote = votes_left
    if vote_mode_enum == VoteMode.EXACT and amount_to_vote > votes_per_account:
        amount_to_vote = votes_per_account
        # logger.info(f"EXACT mode, overriding votes amount: {amount_to_vote}")
    logger.info(f"account_max_votes: {account_max_votes}, vote_remaining: {vote_remaining}, amount_to_vote: {amount_to_vote}")
    return amount_to_vote 
if __name__ == "__main__":
    test_event = {
        # Mock your event data here
    }
    test_context = {}  # Mock your context data if needed
    result = lambda_handler(test_event, test_context)
    logger.info(result)
    # Close the file handler when done
    file_handler.close()
