// app.js

const express = require('express');
const bodyParser = require('body-parser');
const crypto = require('crypto');

const app = express();

// Middleware to parse JSON bodies
app.use(bodyParser.json());

// In-memory storage for demo purposes
const tokens = {}; // Store tokens for Token Authentication
const users = {};  // Store user information
const accounts = {}; // Store account information
const orders = {}; // Store orders
const positions = {}; // Store positions
const instruments = {}; // Store instruments
const marketData = {}; // Store market data
const conversions = {}; // Store conversion rates

// Configurations
const AUTH_TIMEOUT = 30 * 60 * 1000; // 30 minutes

// Helper Functions
function generateToken() {
  return crypto.randomBytes(16).toString('hex');
}

function generateHMAC(data, secret) {
  return crypto.createHmac('sha256', secret).update(data).digest('base64');
}

// Middleware for Token Authentication
function tokenAuth(req, res, next) {
  const authHeader = req.headers['authorization'];
  if (authHeader && authHeader.startsWith('DXAPI ')) {
    const token = authHeader.substring(6);
    const session = tokens[token];
    if (session && Date.now() - session.timestamp < AUTH_TIMEOUT) {
      req.user = session.user;
      session.timestamp = Date.now(); // Reset timeout
      return next();
    }
  }
  res.status(401).json({ errorCode: '1', description: 'Authorization required' });
}

// Middleware for HMAC Authentication
function hmacAuth(req, res, next) {
  const authHeader = req.headers['authorization'];
  if (authHeader && authHeader.startsWith('DXAPI ')) {
    const parts = authHeader.substring(6).split(',');
    const authParams = {};
    parts.forEach((part) => {
      const [key, value] = part.trim().split('=');
      authParams[key] = value.replace(/"/g, '');
    });

    const { principal, timestamp, hash } = authParams;
    const currentTime = Date.now();
    const timeDifference = Math.abs(currentTime - parseInt(timestamp, 10));

    // Check timestamp freshness (within 5 minutes)
    if (timeDifference > 5 * 60 * 1000) {
      return res.status(401).json({ errorCode: '12', description: 'HMAC signature too old' });
    }

    // Retrieve user's secret key
    const user = users[principal];
    if (!user) {
      return res.status(401).json({ errorCode: '13', description: 'HMAC signature mismatch' });
    }

    const privateToken = user.privateToken;

    // Reconstruct the data to hash
    const method = req.method;
    const content = req.rawBody || '';
    const uri = req.originalUrl;
    const dataToHash = `Method=${method}\nContent=${content}\nURI=${uri}\nTimestamp=${timestamp}`;

    // Generate HMAC hash
    const computedHash = generateHMAC(dataToHash, privateToken);

    if (computedHash !== hash) {
      return res.status(401).json({ errorCode: '13', description: 'HMAC signature mismatch' });
    }

    req.user = user;
    return next();
  }
  res.status(401).json({ errorCode: '1', description: 'Authorization required' });
}

// Middleware to parse raw body (needed for HMAC content hashing)
app.use((req, res, next) => {
  let data = '';
  req.on('data', (chunk) => {
    data += chunk;
  });
  req.on('end', () => {
    req.rawBody = data;
    next();
  });
});

// Route Handlers

/** Authentication & Authorization **/

// POST Create Session Token
app.post('/login', (req, res) => {
  const { username, domain, password } = req.body;

  // Validate user credentials (placeholder)
  const userKey = `${username}@${domain}`;
  const user = users[userKey];

  if (user && user.password === password) {
    // Generate token
    const token = generateToken();
    tokens[token] = { user: userKey, timestamp: Date.now() };
    return res.status(200).json({ token });
  } else {
    return res.status(401).json({ errorCode: '1', description: 'Authorization required' });
  }
});

// POST Create Session Token by SSO
app.post('/loginByToken', (req, res) => {
  const { username, domain, token: ssoToken } = req.body;

  // Validate SSO token (placeholder)
  const userKey = `${username}@${domain}`;
  const user = users[userKey];

  if (user && user.ssoToken === ssoToken) {
    // Generate session token
    const token = generateToken();
    tokens[token] = { user: userKey, timestamp: Date.now() };
    return res.status(200).json({ token });
  } else {
    return res.status(401).json({ errorCode: '1', description: 'Authorization required' });
  }
});

// POST Ping
app.post('/ping', tokenAuth, (req, res) => {
  // Session timeout reset is handled in tokenAuth middleware
  res.status(200).send();
});

// POST Logout
app.post('/logout', tokenAuth, (req, res) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader.substring(6);
  delete tokens[token];
  res.status(200).send();
});

