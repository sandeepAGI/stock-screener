#!/bin/bash
# Development script for StockAnalyzer Pro
# Starts FastAPI backend and React frontend for development

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}StockAnalyzer Pro - Development Mode${NC}"
echo "======================================"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found. Run: python -m venv venv${NC}"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    cd frontend && npm install && cd ..
fi

# Start FastAPI backend
echo -e "${GREEN}Starting FastAPI backend on http://127.0.0.1:8000...${NC}"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}Backend is ready!${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}Backend failed to start${NC}"
        exit 1
    fi
done

# Start React frontend
echo -e "${GREEN}Starting React frontend on http://localhost:5173...${NC}"
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${GREEN}Development servers running:${NC}"
echo "  - Backend API: http://127.0.0.1:8000"
echo "  - API Docs:    http://127.0.0.1:8000/api/docs"
echo "  - Frontend:    http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for processes
wait
