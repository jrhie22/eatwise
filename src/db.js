import { MongoClient } from 'mongodb';
import dotenv from 'dotenv';
dotenv.config();

const MONGODB_URL = process.env.MONGODB_URL || 'mongodb://localhost:27017/eatwise';

let db;

export async function connectDB() {
  if (db) return db;
  const client = await MongoClient.connect(MONGODB_URL, { useUnifiedTopology: true });
  db = client.db();
  return db;
}
