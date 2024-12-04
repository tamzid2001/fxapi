# Tick Data Downloader & FX API's (Tradelocker & DXTrade)

A Python script for downloading and saving tick data from Dukascopy for a specified currency pair and date range.

**Author**: Tamzid Ullah

---

## Description

`tickdownloader.py` is a Python script that allows you to download tick data (timestamps and bid prices) for a given currency pair from the Dukascopy data feed over a specified date range. The script organizes each download request into its own subfolder for better data management.

---

## Features

- **Flexible Date Range**: Input a start and end date in `MM-DD-YYYY` format to download data over multiple days.
- **Hourly Data**: Downloads tick data for each hour within the specified date range.
- **Customizable Output**: Saves data with only the `timestamp` and `bid` price columns for simplicity.
- **Organized Storage**: Each download request is stored in a unique subfolder to keep data organized.
- **Supports Multiple Symbols**: Easily change the currency pair symbol to download different instruments.

---

## Requirements

- Python 3.x
- `requests` library
- Standard libraries: `datetime`, `csv`, `os`, `struct`, `lzma`

---

## Installation

### Clone or Download the Repository

Clone the repository or download the `tickdownloader.py` file directly.

```bash
git clone https://github.com/yourusername/tickdata_downloader.git
```

### Navigate to the Directory

```bash
cd tickdata_downloader
```

### Install Required Python Packages

Ensure you have the `requests` library installed:

```bash
pip install requests
```

---

## Usage

### 1. Run the Script

Execute the script using Python:

```bash
python tickdownloader.py
```

### 2. Input the Start and End Dates

When prompted, enter the start date and end date in `MM-DD-YYYY` format:

```
Enter the start date (MM-DD-YYYY): 04-08-2024
Enter the end date (MM-DD-YYYY): 04-10-2024
```

### 3. Wait for the Download to Complete

The script will process each date and hour, displaying progress messages:

```
Processing date: 2024-04-08
  Hour 00: Data saved.
  Hour 01: Data saved.
  ...
All data saved to tick_data/GBPUSD_20240408_to_20240410_20231203_204512/historical_tick_data.csv
```

### 4. Access the Downloaded Data

The tick data is saved in a CSV file within a uniquely named subfolder inside the `tick_data` directory.

**Example Directory Structure:**

```
tick_data/
└── GBPUSD_20240408_to_20240410_20231203_204512/
    └── historical_tick_data.csv
```

---

## Customization

### Changing the Currency Pair Symbol

To download data for a different currency pair, modify the `symbol` variable in the script:

```python
# Set the symbol
symbol = 'EURUSD'  # Change to your desired symbol
```

### Adjusting the Base Output Directory

To change the base directory where data is saved, modify the `base_output_dir` parameter when creating an instance of the downloader:

```python
downloader = DukascopyTickDataDownloader(symbol, start_date, end_date, base_output_dir='my_custom_data_dir')
```

### Including Additional Data Columns

If you want to include more data columns such as `ask`, `ask_volume`, or `bid_volume`, adjust the `fieldnames` list and the `parse_ticks` method:

- **Modify Field Names:**

  ```python
  fieldnames = ['timestamp', 'bid', 'ask', 'bid_volume', 'ask_volume']
  ```

- **Update the `parse_ticks` Method:**

  Include the additional fields in the `tick` dictionary:

  ```python
  tick = {
      'timestamp': tick_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
      'bid': bid_price / self.point_value,
      'ask': ask_price / self.point_value,
      'bid_volume': bid_volume,
      'ask_volume': ask_volume
  }
  ```

- **Adjust the `writer.writerow` Call:**

  ```python
  writer.writerow(tick)
  ```

---

## Notes

- **Data Volume**: Downloading tick data over multiple days can result in large files. Ensure you have sufficient disk space and a stable internet connection.
- **Network Usage**: Be aware of your data usage, especially if on a limited or metered connection.
- **Terms of Service**: Ensure compliance with Dukascopy's terms of service regarding data usage and automated downloads.

