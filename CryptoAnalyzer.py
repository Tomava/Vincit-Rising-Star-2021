import urllib.request
import json
from datetime import datetime, timedelta
import tkinter

COIN_NAME = "bitcoin"
CURRENCY = "eur"
HELP = {"trend <start_date> <end_date>": "Longest downward trend",
        "highest <start_date> <end_date>": "Highest trading volume",
        "best_day <start_date> <end_date>": "Best days to buy and sell"}

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
        # Convert from milliseconds to seconds
        day = datetime.fromtimestamp(int(data[0]) / 1000).replace(hour=0, minute=0, second=0, microsecond=0)
        wanted_data = data[1]
        return day, wanted_data

    def fetch_data(self):
        """
        Fetches data from coingecko api with given parameters
        :return: dict
        """
        url = f"https://api.coingecko.com/api/v3/coins/{self.coin_name}/market_chart/range?vs_currency=" \
              f"{self.currency}&from={int(datetime.timestamp(self.start_date))}&to=" \
              f"{int(datetime.timestamp(self.end_date))}"
        with urllib.request.urlopen(url) as site:
            fetched_data = json.loads(site.read())
        parsed_data = {}
        # Remove duplicate data points for each day
        for key in fetched_data:
            # Add empty list for each key
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
            # Compare to -1 to not add first day of timeframe
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
        :return: tuple, (Datetime, Datetime)
        """
        fetched_data = self.fetch_data().get("prices")
        highest_delta = 0
        best_days = ()
        # Compare every day to all the next
        for i, from_data in enumerate(fetched_data):
            from_day, from_price = self.parse_day_and_price(from_data)
            for to_data in fetched_data[i + 1:]:
                to_day, to_price = self.parse_day_and_price(to_data)
                if to_price - from_price > highest_delta:
                    highest_delta = to_price - from_price
                    best_days = (from_day, to_day)
        return best_days

    def input_parser(self, input_text):
        """
        Parses command and parameters from input text
        :param input_text: str
        :return: str, Command output
        """
        input_parts = input_text.split(" ")
        output_text = ""
        if input_text.lower() == "quit" or input_text.lower() == "exit":
            return "QUIT"
        elif input_text.lower() == "help":
            for help_command in HELP:
                output_text += f"{help_command} : {HELP.get(help_command)}\n"
        # 3 arguments needed
        if len(input_parts) != 3:
            return output_text
        command = input_parts[0].lower()
        start_date = datetime.fromisoformat(input_parts[1])
        end_date = datetime.fromisoformat(input_parts[2]) + timedelta(hours=1)
        self.set_dates(start_date, end_date)
        # Handle commands (could use case in python 3.10)
        if command == "trend":
            longest_trend = self.get_downward_trend()
            output_text = f"In {COIN_NAME}’s historical data from CoinGecko, the price decreased {len(longest_trend)}" \
                          f" days in a row for the inputs from {start_date.strftime('%Y-%m-%d')} and to " \
                          f"{end_date.strftime('%Y-%m-%d')}"
        elif command == "highest":
            highest_volume = self.get_highest_volume()
            output_text = f"In {COIN_NAME}’s historical data from CoinGecko, the highest trading volume was " \
                          f"{highest_volume[1]} on {highest_volume[0]} for the inputs from " \
                          f"{start_date.strftime('%Y-%m-%d')} and to {end_date.strftime('%Y-%m-%d')}"
        elif command == "best_day":
            best_days = self.get_best_days()
            if len(best_days) == 0:
                output_text = f"{COIN_NAME.title()} should not be bought (or sold) for the inputs from " \
                              f"{start_date.strftime('%Y-%m-%d')} and to {end_date.strftime('%Y-%m-%d')}"
            else:
                output_text = f"Best pair of days to buy and sell {COIN_NAME} are {best_days[0]} and " \
                              f"{best_days[1]} for the inputs from {start_date.strftime('%Y-%m-%d')} and to " \
                              f"{end_date.strftime('%Y-%m-%d')}"
        return output_text.strip()


class UI:
    def __init__(self):
        # Setting up ui
        self.main_window = tkinter.Tk()
        self.backend = Backend()
        self.input_label_pane = tkinter.Frame(self.main_window)
        self.input_label_pane.grid(row=0, column=0)
        self.start_date_label = tkinter.Label(self.input_label_pane, text="Start date:")
        self.end_date_label = tkinter.Label(self.input_label_pane, text="End date:")
        self.start_date_label.pack(side=tkinter.LEFT, expand=True, fill=tkinter.BOTH)
        self.end_date_label.pack(side=tkinter.RIGHT, expand=True, fill=tkinter.BOTH)

        self.input_pane = tkinter.Frame(self.main_window)
        self.input_pane.grid(row=1, column=0)
        self.start_date_input = tkinter.Text(self.input_pane, height=1, width=10)
        self.start_date_input.insert(tkinter.END, "2020-01-01")
        self.start_date_input.pack(side=tkinter.LEFT, expand=True, fill=tkinter.BOTH)
        self.end_date_input = tkinter.Text(self.input_pane, height=1, width=10)
        self.end_date_input.insert(tkinter.END, "2020-12-31")
        self.end_date_input.pack(side=tkinter.RIGHT, expand=True, fill=tkinter.BOTH)

        self.trend_button = tkinter.Button(self.main_window, text="Longest downward trend",
                                           command=lambda: self.activate("trend"))
        self.highest_volume_button = tkinter.Button(self.main_window, text="Highest trading volume",
                                                    command=lambda: self.activate("highest"))
        self.best_days_button = tkinter.Button(self.main_window, text="Best days to buy and sell",
                                               command=lambda: self.activate("best_day"))
        self.trend_button.grid(row=2, column=0)
        self.highest_volume_button.grid(row=3, column=0)
        self.best_days_button.grid(row=4, column=0)
        self.output_box = tkinter.Label(self.main_window, text="Output")
        self.output_box.grid(row=5, column=0)
        self.main_window.grid_columnconfigure(0, minsize=1000)

        self.main_window.mainloop()

    def activate(self, command_str):
        output_text = self.backend.input_parser(f"{command_str} {self.start_date_input.get(1.0, 'end').strip()} "
                                                f"{self.end_date_input.get(1.0, 'end').strip()}")
        self.output_box.configure(text=output_text)


def main():
    ui = UI()
    backend = Backend()
    print("Command line usage")
    while True:
        output_text = backend.input_parser(input("> "))
        if output_text == "QUIT":
            print("Quitting")
            break
        else:
            print(output_text)
    # print(backend.input_parser("trend 2020-01-19 2020-01-21"))
    # print(backend.input_parser("trend 2020-03-01 2021-08-01"))
    # print(backend.input_parser("highest 2020-01-19 2020-01-21"))
    # print(backend.input_parser("highest 2020-03-01 2021-08-01"))
    # print(backend.input_parser("best_day 2020-01-19 2020-01-21"))
    # print(backend.input_parser("best_day 2020-03-01 2021-08-01"))


if __name__ == "__main__":
    main()
