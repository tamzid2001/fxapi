// index.js

const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

// Base URL for the TradeLocker API
const TRADELOCKER_API_BASE_URL = 'https://api.tradelocker.com';

// Replace these with your actual TradeLocker credentials
const TRADELOCKER_EMAIL = 'your_email@example.com';
const TRADELOCKER_PASSWORD = 'your_password';
const TRADELOCKER_SERVER = 'SERVER'; // Replace with the appropriate server value

let accessToken = null;
let refreshToken = null;

// Function to authenticate and obtain JWT tokens
async function authenticate() {
  try {
    const response = await axios.post(`${TRADELOCKER_API_BASE_URL}/auth/jwt/token`, {
      email: TRADELOCKER_EMAIL,
      password: TRADELOCKER_PASSWORD,
      server: TRADELOCKER_SERVER,
    }, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = response.data;
    accessToken = data.accessToken;
    refreshToken = data.refreshToken;

    console.log('Authentication successful');
  } catch (error) {
    console.error('Error authenticating with TradeLocker:', error.response ? error.response.data : error.message);
    throw new Error('Authentication failed');
  }
}

// Function to refresh the access token
async function refreshAccessToken() {
  try {
    const response = await axios.post(`${TRADELOCKER_API_BASE_URL}/auth/jwt/refresh`, {
      refreshToken: refreshToken,
    }, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = response.data;
    accessToken = data.accessToken;
    refreshToken = data.refreshToken;

    console.log('Access token refreshed');
  } catch (error) {
    console.error('Error refreshing access token:', error.response ? error.response.data : error.message);
    // Re-authenticate if refreshing fails
    await authenticate();
  }
}

// Middleware to ensure the user is authenticated
async function ensureAuthenticated(req, res, next) {
  if (!accessToken) {
    // No token, authenticate
    await authenticate();
  }

  next();
}

// Route to obtain new JWT tokens
app.post('/auth/jwt/token', async (req, res) => {
  try {
    await authenticate();
    res.status(201).json({
      accessToken,
      refreshToken,
    });
  } catch (error) {
    res.status(400).send('Authentication failed');
  }
});

// Route to refresh JWT tokens
app.post('/auth/jwt/refresh', async (req, res) => {
  try {
    await refreshAccessToken();
    res.status(201).json({
      accessToken,
      refreshToken,
    });
  } catch (error) {
    res.status(400).send('Token refresh failed');
  }
});

// Route to get all user accounts
app.get('/auth/jwt/all-accounts', ensureAuthenticated, async (req, res) => {
  try {
    const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/auth/jwt/all-accounts`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    res.status(201).json(response.data);
  } catch (error) {
    console.error('Error fetching all accounts:', error.response ? error.response.data : error.message);
    res.status(400).send('Error fetching all accounts');
  }
});

// Helper function to get accNum
async function getAccNum() {
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/auth/jwt/all-accounts`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });
  
      const accounts = response.data;
      if (accounts.length > 0) {
        return accounts[0].accNum; // Assuming you use the first account's accNum
      } else {
        throw new Error('No accounts found for the user');
      }
    } catch (error) {
      console.error('Error fetching accNum:', error.response ? error.response.data : error.message);
      throw new Error('Error fetching accNum');
    }
  }

// Route to get the configuration (field names, rate limits, etc.)
app.get('/trade/config', ensureAuthenticated, async (req, res) => {
    let accNum = req.headers['accnum'] || req.query.accNum;
  
    if (!accNum) {
      // If accNum is not provided in headers or query params, fetch it
      try {
        accNum = await getAccNum();
      } catch (error) {
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/trade/config`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
      });
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error fetching config:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message = error.response && error.response.data ? error.response.data : 'Error fetching config';
  
      res.status(status).send(message);
    }
  });

  // Route to get account details
app.get('/trade/accounts', ensureAuthenticated, async (req, res) => {
    let accNum = req.headers['accnum'] || req.query.accNum;
  
    if (!accNum) {
      // If accNum is not provided, fetch it using getAccNum without accountId
      try {
        accNum = await getAccNum();
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/trade/accounts`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
      });
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error fetching account details:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message = error.response && error.response.data ? error.response.data : 'Error fetching account details';
  
      res.status(status).send(message);
    }
  });

  // Route to get executions for an account
