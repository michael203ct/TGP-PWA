const express = require('express');
const path = require('path');
const fs = require('fs');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 3000;
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';

// Proxy API calls to backend - must be first
app.use('/api', createProxyMiddleware({
  target: BACKEND_URL,
  changeOrigin: true,
  pathRewrite: {
    '^/api': '/api'  // Keep /api prefix
  },
  logLevel: 'debug'
}));

// Serve static files from dist directory
app.use(express.static(path.join(__dirname, 'dist')));

// Handle all routes - serve appropriate HTML files
app.use((req, res) => {
  // Check if the request is for a specific HTML file
  const htmlFile = path.join(__dirname, 'dist', req.path + '.html');
  
  if (fs.existsSync(htmlFile)) {
    res.sendFile(htmlFile);
  } else {
    // For all other routes, serve index.html (SPA fallback)
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`The Gig Pulse server running on port ${PORT}`);
  console.log(`Proxying API calls to ${BACKEND_URL}`);
});
