import express from 'express';
import { getStores } from '../controllers/storesController.js';
const router = express.Router();
router.get('/', getStores);
export default router;