app.get('/trade/accounts/:accountId/executions', ensureAuthenticated, async (req, res) => {
    const { accountId } = req.params;
    let accNum = req.headers['accnum'] || req.query.accNum;
  
    if (!accNum) {
      // Fetch accNum using accountId
      try {
        accNum = await getAccNum(accountId);
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/trade/accounts/${accountId}/executions`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
      });
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error fetching executions:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message = error.response && error.response.data ? error.response.data : 'Error fetching executions';
  
      res.status(status).send(message);
    }
  });

  // Route to get instruments for an account
app.get('/trade/accounts/:accountId/instruments', ensureAuthenticated, async (req, res) => {
    const { accountId } = req.params;
    let accNum = req.headers['accnum'] || req.query.accNum;
    const { locale } = req.query; // Optional locale parameter
  
    if (!accNum) {
      try {
        accNum = await getAccNum(accountId);
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/trade/accounts/${accountId}/instruments`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
        params: {
          locale: locale, // Include locale if provided
        },
      });
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error fetching instruments:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message = error.response && error.response.data ? error.response.data : 'Error fetching instruments';
  
      res.status(status).send(message);
    }
  });

  // Route to get non-final orders for an account
app.get('/trade/accounts/:accountId/orders', ensureAuthenticated, async (req, res) => {
    const { accountId } = req.params;
    let accNum = req.headers['accnum'] || req.query.accNum;
    const { from, to, tradableInstrumentId } = req.query;
  
    if (!accNum) {
      try {
        accNum = await getAccNum(accountId);
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    const params = {};
    if (from) params.from = from;
    if (to) params.to = to;
    if (tradableInstrumentId) params.tradableInstrumentId = tradableInstrumentId;
  
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/trade/accounts/${accountId}/orders`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
        params: params,
      });
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message = error.response && error.response.data ? error.response.data : 'Error fetching orders';
  
      res.status(status).send(message);
    }
  });

  // Route to get order history for an account
app.get('/trade/accounts/:accountId/ordersHistory', ensureAuthenticated, async (req, res) => {
    const { accountId } = req.params;
    let accNum = req.headers['accnum'] || req.query.accNum;
    const { from, to, tradableInstrumentId } = req.query;
  
    if (!accNum) {
      try {
        accNum = await getAccNum(accountId);
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    const params = {};
    if (from) params.from = from;
    if (to) params.to = to;
    if (tradableInstrumentId) params.tradableInstrumentId = tradableInstrumentId;
  
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/trade/accounts/${accountId}/ordersHistory`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
        params: params,
      });
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error fetching orders history:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message = error.response && error.response.data ? error.response.data : 'Error fetching orders history';
  
      res.status(status).send(message);
    }
  });

  // Route to get positions for an account
app.get('/trade/accounts/:accountId/positions', ensureAuthenticated, async (req, res) => {
    const { accountId } = req.params;
    let accNum = req.headers['accnum'] || req.query.accNum;
  
    if (!accNum) {
      try {
        accNum = await getAccNum(accountId);
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/trade/accounts/${accountId}/positions`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
      });
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error fetching positions:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message = error.response && error.response.data ? error.response.data : 'Error fetching positions';
  
      res.status(status).send(message);
    }
  });

  // Route to get account state
app.get('/trade/accounts/:accountId/state', ensureAuthenticated, async (req, res) => {
    const { accountId } = req.params;
    let accNum = req.headers['accnum'] || req.query.accNum;
  
    if (!accNum) {
      try {
        accNum = await getAccNum(accountId);
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/trade/accounts/${accountId}/state`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
      });
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error fetching account state:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message = error.response && error.response.data ? error.response.data : 'Error fetching account state';
  
      res.status(status).send(message);
    }
  });

  // Route to get detailed information about an instrument
