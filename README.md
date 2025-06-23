# Instagram Comment Scraper

## Overview
Scrapes top-level comments from Instagram posts using Selenium in mobile emulation mode.

## Setup
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Add your Google Sheets credentials as `creds.json` if using Sheets for input.

## Folder Structure

Before running the scraper, your project directory should look like this:

```
comments-scraping/
│
├── main.py
├── config.py
├── requirements.txt
├── .gitignore
├── README.md
│
├── scrapers/
│   └── instagram_scraper.py
│
├── utils/
│   └── sheet_handler.py
│
└── creds.json   # (DO NOT add to git! Each user adds their own)
```

## ChromeDriver Installation

**chromedriver is not a Python package so cant be added, have to install

You have two options for setting up chromedriver:

### 1. Automated Management
- Add `webdriver-manager` to your `requirements.txt` 
- In your code, use:
  ```python
  from selenium import webdriver
  from webdriver_manager.chrome import ChromeDriverManager

  driver = webdriver.Chrome(ChromeDriverManager().install())
  ```
- This will automatically download and manage the correct chromedriver version for you.

### 2. Manual Installation
- Download the correct version of chromedriver from the [official site](https://sites.google.com/chromium.org/driver/).
- Place the `chromedriver.exe` somewhere on your system and add its location to your system PATH, or reference its path directly in your code.
- Each team member is responsible for ensuring chromedriver is installed and accessible on their machine.

## Usage
1. Add Instagram post URLs to your input source (Google Sheet or list in code), or use the sheet shared.
2. Run:
   ```
   python main.py
   ```
3. On the first run, you will be prompted to log in to Instagram manually in the opened browser window. Once you have logged in, **press Enter in the terminal** to continue. The script will save your login cookies for future sessions, so you won't need to log in again unless the cookies expire or are deleted.
4. Scraped comments will be saved as JSON.

## Notes
- Requires Chrome and ChromeDriver installed (or use `webdriver-manager` for automatic management).
- For Google Sheets integration, set up your API credentials.
- Do NOT commit `creds.json` to version control.
