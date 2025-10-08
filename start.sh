#!/bin/bash
set -o errexit

echo "🚀 Uygulama başlatılıyor..."
echo "🔍 Chrome kontrolü..."
google-chrome --version || echo "Chrome bulunamadı"
chromedriver --version || echo "ChromeDriver bulunamadı"

exec python app.py
