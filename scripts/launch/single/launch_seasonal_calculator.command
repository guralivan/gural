#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
streamlit run apps/seasonal_calculator/seasonal_expenses_calculator.py --server.port 8505


