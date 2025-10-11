import multiprocessing

# Worker sayısı
workers = 2

# Worker class'ı
worker_class = 'sync'

# Timeout süresi (saniye) - Render'ın 30s limitinden uzun tutalım
timeout = 300  # 5 dakika

# Worker bağlantıları
worker_connections = 1000

# Max requests
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Bind
bind = '0.0.0.0:5000'
