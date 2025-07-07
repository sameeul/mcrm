#!/bin/bash

# Secure Order Management System - Run Script
# This script activates the virtual environment and starts the application

echo "Starting Secure Order Management System..."
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if [ ! -f "venv/pyvenv.cfg" ] || ! pip show flask > /dev/null 2>&1; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo "Dependencies installed."
fi

# Check if database exists
if [ ! -f "order_management.db" ]; then
    echo ""
    echo "Database not found. Please run the initialization script first:"
    echo "  source venv/bin/activate"
    echo "  python3 init_db.py"
    echo ""
    echo "Or run this script with 'init' parameter:"
    echo "  ./run.sh init"
    echo ""
    
    if [ "$1" = "init" ]; then
        echo "Running database initialization..."
        python3 init_db.py
    else
        exit 1
    fi
fi

# Set development environment if requested
if [ "$1" = "dev" ] || [ "$2" = "dev" ]; then
    export FLASK_ENV=development
    echo "Running in development mode..."
else
    echo "Running in production mode..."
fi

# Start the application
echo "Starting Flask application..."
echo "Access the application at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
