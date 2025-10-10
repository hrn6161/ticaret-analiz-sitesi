import multiprocessing

# Worker sayısı
workers = 1
worker_class = 'sync'

# Timeout süreleri - Render için optimize
timeout = 30
graceful_timeout = 10
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Worker başlangıç
def on_starting(server):
    print("🚀 OPTİMİZE CRAWLER SİSTEMİ BAŞLATILIYOR...")
