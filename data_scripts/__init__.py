import sys
import os
import glob

DATASTORE = "data-store"

def find_file(pattern, label):
    files = glob.glob(os.path.join(DATASTORE, pattern))
    if not files:
        sys.exit(f"No {pattern} found in {DATASTORE}/")
    return files[0]