## License

This project is licensed under the MIT License.

---

## Contact

For questions or comments, please contact Tamzid Ullah.

## Important Considerations

- **Compliance with Dukascopy's Terms**: Before using this script, please make sure you comply with Dukascopy's terms of service regarding data access and usage.
- **Data Usage**: Be responsible with the amount of data you download to avoid overloading the server or violating any rate limits.

---

If you have any questions or need further assistance with the script, feel free to reach out!

# TradeLocker and DXtrade API Integration

This repository contains the implementation of API endpoints for both **TradeLocker** and **DXtrade** trading platforms. This README provides detailed documentation for each API endpoint, including usage examples, parameters, and expected responses.

---

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Authentication](#authentication)
  - [Token Authentication](#token-authentication)
  - [HMAC Authentication](#hmac-authentication)
- [TradeLocker API Endpoints](#tradelocker-api-endpoints)
  - [Accounts and Positions](#accounts-and-positions)
    - [GET /trade/accounts/:accountId/positions](#get-tradeaccountsaccountidpositions)
  - [Instruments and Sessions](#instruments-and-sessions)
    - [GET /trade/instruments/:tradableInstrumentId](#get-tradeinstrumentstradableinstrumentid)
    - [GET /trade/sessions/:sessionId](#get-tradesessionssessionid)
  - [Market Data](#market-data)
    - [GET /trade/dailyBar](#get-tradedailybar)
    - [GET /trade/depth](#get-tradedepth)
    - [GET /trade/history](#get-tradehistory)
    - [GET /trade/quotes](#get-tradequotes)
  - [Trading](#trading)
    - [POST /trade/accounts/:accountId/orders](#post-tradeaccountsaccountidorders)
    - [DELETE /trade/accounts/:accountId/orders](#delete-tradeaccountsaccountidorders)
    - [DELETE /trade/accounts/:accountId/positions](#delete-tradeaccountsaccountidpositions)
    - [DELETE /trade/orders/:orderId](#delete-tradeordersorderid)
    - [PATCH /trade/orders/:orderId](#patch-tradeordersorderid)
    - [DELETE /trade/positions/:positionId](#delete-tradepositionspositionid)
    - [PATCH /trade/positions/:positionId](#patch-tradepositionspositionid)
- [DXtrade API Endpoints](#dxtrade-api-endpoints)
  - [Authentication & Authorization](#authentication--authorization)
    - [POST /login](#post-login)
    - [POST /loginByToken](#post-loginbytoken)
    - [POST /ping](#post-ping)
    - [POST /logout](#post-logout)
  - [Trading](#trading-1)
    - [POST /accounts/:accountCode/orders](#post-accountsaccountcodeorders)
    - [PUT /accounts/:accountCode/orders](#put-accountsaccountcodeorders)
    - [DELETE /accounts/:accountCode/orders/:orderCode](#delete-accountsaccountcodeordersordercode)
  - [Reference Data](#reference-data)
    - [GET /instruments/:symbol](#get-instrumentssymbol)
    - [GET /instruments/type/:type](#get-instrumentstypetype)
    - [GET /instruments/query](#get-instrumentsquery)
  - [Users and Accounts](#users-and-accounts)
    - [GET /users/:username](#get-usersusername)
    - [GET /accounts/:accountCode/portfolio](#get-accountsaccountcodeportfolio)
    - [GET /accounts/:accountCode/positions](#get-accountsaccountcodepositions)
    - [GET /accounts/:accountCode/orders](#get-accountsaccountcodeorders)
    - [GET /accounts/:accountCode/transfers](#get-accountsaccountcodetransfers)
    - [GET /accounts/:accountCode/events](#get-accountsaccountcodeevents)
  - [Market Data](#market-data-1)
    - [POST /marketdata](#post-marketdata)
  - [Conversion Rates](#conversion-rates)
    - [POST /conversionRates](#post-conversionrates)
- [Best Practices](#best-practices)
- [Contributing](#contributing)
- [License](#license)

---

## Introduction

This project provides a Node.js application using Express.js to interact with the TradeLocker and DXtrade APIs. It includes:

- Implementation of all major API endpoints for both platforms.
- Middleware for handling authentication (Token and HMAC).
- Comprehensive documentation for each endpoint.
- Examples for request and response formats.

---

## Getting Started

### Prerequisites

- **Node.js** (v12 or higher)
- **npm** (Node Package Manager)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

2. **Install dependencies**

   ```bash
   npm install
   ```

3. **Set environment variables**

   Create a `.env` file in the root directory and add the following:

   ```env
   PORT=3000
   TRADELOCKER_API_BASE_URL=https://api.tradelocker.com
   DXTRADE_API_BASE_URL=https://demo.dx.trade/dxsca-web
   ```

4. **Start the server**

   ```bash
   npm start
   ```

   The server will run on `http://localhost:3000`.

---

## Authentication

Both TradeLocker and DXtrade APIs require authentication for most endpoints.

### Token Authentication

For Token Authentication, you must include the `Authorization` header in your requests:

```
Authorization: Bearer {accessToken}
```

- Obtain `accessToken` through the authentication process provided by the platform.
- The `accNum` header is also required for certain endpoints.

### HMAC Authentication

For HMAC Authentication, include the following header in your requests:

```
Authorization: DXAPI principal="<API principal>",timestamp=<timestamp>,hash="<HMAC hash>"
```

- `API principal`: Your public API token.
- `timestamp`: UNIX milliseconds since epoch.
- `HMAC hash`: The hash calculated using your private token and request details.

---

## TradeLocker API Endpoints

### Accounts and Positions

#### GET `/trade/accounts/:accountId/positions`

Retrieve the current positions for a specific account.

- **URL Parameters:**
  - `accountId` (integer): Identifier of the account.
- **Headers:**
  - `Authorization`: `Bearer {accessToken}`
  - `accNum`: Account number.

**Example Request:**

```http
GET /trade/accounts/1234/positions HTTP/1.1
Host: your-server.com
Authorization: Bearer your_access_token
accNum: your_accNum
```

**Response:**

```json
{
  "d": [
    {
      "asset": "string",
      "buyAmount": 0,
      "buyPrice": 0,
      "closeTime": "2024-10-28T06:56:44.262Z",
      "commission": 0,
      "currency": "string",
      "id": 0,
      "instrument": "string",
      "invested": 0,
      "investment": 0,
      "isBuy": true,
      "isOvernight": true,
      "multiplier": 0,
      "openTime": "2024-10-28T06:56:44.262Z",
      "pnl": 0,
      "pnlPercentage": 0,
      "positionId": "string",
      "qty": 0,
      "sellAmount": 0,
      "sellPrice": 0,
      "status": "string",
      "swap": 0,
      "takeProfit": 0,
      "tradeSessionId": 0,
      "tradeSessionStatusId": 0,
      "tradableInstrumentId": 0
    }
  ],
  "s": "ok"
}
```

---

### Instruments and Sessions

#### GET `/trade/instruments/:tradableInstrumentId`

Get detailed information about an instrument.

- **URL Parameters:**
  - `tradableInstrumentId` (integer): Identifier of the instrument.
- **Headers:**
  - `Authorization`: `Bearer {accessToken}`
  - `accNum`: Account number.
- **Query Parameters:**
  - `routeId` (integer): Route identifier (required).
  - `locale` (string): Locale (optional).

**Example Request:**

```http
GET /trade/instruments/5678?routeId=1&locale=en HTTP/1.1
Host: your-server.com
Authorization: Bearer your_access_token
accNum: your_accNum
```

**Response:**

```json
{
  "d": {
    "barSource": "ASK",
    "baseCurrency": "string",
    "betSize": 0,
    // Additional instrument details...
  },
  "s": "ok"
}
```

---

#### GET `/trade/sessions/:sessionId`

Get detailed information about a trade session.

- **URL Parameters:**
  - `sessionId` (integer): Identifier of the trade session.
- **Headers:**
  - `Authorization`: `Bearer {accessToken}`
  - `accNum`: Account number.

**Example Request:**

```http
GET /trade/sessions/123 HTTP/1.1
Host: your-server.com
Authorization: Bearer your_access_token
accNum: your_accNum
```

**Response:**

```json
{
  "d": {
    "blockTrading": true,
    "holidays": [
      {
        "date": "2024-10-27",
        "name": "string",
        // Additional session details...
      }
    ],
    // More session data...
  },
  "s": "ok"
}
```

---

### Market Data

#### GET `/trade/dailyBar`

Get the current daily bar for a financial instrument.

- **Headers:**
  - `Authorization`: `Bearer {accessToken}`
  - `accNum`: Account number.
- **Query Parameters:**
  - `routeId` (integer): Route identifier (required).
  - `barType` (string): Defines the OHCL data source (required).
  - `tradableInstrumentId` (integer): Instrument identifier (required).

**Example Request:**

```http
GET /trade/dailyBar?routeId=1&barType=ASK&tradableInstrumentId=12345 HTTP/1.1
Host: your-server.com
Authorization: Bearer your_access_token
accNum: your_accNum
```

**Response:**

```json
{
  "d": {
    "c": 0,
    "h": 0,
    "l": 0,
    "o": 0,
    "v": 0
  },
  "s": "ok"
}
```

---

#### GET `/trade/depth`

Get the current depth of the market for the instrument.

- **Headers:**
  - `Authorization`: `Bearer {accessToken}`
  - `accNum`: Account number.
- **Query Parameters:**
  - `routeId` (integer): Route identifier (required).
  - `tradableInstrumentId` (integer): Instrument identifier (required).

**Example Request:**

```http
GET /trade/depth?routeId=1&tradableInstrumentId=12345 HTTP/1.1
Host: your-server.com
Authorization: Bearer your_access_token
accNum: your_accNum
```

**Response:**

```json
{
  "d": {
    "asks": [
      [0]
    ],
    "bids": [
      [0]
    ]
  },
  "s": "ok"
}
```

---

#### GET `/trade/history`

Get historical bars for an instrument.

- **Headers:**
  - `Authorization`: `Bearer {accessToken}`
  - `accNum`: Account number.
- **Query Parameters:**
  - `routeId` (integer): Route identifier (required).
  - `from` (integer): Unix timestamp in milliseconds (required).
  - `to` (integer): Unix timestamp in milliseconds (required).
  - `resolution` (string): Symbol resolution (required).
  - `tradableInstrumentId` (integer): Instrument identifier (required).

**Example Request:**

```http
GET /trade/history?routeId=1&from=1622505600000&to=1625097600000&resolution=1D&tradableInstrumentId=12345 HTTP/1.1
Host: your-server.com
Authorization: Bearer your_access_token
accNum: your_accNum
```

**Response:**

```json
{
  "d": {
    "barDetails": [
      {
        "c": 0,
        "h": 0,
        "l": 0,
        "o": 0,
        "t": 0,
        "v": 0
      }
    ]
  },
  "s": "ok"
}
```

---

#### GET `/trade/quotes`

Get current prices of the instrument.

- **Headers:**
  - `Authorization`: `Bearer {accessToken}`
  - `accNum`: Account number.
- **Query Parameters:**
  - `routeId` (integer): Route identifier (required).
  - `tradableInstrumentId` (integer): Instrument identifier (required).

**Example Request:**

```http
GET /trade/quotes?routeId=1&tradableInstrumentId=12345 HTTP/1.1
Host: your-server.com
Authorization: Bearer your_access_token
accNum: your_accNum
```

**Response:**

```json
{
  "d": {
    "ap": 0,
    "as": 0,
    "bp": 0,
    "bs": 0
  },
  "s": "ok"
}
```

---

### Trading

#### POST `/trade/accounts/:accountId/orders`

Place a new order.

- **URL Parameters:**
  - `accountId` (integer): Account identifier.
- **Headers:**
  - `Authorization`: `Bearer {accessToken}`
  - `accNum`: Account number.
  - `Content-Type`: `application/json`
- **Body Parameters:**

  ```json
  {
    "price": 0,
    "qty": 0,
    "routeId": 0,
    "side": "buy",
    "strategyId": "string",
    "stopLoss": 0,
    "stopLossType": "absolute",
    "stopPrice": 0,
    "takeProfit": 0,
    "takeProfitType": "absolute",
    "trStopOffset": 0,
    "tradableInstrumentId": 0,
    "type": "limit",
    "validity": "GTC"
  }
  ```

**Example Request:**

```http
POST /trade/accounts/1234/orders HTTP/1.1
Host: your-server.com
Authorization: Bearer your_access_token
accNum: your_accNum
Content-Type: application/json

{
  "qty": 100,
  "routeId": 1,
  "side": "buy",
  "validity": "GTC",
  "type": "limit",
  "tradableInstrumentId": 5678,
  "price": 1.2345
}
```

**Response:**

```json
{
  "d": {
    "orderId": "1"
  },
  "s": "ok"
}
```

---

#### DELETE `/trade/accounts/:accountId/orders`

Cancel all existing orders.

- **URL Parameters:**
  - `accountId` (integer): Account identifier.
- **Headers:**
  - `Authorization`: `Bearer {accessToken}`
  - `accNum`: Account number.
- **Query Parameters:**
  - `tradableInstrumentId` (integer): Instrument filter (optional).

**Example Request:**

```http
DELETE /trade/accounts/1234/orders?tradableInstrumentId=5678 HTTP/1.1
Host: your-server.com
Authorization: Bearer your_access_token
accNum: your_accNum
```

**Response:**

```json
{
  "s": "ok"
}
```

---

#### DELETE `/trade/accounts/:accountId/positions`

Place orders to close all positions.

- **URL Parameters:**
  - `accountId` (integer): Account identifier.
- **Headers:**
  - `Authorization`: `Bearer {accessToken}`
  - `accNum`: Account number.
- **Query Parameters:**
  - `tradableInstrumentId` (integer): Instrument filter (optional).

**Example Request:**

```http
DELETE /trade/accounts/1234/positions?tradableInstrumentId=5678 HTTP/1.1
Host: your-server.com
Authorization: Bearer your_access_token
accNum: your_accNum
```

**Response:**

```json
{
  "d": {
    "positions": [
      ["string"]
    ]
  },
  "s": "ok"
}
```

---

#### DELETE `/trade/orders/:orderId`

Cancel an existing order.

- **URL Parameters:**
  - `orderId` (integer): Order identifier.
- **Headers:**
  - `Authorization`: `Bearer {accessToken}`
  - `accNum`: Account number.

**Example Request:**

```http
DELETE /trade/orders/9876 HTTP/1.1
Host: your-server.com
Authorization: Bearer your_access_token
accNum: your_accNum
```

**Response:**

```json
{
  "s": "ok"
}
```

---

#### PATCH `/trade/orders/:orderId`

Modify an existing order.

- **URL Parameters:**
  - `orderId` (integer): Order identifier.
- **Headers:**
  - `Authorization`: `Bearer {accessToken}`
  - `accNum`: Account number.
  - `Content-Type`: `application/json`
- **Body Parameters:**

  ```json
  {
    "price": 0,
    "qty": 0,
    "stopLoss": 0,
    "stopLossType": "absolute",
    "stopPrice": 0,
    "takeProfit": 0,
    "takeProfitType": "absolute",
    "trStopOffset": 0,
    "validity": "GTC"
  }
  ```

**Example Request:**

```http
PATCH /trade/orders/9876 HTTP/1.1
Host: your-server.com
Authorization: Bearer your_access_token
accNum: your_accNum
Content-Type: application/json

{
  "price": 1.2340,
  "qty": 150
}
```

**Response:**

```json
{
  "s": "ok"
}
```

---

#### DELETE `/trade/positions/:positionId`

Place an order to close an existing position.

- **URL Parameters:**
  - `positionId` (integer): Position identifier.
- **Headers:**
  - `Authorization`: `Bearer {accessToken}`
  - `accNum`: Account number.
  - `Content-Type`: `application/json`
- **Body Parameters:**

  ```json
  {
    "qty": 0
  }
  ```

**Example Request:**

```http
DELETE /trade/positions/56789 HTTP/1.1
Host: your-server.com
Authorization: Bearer your_access_token
accNum: your_accNum
Content-Type: application/json

{
  "qty": 50
}
```

**Response:**

```json
{
  "s": "ok"
}
```

---

#### PATCH `/trade/positions/:positionId`

Modify an existing position's stop loss, take profit, or both.

- **URL Parameters:**
  - `positionId` (integer): Position identifier.
- **Headers:**
  - `Authorization`: `Bearer {accessToken}`
  - `accNum`: Account number.
  - `Content-Type`: `application/json`
- **Body Parameters:**

  ```json
  {
    "stopLoss": 0,
    "takeProfit": 0,
    "trailingOffset": 0
  }
  ```

**Example Request:**

```http
PATCH /trade/positions/56789 HTTP/1.1
Host: your-server.com
Authorization: Bearer your_access_token
accNum: your_accNum
Content-Type: application/json

{
  "stopLoss": 1.2300,
  "takeProfit": 1.2500
}
```

**Response:**

```json
{
  "s": "ok"
}
```

---

## DXtrade API Endpoints

### Authentication & Authorization

#### POST `/login`

Creates a Token Authentication session token.

- **Headers:**
  - `Content-Type`: `application/json`
- **Body Parameters:**

  ```json
  {
    "username": "user1",
    "domain": "example.com",
    "password": "pass123"
  }
  ```

**Example Request:**

```http
POST /login HTTP/1.1
Host: your-server.com
Content-Type: application/json

{
  "username": "user1",
  "domain": "example.com",
  "password": "pass123"
}
```

**Response:**

```json
{
  "token": "your_generated_token"
}
```

---

#### POST `/loginByToken`

Creates a Token Authentication session token using SSO token.

- **Headers:**
  - `Content-Type`: `application/json`
- **Body Parameters:**

  ```json
  {
    "username": "user1",
    "domain": "example.com",
    "token": "SSO_token_here"
  }
  ```

**Example Request:**

```http
POST /loginByToken HTTP/1.1
Host: your-server.com
Content-Type: application/json

{
  "username": "user1",
  "domain": "example.com",
  "token": "SSO_token_here"
}
```

**Response:**

```json
{
  "token": "your_generated_token"
}
```

---

#### POST `/ping`

Resets the session expiration timeout.

- **Headers:**
  - `Authorization`: `DXAPI {token}`

**Example Request:**

```http
POST /ping HTTP/1.1
Host: your-server.com
Authorization: DXAPI your_token
```

**Response:**

HTTP Status `200 OK`

---

#### POST `/logout`

Explicitly expires the authorization token.

- **Headers:**
  - `Authorization`: `DXAPI {token}`

**Example Request:**

```http
POST /logout HTTP/1.1
Host: your-server.com
Authorization: DXAPI your_token
```

**Response:**

HTTP Status `200 OK`

---

### Trading

#### POST `/accounts/:accountCode/orders`

Places an order or a group of orders on an account.

- **URL Parameters:**
  - `accountCode` (string): Unique code of the account.
- **Headers:**
  - `Authorization`: `DXAPI {token}` or HMAC Authorization header.
  - `Content-Type`: `application/json`
- **Body Parameters:** Single Order Request or Order Group Request.

**Example Request:**

```http
POST /accounts/ACC123/orders HTTP/1.1
Host: your-server.com
Authorization: DXAPI your_token
Content-Type: application/json

{
  "orderCode": "order123",
  "type": "LIMIT",
  "instrument": "EURUSD",
  "quantity": 1000,
  "side": "BUY",
  "limitPrice": 1.2345,
  "tif": "GTC"
}
```

**Response:**

```json
{
  "orderId": "unique_order_id",
  "updateOrderId": "update_order_id"
}
```

---

#### PUT `/accounts/:accountCode/orders`

Modifies an existing order on an account.

- **URL Parameters:**
  - `accountCode` (string): Unique code of the account.
- **Headers:**
  - `Authorization`: HMAC Authorization header.
  - `Content-Type`: `application/json`
- **Body Parameters:** Modified Single Order Request or Order Group Request.

**Example Request:**

```http
PUT /accounts/ACC123/orders HTTP/1.1
Host: your-server.com
Authorization: DXAPI principal="public_token",timestamp=1234567890,hash="hmac_hash"
Content-Type: application/json

{
  "orderCode": "order123",
  "limitPrice": 1.2350,
  "quantity": 1500
}
```

**Response:**

```json
{
  "orderId": "unique_order_id",
  "updateOrderId": "update_order_id"
}
```

---

#### DELETE `/accounts/:accountCode/orders/:orderCode`

Cancels an existing order on an account.

- **URL Parameters:**
  - `accountCode` (string): Unique code of the account.
  - `orderCode` (string): Unique code of the order.
- **Headers:**
  - `Authorization`: HMAC Authorization header.

**Example Request:**

```http
DELETE /accounts/ACC123/orders/order123 HTTP/1.1
Host: your-server.com
Authorization: DXAPI principal="public_token",timestamp=1234567890,hash="hmac_hash"
```

**Response:**

HTTP Status `200 OK`

---

### Reference Data

#### GET `/instruments/:symbol`

Retrieve general information about an instrument.

- **URL Parameters:**
  - `symbol` (string): Symbol of the instrument.
- **Headers:**
  - `Authorization`: `DXAPI {token}` or HMAC Authorization header.

**Example Request:**

```http
GET /instruments/EURUSD HTTP/1.1
Host: your-server.com
Authorization: DXAPI your_token
```

**Response:**

```json
{
  "type": "FX",
  "symbol": "EURUSD",
  "description": "Euro vs US Dollar",
  // Additional instrument details...
}
```

---

#### GET `/instruments/type/:type`

Retrieve instruments by type.

- **URL Parameters:**
  - `type` (string): Type of instrument (e.g., FX, CFD).
- **Headers:**
  - `Authorization`: `DXAPI {token}` or HMAC Authorization header.

**Example Request:**

```http
GET /instruments/type/FX HTTP/1.1
Host: your-server.com
Authorization: DXAPI your_token
```

**Response:**

```json
[
  {
    "type": "FX",
    "symbol": "EURUSD",
    // Additional instrument details...
  },
  // More instruments...
]
```

---

#### GET `/instruments/query`

Retrieve instruments based on query parameters.

- **Headers:**
  - `Authorization`: `DXAPI {token}` or HMAC Authorization header.
- **Query Parameters:** As per requirements.

**Example Request:**

```http
GET /instruments/query?symbol=EUR* HTTP/1.1
Host: your-server.com
Authorization: DXAPI your_token
```

**Response:**

```json
[
  {
    "type": "FX",
    "symbol": "EURUSD",
    // Additional instrument details...
  },
  {
    "type": "FX",
    "symbol": "EURGBP",
    // Additional instrument details...
  }
]
```

---

### Users and Accounts

#### GET `/users/:username`

Retrieve information for a specified user.

- **URL Parameters:**
  - `username` (string): Username of the client.
- **Headers:**
  - `Authorization`: `DXAPI {token}` or HMAC Authorization header.

**Example Request:**

```http
GET /users/user1 HTTP/1.1
Host: your-server.com
Authorization: DXAPI your_token
```

**Response:**

```json
{
  "login": "user1",
  "domain": "example.com",
  "fullName": "John Doe",
  "accounts": [
    {
      "account": "ACC123",
      "baseCurrency": "USD",
      // Additional account details...
    }
    // More accounts...
  ]
}
```

---

#### GET `/accounts/:accountCode/portfolio`

Retrieve account portfolio, including open positions and working orders.

- **URL Parameters:**
  - `accountCode` (string): Unique code of the account.
- **Headers:**
  - `Authorization`: `DXAPI {token}` or HMAC Authorization header.

**Example Request:**

```http
GET /accounts/ACC123/portfolio HTTP/1.1
Host: your-server.com
Authorization: DXAPI your_token
```

**Response:**

```json
{
  "account": "ACC123",
  "balances": [
    {
      "currency": "USD",
      "value": 10000
    }
    // More balances...
  ],
  "positions": [
    {
      "positionCode": "POS123",
      "symbol": "EURUSD",
      "quantity": 1000,
      // Additional position details...
    }
    // More positions...
  ],
  "orders": [
    {
      "orderId": "ORD123",
      "clientOrderId": "order123",
      "instrument": "EURUSD",
      // Additional order details...
    }
    // More orders...
  ]
}
```

---

### Market Data

#### POST `/marketdata`

Request the current or historical market data.

- **Headers:**
  - `Authorization`: `DXAPI {token}` or HMAC Authorization header.
  - `Content-Type`: `application/json`
- **Body Parameters:**

  ```json
  {
    "eventTypes": [
      {
        "type": "Quote",
        "format": "COMPACT"
      }
    ],
    "symbols": ["EURUSD"]
  }
  ```

**Example Request:**

```http
POST /marketdata HTTP/1.1
Host: your-server.com
Authorization: DXAPI your_token
Content-Type: application/json

{
  "eventTypes": [
    {
      "type": "Quote",
      "format": "COMPACT"
    }
  ],
  "symbols": ["EURUSD"]
}
```

**Response:**

```json
{
  "events": [
    {
      "type": "Quote",
      "symbol": "EURUSD",
      "bid": 1.2345,
      "ask": 1.2347,
      "time": "2024-10-28T07:00:00Z"
    }
    // More events...
  ]
}
```

---

### Conversion Rates

#### POST `/conversionRates`

Get the current conversion rate for a given pair of currencies.

- **Headers:**
  - `Authorization`: `DXAPI {token}` or HMAC Authorization header.
- **Query Parameters:**
  - `fromCurrency` (string): Source currency.
  - `toCurrency` (string): Target currency.

**Example Request:**

```http
POST /conversionRates?fromCurrency=EUR&toCurrency=USD HTTP/1.1
Host: your-server.com
Authorization: DXAPI your_token
```

**Response:**

```json
{
  "fromCurrency": "EUR",
  "toCurrency": "USD",
  "convRate": 1.2345
}
```

---

## Best Practices

- **Authentication:** Always ensure that you include the correct authentication headers as required by each endpoint.
- **Error Handling:** Check for possible error responses and handle them appropriately in your application.
- **Data Validation:** Validate all input data before sending requests to the API.
- **Rate Limiting:** Be mindful of the rate limits set by the APIs to avoid receiving `429 Too Many Requests` errors.
- **Secure Storage:** Never hard-code sensitive information like API tokens or private keys in your code. Use environment variables or secure storage solutions.
- **Logging:** Implement logging in your application to help with debugging and monitoring.

---

## Contributing

We welcome contributions from the community. Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Write clear commit messages and include documentation updates if necessary.
4. Submit a pull request describing your changes.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

If you have any questions or need further assistance, please open an issue in the repository.
