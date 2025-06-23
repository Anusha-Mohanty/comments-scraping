import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import SHEET_ID, SHEET_NAME, CREDENTIALS_JSON, COMMENTS_LINK_COLUMN
import pandas as pd

def get_sheet():
    """Authorize and return the worksheet object."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_JSON, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        return sheet
    except FileNotFoundError:
        print(f"Error: The credentials file '{CREDENTIALS_JSON}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while connecting to Google Sheets: {e}")
        return None

def get_all_posts():
    """Fetch all records from the sheet."""
    sheet = get_sheet()
    if sheet:
        return sheet.get_all_records()
    return []

def update_status_for_post(row_index, status, comment_count=None, comments_link=None, analyzed_link=None, wordcloud_link=None):
    """Update the status and output links for a specific row in the sheet."""
    sheet = get_sheet()
    if not sheet:
        return
        
    try:
        # Find column numbers dynamically
        headers = sheet.row_values(1)
        status_col = headers.index('Status') + 1
        count_col = headers.index('Comments Count') + 1
        comments_link_col = headers.index(COMMENTS_LINK_COLUMN) + 1
        analyzed_col = headers.index('Analyzed Comments Link') + 1
        wordcloud_col = headers.index('Wordcloud All Link') + 1
        
        # Update cells
        sheet.update_cell(row_index, status_col, status)
        if comment_count is not None:
            sheet.update_cell(row_index, count_col, comment_count)
        if comments_link:
            sheet.update_cell(row_index, comments_link_col, comments_link)
        if analyzed_link:
            sheet.update_cell(row_index, analyzed_col, analyzed_link)
        if wordcloud_link:
            sheet.update_cell(row_index, wordcloud_col, wordcloud_link)
            
        print(f"Updated sheet for row {row_index}.")
            
    except Exception as e:
        print(f"Failed to update sheet for row {row_index}: {e}") 