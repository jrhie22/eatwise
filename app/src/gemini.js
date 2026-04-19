import fetch from 'node-fetch';

export async function askGemini(prompt) {
  // Replace with your Gemini API endpoint and key
  const GEMINI_API_URL = process.env.GEMINI_API_URL || 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent';
  const GEMINI_API_KEY = process.env.GEMINI_API_KEY || '';
  if (!GEMINI_API_KEY) throw new Error('Missing Gemini API key');

  const body = {
    contents: [{ parts: [{ text: prompt }] }]
  };

  const res = await fetch(`${GEMINI_API_URL}?key=${GEMINI_API_KEY}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error('Gemini API error');
  const data = await res.json();
  // Extract the AI's response text
  return data.candidates?.[0]?.content?.parts?.[0]?.text || 'No response from Gemini.';
}
