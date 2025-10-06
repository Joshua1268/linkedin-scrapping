from scraper.browser import BrowserManager
from scraper.config import Config
from scraper.database import DatabaseManager
from scraper.linkedin_scraper import LinkedInScraper


def main():
    db = DatabaseManager()
    db.connect()

    browser = BrowserManager()
    driver = browser.init()

    try:
        if browser.login():
            scraper = LinkedInScraper(driver, db)
            for keyword in Config.KEYWORDS:
                scraper.scrape_keyword(keyword.strip() + "Hiring")
        else:
            print("Login failed. Exiting.")
    except Exception as e:
        print(f"Critical error: {e}")
    finally:
        browser.quit()
        db.close()


if __name__ == "__main__":
    main()
