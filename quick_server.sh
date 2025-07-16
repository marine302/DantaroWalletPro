#!/bin/bash
cd /Users/danielkwon/DantaroWalletPro/dantarowallet
export PYTHONPATH=/Users/danielkwon/DantaroWalletPro/dantarowallet
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --log-level error --no-access-log
