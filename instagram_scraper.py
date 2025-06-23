from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from typing import List, Optional

def get_comments_from_post(url: str, scrolls: int = 50, driver: Optional[webdriver.Chrome] = None) -> List[str]:
    """Scrapes only top-level comments from an Instagram post using mobile emulation and the comments icon."""
    close_driver = False
    if driver is None:
        mobile_emulation = {
            "deviceMetrics": {"width": 414, "height": 896, "pixelRatio": 3},
            "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        }
        options = webdriver.ChromeOptions()
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        options.add_argument('--disable-blink-features=AutomationControlled')
        driver = webdriver.Chrome(options=options)
        close_driver = True

    comments = set()
    try:
        driver.get(url)
        if close_driver:
            print("Please manually handle the login in the browser window if required. Waiting for 30 seconds...")
            time.sleep(30)
        else:
            time.sleep(3)  # Let the page load

        # Click the comments icon to open the modal or expand comments
        try:
            print("Looking for comments icon...")
            comment_icon = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'svg[aria-label="Comment"]'))
            )
            driver.execute_script("arguments[0].parentNode.click();", comment_icon)
            print("Clicked comments icon.")
            time.sleep(2)
        except Exception as e:
            print(f"Could not find or click comments icon: {e}")

        # Robust loop: keep clicking 'Load more' and scrolling until no new comments for several iterations
        max_no_new = 5
        no_new_count = 0
        last_count = 0
        total_scrolls = 0
        while no_new_count < max_no_new:
            # Click all visible 'Load more'/'View all' buttons (not replies)
            load_more_buttons = driver.find_elements(By.XPATH, "//span[contains(text(), 'View all') or contains(text(), 'Load more') or contains(text(), 'View more')]")
            clicked = False
            for btn in load_more_buttons:
                btn_text = btn.text.strip().lower()
                if 'repl' not in btn_text:
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                        print(f"Clicked button: {btn_text}")
                        time.sleep(1.5)
                        clicked = True
                    except Exception as e:
                        print(f"Failed to click button: {e}")
            # Scroll
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
            total_scrolls += 1
            # Collect comments
            comment_divs = driver.find_elements(By.CSS_SELECTOR, 'div.x1lliihq')
            for div in comment_divs:
                spans = [s for s in div.find_elements(By.CSS_SELECTOR, 'span._ap3a') if not s.find_elements(By.XPATH, './ancestor::a')]
                if spans:
                    comment_text = spans[-1].text.strip()
                    if comment_text:
                        comments.add(comment_text)
            print(f"After scroll {total_scrolls}, found {len(comments)} unique comments.")
            if len(comments) == last_count:
                no_new_count += 1
            else:
                no_new_count = 0
            last_count = len(comments)
        print(f"Finished loading comments after {total_scrolls} scrolls.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if close_driver:
            driver.quit()
    unique_comments = list(comments)
    if unique_comments:
        unique_comments = unique_comments[1:]  # Skip the caption
    print(f"Found {len(unique_comments)} unique top-level comments (excluding caption).")
    return unique_comments 