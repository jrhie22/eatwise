import { connectDB } from '../db.js';

export async function getProgress(req, res) {
  try {
    const db = await connectDB();
    const progress = await db.collection('progress').findOne({ userId: 'demo' });
    if (!progress) {
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
}
