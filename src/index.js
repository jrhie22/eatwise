import express from 'express';
import cors from 'cors';
import { MongoClient } from 'mongodb';

import dotenv from 'dotenv';
dotenv.config();

import { askGemini } from './gemini.js';

// Load environment variables
dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 5000;
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/eatwise';

// MongoDB connection
let db;
MongoClient.connect(MONGODB_URI, { useUnifiedTopology: true })
  .then(client => {
    db = client.db();
    console.log('Connected to MongoDB');
  })
  .catch(err => {
    console.error('MongoDB connection error:', err);
  });

// Mock routes

app.get('/api/profile', async (req, res) => {
  try {
    const profile = await db.collection('profiles').findOne({ userId: 'demo' });
    if (!profile) {
      // Return a default profile if not found
      return res.json({
        health: 'none',
        culture: 'Haitian',
        diet: 'None',
        snapwic: true,
        budget: '100',
        goals: ['General health']
      });
    }
    res.json(profile);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch profile' });
  }
});


app.get('/api/stores', async (req, res) => {
  try {
    const stores = await db.collection('stores').find({}).toArray();
    res.json(stores);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch stores' });
  }
});


app.post('/api/food-evaluate', async (req, res) => {
  const { food } = req.body;
  if (!food) return res.json({ color: 'info', label: 'Unknown', explanation: 'No data available.' });
  try {
    const prompt = `Evaluate the following food for nutrition, health risks, and cultural fit. Give a green/yellow/red rating, a short explanation, and any health/cultural warnings. Food: ${food}`;
    const aiResponse = await askGemini(prompt);
    // Simple parsing: look for green/yellow/red in the response
    let color = 'info', label = 'Unknown', explanation = aiResponse;
    if (/green/i.test(aiResponse)) { color = 'success'; label = 'Green: Safe'; }
    else if (/yellow/i.test(aiResponse)) { color = 'warning'; label = 'Yellow: Moderation'; }
    else if (/red/i.test(aiResponse)) { color = 'error'; label = 'Red: Risky'; }
    res.json({ color, label, explanation });
  } catch (err) {
    res.status(500).json({ color: 'info', label: 'Unknown', explanation: 'Gemini API error.' });
  }
});


app.get('/api/progress', async (req, res) => {
  try {
    const progress = await db.collection('progress').findOne({ userId: 'demo' });
    if (!progress) {
      // Return default progress if not found
      return res.json({
        nutritionScore: 82,
        weeklyTrends: [70, 75, 80, 85, 90, 88, 82],
        rewards: 120,
        prediction: 'Low risk of diabetes, moderate risk of hypertension'
      });
    }
    res.json(progress);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch progress' });
  }
});

app.get('/api/map', (req, res) => {
  res.json({
    cities: [
      { label: 'New York City', latitude: 40.7128, longitude: -74.006 },
      { label: 'Los Angeles', latitude: 34.0522, longitude: -118.2437 },
      { label: 'Chicago', latitude: 41.8781, longitude: -87.6298 },
      { label: 'Houston', latitude: 29.7604, longitude: -95.3698 },
      { label: 'Miami', latitude: 25.7617, longitude: -80.1918 }
    ]
  });
});

app.listen(PORT, () => {
  console.log(`Eatwise backend running on port ${PORT}`);
});
