#!/bin/bash
set -o errexit
cd ~/ticaret-analiz-sitesi
cat > build.sh << 'EOF'
#!/bin/bash
set -o errexit
apt-get update -y

apt-get install -y wget gnupg unzip curl xvfb

wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update -y
apt-get install -y google-chrome-stable
CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip
unzip /tmp/chromedriver.zip -d /usr/local/bin/
chmod +x /usr/local/bin/chromedriver
echo "✅ Chrome versiyonu: $(google-chrome-stable --version)"
echo "✅ ChromeDriver versiyonu: $(chromedriver --version)"
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Build tamamlandı!"
