#!/bin/bash

echo "🧪 Running CBM Analytics Test Suite"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${2}${1}${NC}"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_status "❌ Docker is not running. Please start Docker first." $RED
    exit 1
fi

print_status "🏗️  Building containers..." $YELLOW
docker-compose build --quiet

# Run backend tests
print_status "🐍 Running Backend Tests..." $YELLOW
echo "----------------------------"

if docker-compose run --rm test-backend; then
    print_status "✅ Backend tests passed!" $GREEN
    BACKEND_SUCCESS=true
else
    print_status "❌ Backend tests failed!" $RED
    BACKEND_SUCCESS=false
fi

echo ""

# Run frontend tests
print_status "⚛️  Running Frontend Tests..." $YELLOW
echo "-----------------------------"

if docker-compose run --rm test-frontend; then
    print_status "✅ Frontend tests passed!" $GREEN
    FRONTEND_SUCCESS=true
else
    print_status "❌ Frontend tests failed!" $RED
    FRONTEND_SUCCESS=false
fi

echo ""
echo "=================================="
print_status "📊 Test Summary" $YELLOW

if [ "$BACKEND_SUCCESS" = true ]; then
    print_status "Backend:  ✅ PASSED" $GREEN
else
    print_status "Backend:  ❌ FAILED" $RED
fi

if [ "$FRONTEND_SUCCESS" = true ]; then
    print_status "Frontend: ✅ PASSED" $GREEN
else
    print_status "Frontend: ❌ FAILED" $RED
fi

if [ "$BACKEND_SUCCESS" = true ] && [ "$FRONTEND_SUCCESS" = true ]; then
    print_status "🎉 All tests passed!" $GREEN
    exit 0
else
    print_status "💥 Some tests failed!" $RED
    exit 1
fi