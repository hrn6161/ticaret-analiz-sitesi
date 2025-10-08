#!/bin/bash
set -o errexit

echo "🔧 Sistem bağımlılıkları kuruluyor..."
apt-get update -y
apt-get install -y wget unzip curl xvfb

echo "🔧 Chrome kuruluyor..."
wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get install -y /tmp/chrome.deb

echo "🔧 ChromeDriver kuruluyor..."
CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip
unzip /tmp/chromedriver.zip -d /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

echo "🔧 Python kütüphaneleri kuruluyor..."
pip install -r requirements.txt

echo "✅ Build tamamlandı!"
