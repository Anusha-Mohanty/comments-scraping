import pandas as pd
import os
import re
import json
import csv
from config import *
from scrapers.instagram_scraper import get_comments_from_post
from analysis.sentiment import analyze_comments
from analysis.wordcloud_generator import generate_wordcloud, get_top_words
from analysis.cleaner import clean_comments
from utils.sheet_handler import get_all_posts, update_status_for_post
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

COOKIES_FILE = 'insta_cookies.json'

def sanitize_filename(url: str) -> str:
    """Sanitizes a URL to be used as a valid part of a filename."""
    sanitized = re.sub(r'https?://www.', '', url)
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', sanitized)
    return sanitized.replace('/', '_').replace('?', '_').replace('=', '')

def save_cookies(driver, path=COOKIES_FILE):
    cookies = driver.get_cookies()
    with open(path, 'w') as f:
        json.dump(cookies, f)
    print(f"Cookies saved to {path}")

def load_cookies(driver, path=COOKIES_FILE):
    if not os.path.exists(path):
        return False
    with open(path, 'r') as f:
        cookies = json.load(f)
    for cookie in cookies:
        # Selenium requires expiry to be int, not float
        if 'expiry' in cookie:
            cookie['expiry'] = int(cookie['expiry'])
        try:
            driver.add_cookie(cookie)
        except Exception:
            continue
    print(f"Cookies loaded from {path}")
    return True

def infer_brand_from_urls(urls):
    """Infer a brand name from a list of Instagram post URLs (e.g., by extracting the username or domain)."""
    # Example: https://www.instagram.com/reel/POSTID/?igsh=... or https://www.instagram.com/p/POSTID/
    # We'll extract the part after 'instagram.com/' and before the next '/'
    if not urls:
        return "brand"
    import re
    usernames = []
    for url in urls:
        match = re.search(r"instagram.com/([^/?#]+)/", url)
        if match:
            usernames.append(match.group(1))
    if usernames:
        # If all posts are from the same type (e.g., 'reel', 'p'), just use 'brand'
        # Otherwise, join unique types
        unique = set(usernames)
        if len(unique) == 1:
            return unique.pop()
        return "_".join(sorted(unique))
    return "brand"

