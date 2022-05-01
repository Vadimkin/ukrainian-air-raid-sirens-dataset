from telethon import TelegramClient
from telethon.sessions import StringSession

from config import API_ID, API_HASH, API_SESSION_STRING
from processors.full_data import process_full_data
from processors.oblasts_only import process_oblasts_only

print(str(API_ID).replace('1', '*'))
client = TelegramClient(StringSession(API_SESSION_STRING), API_ID, API_HASH)


with client:
    # process_oblasts_only() creates a dataset with only oblasts info
    # and starts from 26th of February
    client.loop.run_until_complete(process_oblasts_only(client))

    # process_full_data() creates a dataset with all info
    # about oblasts, raions and hromadas and starts from 15th of March
    client.loop.run_until_complete(process_full_data(client))
