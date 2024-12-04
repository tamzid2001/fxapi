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

    def __init__(self, symbol, start_date, end_date, base_output_dir='tick_data'):
        self.symbol = symbol.upper()
        self.start_date = datetime.datetime.strptime(start_date, '%m-%d-%Y')
        self.end_date = datetime.datetime.strptime(end_date, '%m-%d-%Y')
        self.base_output_dir = base_output_dir
        self.data_format = '!3I2f'  # Binary data format
        self.point_value = 1e5 if self.symbol not in ['USDRUB', 'XAGUSD', 'XAUUSD'] else 1e3

        # Create a unique subfolder for each download request
        date_range_str = f"{self.start_date.strftime('%Y%m%d')}_to_{self.end_date.strftime('%Y%m%d')}"
        timestamp_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        subfolder_name = f"{self.symbol}_{date_range_str}_{timestamp_str}"
        self.output_dir = os.path.join(self.base_output_dir, subfolder_name)

        # Ensure the output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Set the output filename within the subfolder
        self.output_filename = os.path.join(self.output_dir, 'historical_tick_data.csv')

    def download_and_save_csv(self):
        # Open the CSV file once and write all data to it
        with open(self.output_filename, 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'bid']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            current_date = self.start_date
            while current_date <= self.end_date:
                print(f"Processing date: {current_date.strftime('%Y-%m-%d')}")
                for hour in range(24):
                    try:
                        data = self.download_hour_data(current_date, hour)
                        if data:
                            ticks = self.parse_ticks(data, current_date, hour)
                            # Write ticks to CSV
                            for tick in ticks:
                                writer.writerow({'timestamp': tick['timestamp'], 'bid': tick['bid']})
                            print(f"  Hour {hour:02d}: Data saved.")
                        else:
                            print(f"  Hour {hour:02d}: No data.")
                    except Exception as e:
                        print(f"  Hour {hour:02d}: Error occurred - {e}")
                # Move to the next date
                current_date += datetime.timedelta(days=1)
        print(f"All data saved to {self.output_filename}")

    def download_hour_data(self, date, hour):
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
        decompressor = LZMADecompressor(FORMAT_AUTO)
        try:
            decompressed_data = decompressor.decompress(compressed_data)
            return decompressed_data
        except Exception as e:
            print(f"Decompression error: {e}")
            return None

    def parse_ticks(self, data, date, hour):
        ticks = []
        data_size = struct.calcsize(self.data_format)
        for offset in range(0, len(data), data_size):
            chunk = data[offset:offset + data_size]
            if len(chunk) == data_size:
                timestamp_ms, ask_price, bid_price, ask_volume, bid_volume = struct.unpack(self.data_format, chunk)
                tick_time = date + datetime.timedelta(hours=hour, milliseconds=timestamp_ms)
                tick = {
                    'timestamp': tick_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],  # Trim to milliseconds
                    'bid': bid_price / self.point_value
                }
                ticks.append(tick)
        return ticks

# Example usage:
if __name__ == "__main__":
    # User inputs for start date and end date in month-day-year format
    start_date = input("Enter the start date (MM-DD-YYYY): ")
    end_date = input("Enter the end date (MM-DD-YYYY): ")

    # Set the symbol
    symbol = 'GBPUSD'

    downloader = DukascopyTickDataDownloader(symbol, start_date, end_date)
    downloader.download_and_save_csv()