app.get('/trade/instruments/:tradableInstrumentId', ensureAuthenticated, async (req, res) => {
    const { tradableInstrumentId } = req.params;
    let accNum = req.headers['accnum'] || req.query.accNum;
    const { routeId, locale } = req.query;
  
    if (!routeId) {
      return res.status(400).send('Missing required query parameter: routeId');
    }
  
    if (!accNum) {
      // Fetch accNum using getAccNum()
      try {
        accNum = await getAccNum();
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/trade/instruments/${tradableInstrumentId}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
        params: {
          routeId: routeId,
          locale: locale, // Include locale if provided
        },
      });
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error fetching instrument details:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message = error.response && error.response.data ? error.response.data : 'Error fetching instrument details';
  
      res.status(status).send(message);
    }
  });

  // Route to get detailed information about a trade session
app.get('/trade/sessions/:sessionId', ensureAuthenticated, async (req, res) => {
    const { sessionId } = req.params;
    let accNum = req.headers['accnum'] || req.query.accNum;
  
    if (!accNum) {
      // Fetch accNum using getAccNum()
      try {
        accNum = await getAccNum();
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/trade/sessions/${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
      });
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error fetching session details:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message = error.response && error.response.data ? error.response.data : 'Error fetching session details';
  
      res.status(status).send(message);
    }
  });

  // Route to get info about allowed orders in a session
app.get('/trade/sessionStatuses/:sessionStatusId', ensureAuthenticated, async (req, res) => {
    const { sessionStatusId } = req.params;
    let accNum = req.headers['accnum'] || req.query.accNum;
  
    if (!accNum) {
      // Fetch accNum using getAccNum()
      try {
        accNum = await getAccNum();
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/trade/sessionStatuses/${sessionStatusId}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
      });
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error fetching session status details:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message = error.response && error.response.data ? error.response.data : 'Error fetching session status details';
  
      res.status(status).send(message);
    }
  });

  // Route to get current daily bar
app.get('/trade/dailyBar', ensureAuthenticated, async (req, res) => {
    let accNum = req.headers['accnum'] || req.query.accNum;
    const { routeId, barType, tradableInstrumentId } = req.query;
  
    // Validate required query parameters
    if (!routeId || !barType || !tradableInstrumentId) {
      return res.status(400).send('Missing required query parameters: routeId, barType, tradableInstrumentId');
    }
  
    if (!accNum) {
      // Fetch accNum using getAccNum()
      try {
        accNum = await getAccNum();
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/trade/dailyBar`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
        params: {
          routeId,
          barType,
          tradableInstrumentId,
        },
      });
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error fetching daily bar:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message = error.response && error.response.data ? error.response.data : 'Error fetching daily bar';
  
      res.status(status).send(message);
    }
  });

  // Route to get market depth
app.get('/trade/depth', ensureAuthenticated, async (req, res) => {
    let accNum = req.headers['accnum'] || req.query.accNum;
    const { routeId, tradableInstrumentId } = req.query;
  
    // Validate required query parameters
    if (!routeId || !tradableInstrumentId) {
      return res.status(400).send('Missing required query parameters: routeId, tradableInstrumentId');
    }
  
    if (!accNum) {
      // Fetch accNum using getAccNum()
      try {
        accNum = await getAccNum();
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/trade/depth`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
        params: {
          routeId,
          tradableInstrumentId,
        },
      });
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error fetching market depth:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message = error.response && error.response.data ? error.response.data : 'Error fetching market depth';
  
      res.status(status).send(message);
    }
  });

  // Route to get historical bars
