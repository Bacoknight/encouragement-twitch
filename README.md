# Twitch Encouragement Bot
A simple bot which uses the TwitchIO library to send an encouraging message to random channels.

# Usage
To use this bot, you must populate a file called botsecrets.py with the following data:
- CLIENT_ID: This will be obtained when you register your application on Twitch using the following link: https://dev.twitch.tv/console
- CLIENT_SECRET: As above
- IRC_TOKEN: This will be obtained by signing into the account you'd want to use as the bot and navigating to: https://twitchapps.com/tmi/
- IRC_NICKNAME: The name of the account you'll be using as the bot
- IRC_INIT_CHANNEL: The initial channel to navigate to once the bot starts. I suggest using your own channel.

You can then run bot.py and your bot will start being friendly all over Twitch!

# Limitations
- This bot cannot detect whether a channel is in followers-only or subscribers-only mode. In these cases, the bot will send a message but it will not appear on the stream chat.

# Notes on how TwitchIO works
TwitchIO (https://github.com/TwitchIO/TwitchIO) is a library used for interacting with Twitch IRC in a relatively simple manner. For a bot created by the library to respond to IRC events, it must implement specific functions.
This function must be an async function annotated with @bot.event. 
The function name must follow a specific naming convention: "event_XXX", where XXX is a specific IRC event. The events currently available are:
- raw_data
- ready
- message
- raw_usernotice
- usernotice_subscription
- userstate
- mode
- join
- part
- raw_pubsub
These functions may receive contextual data, which you can use to send messages to the stream chat.
TwitchIO bots can also respond to chat commands ("!test" for example), but this is much better documented on the library.
