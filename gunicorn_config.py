import multiprocessing

# Worker sayısı
workers = 1
worker_class = 'sync'

# Timeout süreleri
timeout = 25
graceful_timeout = 10
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
