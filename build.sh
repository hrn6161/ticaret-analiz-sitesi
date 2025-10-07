#!/bin/bash
set -o errexit

echo "🔧 Python kütüphaneleri kuruluyor..."
pip install -r requirements.txt

echo "✅ Build tamamlandı!"
