#!/bin/bash
# Quick Start Script for Local Development
# This script starts all services and runs migrations

set -e

echo "🚀 Starting Advanced Task Management - Local Development"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if .env.local exists, create from example if not
if [ ! -f .env.local ]; then
    echo "📝 Creating .env.local from template..."
    cp .env.local.example .env.local
    echo "✅ Created .env.local - Please update JWT_SECRET with a random 32+ character string"
    echo ""
fi

# Start services
echo "🐳 Starting services (PostgreSQL, Backend, Frontend)..."
docker-compose -f docker-compose.local.yml up -d

echo ""
echo "⏳ Waiting for services to be ready..."

# Wait for PostgreSQL to be healthy
echo "📊 Waiting for PostgreSQL..."
until docker-compose -f docker-compose.local.yml exec -T postgres pg_isready -U todouser > /dev/null 2>&1; do
    sleep 2
done
echo "✅ PostgreSQL is ready"

# Wait for backend to be ready
echo "🔧 Waiting for backend API..."
until curl -s http://localhost:8000/ > /dev/null 2>&1; do
    sleep 2
done
echo "✅ Backend API is ready"

# Wait for frontend to be ready
echo "🎨 Waiting for frontend..."
until curl -s http://localhost:3000/ > /dev/null 2>&1; do
    sleep 2
done
echo "✅ Frontend is ready"

echo ""
echo "🎉 All services are running!"
echo ""
echo "📍 Access your application:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📋 Useful commands:"
echo "   View logs:       docker-compose -f docker-compose.local.yml logs -f"
echo "   Stop services:   docker-compose -f docker-compose.local.yml down"
echo "   Restart:         docker-compose -f docker-compose.local.yml restart"
echo ""
echo "🔧 To create a test user, visit: http://localhost:3000/signup"
echo ""
