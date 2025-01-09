#!/usr/bin/env python3

"""
MT5 to TradeLocker Copier
-------------------------
This script monitors MetaTrader5 (MT5) for new and closed positions and replicates these
actions in TradeLocker using the TradeLocker Python client (TLAPI).

Key Features:
1. Authentication for both MT5 and TradeLocker.
2. Magic number filtering to determine which trades to copy.
3. Robust error handling and continuous operation.
4. Mapping between MT5 tickets and TradeLocker orders to prevent duplicate orders.

Ensure all prerequisites are met before running this script.
"""

import MetaTrader5 as mt5
import time
import os
import json
import traceback
from datetime import datetime as dt
from tradelocker import TLAPI  # Ensure this is correctly installed and accessible

# ------------------- Global Variables & Configuration -------------------
MAGIC_NUMBER = 15  # Only copy trades with this magic number

MT5_CREDENTIALS_FILE = "mt5_credentials.json"
TRADE_MAPPING_FILE = "ticket_to_tradelocker.json"  # Optional: Persist mapping between restarts

# ------------------- Trade Mapping -------------------
def load_trade_mapping(file_path):
    """
    Load the trade mapping from a JSON file.
    Returns a dictionary mapping MT5 ticket to TradeLocker order ID.
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                mapping = json.load(f)
            # Convert keys to integers
            mapping = {int(k): v for k, v in mapping.items()}
            print(f"[Mapping] Loaded existing trade mapping from {file_path}.")
            return mapping
        except Exception as e:
            print(f"[Mapping] Error loading mapping file: {e}. Starting with empty mapping.")
            return {}
    else:
        print(f"[Mapping] No existing mapping file found at {file_path}. Starting with empty mapping.")
        return {}

def save_trade_mapping(mapping, file_path):
    """
    Save the trade mapping to a JSON file.
    """
    try:
        with open(file_path, 'w') as f:
            # Convert keys to strings for JSON serialization
            json.dump({str(k): v for k, v in mapping.items()}, f, indent=4)
        print(f"[Mapping] Trade mapping saved to {file_path}.")
    except Exception as e:
        print(f"[Mapping] Error saving mapping file: {e}.")

# ------------------- MT5 Authentication -------------------
def login_to_mt5():
    """
    Logs into MT5 using credentials from the JSON file.
    Returns True if successful, False otherwise.
    """
    if not os.path.exists(MT5_CREDENTIALS_FILE):
        default_data = {
            "account_1": {
                "login": "YOUR_MT5_LOGIN",
                "password": "YOUR_MT5_PASSWORD",
                "server": "YOUR_MT5_SERVER"
            }
        }
        with open(MT5_CREDENTIALS_FILE, 'w') as f:
            json.dump(default_data, f, indent=4)
        print(f"[MT5] Created {MT5_CREDENTIALS_FILE}. Please fill in your MT5 credentials.")
        return False

    try:
        with open(MT5_CREDENTIALS_FILE, 'r') as f:
            creds = json.load(f)["account_1"]
    except Exception as e:
        print(f"[MT5] Error reading credentials: {e}")
        return False

    try:
        mt5.shutdown()
        if not mt5.initialize():
            print(f"[MT5] initialize() failed, error code={mt5.last_error()}")
            return False

        if not mt5.login(int(creds['login']), creds['password'], creds['server']):
            print(f"[MT5] Failed to login to account {creds['login']}")
            return False

        terminal_info = mt5.terminal_info()
        if terminal_info:
            print("[MT5] Terminal Info:")
            print(f"   Name: {terminal_info.name}")
            print(f"   Path: {terminal_info.path}")
            print(f"   Server: {terminal_info.server}")
            print(f"   Company: {terminal_info.company}")
        else:
            print("[MT5] Could not retrieve terminal_info().")

        print("[MT5] Successfully logged in.")
        return True

    except Exception as e:
        print(f"[MT5] Exception during login: {e}")
        return False

# ------------------- TradeLocker Authentication -------------------
def login_to_tradelocker():
    """
    Logs into TradeLocker using environment variables.
    Returns the TLAPI instance if successful, None otherwise.
    """
    tl_environment = os.environ.get("TRADERLOCKER_ENVIRONMENT")
    tl_username = os.environ.get("TRADERLOCKER_USERNAME")
    tl_password = os.environ.get("TRADERLOCKER_PASSWORD")
    tl_server = os.environ.get("TRADERLOCKER_SERVER")

    if not all([tl_environment, tl_username, tl_password, tl_server]):
        print("[TradeLocker] Missing environment variables. Please set TRADERLOCKER_ENVIRONMENT, TRADERLOCKER_USERNAME, TRADERLOCKER_PASSWORD, and TRADERLOCKER_SERVER.")
        return None

    try:
        tl = TLAPI(
            environment=tl_environment,
            username=tl_username,
            password=tl_password,
            server=tl_server,
            log_level="info"
        )
        print("[TradeLocker] Successfully logged in.")
        return tl
    except Exception as e:
        print(f"[TradeLocker] Exception during login: {e}")
        return None

# ------------------- Trade Copier Logic -------------------
def copy_trades(tl, ticket_to_tradelocker, mapping_file):
    """
    Monitors MT5 for new and closed positions and replicates them in TradeLocker.

    Args:
        tl (TLAPI): The TradeLocker API client.
        ticket_to_tradelocker (dict): Mapping from MT5 ticket to TradeLocker order details.
        mapping_file (str): File path to save/load the mapping.
    """
    old_tickets = set(ticket_to_tradelocker.keys())

    while True:
        try:
            current_positions = mt5.positions_get()
            current_tickets = {p.ticket for p in current_positions} if current_positions else set()

            # Detect new positions
            new_tickets = current_tickets - old_tickets
            for ticket in new_tickets:
                position = next((p for p in current_positions if p.ticket == ticket), None)
                if not position:
                    continue
                print(f"\n[MT5] New position detected: Ticket={position.ticket}, Symbol={position.symbol}, Type={'BUY' if position.type == mt5.ORDER_TYPE_BUY else 'SELL'}, Magic={position.magic}")

                if position.magic != MAGIC_NUMBER:
                    print(f"[MT5] Position magic number {position.magic} does not match {MAGIC_NUMBER}. Skipping.")
                    continue

                # Prepare TradeLocker order details
                tradelocker_order = {
                    "symbol": position.symbol,
                    "quantity": position.volume,
                    "side": 'buy' if position.type == mt5.ORDER_TYPE_BUY else 'sell',
                    "type": "market",  # Assuming market orders; adjust if needed
                    "timestamp": dt.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                # Place order in TradeLocker
                order_id = place_tradelocker_order(tl, tradelocker_order)
                if order_id:
                    print(f"[TradeLocker] Placed order ID {order_id} for MT5 Ticket {ticket}.")
                    ticket_to_tradelocker[ticket] = order_id
                    save_trade_mapping(ticket_to_tradelocker, mapping_file)
                else:
                    print(f"[TradeLocker] Failed to place order for MT5 Ticket {ticket}.")

            # Detect closed positions
            closed_tickets = old_tickets - current_tickets
            for ticket in closed_tickets:
                if ticket in ticket_to_tradelocker:
                    order_id = ticket_to_tradelocker[ticket]
                    print(f"[MT5] Position closed: Ticket={ticket}. Closing TradeLocker order ID={order_id}.")

                    # Close the TradeLocker order
                    success = close_tradelocker_order(tl, order_id)
                    if success:
                        print(f"[TradeLocker] Successfully closed order ID {order_id} for MT5 Ticket {ticket}.")
                        del ticket_to_tradelocker[ticket]
                        save_trade_mapping(ticket_to_tradelocker, mapping_file)
                    else:
                        print(f"[TradeLocker] Failed to close order ID {order_id} for MT5 Ticket {ticket}.")

            old_tickets = current_tickets

        except Exception as e:
            print(f"[Copier] Unexpected error: {e}")
            traceback.print_exc()

        time.sleep(2)  # Polling interval in seconds

# ------------------- Helper Functions -------------------
def place_tradelocker_order(tl, order_details):
    """
    Places an order in TradeLocker.

    Args:
        tl (TLAPI): The TradeLocker API client.
        order_details (dict): Details of the order to place.

    Returns:
        int or None: Order ID if successful, None otherwise.
    """
    try:
        instrument_id = tl.get_instrument_id_from_symbol_name(order_details['symbol'])
        quantity = order_details['quantity']
        side = order_details['side']
        order_type = order_details['type']

        order_id = tl.create_order(
            instrument_id=instrument_id,
            quantity=quantity,
            side=side,
            type_=order_type
        )
        return order_id
    except Exception as e:
        print(f"[TradeLocker] Exception while placing order: {e}")
        return None

def close_tradelocker_order(tl, order_id):
    """
    Closes an existing TradeLocker order.

    Args:
        tl (TLAPI): The TradeLocker API client.
        order_id (int): The TradeLocker order ID to close.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        success = tl.close_position(order_id=order_id)
        return success
    except Exception as e:
        print(f"[TradeLocker] Exception while closing order ID {order_id}: {e}")
        return False

# ------------------- Main Function -------------------
def main():
    """
    Main function to run the MT5 to TradeLocker copier.
    """
    # Initialize Trade Mapping
    mapping = load_trade_mapping(TRADE_MAPPING_FILE)

    # Initialize MT5
    while not login_to_mt5():
        print("[MAIN] Retrying MT5 login in 10 seconds...")
        time.sleep(10)

    # Initialize TradeLocker
    tl = None
    while not tl:
        tl = login_to_tradelocker()
        if not tl:
            print("[MAIN] Retrying TradeLocker login in 10 seconds...")
            time.sleep(10)

    # Start copying trades
    copy_trades(tl, mapping, TRADE_MAPPING_FILE)

if __name__ == "__main__":
    main()
