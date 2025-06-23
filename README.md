# Instagram Comment Scraper

## Overview
Scrapes top-level comments from Instagram posts using Selenium in mobile emulation mode.

## Setup
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Add your Google Sheets credentials as `creds.json` if using Sheets for input.

## Usage
1. Add Instagram post URLs to your input source (Google Sheet or list in code). or use the sheet shared.
2. Run:
   ```
   python instagram_scraper.py
   ```
3. Scraped comments will be saved as JSON or printed to console.

## Notes
- Requires ChromeDriver and Chrome installed.
- For Google Sheets integration, set up your API credentials.
