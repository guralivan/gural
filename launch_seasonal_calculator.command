#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
streamlit run seasonal_expenses_calculator.py --server.port 8505


