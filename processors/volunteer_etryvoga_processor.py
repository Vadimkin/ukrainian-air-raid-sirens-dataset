import csv
import datetime
import logging
import pathlib
from typing import Optional

from telethon.tl.types import Message

from .tg_dataclasses import ETryvogaChannelAlert

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# UK means ukrainian language code, not United Kingdom :)
data_uk_file_path = pathlib.Path(__file__).parent.resolve() / "../datasets/volunteer_data_uk.csv"
data_en_file_path = pathlib.Path(__file__).parent.resolve() / "../datasets/volunteer_data_en.csv"


# Order matters (Київська > Київ)
city_keywords = {
    "Київська область": {
        "Київській",
        "Київської",
        "Київська",
        "Ірпінь",
        "️Біла Церква",
        "Борщагівка",
    },
    "Київ": {"Київ", "Києві", "Киев", "Kyiv"},
    "Чернівецька область": {
        "Чернівці",
        "Чернівцях",
        "Чернівців",
        "Чернівців",
        "Чернівецька",
    },
    "Львівська область": {
        "Львів",
        "Львові",
        "Львіва",
        "Львівська",
        "Львівської",
        "Львівській",
        "Подільський",
        "Стрий",
        "Трускавець",
    },
    "Вінницька область": {"Вінниця", "Вінниці", "Вінницькій", "Вінницька"},
    "Волинська область": {
        "Волинь",
        "Волинської",
        "Волинська",
        "Волині",
        "Луцьк",
        "Луцьку",
    },
    "Дніпропетровська область": {
        "Дніпро",
        "Дніпропетровській",
        "Дніпропетровська",
        "Дніпрі",
        "Кривий Ріг",
    },
    "Донецька область": {"Донецьк", "Донецької", "Донецька", "Маріуполь", "Маріуполь"},
    "Житомирська область": {
        "Житомир",
        "Житомирі",
        "Житомирська",
        "Житомирської",
        "Бердичів",
    },
    "Чернігівська область": {"Чернігів", "Чернігові", "Чернігівська", "️Ніжин"},
    "Закарпатська область": {"Закарпаття", "Закарпатської", "Закарпатська"},
    "Запорізька область": {"Запоріжжя", "Запорізька", "Запоріжжі", "️Енергодар"},
    "Івано-Франківська область": {
        "Івано-Франківськ",
        "Івано-Франківській",
        "Івано-Франківська",
        "Івано-Франківщині",
        "Івано-Франківщина",
        "Калуш",
    },
    "Кіровоградська область": {
        "Кропивницький",
        "Кропивницьку",
        "Кіровоградська",
        "Кіровоградської",
        "Кіровоградщина",
        "Гайворон",
    },
    "Луганська область": {"Луганськ", "Луганської", "Луганська", "Луганщина"},
    "Миколаївська область": {
        "Миколаїв",
        "Миколаєві",
        "Миколаївська",
        "Миколаївської",
        "Миколіївської",
    },
    "Одеська область": {"Одеса", "Одесі", "Одеська", "Одеської", "Одещині"},
    "Полтавська область": {
        "Полтава",
        "Полтаві",
        "Полтавська",
        "Полтавської",
        "Лубни",
        "Миргород",
    },
    "Рівненська область": {"Рівне", "Рівненської", "Рівненська"},
    "Черкаська область": {
        "Черкаси",
        "Черкаська",
        "Черкаській",
        "Черкасах",
        "Умань",
        "Уманський",
    },
    "Харківська область": {"Харків", "Харківська", "Харкові", "Балаклія"},
    "Херсонська область": {"Херсон", "Херсонська", "Херсонській"},
    "Хмельницька область": {"Хмельницьк", "Хмельницька", "Хмельницький"},
    "Сумська область": {"Суми", "Сумська", "Охтир", "Киріківка"},
    "Тернопільська область": {"Тернопіль", "Тернопільська"},
}

air_raid_keywords = {
    # keyword: is air raid enabled
    # Order matters: from high to lower priority
    "відбій": False,
    "відміна": False,
    "кінець": False,
    "знято": False,
    "тривога": True,
    "тривоги": True,
    "тривогу": True,
    "тревога": True,
    "загроза": True,
    "сирена": True,
    "сирени": True,
    "загроза ракетного удару": True,
    "небезпека": True,
    "до укриттів": True,
    "в укриття": True,
}


class VolunteerEtryvogaProcessor:
    channel_name = "UkraineAlarmSignal"

    active_alerts_by_location: dict[str, ETryvogaChannelAlert] = {}
    completed_alerts: list[ETryvogaChannelAlert] = []

    def __init__(self, client):
        self.client = client

    async def process(self):
        previous_day = None

        # TODO Fetch latest days from .csv file and just append it
        async for message in self.client.iter_messages(self.channel_name, reverse=True):
            if not previous_day or previous_day != message.date.date():
                previous_day = message.date.date()
                logger.info("Processing day %s", previous_day)

            if not message.message:
                continue

            self.process_message(message)

        self.write()

    def write(self):
        self.completed_alerts.sort(key=lambda x: x.started_at)

        self.write_to_file(lang="uk")
        self.write_to_file(lang="en")

    def write_to_file(self, lang: str = "uk"):
        file_path = data_uk_file_path if lang == "uk" else data_en_file_path

        with open(file_path, "w", newline="") as csvfile:
            fieldnames = ["region", "started_at", "finished_at", "naive"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for record in self.completed_alerts:
                writer.writerow(record.dict(lang=lang))

    def process_message(self, message: Message):
        region_name, is_activated = self.parse_message(message)

        if region_name is None:
            return

        if is_activated:
            if current_alert := self.active_alerts_by_location.get(region_name):
                # Looks like it was started some time ago, but there are no message when alert was completed
                more_than_3_hours_difference = (message.date - current_alert.started_at) > datetime.timedelta(hours=3)
                if more_than_3_hours_difference:
                    # Looks like it was not marked as completed, but another alert was started
                    # otherwise just rewrite this alert
                    current_alert.finished_at = current_alert.started_at + datetime.timedelta(minutes=30)
                    current_alert.naive = True
                    self.completed_alerts.append(current_alert)

            alert = ETryvogaChannelAlert(
                started_at=message.date,
                region=region_name,
            )
            self.active_alerts_by_location[region_name] = alert

        else:
            if alert := self.active_alerts_by_location.get(region_name):
                alert.finished_at = message.date
                self.completed_alerts.append(alert)

                del self.active_alerts_by_location[region_name]

    @staticmethod
    def is_ignored_message(message: Message) -> bool:
        """
        Returns True if it needed to skip this message from processing.
        Usually it's more like notifications than air raid siren is still active.

        :param message: Message to process
        :return: Bool is it needed to process or not
        """
        message_normalized = message.message.lower()

        return "триває" in message_normalized

    def parse_message(self, message: Message) -> tuple[Optional[str], Optional[bool]]:
        """
        :return: tuple (region name, is_enabled)
        """
        if self.is_ignored_message(message):
            logger.error("Message %s (%s) is ignored", message.message, message.date)
            return None, None

        region = self.guess_region(message)

        if not region:
            logger.error("Can't parse region from %s (%s)", message.message, message.date)
            return None, None

        is_air_raid_enabled = self.guess_air_raid_state(message)
        if is_air_raid_enabled is None:
            logger.error("Can't parse siren state %s (%s)", message.message, message.date)
            return None, None

        return region, is_air_raid_enabled

    @staticmethod
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

    @staticmethod
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