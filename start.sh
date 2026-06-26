#!/bin/bash
set -e

echo "🚀 Starting ОфисРайд application..."

# Start Django (Daphne ASGI server for WebSocket support)
echo "🐍 Starting Django on port 8000..."
cd /app/carpool_project
python3 manage.py migrate --noinput
python3 manage.py seed_data 2>/dev/null || true
python3 manage.py collectstatic --noinput 2>/dev/null || true

# Start Daphne in background
daphne -b 0.0.0.0 -p 8000 carpool.asgi:application &
DJANGO_PID=$!

echo "✅ Django started (PID: $DJANGO_PID)"

# Wait for Django to be ready
sleep 3

# Start Next.js proxy on port 3000
echo "⚡ Starting Next.js proxy on port 3000..."
cd /app
node_modules/.bin/next start -p 3000 &
NEXT_PID=$!

echo "✅ Next.js started (PID: $NEXT_PID)"
echo "🌐 Application ready!"

# Wait for any process to exit
wait -n $DJANGO_PID $NEXT_PID
