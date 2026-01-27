const http = require('http');
const fs = require('fs');
const path = require('path');
const httpProxy = require('http-proxy');

const PORT = process.env.PORT || 3000;
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';

// Create a proxy server
const proxy = httpProxy.createProxyServer({});

const mimeTypes = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
};

const server = http.createServer((req, res) => {
  const url = req.url.split('?')[0];
  
  // Proxy API calls to backend
  if (url.startsWith('/api')) {
    proxy.web(req, res, { target: BACKEND_URL }, (err) => {
      console.error('Proxy error:', err);
      res.writeHead(502);
      res.end('Proxy error');
    });
    return;
  }
  
  // Serve static files from dist directory
  let filePath = path.join(__dirname, 'dist', url);
  
  // Check if file exists
  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath);
    const contentType = mimeTypes[ext] || 'application/octet-stream';
    
    // Add CORS headers for font files
    const headers = { 'Content-Type': contentType };
    if (['.ttf', '.woff', '.woff2', '.eot', '.otf'].includes(ext)) {
      headers['Access-Control-Allow-Origin'] = '*';
      headers['Cache-Control'] = 'public, max-age=31536000';
    }
    
    fs.readFile(filePath, (err, data) => {
      if (err) {
        res.writeHead(500);
        res.end('Server error');
      } else {
        res.writeHead(200, headers);
        res.end(data);
      }
    });
    return;
  }
  
  // Check for .html file
  const htmlFile = filePath + '.html';
  if (fs.existsSync(htmlFile)) {
    fs.readFile(htmlFile, (err, data) => {
      if (err) {
        res.writeHead(500);
        res.end('Server error');
      } else {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(data);
      }
    });
    return;
  }
  
  // Serve index.html for all other routes (SPA fallback)
  const indexFile = path.join(__dirname, 'dist', 'index.html');
  if (fs.existsSync(indexFile)) {
    fs.readFile(indexFile, (err, data) => {
      if (err) {
        res.writeHead(500);
        res.end('Server error');
      } else {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(data);
      }
    });
    return;
  }
  
  res.writeHead(404);
  res.end('Not found');
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`The Gig Pulse server running on port ${PORT}`);
  console.log(`Proxying API calls to ${BACKEND_URL}`);
});
