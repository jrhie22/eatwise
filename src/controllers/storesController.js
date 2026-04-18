import { connectDB } from '../db.js';

export async function getStores(req, res) {
  try {
    const db = await connectDB();
    const stores = await db.collection('stores').find({}).toArray();
    res.json(stores);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch stores' });
  }
}
