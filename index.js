const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());

// In-memory data store
let items = [
  { id: 1, name: 'Item 1', description: 'First item' },
  { id: 2, name: 'Item 2', description: 'Second item' }
];

// Routes
app.get('/', (req, res) => {
  res.json({
    message: 'Welcome to Demo Service v2.0',
    status: 'running',
    endpoints: ['GET /', 'GET /health', 'GET /api/items', 'GET /api/items/:id', 'POST /api/items'],
    timestamp: new Date().toISOString()
  });
});

app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy',
    uptime: process.uptime(),
    memory: process.memoryUsage()
  });
});

// CRUD API
app.get('/api/items', (req, res) => {
  res.json({ count: items.length, items });
});

app.get('/api/items/:id', (req, res) => {
  const item = items.find(i => i.id === parseInt(req.params.id));
  if (!item) return res.status(404).json({ error: 'Item not found' });
  res.json(item);
});

app.post('/api/items', (req, res) => {
  const { name, description } = req.body;
  if (!name) return res.status(400).json({ error: 'Name is required' });
  
  const newItem = {
    id: items.length + 1,
    name,
    description: description || ''
  };
  items.push(newItem);
  res.status(201).json(newItem);
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Demo service v2.0 running on port ${PORT}`);
});
