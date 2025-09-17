import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from scraper.config import Config


class BrowserManager:
    def __init__(self):
        self.driver = None

    def init(self):
        options = Options()
        profile_path = os.path.join(os.getcwd(), "selenium_profile")
        options.add_argument(f"user-data-dir={profile_path}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        if Config.HEADLESS_MODE:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        else:
            options.add_argument("--start-maximized")

        try:
            if os.path.exists("/usr/bin/chromedriver"):
                service = Service(executable_path="/usr/bin/chromedriver")
                options.binary_location = "/usr/bin/chromium"
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                self.driver = webdriver.Chrome(options=options)
        except Exception as e:
            print(f"Chrome launch error: {e}")
            exit(1)

        return self.driver

    def login(self):
        try:
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(5)

            if any(x in self.driver.current_url for x in ["login", "guest", "signup"]):
                self.driver.get("https://www.linkedin.com/login")
                time.sleep(3)

                self.driver.find_element(By.ID, "username").send_keys(Config.USERNAME)
                pwd = self.driver.find_element(By.ID, "password")
                pwd.send_keys(Config.PASSWORD)
                pwd.submit()

                for _ in range(24):
                    if "feed" in self.driver.current_url or "search" in self.driver.current_url:
                        return True
                    time.sleep(5)

                raise Exception("Login timeout.")

            return True

        except Exception as e:
            print(f"Login error: {e}")
            return False

    def quit(self):
        if self.driver:
            self.driver.quit()