app.get('/trade/history', ensureAuthenticated, async (req, res) => {
    let accNum = req.headers['accnum'] || req.query.accNum;
    const { routeId, from, to, resolution, tradableInstrumentId } = req.query;
  
    // Validate required query parameters
    if (!routeId || !from || !to || !resolution || !tradableInstrumentId) {
      return res.status(400).send('Missing required query parameters: routeId, from, to, resolution, tradableInstrumentId');
    }
  
    if (!accNum) {
      // Fetch accNum using getAccNum()
      try {
        accNum = await getAccNum();
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/trade/history`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
        params: {
          routeId,
          from,
          to,
          resolution,
          tradableInstrumentId,
        },
      });
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error fetching historical bars:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message = error.response && error.response.data ? error.response.data : 'Error fetching historical bars';
  
      res.status(status).send(message);
    }
  });

  // Route to get current quotes
app.get('/trade/quotes', ensureAuthenticated, async (req, res) => {
    let accNum = req.headers['accnum'] || req.query.accNum;
    const { routeId, tradableInstrumentId } = req.query;
  
    // Validate required query parameters
    if (!routeId || !tradableInstrumentId) {
      return res.status(400).send('Missing required query parameters: routeId, tradableInstrumentId');
    }
  
    if (!accNum) {
      // Fetch accNum using getAccNum()
      try {
        accNum = await getAccNum();
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    try {
      const response = await axios.get(`${TRADELOCKER_API_BASE_URL}/trade/quotes`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
        params: {
          routeId,
          tradableInstrumentId,
        },
      });
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error fetching quotes:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message = error.response && error.response.data ? error.response.data : 'Error fetching quotes';
  
      res.status(status).send(message);
    }
  });

  // Route to place a new order
app.post('/trade/accounts/:accountId/orders', ensureAuthenticated, async (req, res) => {
    const { accountId } = req.params;
    let accNum = req.headers['accnum'] || req.query.accNum;
    const orderData = req.body;
  
    if (!accNum) {
      try {
        accNum = await getAccNum(accountId);
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    // Validate mandatory fields
    const requiredFields = ['qty', 'routeId', 'side', 'validity', 'type', 'tradableInstrumentId'];
    const missingFields = requiredFields.filter(field => !(field in orderData));
  
    if (missingFields.length > 0) {
      return res.status(400).send(`Missing required fields: ${missingFields.join(', ')}`);
    }
  
    try {
      const response = await axios.post(
        `${TRADELOCKER_API_BASE_URL}/trade/accounts/${accountId}/orders`,
        orderData,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'accNum': accNum,
            'Content-Type': 'application/json',
          },
        }
      );
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error placing new order:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message =
        error.response && error.response.data ? error.response.data : 'Error placing new order';
  
      res.status(status).send(message);
    }
  });

  // Route to cancel all orders
app.delete('/trade/accounts/:accountId/orders', ensureAuthenticated, async (req, res) => {
    const { accountId } = req.params;
    const { tradableInstrumentId } = req.query;
    let accNum = req.headers['accnum'] || req.query.accNum;
  
    if (!accNum) {
      try {
        accNum = await getAccNum(accountId);
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    const params = {};
    if (tradableInstrumentId) params.tradableInstrumentId = tradableInstrumentId;
  
    try {
      const response = await axios.delete(
        `${TRADELOCKER_API_BASE_URL}/trade/accounts/${accountId}/orders`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'accNum': accNum,
          },
          params: params,
        }
      );
  
      res.status(response.status === 204 ? 204 : 200).json(response.data);
    } catch (error) {
      console.error('Error cancelling orders:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message =
        error.response && error.response.data ? error.response.data : 'Error cancelling orders';
  
      res.status(status).send(message);
    }
  });

  // Route to close all positions
app.delete('/trade/accounts/:accountId/positions', ensureAuthenticated, async (req, res) => {
    const { accountId } = req.params;
    const { tradableInstrumentId } = req.query;
    let accNum = req.headers['accnum'] || req.query.accNum;
  
    if (!accNum) {
      try {
        accNum = await getAccNum(accountId);
      } catch (error) {
        console.error('Unable to retrieve accNum:', error.message);
        return res.status(500).send('Unable to retrieve accNum');
      }
    }
  
    const params = {};
    if (tradableInstrumentId) params.tradableInstrumentId = tradableInstrumentId;
  
    try {
      const response = await axios.delete(
        `${TRADELOCKER_API_BASE_URL}/trade/accounts/${accountId}/positions`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'accNum': accNum,
          },
          params: params,
        }
      );
  
      res.status(200).json(response.data);
    } catch (error) {
      console.error('Error closing positions:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message =
        error.response && error.response.data ? error.response.data : 'Error closing positions';
  
      res.status(status).send(message);
    }
  });

  // Route to cancel an existing order
app.delete('/trade/orders/:orderId', ensureAuthenticated, async (req, res) => {
    const { orderId } = req.params;
    let accNum = req.headers['accnum'] || req.query.accNum;
  
    if (!accNum) {
      console.error('accNum is required in headers or query parameters');
      return res.status(400).send('accNum is required');
    }
  
    try {
      const response = await axios.delete(`${TRADELOCKER_API_BASE_URL}/trade/orders/${orderId}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'accNum': accNum,
        },
      });
  
      res.status(response.status === 204 ? 204 : 200).json(response.data);
    } catch (error) {
      console.error('Error cancelling order:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message =
        error.response && error.response.data ? error.response.data : 'Error cancelling order';
  
      res.status(status).send(message);
    }
  });

  // Route to modify an existing order
