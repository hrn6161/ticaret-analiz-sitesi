#!/bin/bash
set -o errexit

echo "🔧 Sistem paketleri güncelleniyor..."
apt-get update -y

echo "🔧 Chrome ve dependencies kuruluyor..."
apt-get install -y wget gnupg unzip curl xvfb

# Chrome'u kur
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update -y
apt-get install -y google-chrome-stable

# ChromeDriver'ı kur
CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip
unzip /tmp/chromedriver.zip -d /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

# Chrome versiyonunu kontrol et
echo "✅ Chrome versiyonu: $(google-chrome-stable --version)"
echo "✅ ChromeDriver versiyonu: $(chromedriver --version)"

echo "🔧 Python kütüphaneleri kuruluyor..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build tamamlandı!"
