import multiprocessing

# Worker sayısı
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class'ı
worker_class = "sync"

# Timeout süresi (saniye)
timeout = 120

# Bind adresi
bind = "0.0.0.0:5000"

# Log seviyesi
loglevel = "info"

# Access log
accesslog = "-"

# Error log
errorlog = "-"

# Worker timeout
graceful_timeout = 120

# Keepalive
keepalive = 5
