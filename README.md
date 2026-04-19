# eatwise
From GeorgeHacks Problem Statement 1.
EatWise 🌸
The first AI-powered metabolic companion for women with PCOS.
EatWise was built at GeorgeHacks in response to a healthcare gap that affects 1 in 10 women: PCOS is primarily a metabolic and endocrine disorder, but the standard of care treats it as a reproductive one. Most apps assume every user needs the same diet. They don't. A woman with Insulin-Resistant PCOS needs completely different nutrition than a woman with Adrenal or Post-Pill PCOS. EatWise fixes this by phenotyping each user at onboarding and filtering every recommendation such as food, supplements, and movement through that metabolic lens. EatWise is not a calorie tracker. It is a decision support system built for the woman medicine forgot.

Features

AI Phenotype Survey: classifies users into one of four PCOS metabolic types (Insulin Resistant, Adrenal, Inflammatory, Post-Pill)
Personalized Dashboard: root-cause framing, nutrition guidance, and clinical discussion points filtered by phenotype
Food Label Scanner: GPT-4o-mini vision reads ingredient labels and flags PCOS-relevant additives (maltodextrin, seed oils, hidden sugars) in the context of the user's phenotype
Symptom Diary: daily logging of 10 symptoms + foods consumed, with an AI-generated pattern summary powered by Claude
Medical Summary PDF: one-page export for clinical visits, summarizing the user's metabolic data and discussion points


Tech Stack

Frontend & App: Streamlit (Python)
Label vision analysis: OpenAI GPT-4o-mini
Nutrition extraction: Mistral Large + Pixtral
Symptom pattern summary: Anthropic Claude (claude-sonnet-4)
Food bank data: Capital Area Food Bank open dataset
PDF generation: fpdf2


Setup
1. Clone the repo
bashgit clone https://github.com/jrhie22/eatwise.git
cd eatwise
2. Create a virtual environment and install dependencies
bashpython -m venv .venv

# Mac/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt

3. Set up environment variables
Copy .env.example to .env and fill in your API keys:
bashcp .env.example .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
MISTRAL_API_KEY=...
YELP_API_KEY=...

4. Run the app
bashstreamlit run app.py
The app will open at http://localhost:8501.

Usage

Open the app and click Discover Your Recommendations
Complete the 3-step Phenotype Survey, takes about 2 minutes
View your Dashboard for personalized nutrition and protocol guidance
Use the Food Label Scanner to analyze any packaged food against your phenotype
Use the Food Bank Finder to locate nearby providers with a tailored shopping list
Log daily symptoms in the Symptom Diary and generate a pattern summary over time
Export your Medical Summary PDF to bring to a clinical appointment


License
MIT License — see LICENSE for details.

EatWise is an educational tool. It does not replace medical advice, diagnosis, or treatment.