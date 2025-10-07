#!/bin/bash
set -o errexit

echo "🚀 Uygulama başlatılıyor..."

# Chrome kontrolü
echo "🔍 Chrome kontrolü..."
google-chrome-stable --version || echo "Chrome bulunamadı"
chromedriver --version || echo "ChromeDriver bulunamadı"

# Uygulamayı başlat
exec python app.py
