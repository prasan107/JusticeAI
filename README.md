# JusticeAI ⚖️

AI-Based Legal Research and Case Outcome Prediction System

## Modules
- Module 1: Semantic Legal Search
- Module 2: Case Outcome Prediction  
- Module 3: Legal Chatbot
- Module 4: OCR Document Processing

## Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

### Data Pipeline (run once)
```bash
python scripts/scraper.py
python scripts/auto_label.py
python scripts/ingest_to_vectordb.py
python ml_pipeline/train.py
```

## API Docs
Visit http://localhost:8000/docs after starting the backend.
