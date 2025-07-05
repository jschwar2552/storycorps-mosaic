#!/bin/bash

echo "🚀 Deploying Mosaic App..."
echo ""

# Deploy API to Vercel
echo "📦 Deploying API to Vercel..."
vercel --prod

if [ $? -eq 0 ]; then
    echo "✅ API deployed successfully!"
else
    echo "❌ API deployment failed!"
    exit 1
fi

echo ""

# Deploy Frontend to GitHub Pages
echo "📦 Building and deploying frontend to GitHub Pages..."
cd frontend

# Build the React app
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
else
    echo "❌ Build failed!"
    exit 1
fi

# Deploy to GitHub Pages
npm run deploy

if [ $? -eq 0 ]; then
    echo "✅ Frontend deployed successfully!"
else
    echo "❌ Frontend deployment failed!"
    exit 1
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📍 API URL: https://storycorps-mosaic.vercel.app/api/chat"
echo "📍 Frontend URL: https://jschwar2552.github.io/storycorps-mosaic/"
echo ""
echo "⚡ Test the API with:"
echo "curl -X POST https://storycorps-mosaic.vercel.app/api/chat \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"message\": \"Tell me about family struggles\"}'"