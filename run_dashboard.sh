#!/usr/bin/env bash
set -euo pipefail
source /opt/agentguard/.venv/bin/activate
python3 /opt/agentguard/scripts/build_dashboard_data.py
streamlit run /opt/agentguard/dashboard_app.py --server.address 0.0.0.0 --server.port 8501
