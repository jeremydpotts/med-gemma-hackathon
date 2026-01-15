#!/bin/bash

# KNOVA Quest Think Tank Session Launcher
# Quick-start script for the interactive Think Tank viewer

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║    Med-Gemma Hackathon Think Tank Session Launcher          ║"
echo "║    $100k Impact Challenge Brainstorming System               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Change to parent directory (project root)
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$PROJECT_DIR"

echo "📂 Project directory: $PROJECT_DIR"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check if session file exists
SESSION_FILE="brainstorming/sessions/SESSION_01_initial_ideation.md"
if [ ! -f "$SESSION_FILE" ]; then
    echo "⚠️  Warning: Session file not found: $SESSION_FILE"
    echo "   The viewer will show an error until the session file exists."
    echo ""
fi

# Kill any existing server on port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "🛑 Stopping existing server on port 8000..."
    lsof -Pi :8000 -sTCP:LISTEN -t | xargs kill -9 2>/dev/null
    sleep 1
fi

# Start the server
echo "🚀 Starting Think Tank server..."
echo ""

python3 brainstorming/think-tank-server.py &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo ""
    echo "✅ Server started successfully!"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🌐 Open your browser to:"
    echo "   http://localhost:8000/brainstorming/think-tank-viewer.html"
    echo ""
    echo "📝 Session file:"
    echo "   $SESSION_FILE"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""

    # Wait for user to stop
    wait $SERVER_PID
else
    echo "❌ Failed to start server. Please check for errors above."
    exit 1
fi
