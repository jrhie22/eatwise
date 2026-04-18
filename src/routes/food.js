import express from 'express';
import { evaluateFood } from '../controllers/foodController.js';
const router = express.Router();
router.post('/evaluate', evaluateFood);
export default router;
