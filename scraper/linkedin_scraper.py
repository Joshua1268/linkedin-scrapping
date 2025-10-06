import re
import time

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from scraper.config import Config
from scraper.text_processor import TextProcessor


class LinkedInScraper:
    def __init__(self, driver, db):
        self.driver = driver
        self.db = db
        self.processor = TextProcessor()

    def scrape_keyword(self, keyword):
        url = (
            f"https://www.linkedin.com/search/results/content/"
            f'?keywords={keyword}&sortBy="date_posted"'
        )
        self.driver.get(url)
        time.sleep(5)

        start_time = time.time()
        last_save_time = start_time
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self._expand_posts()

            if time.time() - last_save_time > Config.SAVE_INTERVAL:
                self._save_posts(keyword)
                last_save_time = time.time()

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                time.sleep(4)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
            last_height = new_height

            if time.time() - start_time > Config.MAX_SEARCH_TIME:
                break

        self._save_posts(keyword)

    def _expand_posts(self):
        try:
            btns = self.driver.find_elements(
                By.CLASS_NAME,
                "feed-shared-inline-show-more-text__see-more-less-toggle",
            )
            for btn in btns:
                self.driver.execute_script("arguments[0].click();", btn)
        except Exception:
            pass

    def _save_posts(self, keyword):
        soup = BeautifulSoup(self.driver.page_source.encode("utf-8"), "html.parser")
        posts = soup.find_all(
            "div", class_=re.compile(r"feed-shared-update-v2|occludable-update")
        )
        if not posts:
            posts = soup.select("div[data-urn]")

        count = 0
        for card in posts:
            try:
                author = self._extract_author(card)
                content_raw, content = self._extract_content(card)

                if len(content) < 5:
                    continue

                post_date = self._extract_date(card)
                likes, comments, shares = self._extract_stats(card)

                if not self.db.exists(author, content):
                    self.db.insert_post(
                        author, content, likes, shares, comments, post_date, keyword
                    )
                    count += 1
                    email = self.processor.extract_email(content_raw)
                    if email:
                        print(f"Email found: {email}")

            except Exception:
                continue

        if count > 0:
            print(f"{count} new posts saved.")

    def _extract_author(self, card):
        tag = card.find("span", class_="update-components-actor__name") or card.find(
            "span", class_="update-components-actor__title"
        )
        return tag.get_text(strip=True).split("\n")[0] if tag else "Unknown"

    def _extract_content(self, card):
        tag = card.find("div", class_="update-components-text") or card.find(
            "span", class_="break-words"
        )
        raw = tag.get_text(separator="\n", strip=True) if tag else ""
        return raw, self.processor.clean(raw)

    def _extract_date(self, card):
        tag = card.find("span", class_="update-components-actor__sub-description")
        raw = tag.get_text(strip=True).split("")[0] if tag else ""
        return self.processor.parse_relative_date(raw)

    def _extract_stats(self, card):
        likes_tag = card.find("li", class_="social-details-social-counts__reactions")
        likes = likes_tag.get_text(strip=True) if likes_tag else "0"

        comments, shares = "0", "0"
        for item in card.find_all("li", class_="social-details-social-counts__item"):
            text = item.get_text(strip=True).lower()
            if "comment" in text:
                comments = text.split()[0]
            elif "repost" in text or "diffusion" in text:
                shares = text.split()[0]

        return likes, comments, shares
