import os
import struct
import requests
import datetime
import csv
from lzma import LZMADecompressor, FORMAT_AUTO

class DukascopyTickDataDownloader:
    endpoint = "https://datafeed.dukascopy.com/datafeed/{symbol}/{year}/{month:02d}/{day:02d}/{hour:02d}h_ticks.bi5"
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    def __init__(
            self,
            symbol,
            start_date,
            end_date,
            base_output_dir='tick_data',
            real_ask=True,
            spread_value=0.0,
            include_volumes=False
    ):
        """
        :param symbol: Currency pair symbol (e.g., 'GBPUSD')
        :param start_date: Start date in MM-DD-YYYY format
        :param end_date: End date in MM-DD-YYYY format
        :param base_output_dir: The base directory where data subfolders will be created
        :param real_ask: If True, use the real ask from Dukascopy. If False, ask = bid + spread_value
        :param spread_value: The numerical spread to add to the bid if real_ask is False
        :param include_volumes: If True, store real ask_volume and bid_volume; if False, store them as blank
        """

        # 1) Parse and store user inputs
        self.symbol = symbol.upper()
        self.start_date = datetime.datetime.strptime(start_date, '%m-%d-%Y')
        self.end_date = datetime.datetime.strptime(end_date, '%m-%d-%Y')
        self.base_output_dir = base_output_dir

        # 2) Variables that define how ask is computed and whether volumes are included
        self.real_ask = real_ask
        self.spread_value = spread_value
        self.include_volumes = include_volumes

        # 3) Dukascopy data format constants
        self.data_format = '!3I2f'  # (timestamp_ms, ask_price, bid_price, ask_volume, bid_volume)
        # Note that in Dukascopy's bi5 format, ask_volume and bid_volume are floats,
        # but we will handle them as needed below.

        # 4) Dukascopy point value for each symbol
        # e.g., most currency pairs use 1e5, while USDRUB, XAGUSD, XAUUSD often use 1e3
        if self.symbol in ['USDRUB', 'XAGUSD', 'XAUUSD']:
            self.point_value = 1e3
        else:
            self.point_value = 1e5

        # 5) Create a unique subfolder for each download request
        #    This subfolder includes the date range and a timestamp for uniqueness
        date_range_str = f"{self.start_date.strftime('%Y%m%d')}_to_{self.end_date.strftime('%Y%m%d')}"
        timestamp_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        subfolder_name = f"{self.symbol}_{date_range_str}_{timestamp_str}"
        self.output_dir = os.path.join(self.base_output_dir, subfolder_name)

        # 6) Ensure the output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # 7) Define the CSV filename within this subfolder
        self.output_filename = os.path.join(self.output_dir, 'historical_tick_data.csv')

    def download_and_save_csv(self):
        """
        Main method that:
          - Opens a single CSV file for the entire date range
          - Iterates over each date and hour
          - Downloads and decompresses the data
          - Parses the data
          - Writes the final rows to the CSV file
        """
        # 1) Define the CSV columns. We will always have:
        #    timestamp, bid, ask, Flags (value=6)
        #    If user wants volumes, we add them; if not, we skip them or leave blank.
        if self.include_volumes:
            fieldnames = ['timestamp', 'bid', 'ask', 'Flags', 'bid_volume', 'ask_volume']
        else:
            fieldnames = ['timestamp', 'bid', 'ask', 'Flags']

        # 2) Open CSV file and set up the writer
        with open(self.output_filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # 3) Iterate from the start_date to the end_date
            current_date = self.start_date
            while current_date <= self.end_date:
                print(f"Processing date: {current_date.strftime('%Y-%m-%d')}")

                # For each date, check the 24 hours in that day
                for hour in range(24):
                    try:
                        data = self.download_hour_data(current_date, hour)
                        if data:
                            # Parse ticks
                            ticks = self.parse_ticks(data, current_date, hour)
                            # Write ticks to CSV
                            for tick in ticks:
                                # If volumes are included, we pass them, otherwise we skip
                                row_data = {
                                    'timestamp': tick['timestamp'],
                                    'bid': tick['bid'],
                                    'ask': tick['ask'],
                                    'Flags': 6
                                }

                                # Conditionally include volumes
                                if self.include_volumes:
                                    row_data['bid_volume'] = tick.get('bid_volume', '')
                                    row_data['ask_volume'] = tick.get('ask_volume', '')

                                writer.writerow(row_data)
                            print(f"  Hour {hour:02d}: Data saved.")
                        else:
                            print(f"  Hour {hour:02d}: No data.")
                    except Exception as e:
                        print(f"  Hour {hour:02d}: Error occurred - {e}")
                # Move on to the next date
                current_date += datetime.timedelta(days=1)

        print(f"All data saved to {self.output_filename}")

    def download_hour_data(self, date, hour):
        """
        Downloads the raw bi5 compressed file for a given date and hour,
        then returns the decompressed bytes.
        """
        url = self.endpoint.format(
            symbol=self.symbol,
            year=date.year,
            month=date.month - 1,  # Dukascopy months are zero-based
            day=date.day,
            hour=hour
        )
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200 and response.content:
            decompressed_data = self.decompress_data(response.content)
            return decompressed_data
        else:
            return None

    def decompress_data(self, compressed_data):
        """
        Decompresses the LZMA (.bi5) data from Dukascopy.
        """
        decompressor = LZMADecompressor(FORMAT_AUTO)
        try:
            return decompressor.decompress(compressed_data)
        except Exception as e:
            print(f"Decompression error: {e}")
            return None

    def parse_ticks(self, data, date, hour):
        """
        Parses the raw binary data into a list of dictionary items, each representing a tick.

        Depending on user settings:
          - If self.real_ask == True, we use the ask as in the feed.
          - If self.real_ask == False, we compute ask as bid + self.spread_value.
          - If self.include_volumes == True, we store actual volumes. Otherwise, store blanks.
          - 'Flags' is not directly stored here but is a constant 6 in the final CSV output.
        """
        ticks = []
        data_size = struct.calcsize(self.data_format)

        for offset in range(0, len(data), data_size):
            chunk = data[offset:offset + data_size]
            if len(chunk) == data_size:
                # Unpack the chunk
                timestamp_ms, ask_price, bid_price, ask_volume, bid_volume = struct.unpack(self.data_format, chunk)

                # Convert date + hour + ms offset to a proper datetime
                tick_time = date + datetime.timedelta(hours=hour, milliseconds=timestamp_ms)

                # Convert raw prices to decimal form
                real_bid = bid_price / self.point_value
                real_ask = ask_price / self.point_value

                # Decide how to handle ask based on user preference
                if self.real_ask:
                    final_ask = real_ask
                else:
                    final_ask = real_bid + self.spread_value

                # Decide how to handle volumes
                if self.include_volumes:
                    final_bid_volume = bid_volume
                    final_ask_volume = ask_volume
                else:
                    # We'll store empty strings for volumes if user doesn't want them
                    final_bid_volume = ''
                    final_ask_volume = ''

                tick_dict = {
                    'timestamp': tick_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],  # e.g., 2024-04-08 17:00:00.123
                    'bid': real_bid,
                    'ask': final_ask,
                    # We won't store the 'Flags' here, but in the CSV write process we set it to 6
                }

                # If volumes are included, attach them:
                if self.include_volumes:
                    tick_dict['bid_volume'] = final_bid_volume
                    tick_dict['ask_volume'] = final_ask_volume

                ticks.append(tick_dict)
        return ticks

