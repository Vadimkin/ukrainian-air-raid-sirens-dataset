import copy
import csv
import json
import pathlib
from typing import Optional

from telethon.tl.types import Message
from translitua import translit

channel_name = 'air_alert_ua'

final_filename = pathlib.Path(__file__).parent.resolve() / '../datasets/full_data.csv'
states_filename = pathlib.Path(__file__).parent.resolve() / 'states.json'


siren_state = {}
flat_place_list = {}


def get_normalized_states():
    with open(states_filename, 'r') as json_file:
        raw_states = json.load(json_file)

    normalized_states = {}

    for state in raw_states['states']:
        normalized_states[state['stateName']] = {}

        for district in state['districts']:
            normalized_states[state['stateName']][district['districtName']] = []

            for community in district['communities']:
                normalized_states[state['stateName']][district['districtName']].append(community['communityName'])

    return normalized_states


def patch_flat_list(normalized_state_names):
    for state in normalized_state_names:
        flat_place_list[state] = (state, None, None)
        for district in normalized_state_names[state]:
            flat_place_list[district] = (state, district, None)
            for community in normalized_state_names[state][district]:
                flat_place_list[community] = (state, district, community)


def parse_message(message: Message):
    first_line = message.message.split('\n')[0]

    is_activated = "🔴" in first_line
    is_deactivated = "🟢" in first_line

    if not is_activated and not is_deactivated:
        return None, None, []

    affected_places = []

    for place, location_tuple in flat_place_list.items():
        if place not in first_line:
            continue

        affected_places.append(location_tuple)

    return is_activated, is_deactivated, affected_places


def update_state(message: Message, location_tuple: tuple, is_activated: bool) -> Optional[dict]:
    state, district, community = location_tuple

    if community:
        location = siren_state[state]["districts"][district]["communities"][community]
    elif district:
        location = siren_state[state]["districts"][district]
    else:
        location = siren_state[state]

    location['enabled'] = is_activated

    record = None
    # Only one single edge case, but still a case
    if not is_activated and location['enabled_at']:
        level = "hromada" if community else "raion" if district else "oblast"

        record = {
            'oblast': state,
            'raion': district,
            'hromada': community,
            'level': level,
            'started_at': location['enabled_at'],
            'finished_at': message.date,
        }

    if is_activated and not location['enabled_at']:
        location['enabled_at'] = message.date
        location['disabled_at'] = None
    elif not is_activated and not location['disabled_at']:
        location['disabled_at'] = message.date
        location['enabled_at'] = None

    return record


def write_csv(air_raid_data: list):
    keys_to_transliterate = ['oblast', 'raion', 'hromada']
    special_rules = {
        "м. Київ": "Kyiv City",
    }

    with open(final_filename, 'w', newline='') as csvfile:
        fieldnames = ['oblast', 'raion', 'hromada', 'level', 'started_at', 'finished_at']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for record in air_raid_data:
            record_transliterated = copy.deepcopy(record)

            for key in keys_to_transliterate:
                if record[key] in special_rules:
                    record_transliterated[key] = special_rules[record[key]]
                elif record_transliterated[key]:
                    record_transliterated[key] = translit(record_transliterated[key])

            writer.writerow(record_transliterated)


async def process(client, normalized_state_names):
    for state in normalized_state_names:
        siren_state[state] = {
            'enabled': False,
            'type:': 'state',
            'districts': {},
            'enabled_at': None,
            'disabled_at': None,
        }

        for district in normalized_state_names[state]:
            siren_state[state]['districts'][district] = {
                'enabled': False,
                'type': 'district',
                'communities': {},
                'enabled_at': None,
                'disabled_at': None,
            }

            for community in normalized_state_names[state][district]:
                siren_state[state]['districts'][district]['communities'][community] = {
                    'enabled': False,
                    'type': 'community',
                    'enabled_at': None,
                    'disabled_at': None,
                }

    output_data = []

    async for message in client.iter_messages(channel_name, reverse=True):
        if not message.message:
            continue

        is_activated, is_deactivated, affected_places = parse_message(message)
        if is_activated is None:
            print(f"Can't process message: {message.message}")
            continue

        for location_tuple in affected_places:
            record = update_state(message, location_tuple, is_activated)

            if record:
                output_data.append(record)

    if not output_data:
        print("Nothing to generate...")

    output_data.sort(key=lambda x: x['started_at'])

    write_csv(output_data)


async def process_full_data(client):
    normalized_states = get_normalized_states()
    patch_flat_list(normalized_states)
    await process(client, normalized_states)
