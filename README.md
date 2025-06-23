# Instagram Comment Scraper & Sentiment Analyzer

## Overview
This project scrapes comments from Instagram posts (using Selenium in mobile emulation), translates them to English, and performs sentiment analysis. It generates a word cloud and a sentiment summary for the most frequent words, making it easy to embed insights in campaign reports or dashboards.

## Features
- **Automated Instagram comment scraping** (top-level comments only, robust to dynamic DOM)
- **Mobile browser emulation** for higher scraping reliability
- **Google Sheets integration** for input URLs and output status/links
- **Translation** of all comments to English (using Google Translate API via `deep-translator`)
- **Sentiment analysis** using NLTK VADER
- **Word cloud generation** for brand-level insights
- **Summary CSV/JSON** of top 20 words with frequency, sentiment, and example contexts
- **Modular, extensible codebase**

## Setup
1. **Clone the repository**
   ```sh
   git clone <your-repo-link>
   cd comment_analysis
   ```
2. **Create and activate a virtual environment**
   ```sh
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. **Install dependencies**
   ```sh
   pip install -r social_sentiment_analyzer/requirements.txt
   pip install deep-translator
   ```
4. **Google Sheets & Drive API setup**
   - Place your Google API credentials as `creds.json` in the project root.
   - Update `config.py` with your Sheet ID and column names if needed.

## Usage
1. **Add Instagram post URLs to your Google Sheet** (one per row, in the `Post Urls` column).
2. **Run the main script**
   ```sh
   python social_sentiment_analyzer/main.py
   ```
3. **What happens:**
   - The script logs into Instagram (using cookies if available).
   - For each post:
     - Scrapes all top-level comments (skipping replies/captions).
     - Translates comments to English.
     - Performs sentiment analysis on each comment.
   - Aggregates all comments for the brand/campaign.
   - Generates:
     - `output/wordcloud_{brand}.png` (word cloud image)
     - `output/sentiment_summary_{brand}.csv` (top 20 words, frequency, sentiment, examples)
     - `output/sentiment_summary_{brand}.json` (same as CSV, for dashboards)
   - Updates the Google Sheet with output links.

## Output Files
- **Word Cloud:** `output/wordcloud_{brand}.png`
- **Sentiment Summary CSV:** `output/sentiment_summary_{brand}.csv`
- **Sentiment Summary JSON:** `output/sentiment_summary_{brand}.json`

## Notes for Team Use
- **Extensible:** Add new brands/campaigns by updating the Google Sheet—no code changes needed.
- **Cloud Sharing:** For sharing outputs, upload PNG/CSV/JSON to Google Drive and update the sheet with shareable links.
- **Deployment:** Selenium requires ChromeDriver and a GUI or headless environment. Confirm server support before deploying.
- **Customization:**
  - Number of top words is configurable in code (default: 20).
  - Stopword lists and language support can be extended.
  - Can be adapted for other social platforms with minor changes.

## Troubleshooting
- If scraping fails, check Instagram layout changes and update selectors in `instagram_scraper.py`.
- If translation fails, ensure `deep-translator` is installed and you have internet access.
- For Google Sheets/Drive issues, verify your API credentials and sheet permissions.