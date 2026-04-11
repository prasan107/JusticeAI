#!/bin/bash
echo "Starting JusticeAI..."

# Start backend
cd backend
uvicorn main:app --reload --port 8000 &
cd ..

# Start frontend
cd frontend
npm start &
cd ..

echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