/** Trading **/

// POST Place Order
app.post('/accounts/:accountCode/orders', hmacAuth, (req, res) => {
  const { accountCode } = req.params;
  const orderRequest = req.body;

  // Placeholder for order processing logic
  // Validate and store the order
  const orderId = crypto.randomBytes(8).toString('hex');
  orders[orderId] = { ...orderRequest, account: accountCode, orderId };

  res.status(200).json({ orderId, updateOrderId: orderId });
});

// PUT Modify Order
app.put('/accounts/:accountCode/orders', hmacAuth, (req, res) => {
  const { accountCode } = req.params;
  const orderRequest = req.body;

  // Placeholder for order modification logic
  // Find and update the order
  const existingOrder = orders[orderRequest.orderId];
  if (existingOrder) {
    orders[orderRequest.orderId] = { ...existingOrder, ...orderRequest };
    res.status(200).json({ orderId: orderRequest.orderId, updateOrderId: orderRequest.orderId });
  } else {
    res.status(404).json({ errorCode: '404', description: 'Order not found' });
  }
});

// DELETE Cancel Order
app.delete('/accounts/:accountCode/orders/:orderCode', hmacAuth, (req, res) => {
  const { accountCode, orderCode } = req.params;

  // Placeholder for order cancellation logic
  if (orders[orderCode]) {
    delete orders[orderCode];
    res.status(200).send();
  } else {
    res.status(404).json({ errorCode: '404', description: 'Order not found' });
  }
});

/** Reference Data **/

// GET List Instruments
app.get('/instruments/:symbol?', tokenAuth, (req, res) => {
  const { symbol } = req.params;

  // Placeholder for instrument retrieval logic
  if (symbol) {
    const instrument = instruments[symbol];
    if (instrument) {
      res.status(200).json([instrument]);
    } else {
      res.status(404).json({ errorCode: '404', description: 'Instrument not found' });
    }
  } else {
    // Return all instruments
    res.status(200).json(Object.values(instruments));
  }
});

// GET List Instrument Details
app.get('/accounts/:accountCode/instruments/:symbol?', tokenAuth, (req, res) => {
  const { accountCode, symbol } = req.params;

  // Placeholder for account-specific instrument details
  if (symbol) {
    const instrument = instruments[symbol];
    if (instrument) {
      res.status(200).json([{ ...instrument, account: accountCode }]);
    } else {
      res.status(404).json({ errorCode: '404', description: 'Instrument not found' });
    }
  } else {
    // Return all instruments for account
    res.status(200).json(
      Object.values(instruments).map((instr) => ({ ...instr, account: accountCode }))
    );
  }
});

/** Users and Accounts **/

// GET Get Users
app.get('/users/:username?', tokenAuth, (req, res) => {
  const { username } = req.params;

  // Placeholder for user retrieval logic
  if (username) {
    const user = users[username];
    if (user) {
      res.status(200).json(user);
    } else {
      res.status(404).json({ errorCode: '404', description: 'User not found' });
    }
  } else {
    // Return current user
    const user = users[req.user];
    res.status(200).json(user);
  }
});

// GET List Account Portfolio
app.get('/accounts/:accountCode/portfolio', tokenAuth, (req, res) => {
  const { accountCode } = req.params;

  // Placeholder for portfolio retrieval logic
  const portfolio = {
    account: accountCode,
    balances: [],
    positions: [],
    orders: [],
  };

  res.status(200).json(portfolio);
});

/** Market Data **/

// POST Request Market Data
app.post('/marketdata', tokenAuth, (req, res) => {
  const { eventTypes, symbols } = req.body;

  // Placeholder for market data retrieval logic
  const data = [];

  res.status(200).json({ events: data });
});

/** Conversion Rates **/

// POST Get Conversion Rates
app.post('/conversionRates', tokenAuth, (req, res) => {
  const { fromCurrency, toCurrency } = req.query;

  // Placeholder for conversion rate retrieval logic
  const rate = conversions[`${fromCurrency}_${toCurrency}`];

  if (rate) {
    res.status(200).json({
      fromCurrency,
      toCurrency,
      convRate: rate,
    });
  } else {
    res.status(404).json({ errorCode: '404', description: 'Conversion rate not found' });
  }
});

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`DXtrade API server is running on port ${PORT}`);
});
