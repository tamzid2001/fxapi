#!/usr/bin/env python3

"""
MT5 -> Robinhood Copier with Robust Exception Handling
------------------------------------------------------
1) Watches for new trades on an MT5 account, copying them to Robinhood as options trades:
   - If MT5 places a BUY, we buy a CALL (by default).
   - If MT5 places a SELL, we buy a PUT (by default).
2) Respects market hours (9:30am to 4:00pm EST, M-F).
3) Checks pattern day trade (PDT) constraints if the account < $25k.
4) Closes corresponding Robinhood positions if MT5 positions are closed.
5) Retries logins and gracefully handles exceptions in the main monitoring loop.
6) Passes the explicit 'rhs_account_number' to each .robinhood.orders call.

Note:
 - We add try/except around critical sections so the script 
   won't terminate on transient or unexpected errors.
 - If an error happens, we log it, sleep, and continue 
   rather than calling exit().
"""

import MetaTrader5 as mt5
import robin_stocks as rs
import time
import os
import json
import datetime
import pytz

from datetime import datetime as dt, timedelta, date

# ------------------- Global Variables -------------------
day_trades_count = {}  # in-memory dict for day trade usage
account_number = None  # we'll set after logging in
# Path to local 'accounts.json' for MT5 credentials
file_path = "accounts.json"

# ---------------------------------------------------------
# 1. Repeated login attempts for MT5
# ---------------------------------------------------------
def login_to_mt5_account_loop():
    """
    Repeatedly attempt to:
      1) Shutdown any existing MT5 connection
      2) Initialize
      3) Load credentials from file
      4) Log in

    If login fails, sleep and try again, indefinitely.
    """
    global file_path

    # Ensure credentials file exists, or create a default
    default_data = {
        "account_1": {
            "login": 0,
            "password": "password",
            "server": "server"
        }
    }
    if not os.path.exists(file_path):
        with open(file_path, 'w') as json_file:
            json.dump(default_data, json_file, indent=4)
        print(f"{file_path} created.\nPlease fill with correct MT5 account credentials!")
        # We won't exit; we'll keep trying, but realistically 
        # the user must fill credentials or the loop will be infinite:
        time.sleep(15)
        return False

    # Load credentials
    try:
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        account_1 = data["account_1"]
    except Exception as e:
        print(f"[MT5] Error loading credentials from {file_path}: {e}")
        time.sleep(15)
        return False

    # Attempt to log in
    try:
        mt5.shutdown()  # in case a session is open
        if not mt5.initialize():
            print(f"[MT5] initialize() failed, error code: {mt5.last_error()}")
            time.sleep(15)
            return False

        if not mt5.login(account_1['login'], account_1['password'], account_1['server']):
            print(f"[MT5] Failed to connect to account {account_1['login']}")
            time.sleep(15)
            return False

        print(f"[MT5] Connected to account {account_1['login']}")
        return True

    except Exception as ex:
        print(f"[MT5] Exception during login: {ex}")
        time.sleep(15)
        return False


# ---------------------------------------------------------
# 2. Repeated login attempts for Robinhood
# ---------------------------------------------------------
def login_to_robinhood_loop():
    """
    Repeatedly attempt to log in to Robinhood using environment 
    variables for user/password. If login fails, sleep and try again.
    Once logged in, retrieve the 'rhs_account_number' from the 
    user's profile.
    """
    global account_number

    r_user = os.environ.get("robinhood_username")
    r_pass = os.environ.get("robinhood_password")

    if not r_user or not r_pass:
        print("[ERROR] Robinhood credentials not found in env variables (robinhood_username, robinhood_password).")
        print("Sleeping 15s and will retry...")
        time.sleep(15)
        return False

    try:
        rs.robinhood.authentication.login(
            username=r_user,
            password=r_pass,
            expiresIn=86400,  # 24 hours
            by_sms=True
        )
        print("[Robinhood] Logged in successfully.")
    except Exception as ex:
        print(f"[Robinhood] Login failed: {ex}")
        print("Sleeping 15s and will retry...")
        time.sleep(15)
        return False

    # Attempt to load profile to get account_number
    try:
        profile_data = rs.robinhood.profiles.load_account_profile(info=None)
        local_acc_number = profile_data.get("rhs_account_number")
        # ensure it's a string
        local_acc_number = str(local_acc_number)
        account_number = local_acc_number
        print(f"[Robinhood] Using account_number='{account_number}'.")
    except Exception as ex:
        print(f"[Robinhood] Could not load profile or extract account_number: {ex}")
        print("Sleeping 15s and will retry...")
        time.sleep(15)
        return False

    return True


