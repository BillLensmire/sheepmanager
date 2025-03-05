"""
Gunicorn configuration file for the Sheep Manager application
"""

# The socket to bind
bind = "0.0.0.0:8000"

# Number of worker processes
workers = 3

# Number of threads per worker
threads = 2

# The directory to use for the worker heartbeat file
worker_tmp_dir = "/dev/shm"

# The type of workers to use
worker_class = "sync"

# The maximum number of requests a worker will process before restarting
max_requests = 1000
max_requests_jitter = 50

# Timeout for graceful workers restart
timeout = 30

# Logging
accesslog = "/var/log/gunicorn/sheepmanager-access.log"
errorlog = "/var/log/gunicorn/sheepmanager-error.log"
loglevel = "info"

# Process name
proc_name = "sheepmanager"
