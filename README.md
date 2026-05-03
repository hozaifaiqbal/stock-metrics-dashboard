# Stock Metrics Dashboard

A privacy-first portfolio analytics and reporting system for Indian equity investors.

## Overview

Stock Metrics Dashboard connects portfolio transaction data from Google Sheets or uploaded Excel/CSV files, calculates live portfolio metrics, compares performance against benchmarks, generates dashboards, and sends weekly PDF reports through email automation.

## Features

- Google Sheets integration
- CSV/Excel upload support
- Live market price fetching
- Realized and unrealized P&L
- CAGR and return metrics
- Nifty 50 benchmark comparison
- USD-INR comparison
- Streamlit dashboard
- Weekly PDF report generation
- Email automation
- Template download for public users

## Tech Stack

- Python
- pandas
- yfinance
- gspread
- Google Sheets API
- Streamlit
- Plotly
- Playwright
- Gmail SMTP
- GitHub Actions

## Project Pipeline

Google Sheet / Excel  
→ Python ingestion  
→ Data cleaning  
→ Portfolio engine  
→ Live prices  
→ Benchmark comparison  
→ Dashboard  
→ HTML/PDF report  
→ Email automation

## How To Run Locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
