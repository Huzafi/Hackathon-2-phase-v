#!/bin/bash
# Stop Script for Local Development
# This script stops all services and optionally removes data

set -e

echo "🛑 Stopping Advanced Task Management - Local Development"
echo ""

# Check if user wants to remove data
read -p "Do you want to remove database data? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Stopping services and removing data..."
    docker-compose -f docker-compose.local.yml down -v
    echo "✅ Data removed"
else
    echo "🛑 Stopping services (data preserved)..."
    docker-compose -f docker-compose.local.yml down
    echo "✅ Services stopped"
fi

echo ""
echo "💡 To start again, run: ./start-local.sh"
echo ""
