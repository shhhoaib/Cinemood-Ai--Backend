import os

DATA_DIR = os.environ.get("CINEMOOD_DATA_DIR", "")
if not DATA_DIR:
    is_vercel = os.environ.get("VERCEL", "")
    if is_vercel:
        DATA_DIR = "/tmp/cinemood_data"
    else:
        DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "user_data")

os.makedirs(DATA_DIR, exist_ok=True)
