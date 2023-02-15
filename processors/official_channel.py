import csv
import datetime
import json
import logging
import pathlib
from typing import Optional

from telethon.tl.types import Message

from .tg_dataclasses import OfficialAirRaidAlertChannelAlert, PLACE_LEVEL

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# UK means ukrainian language code, not United Kingdom :)
data_uk_file_path = (
    pathlib.Path(__file__).parent.resolve() / "../datasets/official_data_uk.csv"
)
data_en_file_path = (
    pathlib.Path(__file__).parent.resolve() / "../datasets/official_data_en.csv"
)


class OfficialAirAlertProcessor:
    channel_name = "air_alert_ua"

    # State
    # key is place name in hashtag format, value is tuple (oblast name, raion name, hromada name, level)
    hash_states_by_name: dict[str, tuple[str, str, str, PLACE_LEVEL]] = {}

    active_alerts_by_location: dict[str, OfficialAirRaidAlertChannelAlert] = {}
    completed_alerts: list[OfficialAirRaidAlertChannelAlert] = []

    def __init__(self, client):
        self.client = client

        self.load_states()

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
            fieldnames = [
                "oblast",
                "raion",
                "hromada",
                "level",
                "started_at",
                "finished_at",
                "source",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for record in self.completed_alerts:
                writer.writerow(record.dict(lang=lang))

    def process_message(self, message: Message):
        hashed_location, is_activated, is_deactivated = self.parse_message(message)

        if not is_activated and not is_deactivated:
            logger.error("Can't parse %s, skipping...", message.message)
            return

        oblast_name, raion_name, hromada_name, level = self.hash_states_by_name[
            hashed_location
        ]

        if is_activated:
            if current_alert := self.active_alerts_by_location.get(hashed_location):
                # Looks like it was started some time ago, but there are no message when alert was completed
                more_than_3_hours_difference = (message.date - current_alert.started_at) > datetime.timedelta(hours=3)
                if more_than_3_hours_difference:
                    # Looks like it was not marked as completed, but another alert was started
                    # otherwise just rewrite this alert
                    current_alert.finished_at = current_alert.started_at + datetime.timedelta(hours=1)
                    self.completed_alerts.append(current_alert)

            alert = OfficialAirRaidAlertChannelAlert(
                started_at=message.date,
                oblast=oblast_name,
                raion=raion_name,
                hromada=hromada_name,
                level=level,
            )
            self.active_alerts_by_location[hashed_location] = alert

        if is_deactivated:
            if alert := self.active_alerts_by_location.get(hashed_location):
                alert.finished_at = message.date
                self.completed_alerts.append(alert)

                del self.active_alerts_by_location[hashed_location]

    @staticmethod
    def is_ignored_message(message: Message) -> bool:
        return "Тестовий Регіон" in message.message

    def parse_message(
        self, message: Message
    ) -> tuple[Optional[str], Optional[bool], Optional[bool]]:
        """
        :return: tuple (hashed location name, is_enabled, is_disabled)
        """
        # 🔴 16:29 Повітряна тривога в Донецька область
        # 🟢 17:02 Відбій тривоги в Донецька область.
        # 🟡 06:22 Відбій тривоги в Дніпропетровська область
        #          (тривога ще триває у якомусь районі)

        if self.is_ignored_message(message):
            logger.error("Message %s is ignored", message.message)
            return None, None, None

        first_line = message.message.split("\n")[0]

        # #Донецька_область
        # #м_Нікополь_та_Нікопольська_територіальна_громада
        last_line = message.message.split("\n")[-1].lower()

        if last_line == "#херсон":
            # Special rule for https://t.me/air_alert_ua/5538
            last_line = "#м_херсон_та_херсонська_територіальна_громада"

        if not self.hash_states_by_name.get(last_line):
            # TODO Raise an exception someday
            logger.error("Can't process %s", last_line)
            return None, None, None

        is_activated = ("Повітряна" in first_line) or ("🔴" in first_line)
        is_deactivated = ("Відбій" in first_line) or ("🟢" in first_line)

        if not is_activated and not is_deactivated:
            # TODO Raise an exception someday
            logging.info(
                "Can't parse siren state %s at %s. First line: %s",
                message.message,
                message.date,
                first_line,
            )
            return None, None, None

        return last_line, is_activated, is_deactivated

    @staticmethod
    def location_to_hashtag(location: str) -> str:
        # Івано-Франківськ => #ІваноФранківськ
        # Запорізька область => #Запорізька_область
        # м. Кривий Ріг... → м_Кривий_Ріг_та_Криворізька_територіальна_громада

        hashtag_value = (
            location.lower()
            .replace("-", "")
            .replace(" ", "_")
            .replace(".", "")
            .replace("'", "")
            .replace("’", "")
        )
        return f"#{hashtag_value}"

    def load_states(self):
        states_file_path = pathlib.Path(__file__).parent.resolve() / "states.json"

        with open(states_file_path, "r") as json_file:
            raw_states = json.load(json_file)

        for state in raw_states["states"]:
            state_name = state["stateName"]
            hashed_state_name = self.location_to_hashtag(state_name)
            self.hash_states_by_name[hashed_state_name] = (state_name, "", "", "oblast")

            for raion in state["districts"]:
                raion_name = raion["districtName"]
                hashed_raion_name = self.location_to_hashtag(raion_name)
                self.hash_states_by_name[hashed_raion_name] = (
                    state_name,
                    raion_name,
                    "",
                    "raion",
                )

                for hromada in raion["communities"]:
                    hromada_name = hromada["communityName"]
                    hashed_hromada_name = self.location_to_hashtag(hromada_name)

                    # There are hromadas with duplicated names, so adding only hromadas where sirens were used at least once.
                    # Other hromadas located far away from battlefield.
                    hromada_special_rules = {
                        # hromada: (raion, oblast)
                        "Широківська територіальна громада": ("Баштанський район", "Миколаївська область"),
                        "Воскресенська територіальна громада": ("Миколаївський район", "Миколаївська область"),
                        "Софіївська територіальна громада": ("Баштанський район", "Миколаївська область"),
                        "Костянтинівська територіальна громада": ("Миколаївський район", "Миколаївська область"),
                        "Привільненська територіальна громада": ("Баштанський район", "Миколаївська область"),
                        "Горохівська територіальна громада": ("Баштанський район", "Миколаївська область"),
                        "Гребінківська територіальна громада": ("Полтавська область", "Лубенський район"),
                        "Покровська територіальна громада": ("Покровський район", "Донецька область"),
                        "Лиманська територіальна громада": ("Краматорський район", "Донецька область"),
                        "Олександрівська територіальна громада": ("Вознесенський район", "Миколаївська область"),
                        "Золочівська територіальна громада": ("Богодухівський район", "Харківська область"),
                        "Українська територіальна громада": ("Обухівський район", "Київська область"),
                    }

                    if hromada_name in hromada_special_rules:
                        special_hromada = hromada_special_rules[hromada_name]
                        self.hash_states_by_name[hashed_hromada_name] = (
                            special_hromada[1],
                            special_hromada[0],
                            hromada_name,
                            "hromada",
                        )
                    else:
                        self.hash_states_by_name[hashed_hromada_name] = (
                            state_name,
                            raion_name,
                            hromada_name,
                            "hromada",
                        )
