import multiprocessing
import os

bind = ["0.0.0.0:9999"]
workers = int(os.getenv("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2))
threads = int(os.getenv("PYTHON_MAX_THREADS", 1))
timeout = 240