def main():
    """Main function to run the social sentiment analysis pipeline."""
    print("Starting the sentiment analysis pipeline with Google Sheets integration...")

    posts_to_process = get_all_posts()
    if not posts_to_process:
        print("No posts found in the Google Sheet. Exiting.")
        return

    # Set up the Selenium driver with mobile emulation
    print("Launching Chrome browser for Selenium (mobile emulation)...")
    mobile_emulation = {
        "deviceMetrics": {"width": 414, "height": 896, "pixelRatio": 3},
        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    }
    options = webdriver.ChromeOptions()
    options.add_experimental_option("mobileEmulation", mobile_emulation)
    options.add_argument('--disable-blink-features=AutomationControlled')
    try:
        driver = webdriver.Chrome(options=options)
        print("Chrome browser launched successfully in mobile emulation mode.")
    except Exception as e:
        print(f"Failed to launch Chrome browser: {e}")
        return

    try:
        # Open Instagram home and try to load cookies
        driver.get("https://www.instagram.com/")
        if load_cookies(driver):
            driver.refresh()
            time.sleep(3)
            print("Logged in using saved cookies.")
        else:
            print("Please log in to Instagram in the browser window.")
            input("After you have logged in and see your feed, press Enter here to continue scraping posts...")
            save_cookies(driver)

        all_cleaned_comments = []  # Aggregate for brand-level word cloud
        processed_row_indices = []  # To update sheet with brand-level word cloud link
        post_urls = []
        
        for idx, post in enumerate(posts_to_process):
            row_index = idx + 2  # GSpread rows are 1-indexed, +1 for header
            url = post.get(URL_COLUMN)
            status = post.get(STATUS_COLUMN)

            if not url or status == 'Completed':
                print(f"Skipping row {row_index}: URL is missing or status is 'Completed'.")
                continue

            post_urls.append(url)
            processed_row_indices.append(row_index)
            print(f"Processing post from row {row_index}: {url}")
            update_status_for_post(row_index, "In Progress")

            # --- 1. Scrape comments ---
            comments = get_comments_from_post(url, SCROLL_COUNT, driver=driver)
            if not comments:
                print(f"No comments were scraped for {url}. Skipping to next post.")
                update_status_for_post(row_index, "Failed: No comments found")
                continue
            
            # --- File Paths ---
            base_filename = sanitize_filename(url)
            data_dir = "social_sentiment_analyzer/data"
            output_dir = "social_sentiment_analyzer/output"
            os.makedirs(data_dir, exist_ok=True)
            os.makedirs(output_dir, exist_ok=True)

            comments_json_path = os.path.join(data_dir, f"comments_{base_filename}.json")
            analyzed_path = os.path.join(data_dir, f"analyzed_{base_filename}.csv")
            wordcloud_path = os.path.join(output_dir, f"wordcloud_{base_filename}.png")
            
            # --- 2. Save Comments as JSON ---
            with open(comments_json_path, 'w', encoding='utf-8') as f:
                json.dump(comments, f, ensure_ascii=False, indent=2)
            print(f"Comments saved to {comments_json_path}")

            # --- 3. Analyze and Save Sentiment ---
            sentiment_df = analyze_comments(comments)
            if sentiment_df.empty:
                print(f"Sentiment analysis returned no results for {url}.")
                update_status_for_post(row_index, "Failed: Analysis error")
                continue
            sentiment_df.to_csv(analyzed_path, index=False)
            print(f"Sentiment analysis saved to {analyzed_path}")

            # --- 4. Clean and Generate Word Cloud ---
            sentiment_df['cleaned_comment'] = clean_comments(sentiment_df['comment'].tolist())
            all_comments_for_cloud = sentiment_df['cleaned_comment'].tolist()
            all_cleaned_comments.extend(sentiment_df['cleaned_comment'].tolist())  # Aggregate for brand
            generate_wordcloud(all_comments_for_cloud, wordcloud_path)

            # --- 5. Update Google Sheet ---
            update_status_for_post(
                row_index, 
                "Completed",
                comment_count=len(comments),
                comments_link=comments_json_path,
                analyzed_link=analyzed_path,
                wordcloud_link=wordcloud_path
            )
            print(f"Finished processing post from row {row_index}.")
    finally:
        driver.quit()

    # --- Brand-level word cloud ---
    if all_cleaned_comments:
        brand_name = infer_brand_from_urls(post_urls)
        output_dir = "social_sentiment_analyzer/output"
        os.makedirs(output_dir, exist_ok=True)
        brand_wordcloud_path = os.path.join(output_dir, f"wordcloud_{brand_name}.png")
        generate_wordcloud(all_cleaned_comments, brand_wordcloud_path)
        print(f"Brand-level word cloud saved to {brand_wordcloud_path}")
        # --- Sentiment summary for top 20 words ---
        top_words = get_top_words(all_cleaned_comments, top_n=20)
        # Load all original (translated & cleaned) comments for context
        # We'll use the sentiment_df from all posts for this
        all_original_comments = []
        all_sentiments = []
        for idx, post in enumerate(posts_to_process):
            url = post.get(URL_COLUMN)
            status = post.get(STATUS_COLUMN)
            if not url or status == 'Completed':
                continue
            base_filename = sanitize_filename(url)
            analyzed_path = os.path.join("social_sentiment_analyzer/data", f"analyzed_{base_filename}.csv")
            if os.path.exists(analyzed_path):
                df = pd.read_csv(analyzed_path)
                all_original_comments.extend(df['comment'].tolist())
                all_sentiments.extend(df['compound'].tolist())
        # For each word, find frequency, avg sentiment, sentiment label, and example contexts
        summary = []
        for word, freq in top_words:
            # Find all comments containing this word
            indices = [i for i, c in enumerate(all_cleaned_comments) if word in c.split()]
            example_contexts = [all_original_comments[i] for i in indices[:3] if i < len(all_original_comments)]
            sentiments = [float(all_sentiments[i]) for i in indices if i < len(all_sentiments)]
            avg_sentiment = sum(sentiments)/len(sentiments) if sentiments else 0.0
            if avg_sentiment >= 0.05:
                sentiment_label = 'Positive'
            elif avg_sentiment <= -0.05:
                sentiment_label = 'Negative'
            else:
                sentiment_label = 'Neutral'
            summary.append({
                'word': word,
                'frequency': freq,
                'avg_sentiment': avg_sentiment,
                'sentiment_label': sentiment_label,
                'examples': example_contexts
            })
        # Save as CSV
        csv_path = os.path.join(output_dir, f"sentiment_summary_{brand_name}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['word', 'frequency', 'avg_sentiment', 'sentiment_label', 'examples'])
            writer.writeheader()
            for row in summary:
                row_copy = row.copy()
                row_copy['examples'] = "; ".join(row_copy['examples'])
                writer.writerow(row_copy)
        print(f"Sentiment summary CSV saved to {csv_path}")
        # Save as JSON
        json_path = os.path.join(output_dir, f"sentiment_summary_{brand_name}.json")
        with open(json_path, 'w', encoding='utf-8') as jsonfile:
            json.dump({'brand': brand_name, 'top_words': summary}, jsonfile, ensure_ascii=False, indent=2)
        print(f"Sentiment summary JSON saved to {json_path}")
        # Update the Google Sheet for all processed rows
        for row_index in processed_row_indices:
            update_status_for_post(row_index, None, wordcloud_link=brand_wordcloud_path)
    else:
        print("No comments found for brand-level word cloud.")

    print("Pipeline finished successfully!")

if __name__ == '__main__':
    main() 