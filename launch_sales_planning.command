#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
streamlit run sales_planning_app.py --server.port 8509
