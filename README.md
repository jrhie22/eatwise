# EatWise 🌸

**The first AI-powered metabolic companion for women with PCOS.**

EatWise was built at GeorgeHacks in response to a healthcare gap that affects 1 in 10 women: PCOS is primarily a metabolic and endocrine disorder, but the standard of care treats it as a reproductive one. Most apps assume every user needs the same diet. They don't. A woman with Insulin-Resistant PCOS needs completely different nutrition than a woman with Adrenal or Post-Pill PCOS. EatWise fixes this by phenotyping each user at onboarding and filtering every recommendation — food, supplements, movement — through that metabolic lens. It also addresses food equity directly: the Food Bank Finder maps Capital Area Food Bank providers by ZIP code and turns a free pantry visit into a personalized metabolic strategy, including SNAP-eligible guidance. EatWise is not a calorie tracker. It is a decision support system built for the woman medicine forgot.

---

## Features

- **AI Phenotype Survey** — classifies users into one of four PCOS metabolic types (Insulin Resistant, Adrenal, Inflammatory, Post-Pill)
- **Personalized Dashboard** — root-cause framing, nutrition guidance, and clinical discussion points filtered by phenotype
- **Symptom Diary** — daily logging of 10 symptoms + foods consumed, with an AI-generated pattern summary powered by Claude
- **Medical Summary PDF** — one-page export for clinical visits, summarizing the user's metabolic data and discussion points

---

## Tech Stack

- **Frontend & App:** Streamlit (Python)
- **Nutrition extraction:** Mistral 
- **PDF generation:** fpdf2

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/jrhie22/eatwise.git
cd eatwise
```

**2. Create a virtual environment and install dependencies**
```bash
python -m venv .venv

# Mac/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

**3. Set up environment variables**

Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

```
MISTRAL_API_KEY=...

```

**4. Run the app**
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Usage

1. Open the app and click **Discover Your Recommendations**
2. Complete the 3-step **Phenotype Survey** — takes about 2 minutes
3. View your **Dashboard** for personalized nutrition and protocol guidance
6. Log daily symptoms in the **Symptom Diary** and generate a pattern summary over time
7. Export your **Medical Summary PDF** to bring to a clinical appointment

---

## License

MIT License — see `LICENSE` for details.

---

*EatWise is an educational tool. It does not replace medical advice, diagnosis, or treatment.*
