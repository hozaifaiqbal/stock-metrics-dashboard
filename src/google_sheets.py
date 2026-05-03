import os
import pandas as pd
import gspread
from dotenv import load_dotenv

load_dotenv()

SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")


def get_worksheet_df(spreadsheet, worksheet_name):
    worksheet = spreadsheet.worksheet(worksheet_name)
    records = worksheet.get_all_records()
    return pd.DataFrame(records)


def load_all_sheets():
    if not CREDENTIALS_PATH:
        raise ValueError("GOOGLE_CREDENTIALS_PATH is missing in .env")

    if not SHEET_NAME:
        raise ValueError("GOOGLE_SHEET_NAME is missing in .env")

    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    if SHEET_ID:
        spreadsheet = gc.open_by_key(SHEET_ID)
    else:
        if not SHEET_NAME:
            raise ValueError("GOOGLE_SHEET_NAME or GOOGLE_SHEET_ID is missing")
        spreadsheet = gc.open(SHEET_NAME)


    transactions = get_worksheet_df(spreadsheet, "1_TRANSACTIONS")
    stock_master = get_worksheet_df(spreadsheet, "2_STOCK_MASTER")
    thesis = get_worksheet_df(spreadsheet, "3_THESIS_TRACKER")
    corporate_actions = get_worksheet_df(spreadsheet, "4_CORPORATE_ACTIONS")
    settings = get_worksheet_df(spreadsheet, "5_SETTINGS")

    return {
        "transactions": transactions,
        "stock_master": stock_master,
        "thesis": thesis,
        "corporate_actions": corporate_actions,
        "settings": settings,
    }


if __name__ == "__main__":
    # Sanity Check
    print(f"Targeting Sheet: '{SHEET_NAME}'")
    print(f"Using Credentials at: '{CREDENTIALS_PATH}'")
    
    if not SHEET_NAME or not CREDENTIALS_PATH:
        print("ERROR: Environment variables not loaded. Check your .env file path!")
    else:
        try:
            data = load_all_sheets()
            print("Successfully connected!")
            print(data["transactions"].head())
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"\n[!] ERROR: Could not find '{SHEET_NAME}'.")
            print("Did you share the sheet with the email found in your JSON file?")