# Required imports.
from twitchio.ext import commands
from random import random, choice
from time import sleep, time
from collections import deque
import requests
import json

# The following import is created by the user and contains the required
from botsecrets import CLIENT_ID, CLIENT_SECRET, IRC_TOKEN, IRC_NICKNAME, IRC_INIT_CHANNEL

# Maximum time to wait between leaving one channel and joining another. This prevents the bot darting around Twitch (we've got all the time in the world).
MAX_WAIT_SECS = 60

# Value [0, 1] (0 and 1 inclusive) above which the channel request travels further down the list.
SCROLL_VAL = 0.01

# Number of channels returned per Twitch API request. Should be larger than the maximum size of the 'visited_channels' list to prevent infinite loops. Maximum is 100 as defined by Twitch.
RESPONSE_SIZE = "100"

# Defines the maximum size of the deque which stores previously visited channels (in this session). Should be smaller than 'RESPONSE_SIZE' to prevent infinite loops.
DEQUE_SIZE = 50

# Define what language you want the returned streams to be in.
RESPONSE_LANGUAGE = "en"

# What message do you want to send to every channel?
CHATBOT_MESSAGE = "Hey there. I'm here to encourage you to keep on streaming - you're doing great! :)"

# Determines whether that channel was already joined by the bot. Prevents processing the join command multiple times.
is_joined = False

# Keeps a list of recently visited channels, to prevent spam.
visited_channels = deque([], DEQUE_SIZE)

# Note the time when the current token will expire.
expiry_time = None

# Stores the request token.
bearer_token = None

# Initialise the bot. I'm not actually sure what the prefix does...
bot = commands.Bot(
irc_token=IRC_TOKEN,
nick=IRC_NICKNAME,
prefix='!',
initial_channels=[IRC_INIT_CHANNEL]
)

def setup_http():
    """
    Generates the authorisation token required for HTTP calls to the Twitch API.
    """

    # Create the OAuth request for a token.
    access_url = "https://id.twitch.tv/oauth2/token?client_id="+ CLIENT_ID + "&client_secret=" + CLIENT_SECRET + "&grant_type=client_credentials"
    token = requests.post(access_url)

    # Save the token and required refresh time.
    if token.status_code == 200:
        print("Twitch API authentication token successfully obtained: {0}".format(json.loads(token.text)))
        access_token = json.loads(token.text)['access_token']
        token_expiry = json.loads(token.text)['expires_in']

        # Set the timer for expiry (with a bit of leeway). Since the expiry time is large we don't need millisecond precision.
        global expiry_time
        expiry_time = round((time() + (token_expiry * 0.9)), 0)

        # Set the bearer token so that other functions can use it.
        global bearer_token
        bearer_token = access_token

        return
    else:
        raise Exception("Could not obtain an authorisation token. Response: {0}".format(json.loads(token.text)))


@bot.event
async def event_ready():
    """
    This function is called once the Twitch Encouragement Bot comes online.
    """
    
    print("The Twitch Encouragement Bot has successfully come online!")
    return

@bot.event
async def event_join(user_context):
    """
    This function is called once anyone joins the channel the bot is connected to.
    """
    
    # Check who it is that joined.
    if user_context.name.lower() == "twitchencouragement":
        # Check if this channel has been joined consecutively.
        global is_joined
        if is_joined:
            return
        else:
            is_joined = True
        
        # This bot joined the channel, send a message of encouragement.
        await user_context.channel.send(CHATBOT_MESSAGE)

        # Access the underlying WebSocket connection to leave the channel.
        web_socket = bot._ws

        # Leave the current channel.
        await web_socket.part_channels(user_context.channel.name)
        print("The following channel has been visited and messaged by the bot: {0}".format(user_context.channel.name))

        # Wait a small amount of time before moving on. Helps keep logs tidy.
        sleep(random() * MAX_WAIT_SECS)
        is_joined = False

        # Join a new channel.
        new_channel = get_new_channel()
        
        """
        Uncomment below if you'd like a chance to visit the channel before the messages are sent.
        """
        #sleep(random() * MAX_WAIT_SECS)

        await web_socket.join_channels(new_channel)

        return
    else:
        # Someone else joined the channel - don't do anything.
        return

def get_new_channel(page_cursor = None, num_rerolls = 0):
    """
    Picks a random channel to join out of those on Twitch.
    """

    # Ensure the token has not expired.
    global expiry_time
    global bearer_token
    if (expiry_time is None) or (time() > expiry_time) or (bearer_token is None):
        # Request a new token.
        setup_http()
    
    # With a valid token, we can obtain a list of channels.
    if page_cursor is None:
        channel_url = "https://api.twitch.tv/helix/streams?first=" + RESPONSE_SIZE + "&language=" + RESPONSE_LANGUAGE
    else:
        channel_url = "https://api.twitch.tv/helix/streams?first=" + RESPONSE_SIZE + "&language=" + RESPONSE_LANGUAGE + "&after=" + page_cursor
    headers = {"Client-ID": "7axjvxewsf99z0qrg35qop0o5s28rv",
               "Authorization": "Bearer " + bearer_token
    }
    response = requests.get(channel_url, headers=headers)

    if response.status_code == 200:
        num_rerolls += 1
        response_json = json.loads(response.text)
        # Check whether we could/should travel further down.
        if "cursor" in response_json["pagination"]:
            # Roll a random number to check whether we should move further down the channel list.
            if random() > SCROLL_VAL:
                page_cursor = response_json["pagination"]["cursor"]
                return get_new_channel(page_cursor, num_rerolls)

        # If we're here, we've either reached the end of the list, or we 'failed' the roll.
        sampling_data = response_json["data"]

        # Choose a random channel from the list and ensure it is live.
        channel_status = None
        channel_name = None
        global visited_channels
        while (channel_status != "live") or (channel_name in visited_channels):
            # Choose a random channel from the list.
            chosen_channel = choice(sampling_data)
            channel_status = chosen_channel["type"]
            channel_name = chosen_channel["user_name"]
        
        print("The next channel the bot will visit is: {0}. It took {1} rerolls to get to this channel.".format(channel_name, num_rerolls))
        
        # Add the channel to the list of visited channels.
        visited_channels.append(channel_name)

        return chosen_channel["user_name"]

    else:
        raise Exception("Could not obtain list of channels. Response: {0}".format(json.loads(response.text)))

if __name__ == "__main__":
    bot.run()