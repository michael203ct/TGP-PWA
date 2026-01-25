const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// Serve static files from dist directory
app.use(express.static(path.join(__dirname, 'dist')));

// Handle all routes
app.use((req, res, next) => {
  // Check if the request is for a specific HTML file
  const htmlFile = path.join(__dirname, 'dist', req.path + '.html');
  
  if (fs.existsSync(htmlFile)) {
    res.sendFile(htmlFile);
  } else if (req.path.includes('.')) {
    // If it's a file request (has extension), let it 404
    next();
  } else {
    // For all other routes, serve index.html (SPA fallback)
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`The Gig Pulse server running on port ${PORT}`);
});