# ---------------------------------------------------------
# 3. Helper: Market Hours Check (9:30–16:00 EST, M-F)
# ---------------------------------------------------------
def is_market_open_now():
    """
    Returns True if the current time is between 9:30 AM and 4:00 PM 
    Eastern Time, Monday-Friday.
    """
    try:
        eastern = pytz.timezone('US/Eastern')
        now_est = dt.now(eastern)

        # 0=Mon ... 6=Sun
        if now_est.weekday() >= 5:
            return False

        open_time = now_est.replace(hour=9, minute=30, second=0, microsecond=0)
        close_time = now_est.replace(hour=16, minute=0, second=0, microsecond=0)
        return (now_est >= open_time) and (now_est <= close_time)

    except Exception as ex:
        print(f"[Market Hours Check] Error: {ex}")
        # If we can't determine, assume not open
        return False


# ---------------------------------------------------------
# 4. PDT Check if <25k
# ---------------------------------------------------------
def account_equity_and_pdt_check():
    """
    Returns (bool, reason). 
    If < 25k => only 3 day trades in a rolling 7 days.
    If >= 25k => no restriction.

    Will not raise an exception. If error, returns (False, reason).
    """
    global day_trades_count

    try:
        profile = rs.robinhood.profiles.load_account_profile(info=None)
        portfolio_cash_str = profile.get("portfolio_cash", "0")
        account_val = float(portfolio_cash_str)
    except Exception as ex:
        # If we can't load or parse, be safe => block new trades
        return (False, f"Error retrieving portfolio_cash from profile: {ex}")

    if account_val >= 25000:
        return True, "Account >= $25k, no PDT restrictions"

    # If < 25k, check in-memory day trades
    cutoff_date = dt.now() - timedelta(days=7)
    day_trades_in_7_days = 0
    for day_str, count in day_trades_count.items():
        try:
            day_dt = dt.strptime(day_str, "%Y-%m-%d")
            if day_dt >= cutoff_date:
                day_trades_in_7_days += count
        except:
            # skip any malformed keys
            continue

    if day_trades_in_7_days >= 3:
        return False, "PDT limit reached (3+ day trades in last 7 days)"

    return True, f"Used {day_trades_in_7_days} day trades in last 7 days"


# ---------------------------------------------------------
# 5. Generic function: place an option order (buy/sell)
# ---------------------------------------------------------
def place_robinhood_option_order(symbol, exp_date, strike, option_type,
                                 quantity, side, position_effect, limit_price):
    """
    Submits an options limit order via .robinhood.orders.
    side: 'buy' or 'sell'
    position_effect: 'open' or 'close'
    credit_or_debit: 'debit' if buying, 'credit' if selling
    """
    global account_number

    try:
        limit_price_str = f"{limit_price:.2f}"
        print(f"[RH] {side.upper()} {option_type.upper()} x{quantity}, "
              f"sym={symbol}, exp={exp_date}, strike={strike}, "
              f"posEffect={position_effect}, limit={limit_price_str}")

        if side.lower() == 'buy':
            # buy => credit_or_debit='debit'
            order_resp = rs.robinhood.orders.order_buy_option_limit(
                positionEffect=position_effect,
                credit_or_debit='debit',
                price=limit_price,
                symbol=symbol,
                quantity=quantity,
                expirationDate=exp_date,
                strike=strike,
                optionType=option_type,
                timeInForce='gfd',
                account_number=account_number
            )
        else:
            # sell => credit_or_debit='credit'
            order_resp = rs.robinhood.orders.order_sell_option_limit(
                positionEffect=position_effect,
                credit_or_debit='credit',
                price=limit_price,
                symbol=symbol,
                quantity=quantity,
                expirationDate=exp_date,
                strike=strike,
                optionType=option_type,
                timeInForce='gfd',
                account_number=account_number
            )

        return order_resp

    except Exception as ex:
        print(f"[RH] Error placing {side.upper()} {option_type.upper()} order: {ex}")
        return None


