import { MongoClient } from 'mongodb';
import dotenv from 'dotenv';
dotenv.config();

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/eatwise';

let db;

export async function connectDB() {
  if (db) return db;
  const client = await MongoClient.connect(MONGODB_URI, { useUnifiedTopology: true });
  db = client.db();
  return db;
}
