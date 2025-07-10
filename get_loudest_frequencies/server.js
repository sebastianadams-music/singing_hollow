const express = require('express');
const path = require('path');

const app = express();
const PORT = 3000;

app.use(express.static('public'));

app.get('/', (req, res) => {
  res.send(`
    <html>
      <head>
        <title>Dynamic LilyPond SVG</title>
        <style>
          body { font-family: sans-serif; background: #f0f0f0; text-align: 
center; }
        </style>
      </head>
      <body>
        <h1>Dynamic LilyPond SVG</h1>
        <img id="score" src="combined.svg" width="800" height="300"/>
        <script>
          setInterval(() => {
            const img = document.getElementById('score');
            img.src = 'combined.svg?t=' + Date.now(); // bust cache
          }, 200);
        </script>
      </body>
    </html>
  `);
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});