# ---------------------------------------------------------
# 6. Copy an MT5 position to Robinhood (Buy->Call, Sell->Put)
# ---------------------------------------------------------
def copy_mt5_trade_to_robinhood(trade):
    """
    If trade.type=BUY => place a 'buy' call,
       trade.type=SELL => place a 'buy' put.
    The strike is approximate the underlying's current price,
    with expiration = today's date.
    """
    try:
        if not is_market_open_now():
            print("[RH] Market CLOSED. Skipping open.")
            return None

        can_trade, reason = account_equity_and_pdt_check()
        if not can_trade:
            print(f"[RH] PDT/Equity check FAIL: {reason}")
            return None
        print(f"[RH] PDT/Equity check PASS: {reason}")

        # Map trade type
        if trade.type == mt5.ORDER_TYPE_BUY:
            side = 'buy'
            option_type = 'call'
        else:
            side = 'buy'
            option_type = 'put'

        quantity = int(trade.volume)
        symbol = "TSLA"
        today_str = date.today().strftime("%Y-%m-%d")

        # Underlying last price
        try:
            last_price_str = rs.robinhood.stocks.get_latest_price(symbol, includeExtendedHours=True)[0]
            last_price = float(last_price_str)
        except Exception as ex:
            print(f"[RH] Error getting underlying price: {ex}")
            return None

        strike_price = round(last_price, 2)

        # get best bid
        try:
            best_bid_list = rs.robinhood.options.find_options_by_expiration_and_strike(
                inputSymbols=symbol,
                expirationDate=today_str,
                strikePrice=str(strike_price),
                optionType=option_type,
                info='bid_price'
            )
            if not best_bid_list or best_bid_list[0] in (None, 'None'):
                print(f"[RH] No best bid found => {symbol}, {strike_price}, {option_type}")
                return None
            best_bid = float(best_bid_list[0])
        except Exception as e:
            print(f"[RH] Error fetching best bid: {e}")
            return None

        limit_price = 1.001 * best_bid  # slightly above best bid

        order_resp = place_robinhood_option_order(
            symbol=symbol,
            exp_date=today_str,
            strike=strike_price,
            option_type=option_type,
            quantity=quantity,
            side=side,
            position_effect='open',
            limit_price=limit_price
        )
        print("[RH] OPEN order response:", order_resp)
        if not order_resp:
            return None

        return {
            "symbol": symbol,
            "expiration_date": today_str,
            "strike": strike_price,
            "option_type": option_type,
            "quantity": quantity,
            "side": side
        }

    except Exception as ex:
        print(f"[copy_mt5_trade_to_robinhood] Unexpected error: {ex}")
        return None


# ---------------------------------------------------------
# 7. Close a Robinhood position
# ---------------------------------------------------------
def close_robinhood_position(rh_info):
    """
    If we 'bought to open', we 'sell to close'. 
    We'll fetch best ask, place slightly below that.
    """
    try:
        if not rh_info:
            print("[RH] No rh_info to close.")
            return None

        if not is_market_open_now():
            print("[RH] Market CLOSED. Skip close.")
            return None

        can_trade, reason = account_equity_and_pdt_check()
        if not can_trade:
            print(f"[RH] PDT/Equity check FAIL (closing): {reason}")
            return None
        print(f"[RH] PDT/Equity check PASS (closing): {reason}")

        symbol = rh_info["symbol"]
        exp_date = rh_info["expiration_date"]
        strike = rh_info["strike"]
        option_type = rh_info["option_type"]
        quantity = rh_info["quantity"]
        original_side = rh_info["side"]

        if original_side == 'buy':
            side_to_close = 'sell'
        else:
            side_to_close = 'buy'

        try:
            best_ask_list = rs.robinhood.options.find_options_by_expiration_and_strike(
                inputSymbols=symbol,
                expirationDate=exp_date,
                strikePrice=str(strike),
                optionType=option_type,
                info='ask_price'
            )
            if not best_ask_list or best_ask_list[0] in (None, 'None'):
                print(f"[RH] No best ask => {symbol}, strike={strike}, type={option_type}")
                return None
            best_ask = float(best_ask_list[0])
        except Exception as ex:
            print(f"[RH] Error fetching best ask (close): {ex}")
            return None

        limit_price = 0.995 * best_ask
        order_resp = place_robinhood_option_order(
            symbol=symbol,
            exp_date=exp_date,
            strike=strike,
            option_type=option_type,
            quantity=quantity,
            side=side_to_close,
            position_effect='close',
            limit_price=limit_price
        )
        print("[RH] CLOSE order response:", order_resp)
        return order_resp

    except Exception as ex:
        print(f"[close_robinhood_position] Unexpected error: {ex}")
        return None


