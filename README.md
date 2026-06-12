# ⚖️ JusticeAI — Intelligent Legal Research System

> AI-powered semantic search, outcome prediction, and RAG-based legal analysis for the Indian judiciary.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18-blue?style=flat-square&logo=react)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-orange?style=flat-square)
![XGBoost](https://img.shields.io/badge/XGBoost-ML_Model-red?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 📌 About

**JusticeAI** is a full-stack AI-powered legal research platform built specifically for the Indian judiciary. It addresses the critical gap in Indian legal technology by replacing keyword-based search with intelligent semantic retrieval, outcome prediction, and AI-generated legal analysis grounded in real court precedents.

### 🎯 Problem
- Indian platforms (Indian Kanoon, Manupatra) use keyword search — missing semantic intent
- No AI tool predicts bail/appeal outcomes for Indian courts
- 50M+ pending cases, 70% citizens cannot afford legal consultation
- Scanned PDF judgments remain inaccessible

### 💡 Solution
A 4-module AI system that democratizes access to Indian legal research.

1.Home Page
<img width="1105" height="521" alt="image" src="https://github.com/user-attachments/assets/a67b992a-b237-4b40-8485-5486cc4720d3" />

2.Semantic Search
<img width="1366" height="768" alt="Screenshot (606)" src="https://github.com/user-attachments/assets/0721e4a4-ff24-4094-add0-c02e0a063650" />

3.Case Prediction Outcome
<img width="1366" height="768" alt="Screenshot (605)" src="https://github.com/user-attachments/assets/a2bb264b-f7dc-4d08-a656-4bda2943fd4e" />

4.AI Legal Assistant
<img width="1366" height="768" alt="Screenshot (610)" src="https://github.com/user-attachments/assets/3f9c89b8-1ceb-4416-ad29-a196d992da83" />

5.Document Analysis
<img width="1366" height="768" alt="Screenshot (616)" src="https://github.com/user-attachments/assets/e7232b1b-ae59-456f-9fbc-f75bceecfee2" />






---

## 🏗️ System Architecture

<img width="1172" height="514" alt="image" src="https://github.com/user-attachments/assets/c663eed0-44c1-41f2-8a07-78b986b05eb4" />

```
User Query
    │
    ▼
Query Preprocessing (normalize · expand · stopwords)
    │
    ▼
Sentence Embedding (multi-qa-MiniLM-L6-cos-v1 → 384-dim)
    │
    ├──► Module 1: Semantic Retrieval ──► ChromaDB (4,526 judgments)
    │
    ├──► Module 2: Outcome Prediction ──► XGBoost Classifier
    │
    ├──► Module 3: RAG Legal Analysis ──► DeepSeek-R1 (SambaNova API)
    │
    └──► Module 4: OCR Pipeline ──────► Tesseract + PyMuPDF
                                              │
                                              ▼
                                    FastAPI Backend
                                              │
                                              ▼
                                    React 18 Frontend
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 Semantic Search | Natural language query over 4,526 Indian court judgments |
| 🎯 Outcome Prediction | XGBoost predicts bail/appeal outcome with confidence % |
| 🤖 RAG Legal Analysis | DeepSeek-R1 generates 4-section legal analysis from precedents |
| 📄 OCR Ingestion | Upload scanned PDF judgments — auto-indexed to vector store |
| 🏷️ IPC Section Tags | Auto-extracted IPC sections displayed as badges |
| ⚖️ Indian Kanoon Links | Direct link to source judgment for every result |
| 📋 Copy Citation | One-click citation export for legal documents |

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Dataset size | 4,526 Indian court judgments |
| Retrieval similarity | 72–75% cosine similarity |
| Outcome prediction F1 | 0.76 weighted (6 classes) |
| Bail prediction accuracy | 74% |
| API response time | < 250ms core pipeline |
| Embedding model | multi-qa-MiniLM-L6-cos-v1 (384-dim) |

---

## 🗂️ Project Structure

```
justiceai/
├── backend/
│   ├── api/
│   │   ├── search.py          # /search/query endpoint
│   │   ├── predict.py         # /predict/outcome endpoint
│   │   ├── legal.py           # /legal/analyze endpoint
│   │   ├── ocr.py             # /ocr/upload endpoint
│   │   └── chatbot.py         # /chat endpoint
│   ├── services/
│   │   ├── search_service.py
│   │   ├── predict_service.py
│   │   └── ocr_service.py
│   ├── schemas/schemas.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx            # Main search UI
│       └── pages/
│           ├── SearchPage.jsx
│           ├── PredictPage.jsx
│           ├── ChatPage.jsx
│           └── UploadOCR.jsx
├── ml_pipeline/
│   ├── train.py               # XGBoost training pipeline
│   └── predictor.py           # Inference wrapper
├── rag_pipeline/
│   ├── retriever.py           # Semantic retrieval + metadata parsing
│   ├── rag_chain.py           # DeepSeek-R1 RAG pipeline
│   ├── vector_store.py        # ChromaDB wrapper
│   └── embeddings.py          # Sentence transformer utils
├── scripts/
│   ├── ingest_to_vectordb.py  # Bulk ChromaDB ingestion
│   ├── scraper.py             # Court judgment scraper
│   └── auto_label.py          # Outcome auto-labeling
├── data/                      # ⚠️ Not included — see Dataset Setup
├── chroma_store/              # ⚠️ Not included — run ingest script
└── README.md
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Tesseract OCR installed ([Windows](https://github.com/UB-Mannheim/tesseract/wiki) / `apt install tesseract-ocr`)
- SambaNova API key (free at [sambanova.ai](https://sambanova.ai))

### 1. Clone the repository
```bash
git clone https://github.com/prasan107/JusticeAI.git
cd JusticeAI
```

### 2. Create virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3. Install backend dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the root directory:
```env
SAMBANOVA_API_KEY=your_sambanova_api_key_here
CHROMA_DB_PATH=./chroma_store
```

### 5. Download and set up dataset
```
Download the processed dataset from:
👉 https://drive.google.com/drive/folders/1yR9tLaZ9umTsf8Vh123Z_VWliKi1FHuZ

Place files as:
data/processed/judgments_clean.json
```

### 6. Ingest data into ChromaDB
```bash
python scripts/ingest_to_vectordb.py
```
This will create the `chroma_store/` vector database (~4,526 embeddings).

### 7. Train the ML model
```bash
python ml_pipeline/train.py
```
This generates `ml_pipeline/xgboost_model.pkl`.

### 8. Start the backend
```bash
cd backend
uvicorn main:app --reload
```
Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 9. Start the frontend
```bash
cd frontend
npm install
npm start
```
Frontend runs at: `http://localhost:3000`

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/search/query` | Semantic case search |
| POST | `/predict/outcome` | Outcome prediction |
| POST | `/legal/analyze` | RAG legal analysis |
| POST | `/ocr/upload` | Upload PDF/image judgment |
| POST | `/chat` | Legal chatbot |

### Example — Search Request
```json
POST /search/query
{
  "query": "bail application murder accused IPC 302 first offender",
  "top_k": 5
}
```

### Example — Predict Request
```json
POST /predict/outcome
{
  "query": "accused charged under IPC 302 murder sessions court bail application"
}
```

---

## 🧠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Embedding | `multi-qa-MiniLM-L6-cos-v1` (sentence-transformers) |
| Vector DB | ChromaDB 0.4.x |
| ML Model | XGBoost + TF-IDF + Capped SMOTE |
| LLM | DeepSeek-R1 via SambaNova API |
| OCR | Tesseract v5 + PyMuPDF |
| Backend | FastAPI + Uvicorn |
| Frontend | React 18 + Axios |
| Dataset | 4,526 Indian court judgments (1990–2025) |

---

## 📚 Dataset Sources

| Source | Cases | Description |
|--------|-------|-------------|
| Bail judgment dataset | ~2,000 | Bail application cases |
| JUDIPL corpus | ~1,200 | High Court judgments |
| Scraped HC judgments | ~800 | Web-scraped orders |
| CSV corpus | ~526 | Annotated case records |

> ⚠️ Dataset not included in repo due to size. Download from Google Drive link above.

---

## 👥 Team

**Department of Artificial Intelligence and Data Science**
**SRM Valliammai Engineering College, Chennai**

| Name | Role |
|------|------|
| Prasannaraj S | Full-Stack Development, ML Pipeline, RAG Pipeline, Integration |

---

## 📄 Publication

> **JusticeAI: An Intelligent Legal Research System for the Indian Judiciary Using Semantic Search, Outcome Prediction, and Retrieval-Augmented Generation**
>
> 📰 **Indonesian Journal of Science and Technology** — ISSN: 2528-1410
> 🔖 Indexed in **SCOPUS**
> 🎤 Presented at **ICCET 2026** — 24th March 2026
> ✅ **Accepted & Registered**

---

## 🔭 Future Work

- [ ] ILDC corpus integration (35,000 Supreme Court cases)
- [ ] Hybrid BM25 + semantic search
- [ ] Multilingual query support (Tamil, Hindi)
- [ ] Legal-BERT fine-tuning on Indian corpus
- [ ] Cloud deployment (AWS / Azure)
- [ ] Mobile app (React Native)

---

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">Built with ❤️ for democratizing legal access in India</p>