# -----------------------------------------------------------------------------
# Main script logic
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Example usage of the updated Tick Downloader script.
    Prompts the user for:
      - Start date (MM-DD-YYYY)
      - End date (MM-DD-YYYY)
      - Whether to use real ask or rely on a spread
      - Spread value (if using a spread)
      - Whether or not to include volume data
    Everything else remains the same.
    """
    # 1) Prompt user for start and end dates
    start_date = input("Enter the start date (MM-DD-YYYY): ")
    end_date = input("Enter the end date (MM-DD-YYYY): ")

    # 2) Prompt for real ask or ask = bid + spread
    user_real_ask = input("Use real ask from Dukascopy? (y/n): ").strip().lower()
    if user_real_ask == 'y':
        real_ask_flag = True
        user_spread = 0.0
    else:
        real_ask_flag = False
        # Prompt user for how big the spread should be
        try:
            user_spread = float(input("Enter spread amount to add to bid: "))
        except ValueError:
            user_spread = 0.0
            print("Invalid spread input, defaulting to 0.0")

    # 3) Prompt whether we should store real volumes or leave blank
    user_include_volumes = input("Include real volumes? (y/n): ").strip().lower()
    if user_include_volumes == 'y':
        volumes_flag = True
    else:
        volumes_flag = False

    # 4) Prompt for symbol
    symbol = input("Enter the symbol (e.g., GBPUSD): ").strip().upper()
    if not symbol:
        symbol = 'GBPUSD'

    # 5) Instantiate and run
    downloader = DukascopyTickDataDownloader(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        base_output_dir='tick_data',
        real_ask=real_ask_flag,
        spread_value=user_spread,
        include_volumes=volumes_flag
    )
    downloader.download_and_save_csv()
