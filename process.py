import csv
from datetime import timedelta
from typing import Optional

from telethon import TelegramClient
from telethon.tl.types import Message
from config import API_ID, API_HASH, CHANNEL_NAME

client = TelegramClient('air-raid-app', API_ID, API_HASH)

# Order matters (Київська > Київ)
city_keywords = {
    "Київська область": {"Київській", "Київської", "Київська"},
    "Київ": {'Київ', 'Києві', "Киев"},
    "Чернівецька область": {"Чернівці", "Чернівцях", "Чернівців", "Чернівців", "Чернівецька"},
    "Львівська область": {"Львів", "Львові", "Львіва", "Львівська", "Львівської", "Львівській"},
    "Вінницька область": {"Вінниця", "Вінниці", "Вінницькій", "Вінницька"},
    "Волинська область": {"Волинь", "Волинської", "Волинська", "Волині"},
    "Дніпропетровська область": {"Дніпро", "Дніпропетровській", "Дніпропетровська"},
    "Донецька область": {"Донецьк", "Донецької", "Донецька", "Маріуполь", "Маріуполь"},
    "Житомирська область": {"Житомир", "Житомирі", "Житомирська", "Житомирської"},
    "Чернігівська область": {"Чернігів", "Чернігові", "Чернігівська"},
    "Закарпатська область": {"Закарпаття", "Закарпатської", "Закарпатська"},
    "Запорізька область": {"Запоріжжя", "Запорізька", "Запоріжжі"},
    "Івано-Франківська область": {"Івано-Франківськ", "Івано-Франківській", "Івано-Франківська"},
    "Кіровоградська область": {"Кропивницький", "Кропивницьку", "Кіровоградська", "Кіровоградської", "Кіровоградщина"},
    "Луганська область": {"Луганськ", "Луганської", "Луганська", "Луганщина"},
    "Миколаївська область": {"Миколаїв", "Миколаєві", "Миколаївська", "Миколаївської"},
    "Одеська область": {"Одеса", "Одесі", "Одеська", "Одеської"},
    "Полтавська область": {"Полтава", "Полтаві", "Полтавська", "Полтавської"},
    "Рівненська область": {"Рівне", "Рівненської", "Рівненська"},
    "Черкаська область": {"Черкаси", "Черкаська", "Черкаській"},
    "Харківська область": {"Харків", "Харківська", "Харкові"},
    "Херсонська область": {"Херсон", "Херсонська", "Херсонській"},
    "Хмельницька область": {"Хмельницьк", "Хмельницька"},
    "Сумська область": {"Суми", "Сумська"},
    "Тернопільська область": {"Тернопіль", "Тернопільська"}
}

city_air_raid_siren_state = {
    city: False for city in city_keywords.keys()
}

air_raid_keywords = {
    # keyword: is air raid enabled
    "тривога": True,
    "відбій": False,
    "сирена": True,
    "сирени": True,
    "відміна": False,
    "небезпека": True,
    "в укриття": True,
}

ignore_keywords = [
    "триває"
]

naive_timedelta_interval = timedelta(minutes=30)


def is_ignored_message(message: Message) -> bool:
    """
    Returns True if it needed to skip this message from processing.
    Usually it's more like notifications than air raid siren is still active.

    :param message: Message to process
    :return: Bool is it needed to process or not
    """
    message_normalized = message.message.lower()

    return any(keyword.lower() in message_normalized for keyword in ignore_keywords)


def guess_region(message: Message) -> Optional[str]:
    """
    Returns region name of related region name.

    :param message: Message object to process
    :return: Region name or None if can't be determined
    """
    message_normalized = message.message.lower()

    for city, keywords in city_keywords.items():
        if any(keyword.lower() in message_normalized for keyword in keywords):
            return city

    return None


def guess_air_raid_state(message: Message) -> Optional[bool]:
    """
    Returns air raid siren state based on message and keywords.

    :param message: Message object to parse
    :return: Bool if enabled/disabled, None if can't be determined
    """
    message_normalized = message.message.lower()

    for keyword, is_enabled in air_raid_keywords.items():
        if keyword.lower() in message_normalized:
            return is_enabled

    return None


def write_csv(air_raid_data: list):
    with open('air-raid-dataset.csv', 'w', newline='') as csvfile:
        fieldnames = ['region', 'started_at', 'finished_at', 'naive']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for record in air_raid_data:
            writer.writerow(record)


async def main():
    output_data = []

    async for message in client.iter_messages(CHANNEL_NAME, reverse=True):
        if not message.message:
            continue

        if is_ignored_message(message):
            continue

        region = guess_region(message)

        if not region:
            continue

        print(f"Processing {region} at {message.date}...")

        is_air_raid_enabled = guess_air_raid_state(message)
        if is_air_raid_enabled is None:
            continue

        region_state_started_time = city_air_raid_siren_state[region]

        if is_air_raid_enabled:
            if region_state_started_time:
                # Looks like previous data is here, let's consider all air raid sirens within 30 minutes interval as duplicate
                naive_end_time = region_state_started_time + naive_timedelta_interval

                if message.date < naive_end_time:
                    # Looks like duplicate (might be messages with city + another one for region)
                    # so skip this message
                    continue

                # "Complete" manually uncompleted air raid siren
                # and create new record
                record = {'region': region, 'started_at': region_state_started_time, "finished_at": naive_end_time, "naive": True}
                output_data.append(record)

            city_air_raid_siren_state[region] = message.date
        else:
            if not region_state_started_time:
                continue

            # If air raid siren is disabled within 6 hours – it's the same time interval
            safe_time_interval = timedelta(hours=6)
            if message.date < (region_state_started_time + safe_time_interval):
                record = {'region': region, 'started_at': region_state_started_time, "finished_at": message.date, "naive": False}
                output_data.append(record)
            else:
                # Looks like something wrong with telegram bot since siren is disabled for more than 6 hours
                # Luckily we don't have it in real life, so create two new records with naive interval
                records = [
                    {'region': region, 'started_at': region_state_started_time,
                     "finished_at": region_state_started_time + naive_timedelta_interval, "naive": True},
                    {'region': region, 'started_at': message.date - naive_timedelta_interval, "finished_at": message.date, "naive": True}
                ]
                output_data.extend(records)

            city_air_raid_siren_state[region] = False

    if not output_data:
        print("Nothing to generate...")

    output_data.sort(key=lambda x: x['started_at'])

    write_csv(output_data)

with client:
    client.loop.run_until_complete(main())