app.patch('/trade/orders/:orderId', ensureAuthenticated, async (req, res) => {
    const { orderId } = req.params;
    const updateData = req.body;
    let accNum = req.headers['accnum'] || req.query.accNum;
  
    if (!accNum) {
      console.error('accNum is required in headers or query parameters');
      return res.status(400).send('accNum is required');
    }
  
    try {
      const response = await axios.patch(
        `${TRADELOCKER_API_BASE_URL}/trade/orders/${orderId}`,
        updateData,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'accNum': accNum,
            'Content-Type': 'application/json',
          },
        }
      );
  
      res.status(response.status === 204 ? 204 : 200).json(response.data);
    } catch (error) {
      console.error('Error modifying order:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message =
        error.response && error.response.data ? error.response.data : 'Error modifying order';
  
      res.status(status).send(message);
    }
  });

  // Route to close an existing position
app.delete('/trade/positions/:positionId', ensureAuthenticated, async (req, res) => {
    const { positionId } = req.params;
    const { qty } = req.body;
    let accNum = req.headers['accnum'] || req.query.accNum;
  
    if (!accNum) {
      console.error('accNum is required in headers or query parameters');
      return res.status(400).send('accNum is required');
    }
  
    // qty is required in the body
    if (qty === undefined) {
      return res.status(400).send('Missing required field: qty in the request body');
    }
  
    try {
      const response = await axios.delete(
        `${TRADELOCKER_API_BASE_URL}/trade/positions/${positionId}`,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'accNum': accNum,
            'Content-Type': 'application/json',
          },
          data: { qty }, // Include qty in the request body
        }
      );
  
      res.status(response.status === 204 ? 204 : 200).json(response.data);
    } catch (error) {
      console.error('Error closing position:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message =
        error.response && error.response.data ? error.response.data : 'Error closing position';
  
      res.status(status).send(message);
    }
  });

  // Route to modify an existing position
app.patch('/trade/positions/:positionId', ensureAuthenticated, async (req, res) => {
    const { positionId } = req.params;
    const updateData = req.body;
    let accNum = req.headers['accnum'] || req.query.accNum;
  
    if (!accNum) {
      console.error('accNum is required in headers or query parameters');
      return res.status(400).send('accNum is required');
    }
  
    // At least one field must be provided in the body
    if (!updateData || Object.keys(updateData).length === 0) {
      return res.status(400).send('At least one field (stopLoss, takeProfit, trailingOffset) must be provided in the request body');
    }
  
    try {
      const response = await axios.patch(
        `${TRADELOCKER_API_BASE_URL}/trade/positions/${positionId}`,
        updateData,
        {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'accNum': accNum,
            'Content-Type': 'application/json',
          },
        }
      );
  
      res.status(response.status === 204 ? 204 : 200).json(response.data);
    } catch (error) {
      console.error('Error modifying position:', error.response ? error.response.data : error.message);
  
      const status = error.response ? error.response.status : 500;
      const message =
        error.response && error.response.data ? error.response.data : 'Error modifying position';
  
      res.status(status).send(message);
    }
  });
  
// Start the Express server (optional if using as a module)
const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
