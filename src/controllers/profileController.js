import { connectDB } from '../db.js';

export async function getProfile(req, res) {
  try {
    const db = await connectDB();
    const profile = await db.collection('profiles').findOne({ userId: 'demo' });
    if (!profile) {
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
}
