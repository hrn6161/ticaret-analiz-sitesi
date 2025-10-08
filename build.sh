#!/bin/bash
set -o errexit

echo "🔧 Pip ve wheel güncelleniyor..."
pip install --upgrade pip wheel

echo "🔧 Python kütüphaneleri kuruluyor..."
pip install -r requirements.txt

echo "✅ Build tamamlandı!"