# ---------------------------------------------------------
# 8. If close same day => day trade
# ---------------------------------------------------------
def record_day_trade_if_applicable(open_time):
    global day_trades_count
    try:
        now_day_str = dt.now().strftime("%Y-%m-%d")
        open_day_str = open_time.strftime("%Y-%m-%d")
        if now_day_str == open_day_str:
            day_trades_count.setdefault(now_day_str, 0)
            day_trades_count[now_day_str] += 1
            print(f"[PDT] Day trade count for {now_day_str} => {day_trades_count[now_day_str]}")
    except Exception as ex:
        print(f"[record_day_trade_if_applicable] Unexpected error: {ex}")


# ---------------------------------------------------------
# 9. Main monitoring loop
# ---------------------------------------------------------
def monitor_trades_forever():
    """
    1) Login loops for MT5 & Robinhood (retry until success).
    2) Then monitor new/closed trades in a loop indefinitely.
       - If we lose connection or something fails, we log
         the error, wait, attempt to re-login, and continue.
    """
    global day_trades_count

    # 9.1: Login loops for MT5 & Robinhood
    while True:
        if login_to_mt5_account_loop():
            print("[MAIN] Successfully logged into MT5.")
            break
        print("[MAIN] Retry MT5 login in 10s...")
        time.sleep(10)

    while True:
        if login_to_robinhood_loop():
            print("[MAIN] Successfully logged into Robinhood.")
            break
        print("[MAIN] Retry Robinhood login in 10s...")
        time.sleep(10)

    print("[MAIN] Ready to monitor trades...")

    # 9.2: Prepare to track existing positions
    old_tickets = set()
    try:
        # Wrap in try/except so if positions_get fails, we skip
        initial_positions = mt5.positions_get()
        if initial_positions:
            old_tickets = {p.ticket for p in initial_positions}
    except Exception as ex:
        print(f"[MT5] Error fetching initial positions: {ex}")
        old_tickets = set()

    # store: mt5_ticket => (rh_info, open_time)
    ticket_to_rh = {}

    # 9.3: Main monitoring loop
    while True:
        try:
            # Re-check or keep using an existing session
            # If a major error occurs, we might log out/in again.

            # Fetch current positions
            try:
                current_positions = mt5.positions_get()
            except Exception as ex:
                print(f"[MT5] Error in positions_get(): {ex}")
                time.sleep(5)
                continue  # skip this iteration

            current_tickets = set()
            if current_positions:
                current_tickets = {p.ticket for p in current_positions}

            # (A) new positions
            new_tickets = current_tickets - old_tickets
            for nt in new_tickets:
                pos = next((p for p in current_positions if p.ticket == nt), None)
                if not pos:
                    continue
                print(f"\n[MT5] New position => ticket={nt}, type={pos.type}, price={pos.price_current}")
                rh_info = copy_mt5_trade_to_robinhood(pos)
                if rh_info:
                    ticket_to_rh[nt] = (rh_info, dt.now())

            # (B) closed positions
            closed_tickets = old_tickets - current_tickets
            for ct in closed_tickets:
                if ct in ticket_to_rh:
                    print(f"[MT5] Position closed => ticket={ct}. Closing on RH...")
                    rh_info, open_time = ticket_to_rh[ct]
                    close_robinhood_position(rh_info)
                    record_day_trade_if_applicable(open_time)
                    del ticket_to_rh[ct]

            # Update old tickets
            old_tickets = current_tickets

        except Exception as ex:
            print(f"[MAIN LOOP] Unexpected error: {ex}")
            # Possibly re-init or re-login. We'll try a short wait
            time.sleep(10)

        # A brief sleep before next iteration
        time.sleep(2)


# ---------------------------------------------------------
# Main entry point
# ---------------------------------------------------------
if __name__ == "__main__":
    """
    We'll run monitor_trades_forever() which:
    1) Repeatedly attempts logins to MT5 and RH
    2) Monitors trades in an infinite loop, 
       handling errors along the way.
    """
    monitor_trades_forever()
