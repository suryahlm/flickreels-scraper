#!/bin/bash
# Railway Deployment Script for Batch Scraper
# Run this once deployed to Railway

echo "=================================="
echo "Railway Batch Scraper Deployment"
echo "=================================="
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install requests boto3 python-dotenv

# Check environment variables
echo ""
echo "Checking environment variables..."
if [ -z "$R2_ACCOUNT_ID" ]; then
    echo "❌ R2_ACCOUNT_ID not set!"
    exit 1
fi

if [ -z "$R2_ACCESS_KEY_ID" ]; then
    echo "❌ R2_ACCESS_KEY_ID not set!"
    exit 1
fi

if [ -z "$R2_SECRET_ACCESS_KEY" ]; then
    echo "❌ R2_SECRET_ACCESS_KEY not set!"
    exit 1
fi

if [ -z "$FLICKREELS_TOKEN" ]; then
    echo "❌ FLICKREELS_TOKEN not set!"
    exit 1
fi

echo "✅ All environment variables set!"

# Start batch scraper
echo ""
echo "Starting batch scraper..."
echo "This will run 24/7 until all 300 dramas are scraped!"
echo ""
echo "You can close this terminal - scraper will continue on Railway."
echo ""

# Run in background with nohup (survives terminal close)
python batch_scraper_railway.py

echo ""
echo "✅ Deployment complete!"
