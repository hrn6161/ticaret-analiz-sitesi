#!/bin/bash
set -o errexit

echo "🔧 Python kütüphaneleri kuruluyor..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build tamamlandı!"
