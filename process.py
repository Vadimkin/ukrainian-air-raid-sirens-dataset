from telethon import TelegramClient
from telethon.sessions import StringSession

from config import API_ID, API_HASH, API_SESSION_STRING
from processors.official_channel_processor import OfficialAirAlertProcessor
from processors.volunteer_etryvoga_processor import VolunteerEtryvogaProcessor

client = TelegramClient(StringSession(API_SESSION_STRING), API_ID, API_HASH)


with client:
    # process_oblasts_only() creates a dataset with only oblasts info
    # and starts from 26th of February
    processor = VolunteerEtryvogaProcessor(client)
    client.loop.run_until_complete(processor.process())

    # Create a dataset with all official data
    #  for oblasts, raions and hromadas,
    #  and it starts from 15th of March
    processor = OfficialAirAlertProcessor(client)
    client.loop.run_until_complete(processor.process())
