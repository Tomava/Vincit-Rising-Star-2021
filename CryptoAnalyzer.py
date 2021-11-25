import urllib.request
import json
from datetime import datetime, timedelta

COIN_NAME = "bitcoin"
CURRENCY = "eur"


class Backend:
    def __init__(self):
        self.start_date = datetime.fromtimestamp(0)
        self.end_date = datetime.fromtimestamp(1)
        self.coin_name = COIN_NAME
        self.currency = CURRENCY

    def set_dates(self, start_date, end_date, coin_name=COIN_NAME, currency=CURRENCY):
        """
        :param start_date: Datetime
        :param end_date: Datetime
        :param coin_name: str
        :param currency: str
        """
        self.start_date = start_date
        self.end_date = end_date
        self.coin_name = coin_name
        self.currency = currency

    def parse_day_and_price(self, data):
        """
        Parses day and wanted data from a list of two
        :param data: list
        :return: Datetime, int
        """
        day = datetime.fromtimestamp(int(data[0]) / 1000).strftime("%Y-%m-%d")
        wanted_data = data[1]
        return day, wanted_data

    def fetch_data(self):
        """
        Fetches data from coingecko with given parameters
        :return: dict
        """
        url = f"https://api.coingecko.com/api/v3/coins/{self.coin_name}/market_chart/range?vs_currency=" \
              f"{self.currency}&from={int(datetime.timestamp(self.start_date))}&to=" \
              f"{int(datetime.timestamp(self.end_date))}"
        with urllib.request.urlopen(url) as site:
            fetched_data = json.loads(site.read())
        parsed_data = {}
        for key in fetched_data:
            parsed_data[key] = []
            iterated_days = set()
            for data in fetched_data.get(key):
                day, wanted_data = self.parse_day_and_price(data)
                # Only add one data point per day
                if day in iterated_days:
                    continue
                iterated_days.add(day)
                parsed_data.get(key).append(data)
        return parsed_data

    def get_downward_trend(self):
        """
        Get the longest downward trend from a given timeframe
        :return: list, contains tuples like (Datetime, int)
        """
        fetched_data = self.fetch_data().get("prices")
        longest_trend = []
        current_trend = []
        last_price = -1
        for data in fetched_data:
            day, price = self.parse_day_and_price(data)
            # Don't add first day
            if price < last_price != -1:
                current_trend.append(data)
            if len(current_trend) > len(longest_trend):
                longest_trend = current_trend.copy()
            if price >= last_price:
                current_trend.clear()
            last_price = price
        return longest_trend

    def get_highest_volume(self):
        """
        Find the day which has the highest volume of trade from a given timeframe
        :return: tuple, (Datetime, int)
        """
        fetched_data = self.fetch_data().get("total_volumes")
        highest_volume = (0, -1)
        for data in fetched_data:
            day, volume = self.parse_day_and_price(data)
            if volume > highest_volume[1]:
                highest_volume = (day, volume)
        return highest_volume

    def get_best_days(self):
        """
        Calculate the best days to buy and sell in a given timeframe
        O(n^2)
        :return: tuple, (Datetime, Datetime)
        """
        fetched_data = self.fetch_data().get("prices")
        highest_delta = 0
        best_days = ()
        # Compare every day to all the next
        for i, from_data in enumerate(fetched_data):
            from_day, from_price = self.parse_day_and_price(from_data)
            for to_data in fetched_data[i:]:
                to_day, to_price = self.parse_day_and_price(to_data)
                if to_price - from_price > highest_delta:
                    highest_delta = to_price - from_price
                    best_days = (from_day, to_day)
        return best_days

    def input_parser(self, input_text):
        """
        Parses command and parameters from input text
        :param input_text: str
        :return: bool, Successful command
        """
        input_parts = input_text.split(" ")
        if len(input_parts) != 3:
            return False
        command = input_parts[0].lower()
        start_date = datetime.fromisoformat(input_parts[1])
        end_date = datetime.fromisoformat(input_parts[2]) + timedelta(hours=1)
        self.set_dates(start_date, end_date)
        if command == "trend":
            longest_trend = self.get_downward_trend()
            print(f"In {COIN_NAME}’s historical data from CoinGecko, the price decreased {len(longest_trend)} days in a"
                  f" row for the inputs from {start_date.strftime('%Y-%m-%d')} and to {end_date.strftime('%Y-%m-%d')}")
        elif command == "highest":
            highest_volume = self.get_highest_volume()
            print(f"In {COIN_NAME}’s historical data from CoinGecko, the highest trading volume was {highest_volume[1]} on " 
                  f"{highest_volume[0]} for the inputs from {start_date.strftime('%Y-%m-%d')} and to "
                  f"{end_date.strftime('%Y-%m-%d')}")
        elif command == "best_day":
            best_days = self.get_best_days()
            if len(best_days) == 0:
                print(f"{COIN_NAME.title()} should not be bought (or sold) for the inputs from {start_date.strftime('%Y-%m-%d')} and"
                      f" to {end_date.strftime('%Y-%m-%d')}")
            else:
                print(f"Best pair of days to buy and sell {COIN_NAME} are {best_days[0]} and {best_days[1]} for the inputs"
                      f" from {start_date.strftime('%Y-%m-%d')} and to {end_date.strftime('%Y-%m-%d')}")
        return True


def main():
    backend = Backend()
    backend.input_parser("trend 2020-01-19 2020-01-21")
    backend.input_parser("trend 2020-03-01 2020-08-01")
    backend.input_parser("highest 2020-01-19 2020-01-21")
    backend.input_parser("highest 2020-03-01 2020-08-01")
    backend.input_parser("best_day 2020-01-19 2020-01-21")
    backend.input_parser("best_day 2020-03-01 2020-08-01")


if __name__ == "__main__":
    main()
