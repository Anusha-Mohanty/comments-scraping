import os
import re
import json
from config import *
from scrapers.instagram_scraper import get_comments_from_post
from utils.sheet_handler import get_all_posts, update_status_for_post
from selenium import webdriver
import time

COOKIES_FILE = 'insta_cookies.json'

def sanitize_filename(url: str) -> str:
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
        if 'expiry' in cookie:
            cookie['expiry'] = int(cookie['expiry'])
        try:
            driver.add_cookie(cookie)
        except Exception:
            continue
    print(f"Cookies loaded from {path}")
    return True

def main():
    print("Starting Instagram comment scraping with Google Sheets integration...")

    posts_to_process = get_all_posts()
    if not posts_to_process:
        print("No posts found in the Google Sheet. Exiting.")
        return

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
        driver.get("https://www.instagram.com/")
        if load_cookies(driver):
            driver.refresh()
            time.sleep(3)
            print("Logged in using saved cookies.")
        else:
            print("Please log in to Instagram in the browser window.")
            input("After you have logged in and see your feed, press Enter here to continue scraping posts...")
            save_cookies(driver)

        for idx, post in enumerate(posts_to_process):
            row_index = idx + 2
            url = post.get(URL_COLUMN)
            status = post.get(STATUS_COLUMN)

            if not url or status == 'Completed':
                print(f"Skipping row {row_index}: URL is missing or status is 'Completed'.")
                continue

            print(f"Processing post from row {row_index}: {url}")
            update_status_for_post(row_index, "In Progress")

            comments = get_comments_from_post(url, SCROLL_COUNT, driver=driver)
            if not comments:
                print(f"No comments were scraped for {url}. Skipping to next post.")
                update_status_for_post(row_index, "Failed: No comments found")
                continue

            base_filename = sanitize_filename(url)
            data_dir = "social_sentiment_analyzer/data"
            os.makedirs(data_dir, exist_ok=True)
            comments_json_path = os.path.join(data_dir, f"comments_{base_filename}.json")
            with open(comments_json_path, 'w', encoding='utf-8') as f:
                json.dump(comments, f, ensure_ascii=False, indent=2)
            print(f"Comments saved to {comments_json_path}")

            update_status_for_post(
                row_index,
                "Completed",
                comment_count=len(comments),
                comments_link=comments_json_path
            )
            print(f"Finished processing post from row {row_index}.")
    finally:
        driver.quit()

    print("Scraping finished successfully!")

if __name__ == '__main__':
    main()
