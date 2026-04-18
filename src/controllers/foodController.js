import { askGemini } from '../gemini.js';

export async function evaluateFood(req, res) {
  const { food } = req.body;
  if (!food) return res.json({ color: 'info', label: 'Unknown', explanation: 'No data available.' });
  try {
    const prompt = `Evaluate the following food for nutrition, health risks, and cultural fit. Give a green/yellow/red rating, a short explanation, and any health/cultural warnings. Food: ${food}`;
    const aiResponse = await askGemini(prompt);
    let color = 'info', label = 'Unknown', explanation = aiResponse;
    if (/green/i.test(aiResponse)) { color = 'success'; label = 'Green: Safe'; }
    else if (/yellow/i.test(aiResponse)) { color = 'warning'; label = 'Yellow: Moderation'; }
    else if (/red/i.test(aiResponse)) { color = 'error'; label = 'Red: Risky'; }
    res.json({ color, label, explanation });
  } catch (err) {
    res.status(500).json({ color: 'info', label: 'Unknown', explanation: 'Gemini API error.' });
  }
}
