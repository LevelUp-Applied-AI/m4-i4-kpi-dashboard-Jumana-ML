"""
Environment validation script — do not modify.

Run this after installing requirements.txt to confirm your environment is correct:
    python test_environment.py

Expected output:
    pandas: <version>
    matplotlib: <version>
    Environment OK
"""

import sys


def check_environment():
    try:
        import pytest
        import numpy
        import pandas
        import torch
        import matplotlib
        import seaborn
        import scipy
        import statsmodels
        import sqlalchemy
        import psycopg2
        print(f"pytest: {pytest.__version__}")
        print(f"numpy: {numpy.__version__}")
        print(f"pandas: {pandas.__version__}")
        print(f"torch: {torch.__version__}")
        print(f"matplotlib: {matplotlib.__version__}")
        print(f"seaborn: {seaborn.__version__}")    
        print(f"scipy: {scipy.__version__}")
        print(f"statsmodels: {statsmodels.__version__}")
        print(f"sqlalchemy: {sqlalchemy.__version__}")
        print(f"psycopg: {psycopg.__version__}")
        print("Environment OK")
    except ImportError as e:
        print(f"ImportError: {e}", file=sys.stderr)
        print(
            "\nYour environment is missing a required package.",
            file=sys.stderr,
        )
        print(
            "Confirm your venv is active ((.venv) prefix in prompt), then run:",
            file=sys.stderr,
        )
        print("    pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    check_environment()