import express from 'express';
import { getProgress } from '../controllers/progressController.js';
const router = express.Router();
router.get('/', getProgress);
export default router;
