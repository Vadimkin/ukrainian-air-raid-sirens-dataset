from telethon import TelegramClient
from telethon.sessions import StringSession

from config import API_ID, API_HASH, API_SESSION_STRING
from processors.oblasts_only import process_oblasts_only
from processors.official_channel import OfficialAirAlertProcessor

client = TelegramClient(StringSession(API_SESSION_STRING), API_ID, API_HASH)


with client:
    # process_oblasts_only() creates a dataset with only oblasts info
    # and starts from 26th of February
    client.loop.run_until_complete(process_oblasts_only(client))

    # Create a dataset with all official data
    #  for oblasts, raions and hromadas,
    #  and it starts from 15th of March
    processor = OfficialAirAlertProcessor(client)
    client.loop.run_until_complete(processor.process())
