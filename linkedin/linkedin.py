from pathlib import Path
import time
import os
import sys
import pandas as pd
import numpy as np
import smtplib
import random
import imaplib
import email
import math
import ssl
import re
import glob
import subprocess

ROOT_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(ROOT_DIR)

from functools import partial

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from selenium.webdriver.common.action_chains import ActionChains, ActionBuilder
from selenium.common.exceptions import TimeoutException, WebDriverException, StaleElementReferenceException
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager



from random import randint
from PIL import Image

from datetime import datetime
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header

from typing import Optional


from logger import setup_logger
from .user_agents import list_users
from exceptions import (
    LoginException, ReachedDailyLimitSetException, NoMoreOrgException,
    NoConnectionException, CaptchaNeededException, AccountRestrictedException,
    UnexpectedException, NoSendButtonException, ReachedLimitException, ReachedWithdrawLimitException,
    LastPageException
)
from .utils import extract_number_from_text, get_week_number, remove_files_in_directory, check_internet_connection



logger = setup_logger(__name__)
cwd = os.getcwd()

class Linkedin:

    def __init__(self, username, password):
        logger.info(f"Current working directory: {cwd}")

        self.username = username
        self.password = password
        
        self.options = webdriver.ChromeOptions()
        self.options_set()
        logger.info("Options set")
        self.chromedriver_path = None
        self.chrome_exec_path = None
        self.check_if_chromedriver_exists()
        logger.info(f"Chrome exec path: {self.chrome_exec_path}")
        logger.info(f"Chrome driver path: {self.chromedriver_path}")
        service = webdriver.ChromeService(executable_path=self.chromedriver_path)
        self.options.binary_location = self.chrome_exec_path
        try:
            self.driver = webdriver.Chrome(options=self.options, service=service)
        except Exception as e:
            logger.error(f"Error creating driver: {str(e)}")
            raise e
        logger.info("Driver created")
        stealth(self.driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        logger.info("Stealth mode enabled")
        self.error_login_html = "error_login.html"
        self.num_page = 1
        self.total_pages = 1
        self.timeout_minutes = 960
        self.viewport_width = self.driver.execute_script("return window.innerWidth;")
        self.viewport_height = self.driver.execute_script("return window.innerHeight;")
        self.captcha_xpath = "//main//h1[contains(., 'Let’s do a quick security check')]"
        self.general_iframe_xpath = "//iframe"
        self.saved_iframe = None
        self.orgs_path = os.path.join(ROOT_DIR, "org", "orgs.csv")
        self.org_dt = pd.read_csv(self.orgs_path)
        self.withdraw_perc_per_page = 0.8
        self.home_page = "https://www.Linkedin.com/feed/"
        self.logger = logger
        self.waiting_before_check = int(os.getenv("WAITING_BEFORE_CHECK"))
        self.waiting_before_code_retry = 57600
        self.waiting_to_back_home = 240
        self.perc_to_withdraw = 0.5
        self.min_connections_pending = int(os.getenv("MIN_CONNECTIONS_PENDING"))
        self.MIN_CONNECTION_WITHDRAWABLE = 3
        self.button_tot_withdrawable = "//button[@id='mn-invitation-manager__invitation-facet-pills--CONNECTION']"
        self.sent_requests = 0
        self.filename_week = "reached_limit_week"
        self.filename_day = "reached_limit_day"
        self.file_extension = ".txt"
        self.num_connections = 0
        self.max_requests_per_day = np.random.randint(int(os.getenv("MIN_REQUESTS_PER_DAY")), int(os.getenv("MAX_REQUESTS_PER_DAY")))
        self.weeks_path = os.path.join(ROOT_DIR, "weeks")
        self.htmls_path = os.path.join(ROOT_DIR, "htmls")
        self.days_path = os.path.join(ROOT_DIR, "days")
        self.orgs_chosen_month_path = os.path.join(ROOT_DIR, "months", "orgs_chosen_month.csv")
        self.total_scroll_times = int(os.getenv("TOTAL_SCROLL_TIMES"))
        self.reached_limit_search = False
        self.org_chose_dt = None
        self.sent_connections_org = dict()
        self.org_name = None
        self.max_WDWT = int(os.getenv("MAX_WEBDRIVER_WAIT_TIME", 10))
        self.min_WDWT = int(os.getenv("MIN_WEBDRIVER_WAIT_TIME", 5))
        self.web_driver_wait_time = np.random.uniform(self.min_WDWT, self.max_WDWT)


    def get_chromedriver_version(self, base_dir = Path.home() / ".cache" / "selenium" , folder='chromedriver'):
        base_dir = base_dir / folder
        if base_dir.exists():
            folders = [item for item in base_dir.iterdir() if item.is_dir()]
            if len(folders) > 0:
                return self.get_chromedriver_version(base_dir=base_dir, folder=folders[-1].name)
            else:
                all_files = set([item for item in base_dir.iterdir() if item.is_file()])

                if base_dir / 'chromedriver' in all_files:
                    return base_dir.name
            
        return None

    def check_if_chromedriver_exists(self):
        chrome_driver_version = None
        if not os.path.exists(os.getenv("CHROMEDRIVER_PATH")):
            chrome_driver_version = self.get_chromedriver_version()
            if chrome_driver_version:
                self.chromedriver_path = str(Path.home() / ".cache" / "selenium" / "chromedriver" / chrome_driver_version / "chromedriver")
            else:    
                logger.error("Chromedriver does not exist")
                raise FileNotFoundError("Chromedriver does not exist")
        else:
            self.chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
            args = (self.chromedriver_path, "--version")
            popen = subprocess.Popen(args, stdout=subprocess.PIPE)
            popen.wait()
            output = popen.stdout.read().decode("utf-8")
            match = re.search(r"ChromeDriver (\d+\.\d+\.\d+\.\d+)", output)
            if match:
                chrome_driver_version = match.group(1)
        path_ = os.getenv("CHROME_EXEC_PATH") or "/usr/bin/google-chrome"
        if not os.path.exists(path_):
            base_dir = Path.home() / ".cache" / "selenium" / "chrome" / chrome_driver_version
            if base_dir.exists():
                self.chrome_exec_path = base_dir / "chrome"
                return
            else:
                chrome_driver_version = self.get_chromedriver_version()
                
                if chrome_driver_version:

                    base_dir = Path.home() / ".cache" / "selenium" / "chrome" 
                    folders = [item for item in base_dir.iterdir() if item.is_dir()]
                    base_dir = base_dir / folders[-1].name /  chrome_driver_version
                    if base_dir.exists():
                        self.chrome_exec_path = str(base_dir / "chrome")
                    return
            logger.error(f"HERE {chrome_driver_version}")
            raise FileNotFoundError("Chrome does not exist")
        self.chrome_exec_path = path_
    
    def remove_orgs_chosen_from_dt(self):
        to_remove = datetime.now().day == 1 and datetime.now().month % 2 == 0

        if not os.path.exists(self.orgs_chosen_month_path):
            self.org_chose_dt = pd.DataFrame(columns=['org_name'])
            self.org_chose_dt.to_csv(self.orgs_chosen_month_path, index=False)
            logger.info("Orgs chosen last 2 months csv file does not exist. Created new one.")
            return

        if to_remove:
            os.remove(self.orgs_chosen_month_path)
            logger.info("First day of the even month. Time to remove orgs chosen last 2 months csv file.")
            self.org_chose_dt = pd.DataFrame(columns=['org_name'])
            self.org_chose_dt.to_csv(self.orgs_chosen_month_path, index=False)
        else:
            logger.info("Removing orgs already chosen")
            self.org_chose_dt = pd.read_csv(self.orgs_chosen_month_path)
            self.org_dt = self.org_dt[~self.org_dt['org_name'].isin(self.org_chose_dt['org_name'])].reset_index(drop=True)


            if len(self.org_dt) == 0:
                self.org_dt = pd.read_csv(self.orgs_path)
            
        
    def options_set(self):
        self.options.add_argument('--no-sandbox')

        if os.getenv("HEADLESS") == "True":
            self.options.add_argument('--headless=new')
            self.options.add_argument('--no-zygote')
            self.options.add_argument('--disable-features=VizDisplayCompositor')
            self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
            self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument("--disable-gpu")
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--remote-debugging-port=9222')
        self.options.add_argument("--disable-browser-side-navigation")
        # disable the AutomationControlled feature of Blink rendering engine
            
        self.options.add_argument('--disable-blink-features=AutomationControlled')

        # disable pop-up blocking
        self.options.add_argument('--disable-popup-blocking')

        # start the browser window in maximized mode
        self.options.add_argument('--start-maximized')

        # disable extensions
        self.options.add_argument('--disable-extensions')

        # disable sandbox mode

        # disable shared memory usage
        self.options.add_argument('--disable-setuid-sandbox')
        
        user_agent = random.choice(list_users)
        logger.info(f"User agent: {user_agent}")
        self.options.add_argument(f"user-agent={user_agent}")
        self.options.add_argument("--incognito")
        self.options.add_argument("--nogpu")
        self.options.add_argument("--window-size=1280,1280")
        self.options.add_argument("--enable-javascript")
        self.options.add_argument('--silent')
        self.options.add_argument('--disable-logging')
        # Set shared memory size
        

    def check_if_exists_delete_rest(self, filename):
        match = re.search(r"(\w+)\/", filename)
        folder = match.group(1)
        if os.path.exists(filename):
            logger.info(f"This week limit reached. File exists: {self.filename_week}")
            return True
        else:
            files = glob.glob(f"{folder}/*")
            for f in files:
                try:
                    os.remove(f)
                except OSError as e:
                    logger.error(f"Error: {e.filename} - {e.strerror}")
                    raise e
        return False

    def send_connection_request(self):
        week_number = get_week_number()
        filename_week_comp = os.path.join(self.weeks_path, f"reached_limit_week-{week_number}{self.file_extension}")
        today = datetime.now().strftime('%a')
        # check if file exists

        if self.check_if_exists_delete_rest(filename_week_comp):
            logger.info("Week limit reached")
            return
        remove_files_in_directory(self.weeks_path)
        filename_day_comp = os.path.join(self.days_path, f"{self.filename_day}-{today}{self.file_extension}")
        if self.check_if_exists_delete_rest(filename_day_comp):
            logger.info("Day limit reached")
            return
        remove_files_in_directory(self.days_path)
        try:
            self.login()
        except Exception as e:
            logger.error(f"Failed to login: {str(e)}")
            raise e
        self.remove_orgs_chosen_from_dt()
        logger.info(f"Today will send {self.max_requests_per_day} connection requests")
        MAX_TRIES = 1000
        curr_try = 0
        try:
            while curr_try < MAX_TRIES:
                curr_try += 1
                if curr_try == MAX_TRIES:
                    logger.error("This should not happen. Reached max tries")
                    self.send_error_email("The bot has a bug. Contact the developer. Include the log file.")
                    return
                try:
                    self.org_name = self.get_org(self.org_dt)

                    if self.reached_limit_search:
                        logger.info("Searching for organization people with reached limit")
                        result = self.search_org_limit(self.org_name)
                    else:
                        logger.info("Searching for organization people with no reached limit")
                        result = self.search_org_no_limit(self.org_name)
                    logger.info(f"Result: {result}")
                    if result:
                        self.connect_to_alumni()
                except NoMoreOrgException as e:
                    logger.info("No more organizations to search")
                    self.send_limit_reached_email("No more organizations to search")
                    return
                except NoConnectionException as e:
                    logger.info("No more alumni to connect")
                    self.return_home()
                    continue
                except ReachedLimitException as e:
                    with open(filename_week_comp, "w") as f:
                        f.write("Reached limit")
                    self.send_limit_reached_email()
                    return
                except ReachedDailyLimitSetException as e:
                    if today == "Sun":
                        logger.info("Reached daily limit set, but it's Sunday. Will continue to send connections.")
                        continue
                    with open(filename_day_comp, "w") as f:
                        f.write("Reached limit")
                    self.send_limit_reached_email("Reached daily limit set. Will continue tomorrow.")
                    return
                except:
                    raise
        except Exception as e:
            self.logger.error(f"Error sending connection request: {e}")
            self.send_error_email(str(e))
            raise
        finally:
            if self.sent_connections_org.get(self.org_name, None):
                    new_row = pd.DataFrame({'org_name': [self.org_name]})
                    self.org_chose_dt = pd.concat([self.org_chose_dt, new_row], ignore_index=True)
                    logger.info(f"Added {self.org_name} to orgs chosen this month")
                    self.org_chose_dt.to_csv(self.orgs_chosen_month_path, index=False)

    

    def send_error_email(self, error: str, max_retries: int = 3):
        """
        Sends email notification when an error occurs in the Linkedin bot.
        
        Args:
            error (str): Error message to send
            
        Raises:
            Exception: If email sending fails
        """

        for attempt in range(max_retries):
            try:
                message = MIMEMultipart()
                message["From"] = os.getenv("SENDER")
                message["To"] = os.getenv("RECEIVER")
                message["Subject"] = "Linkedin Bot - Error Report"

                # Create detailed error message
                body = f"""
                Linkedin Bot encountered an error and stopped working.

                Error details:
                -------------
                Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                Error: {error}
                
                Please check the bot and restart if necessary.
                """
                
                message.attach(MIMEText(body, "plain"))

                # Try to attach screenshot if available
                try:
                    screenshot_path = self.save_centered_screenshot()
                    if screenshot_path:
                        with open(screenshot_path, 'rb') as f:
                            img_data = f.read()
                            image = MIMEImage(img_data, name=os.path.basename(screenshot_path))
                            message.attach(image)
                except Exception as e:
                    logger.warning(f"Could not attach screenshot: {str(e)}")

                # Send email using SSL
                with smtplib.SMTP_SSL(os.getenv("SMTP_SERVER_SENDER"), os.getenv("SMTP_PORT_SENDER")) as server:
                    server.login(os.getenv("SENDER"), os.getenv("SENDER_PASS"))
                    server.sendmail(
                        os.getenv("SENDER"),
                        os.getenv("RECEIVER"), 
                        message.as_string()
                    )
                    
                logger.info("Successfully sent error notification email")
                return
                
            except Exception as e:
                if attempt < max_retries - 1:
                    result = check_internet_connection(logger, retries=3, timeout=5)
                    
                    if not result:
                        logger.error("No internet connection available")
                        time.sleep(60)
                    else:
                        logger.error(f"Failed with this error: {str(e)}. Retrying ({attempt})...")
                        time.sleep(5)
                    continue
                else:
                    logger.error(f"Failed to send error email: {str(e)}")
                    raise
    
    def get_number_withdrawable(self, button_xpath):
        button = self.driver.find_element(By.XPATH, button_xpath)
        span = button.find_element(By.XPATH, ".//span")
        span_text = span.text
        num_connections_sent = extract_number_from_text(span_text, logger)
        return num_connections_sent
            
    def withdraw_connection(self):
        url = "https://www.Linkedin.com/mynetwork/invitation-manager/sent/"
        self.login()
        self.driver.get(url)
        time.sleep(np.random.randint(3, 5))
        num_connections_sent = self.get_number_withdrawable(self.button_tot_withdrawable)   
        withdraw_button = "//button[contains(., 'Withdraw')]"

        if num_connections_sent < self.min_connections_pending:
            logger.info("Number of connections pending is less than minimum connections pending")
            return

        for all_withdraw_buttons in self.withdraw_conn_generator(withdraw_button, num_connections_sent):
            array_len = len(all_withdraw_buttons)

            if array_len <= self.MIN_CONNECTION_WITHDRAWABLE:
                logger.info(f"Less than {self.MIN_CONNECTION_WITHDRAWABLE} connections to withdraw per page.")
                continue
            num_elemnts = int( array_len* self.withdraw_perc_per_page)
            indeces = np.random.choice(array_len, num_elemnts, replace=False)
            all_withdraw_buttons = [all_withdraw_buttons[i] for i in indeces]
    
            for withdraw_button in all_withdraw_buttons:
                try:
                    # Wait for button to be clickable
                    clickable_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                        EC.element_to_be_clickable(withdraw_button)
                    )
                    
                    # Scroll into view
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", clickable_button)
                    time.sleep(np.random.uniform(1.5, 3.5))
                    
                    # Try JavaScript click if regular click fails
                    ActionChains(self.driver).click(clickable_button).perform()
                    
                    time.sleep(np.random.randint(1, 3))
                    
                    # Wait and click confirm withdraw button
                    confirm_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Withdraw')]"))
                    )
                    ActionChains(self.driver).click(confirm_button).perform()
                    
                    time.sleep(np.random.randint(1.5, 3.5))
                    
                except Exception as e:
                    logger.error(f"Error in withdraw: {str(e)}")
                    self.write_response(self.driver.page_source, "error_withdraw.html")
                    continue
        logger.info("All connections withdrawn")

    def withdraw_conn_generator(self, button_xpath, starting_withdrawable):
        """
        Generator that yields withdraw buttons with stale element handling
        """
        last_page_but_xpath = "(//button[not(@disabled) and contains(@aria-label, 'Page ')])[last()]"
        previous_page_button_xpath = "//button[not(@disabled) and @aria-label='Previous']"
        next_page_button_xpath = "//button[not(@disabled) and @aria-label='Next']"
        time.sleep(3)
        
        try:
            # Get last page number
            try:
                
                next_page_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                    EC.presence_of_element_located((By.XPATH, next_page_button_xpath))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_page_button)

                last_page_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                    EC.presence_of_element_located((By.XPATH, last_page_but_xpath))
                )
                last_page = int(last_page_button.text)
                logger.info(f"Found {last_page} pages")
                ActionChains(self.driver).click(last_page_button).perform()
                # Click last page
            except Exception as e:
                logger.warning(f"Error finding last page button. This should not happen. ({str(e)})")
                raise e

            curr_page = last_page

            while True:
                try:
                    time.sleep(np.random.uniform(2.5, 5))
            
                    # Re-fetch buttons on each iteration
                    all_buttons = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                        EC.visibility_of_any_elements_located((By.XPATH, button_xpath))
                    )
                    # Ensure buttons are visible
                    visible_buttons = []
                    for button in all_buttons:
                        try:
                            if button.is_displayed() and button.is_enabled():
                                visible_buttons.append(button)
                        except StaleElementReferenceException:
                            continue

                    logger.info(f"Found {len(visible_buttons)} withdraw buttons")
                    time.sleep(np.random.uniform(1, 3))
                    
                    if visible_buttons:
                        yield visible_buttons

                    # Navigate to previous page
                    try:
                        previous_button = WebDriverWait(self.driver, ).until(
                            EC.element_to_be_clickable((By.XPATH, previous_page_button_xpath))
                        )
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                            previous_button
                        )
                        ActionChains(self.driver).click(previous_button).perform()
                    except:
                        logger.info("Reached first page")
                        return

                    curr_page -= 1
                    if curr_page == 0:
                        logger.info("Reached first page")
                        return

                    # Wait for page transition
                    next_page_button =  WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                        EC.presence_of_element_located((By.XPATH, next_page_button_xpath))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_page_button)
                    time.sleep(np.random.uniform(2, 5))

                    # Check withdraw count
                    curr_num_withdrawable = self.get_number_withdrawable(
                        self.button_tot_withdrawable
                    )
                    if curr_num_withdrawable == 0:
                        logger.info("No more connections to withdraw")
                        return
                    
                    if curr_num_withdrawable < int(starting_withdrawable * self.perc_to_withdraw):
                        logger.info(f"Withdrew {self.perc_to_withdraw*100}% connections")
                        raise ReachedWithdrawLimitException("Reached withdraw limit: {self.perc_to_withdraw*100}%")

                except StaleElementReferenceException:
                    logger.warning("Stale elements encountered, retrying page...")
                    self.driver.refresh()
                    time.sleep(2)
                    continue

        except Exception as e:
            logger.error(f"Error in withdraw generator: {str(e)}")
            raise e

    def click_next_page(self, next_page_button, max_retries=3):

        for attempt in range(max_retries):
            try:
                # Find and scroll to next button
                next_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                    EC.presence_of_element_located((By.XPATH, next_page_button))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_button)
                time.sleep(np.random.uniform(0.5, 1.5))
                
            
                next_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                    EC.element_to_be_clickable((By.XPATH, next_page_button))
                )
                ActionChains(self.driver).click(next_button).perform()
        
                time.sleep(np.random.uniform(2, 4))
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    result = check_internet_connection(logger, retries=3, timeout=5)

                    if not result:
                        logger.error("No internet connection available")
                        time.sleep(60)
                    else:
                        logger.error(f"Failed with this error: {str(e)}. Retrying ({attempt})...")
                        time.sleep(5)
                    continue
                else:
                    logger.error(f"Failed to click next page button: {str(e)}")
                    raise
            
        

    def is_page_scrolled_to_end(self):
        script = """
        return (window.innerHeight + window.scrollY) >= document.body.scrollHeight;
        """
        return self.driver.execute_script(script)

    def generator_when_limit(self, button_xpath):
        people_card_xpath = "//div//h2[contains(., 'People you may know')]"
    

        try:
            card_people = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                EC.presence_of_element_located((By.XPATH, people_card_xpath))
            )
        except:
            logger.info("No people card found in `generator_when_limit`")
            raise UnexpectedException("No people card found in `generator_when_limit`")
        
        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", card_people)
        time.sleep(np.random.uniform(2, 4))

        for scroll in range(self.total_scroll_times):
            try:
                all_buttons = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                    EC.visibility_of_any_elements_located((By.XPATH, button_xpath))
                )
                yield all_buttons
            except Exception as e:
                logger.info(f"No found buttons on the scroll: {scroll}")
                self.driver.execute_script("window.scrollTo({top: document.body.scrollHeight, left:0, behavior: 'smooth'});")
                time.sleep(np.random.uniform(2, 4))


            if self.is_page_scrolled_to_end():
                logger.info("Reached end of page")
                return
            
        

    def generator_pages(self, button_xpath):
        next_page_button = "//button[not(@disabled) and @aria-label='Next']"
        modal_overlay = "//div[contains(@class, 'artdeco-modal-overlay')]"
        last_page_but_xpath = "(//button[not(@disabled) and contains(@aria-label, 'Page ')])[last()]"
        limit_search_xpath = "//div[@data-view-name='search-results-promo' and contains(., 'You’ve reached the monthly limit for profile searches')]"

        try:
            last_page_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                EC.element_to_be_clickable((By.XPATH, last_page_but_xpath))
            )
            last_page = int(last_page_button.text)
            logger.info(f"Found {last_page} pages")
        except:
            last_page = 1
        pages_before_quit = int(os.getenv("PAGES_BEFORE_QUIT"))
        for page in range(pages_before_quit):

            try:
                # Wait for withdraw buttons on current page
                all_buttons = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                    EC.visibility_of_any_elements_located((By.XPATH, button_xpath))
                )

                try:
                    WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                        EC.presence_of_element_located((By.XPATH, limit_search_xpath))
                    )
                    logger.info("Reached monthly limit for profile searches")
                    self.reached_limit_search = True
                except:
                    pass
                yield all_buttons
                
                if self.reached_limit_search:
                    return

                # Try to go to next page
                try:
                    # Check and handle any modal overlays first
                    try:
                        overlay = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                            EC.presence_of_element_located((By.XPATH, modal_overlay))
                        )
                        # Wait for overlay to disappear or close it
                        try:
                            WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                                EC.invisibility_of_element_located((By.XPATH, modal_overlay))
                            )
                        except TimeoutException:
                            # Try to close modal if it doesn't disappear
                            close_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Dismiss']"))
                            )
                            ActionChains(self.driver).click(close_button).perform()
                            time.sleep(1)
                    except TimeoutException:
                        pass  # No modal present

                    self.click_next_page(next_page_button)
                    
                except:
                    logger.info("No next page button found")
                    raise LastPageException("No next page button found")
            except LastPageException:
                raise
                        
            except Exception as e:
                logger.info(f"No found buttons: {button_xpath} on page: {page}")
                self.click_next_page(next_page_button)
                
        return
    def check_if_remember_me(self):
        checkbox_xpath = "//label[@for='rememberMeOptIn-checkbox']"
        input_xpath = "//input[@id='rememberMeOptIn-checkbox']"

        try:
            label = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                EC.presence_of_element_located((By.XPATH, checkbox_xpath))
            )
            input_checkbox = label.find_element(By.XPATH, input_xpath)
            if input_checkbox.is_selected():
                logger.info("Remember me checkbox is selected")
                ActionChains(self.driver).click(label).perform()
        except:
            return
        

    def check_if_app(self):
        h1_app_xpath = "//h1[contains(., 'Check your LinkedIn app')]"
        resend_button_xpath = "//button[contains(@class, 'form__submit__inapp') and contains(., 'Resend')]"

        try:
            WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                EC.presence_of_element_located((By.XPATH, h1_app_xpath))
            )
            logger.warning("Authorization needed by LinkedIn app")
            while True:
                self.send_email("Authorization needed by LinkedIn app. Resend the request: [Yes/No]? (If not correct will assume no.)", "Linkedin Bot - Authorization Needed")
                message = self.waiting_for_confirmation_email()
                match =re.search(r"Yes", message, re.IGNORECASE)
                if match:
                    resend_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                        EC.element_to_be_clickable((By.XPATH, resend_button_xpath))
                    )
                    ActionChains(self.driver).click(resend_button).perform()
                else:
                    break
            time.sleep(np.random.uniform(4, 7))
            self.driver.refresh()
        except:
            return False
            

    def check_if_feed(self):
        try:
            start_post_button = "//button[contains(@class, 'artdeco-button')]//strong[contains(., 'Start a post')]"

            WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                    EC.presence_of_element_located((By.XPATH, start_post_button))
                )
        except Exception as e:
            raise e

    def handle_cookie_popup(self, max_retries=3):
        cookie_button_selectors = [
            "//button[contains(., 'Reject')]",
            "//button[@aria-label='Reject cookies']",
            "//button[contains(@class, 'cookie-reject')]"
        ]
        
        for attempt in range(max_retries):
            try:
                # Try each selector
                for selector in cookie_button_selectors:
                    try:
                        # Wait for button
                        cookie_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        
                        # Scroll into view if needed
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", cookie_button)
                        time.sleep(np.random.uniform(0.3, 0.7))
                        
                        # Simulate human behavior
                        # self.human_like_mouse_move(cookie_button)
                        
                        ActionChains(self.driver).click(cookie_button).perform()
                        
                        # Verify popup is gone
                        WebDriverWait(self.driver, self.get_web_driver_wait_time()).until_not(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        
                        logger.info(f"Successfully handled cookie popup with selector: {selector}")
                        return True
                        
                    except TimeoutException:
                        continue
                        
                logger.info("No cookie popup found with any selector")
                return False
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed to handle cookie popup: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(np.random.uniform(1, 2))
                else:
                    return False

    def check_if_restricted(self):
        temporary_restricted_button = "//a[@role='button' and contains(@class, 'id__verify-btn__primary')]"

        try:
            WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                EC.presence_of_element_located((By.XPATH, temporary_restricted_button))
            )
            logger.warning("Access to account restricted")
            raise AccountRestrictedException("Access to account restricted")
        except AccountRestrictedException:
            raise
        except:
            return False

    def check_if_need_waiting(self):
        h2_msg = "//h1[@class='heading' and contains(., 'Your LinkedIn Network Will Be Back Soon')]"

        try:
            WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                EC.presence_of_element_located((By.XPATH, h2_msg))
            )
            logger.info(f"Found: 'Your LinkedIn Network Will Be Back Soon' message. Lets wait for: {self.waiting_to_back_home//60} minutes")
            time.sleep(self.waiting_to_back_home)
            self.driver.refresh()
        except:
            return False
            
    def login(self, max_retries=3):
        for attempt in range(max_retries):
            try:
                driver = self.driver
                driver.get("https://www.Linkedin.com/login")
                
                # Wait for page load
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
                
                self.handle_cookie_popup()
                time.sleep(np.random.uniform(1, 2))
                self.check_if_remember_me()
                time.sleep(np.random.uniform(0.5, 1.5))
                logger.info("Got Linkedin login page")
                
                # Get login elements
                username_element = driver.find_element(By.ID, "username")
                password_element = driver.find_element(By.ID, "password")
                
                # Simulate human behavior
                # self.human_like_mouse_move(username_element)
                for char in self.username:
                    username_element.send_keys(char)
                    time.sleep(np.random.uniform(0.1, 0.3))
                time.sleep(np.random.uniform(0.5, 1.5))
                
                # self.human_like_mouse_move(password_element)
                for char in self.password:
                    password_element.send_keys(char)
                    time.sleep(np.random.uniform(0.1, 0.3))
                
                logger.info("Filled credentials")
                
                # Click login button instead of hitting enter
                submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                self.human_like_mouse_move(submit_button)
                ActionChains(self.driver).click(submit_button).perform()
                time.sleep(np.random.uniform(1, 2))
                
                # Verify login success
                try:
                    self.check_if_captcha()
                    self.check_if_app()
                    try:
                        self.check_if_feed()
                    except:
                        res = self.check_if_restricted()
                        self.check_if_need_waiting()
                        res = self.check_if_email_code()
                        if not res:
                            res = self.check_if_phone_number()
                        self.after_login_card()
                    
                    self.check_if_feed()
                    
                    # Wait for feed to verify successful login
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "global-nav"))
                    )
                    
                    logger.info("Successfully logged in")
                    return True
                except AccountRestrictedException:
                    raise
                except Exception as e:
                    if "security verification" in driver.page_source.lower():
                        logger.error("Security verification required")
                        self.write_response(driver.page_source, "security_verification.html")
                    raise
            except AccountRestrictedException:
                raise
            except Exception as e:
                logger.error(f"Login attempt {attempt + 1} failed: {e.msg}")
                self.write_response(driver.page_source, f"login_error_{attempt}.html")
                self.check_if_restricted() 
                if attempt < max_retries - 1:
                    logger.info(f"Retrying login... ({attempt + 2}/{max_retries})")
                    time.sleep(np.random.randint(30, 60))  # Wait before retry
                    continue
                else:
                    raise LoginException(f"Failed to login after {max_retries} attempts") from e
                    
            finally:
                if "Sign In" in driver.title:
                    logger.error("Still on login page")
                    raise LoginException("Failed to login")
        


    def get_org(self, org_dt):
        

        weights = 1 / (np.arange(len(org_dt)) + 1)
        probabilities = weights / weights.sum()

        if len(org_dt) == 0:
            raise NoMoreOrgException("No more organizations to search")
        selected_idxs =  np.random.choice(len(org_dt), size=15, p=probabilities)
        selected_idxs = np.random.permutation(selected_idxs)

        indx = selected_idxs[np.random.randint(0, len(selected_idxs))]
        org = org_dt.iloc[indx]['org_name']
        org_dt.drop(indx, inplace=True, errors='ignore')
        org_dt = org_dt.reset_index(drop=True)
        logger.info(f"Selected organization: {org}")

        return org

    def return_home(self):
        self.driver.get(self.home_page)

    def choose_result(self):
        div_xpath = "//div[@aria-label='Search suggestions']"
        suggestion_xpath = "//div[contains(@id, 'basic-result-') and not(contains(., 'See all results'))]"

        try:
            # Wait for suggestions container
            WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                EC.presence_of_element_located((By.XPATH, div_xpath))
            )
            
            # Get all suggestions
            suggestions = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                EC.visibility_of_any_elements_located((By.XPATH, suggestion_xpath))
            )
            logger.info(f"Found {len(suggestions)} search suggestions")

            if not suggestions:
                raise NoMoreOrgException("No search suggestions found")

            valid_indices = []
            for idx, suggestion in enumerate(suggestions, 1):
                try:
                    # Check for Company or School text
                    WebDriverWait(suggestion, 4).until(
                        lambda element: element.find_element(By.XPATH, 
                            ".//span[contains(@class, 'truncate') and (contains(., 'School') or contains(., 'Company'))]"
                        )
                    )
                    return idx
                except:
                    valid_indices.append(idx)
                    continue

            # If no Company/School found, choose random suggestion
            logger.info(f"No Company/School found, using random index")
            return random.choice(valid_indices)

        except TimeoutException:
            logger.info("No search suggestions found")
            raise NoMoreOrgException("Search suggestions not found")
        
    def _search_common(self, org_name):
        selectors = {
            'search_input': "input[class^='search-global-typeahead__input']",
            'search_button': "//button[contains(@class, 'search-global-typeahead__collapsed-search-button')]",
            'company_button': "//div[@id='search-reusables__filters-bar']/ul/li/button[contains(., 'Companies')]",
            'org_div': "//ul[@role = 'list']/li[1]/div",
            'no_found_company': "//h2[contains(., 'No results found')]"
        }
        try:
                # Find and click search button first
            search_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                EC.element_to_be_clickable((By.XPATH, selectors['search_button']))
            )
            ActionChains(self.driver).click(search_button).perform()
            time.sleep(np.random.uniform(0.5, 1))
        except:
            pass
        search_element = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selectors['search_input']))
        )
        
        # Clear search input
        try:
            search_element.clear()
        except:
            self.driver.execute_script("arguments[0].value = '';", search_element)
        time.sleep(0.5)
        
        # Type organization name
        len_name = len(org_name)
        if len_name > 6:
            search_text = org_name[:int(len_name * np.random.uniform(0.75, 0.92))]
        else:
            search_text = org_name

        for char in search_text:
            try:
                # Relocate element for each character to avoid stale reference
                search_element = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selectors['search_input']))
                )
                search_element.send_keys(char)
                time.sleep(np.random.uniform(0.1, 0.3))
            except:
                # If element becomes stale, find it again
                search_element = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selectors['search_input']))
                )
                search_element.send_keys(char)
                
        time.sleep(np.random.uniform(0.5, 2))
        try:
            num_presses = self.choose_result()
            logger.info(f"Pressing down {num_presses} times")
            for _ in range(num_presses):
                search_element.send_keys(Keys.DOWN)
                time.sleep(np.random.uniform(0.5, 1.3))
        except NoMoreOrgException as e:
            logger.info("No more organizations to search")
            return False
        search_element.send_keys(Keys.RETURN)
        time.sleep(np.random.uniform(1, 2))
        
        # Wait for company filter button
        company_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
            EC.element_to_be_clickable((By.XPATH, selectors['company_button']))
        )
        logger.info("Found search results")
        
        ActionChains(self.driver).click(company_button).perform()
        try:
            WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                EC.presence_of_element_located((By.XPATH, selectors['no_found_company']))
            )
            return False
        except TimeoutException:
            pass

        time.sleep(np.random.uniform(1, 2))

        # Click organization div
        org_div = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
            EC.element_to_be_clickable((By.XPATH, selectors['org_div']))
        )
        ActionChains(self.driver).click(org_div).perform()
        time.sleep(np.random.uniform(1, 2))
        return True
            
       
        
    def search_org_limit(self, org_name, max_retries=3):
        selectors ={
            'people_tab': "//nav[@aria-label='Organization’s page navigation']//a[contains(., 'People')]",
            'alumni_tab': "//nav[@aria-label='Organization’s page navigation']//a[contains(., 'Alumni')]",
        }
        for attempt in range(max_retries):
            try:
                result = self._search_common(org_name)
                if not result:
                    return False

                # Try people tab first, then alumni
                try:
                    people_tab = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                        EC.element_to_be_clickable((By.XPATH, selectors['people_tab']))
                    )
                    # self.human_like_mouse_move(people_tab)
                    ActionChains(self.driver).click(people_tab).perform()

                except:
                    try:
                        alumni_tab = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                            EC.element_to_be_clickable((By.XPATH, selectors['alumni_tab']))
                        )
                        # self.human_like_mouse_move(alumni_tab)
                        ActionChains(self.driver).click(alumni_tab).perform()
                    except TimeoutException:
                        logger.warning(f"Neither people nor alumni tab found: {org_name} ")
                        self.write_response(self.driver.page_source, "error_tabs_with_limit.html")
                        return False
                logger.info("Successfully navigated to people/alumni page")
                return True
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed in search : {str(e)}")
                self.write_response(self.driver.page_source, f"error_search_org_{attempt}.html")
                
                self.return_home()
                if attempt < max_retries - 1:
                    logger.info(f"Retrying... ({attempt + 2}/{max_retries})")
                    time.sleep(np.random.randint(5, 10))
                else:
                    raise


    def search_org_no_limit(self, org_name, max_retries=3):
        selectors = {
            
            'alumni_tab': "//div[@class='inline-block']//span[contains(., 'alumni')]",
            'employees_tab': "//div[@class='org-top-card-summary-info-list']//a",
            'connection_2nd': "//ul[contains(@class, 'inline-flex')]/li/button[contains(., '2nd')]",
            'connection_3rd': "//ul[contains(@class, 'inline-flex')]/li/button[contains(., '3rd')]"
        }
        
        for attempt in range(max_retries):
            try:
                result = self._search_common(org_name)
                if not result:
                    return False                
                # Try alumni tab first, then employees
                try:
                    alumni_tab = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                        EC.element_to_be_clickable((By.XPATH, selectors['alumni_tab']))
                    )
                    # self.human_like_mouse_move(alumni_tab)
                    ActionChains(self.driver).click(alumni_tab).perform()
                except TimeoutException:
                    try:
                        employees_tab = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                            EC.element_to_be_clickable((By.XPATH, selectors['employees_tab']))
                        )
                        # self.human_like_mouse_move(employees_tab)
                        ActionChains(self.driver).click(employees_tab).perform()
                    except TimeoutException:
                        logger.warning(f"Neither alumni nor employees tab found: {org_name} ")
                        self.write_response(self.driver.page_source, "error_tabs_no_limit.html")
                        return False
                try:
                    # Select connection levels
                    for connection in ['connection_2nd', 'connection_3rd']:
                        button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                            EC.element_to_be_clickable((By.XPATH, selectors[connection]))
                        )
                        # self.human_like_mouse_move(button)
                        ActionChains(self.driver).click(button).perform()
                        time.sleep(np.random.uniform(1, 2))
                except:
                    pass
                
                logger.info("Successfully navigated to alumni page")
                return True
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed in search : {str(e)}")
                self.write_response(self.driver.page_source, f"error_search_org_{attempt}.html")
                
                self.return_home()
                if attempt < max_retries - 1:
                    logger.info(f"Retrying... ({attempt + 2}/{max_retries})")
                    time.sleep(np.random.randint(5, 10))
                else:
                    raise

    def after_login_card(self, max_retries=3):
        card_div_xpath = "//div[contains(@class, 'connect-services-card')]"
        button_xpath = "//button[@aria-label='Connect none']"

        for attempt in range(max_retries):
            try:
                # Wait for card to appear
                card = WebDriverWait(self.driver, np.random.randint(3, 6)).until(
                    EC.presence_of_element_located((By.XPATH, card_div_xpath))
                )
                logger.info("Found connect services card")
                
                # Wait for button to be clickable
                button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                    EC.element_to_be_clickable((By.XPATH, button_xpath))
                )
                
                # Simulate human behavior
                # self.human_like_mouse_move(button)
                
                # Try JavaScript click if regular click fails
                ActionChains(self.driver).click(button).perform()
                
                # Verify card disappeared
                WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                    EC.invisibility_of_element_located((By.XPATH, card_div_xpath))
                )
                logger.info("Successfully handled connect services card")
                return True
                
            except TimeoutException:
                logger.info("No connect services card found")
                return False
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed to handle card: {str(e)}")
                self.write_response(self.driver.page_source, f"error_card_{attempt}.html")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying... ({attempt + 2}/{max_retries})")
                    time.sleep(np.random.randint(2, 4))
                else:
                    logger.error("Failed to handle connect services card")
                    return False  
        

    def connect_to_alumni(self):
        selectors = {
            'connect_button': "//button[contains(@aria-label, 'Invite') and span[contains(., 'Connect')]]",
            'no_results': "//div[contains(@class, 'search-reusable-search-no-results ')]/section/h2[contains(.,'No results found')]",
            'results_container': "//div[contains(@class, 'search-results-container')]",
            'button_send1': "//button[contains(@aria-label, 'Send invitation')]",
            'button_send2': "//button[contains(@aria-label, 'Send without a note')]",
            'dismiss_button': "//button[@aria-label='Dismiss']",
            'close_to_reach_limit_button': "//div[//h2[contains(., \"You're approaching the weekly invitation limit\") or contains(., \"You're close to the weekly invitation limit\")]]/button[contains(@aria-label, 'Got it')]",
            'reached_limit_button': "//button[contains(@aria-label, 'Got it')]",
            'limit_search_xpath':"//div[@data-view-name='search-results-promo' and contains(., 'You’ve reached the monthly limit for profile searches')]",
            'growing_popup': "//div[//h2[contains(., \"You're growing your network!\")]]/button[@aria-label='Got it']",
            'popup_box': "//div[contains(@class, 'ip-fuse-limit-alert') and @role='dialog']"

        }

        try:
            # Wait for either results or no results
            

            func_to_call = None
            try:
                if self.reached_limit_search:
                    func_to_call = partial(self.generator_when_limit, selectors['connect_button'])
                else:
                    WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                        EC.presence_of_element_located((By.XPATH, selectors['limit_search_xpath']))
                    )
                    self.reached_limit_search = True
                    raise UnexpectedException("Reached limit search but not set")
            except:
                try:
                    WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                        EC.presence_of_element_located((By.XPATH, selectors['no_results']))
                    )
                    logger.info("No connectable people found")
                    raise NoConnectionException("No connectable people found")
                except:
                    pass
            
                # Wait for results container to be fully loaded
                WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                    EC.presence_of_element_located((By.XPATH, selectors['results_container']))
                )
                logger.info("Found connectable people")
                # Add random delay to simulate human behavior
                time.sleep(np.random.uniform(1, 2))
                func_to_call = partial(self.generator_pages, selectors['connect_button'])

            # Get all connectable alumni
            logger.info("Getting connectable alumni")
            for all_connect_buttons in func_to_call():
                connection_len = len(all_connect_buttons)
                logger.info(f"Found {connection_len} connectable alumni")
                
                if connection_len > 6:
                    num_elements = int(connection_len * 0.5)
                    indeces = np.random.choice(connection_len, num_elements, replace=False)
                    all_connect_buttons = [all_connect_buttons[i] for i in indeces]
            
                for connect_button in all_connect_buttons:
                    try:
                        # Wait for button to be clickable
                        clickable_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                            EC.element_to_be_clickable(connect_button)
                        )
                        
                        # Scroll into view
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", clickable_button)
                        time.sleep(np.random.uniform(1.5, 7.5))
                        
                        # Try JavaScript click if regular click fails
                        ActionChains(self.driver).click(clickable_button).perform()
                        
                        time.sleep(np.random.uniform(0.5, 4))
                        try:
                            clickable_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                                EC.element_to_be_clickable((By.XPATH, selectors['button_send1']))
                            )
                        except:
                            try:
                                clickable_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                                    EC.element_to_be_clickable((By.XPATH, selectors['button_send2']))
                                )
                            except:
                                try:
                                    toast_xpath = "//div[contains(@class, 'artdeco-toast-item') and //p[@class='artdeco-toast-item__message']]/li-icon[@type='error-pebble-icon']"
                                    toast_element = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                                        EC.visibility_of_element_located((By.XPATH, toast_xpath))
                                    )
                                    logger.info(f"Error toast message found: {toast_element.text}")
                                except TimeoutException:
                                    logger.info("No error toast message found, will continue")
                                    continue
                                except Exception as e:
                                    logger.error(f"Error in toast message: {str(e)}")
                                    raise NoSendButtonException("No send button found")
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", clickable_button)
                        ActionChains(self.driver).click(clickable_button).perform()
                        time.sleep(np.random.uniform(1.5, 2.5))

                        try:
                            dismiss_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                                EC.element_to_be_clickable((By.XPATH, selectors['dismiss_button']))
                            )
                            logger.info("Found dismiss button, clicking it")
                            ActionChains(self.driver).click(dismiss_button).perform()

                            time.sleep(np.random.uniform(0.5, 1))
                        except TimeoutException:
                            logger.debug("No dismiss button found")
                            pass

                        try:
                            WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                                EC.presence_of_element_located((By.XPATH, selectors['popup_box']))
                            )

                            try:
                                growing_popup = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                                    EC.element_to_be_clickable((By.XPATH, selectors['growing_popup']))
                                )
                                logger.info("Found growing network message popup")
                                ActionChains(self.driver).click(growing_popup).perform()
                            except TimeoutException as e:
                                try:
                                    close_to_reach_limit_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                                        EC.element_to_be_clickable((By.XPATH, selectors['close_to_reach_limit_button']))
                                    )
                                    logger.info("Found close to reach limit button, clicking it")
                                    ActionChains(self.driver).click(close_to_reach_limit_button).perform()

                                except TimeoutException as e:
                                    try:
                                        reached_limit_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                                            EC.element_to_be_clickable((By.XPATH, selectors['reached_limit_button']))
                                        )
                                        logger.info("Found reached limit button, clicking it")
                                        self.write_response(self.driver.page_source, "reached_limit.html")

                                        ActionChains(self.driver).click(reached_limit_button).perform()

                                        time.sleep(np.random.uniform(0.5, 1))
                                        logger.info("Reached weekly connection limit")
                                        raise ReachedLimitException("Reached connection limit")
                                    except ReachedLimitException:
                                        raise
                                    except:
                                        pass
                        except TimeoutException as e:
                            pass
                        time.sleep(np.random.uniform(1, 2))
    
                        logger.info(f"Successfully connected to alumni")
                        self.num_connections += 1
                        self.sent_connections_org.update({self.org_name: self.num_connections})
                        if self.num_connections >= self.max_requests_per_day:
                            logger.info("Reached daily connection limit")
                            raise ReachedDailyLimitSetException("Reached daily connection limit")

                    except (ReachedLimitException, ReachedDailyLimitSetException) as e:
                        raise
                    except Exception as e:
                        logger.warning(f"Error in connect_to_alumni: {str(e)}")
                        self.write_response(self.driver.page_source, "error_connect.html")
                        continue

        except (ReachedLimitException, ReachedDailyLimitSetException, NoConnectionException) as e:
            raise e
        except LastPageException:
            logger.info("Reached last page")
            return
        except Exception as e:
            logger.error(f"Attempt failed in connect_to_alumni: {str(e)}")
            self.write_response(self.driver.page_source, f"error_get_connectable_alumni.html")


    def write_response(self, response, name):
        with open(os.path.join(ROOT_DIR, self.htmls_path, name), "w") as file:
            file.write(response)


    def send_limit_reached_email(self, string_to_write: str = "Linkedin Bot has stopped working because the weekly connection request limit has been reached."):
        """
        Sends email notification when Linkedin connection request limit is reached.
        """
        try:
            message = MIMEMultipart()
            message["From"] = os.getenv("SENDER")
            message["To"] = os.getenv("RECEIVER")
            message["Subject"] = "Linkedin Bot - Connection Limit Reached"

            body = f"""
            {string_to_write}
            
            The bot will now close.

            -----------------------------
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

            """            
            message.attach(MIMEText(body, "plain"))

            # Send email using SSL
            with smtplib.SMTP_SSL(os.getenv("SMTP_SERVER_SENDER"), os.getenv("SMTP_PORT_SENDER")) as server:
                server.login(os.getenv("SENDER"), os.getenv("SENDER_PASS"))
                server.sendmail(
                    os.getenv("SENDER"),
                    os.getenv("RECEIVER"), 
                    message.as_string()
                )
                
            logger.info("Successfully sent connection limit notification email")
            
        except Exception as e:
            logger.error(f"Failed to send connection limit email: {str(e)}")
            raise
    
    def get_last_iframe(
        self,
        needed_xpath: Optional[str] = None, 
        max_timeout: int = 10
    ) -> int:
        self.driver.switch_to.default_content()
        waiter = WebDriverWait(self.driver, max_timeout)
        div_xpath = "//div[contains(@id, 'ctn')]"
        div_iframes_xpath = f"{div_xpath}//iframe"

        _,found = self._get_last_iframe_helper(driver=self.driver, stop_if_xpath=div_xpath, max_timeout=max_timeout)
        if not found:
            raise UnexpectedException("Not found the 'ctn' div")
        
        try:
            
            # Try presence first instead of visibility
            iframes = waiter.until(
                EC.presence_of_all_elements_located((By.XPATH, div_iframes_xpath))
            )
            
            # Filter for only displayed iframes
            visible_iframes = [
                iframe for iframe in iframes 
                if iframe.is_displayed() and iframe.size['height'] > 0
            ]
            
            logger.info(f"Found {len(visible_iframes)} visible iframes out of {len(iframes)} total")

            if not visible_iframes:
                raise UnexpectedException("No visible iframes found")

            for iframe in visible_iframes:
                try:
                    self.driver.switch_to.frame(iframe)
                    _, found = self._get_last_iframe_helper(
                        driver=self.driver,
                        stop_if_xpath=needed_xpath or "//div", 
                        max_timeout=max_timeout
                    )
                    if found:
                        return True
                    self.driver.switch_to.parent_frame()
                except Exception as e:
                    logger.warning(f"Failed to switch to iframe: {str(e)}")
                
            self.write_response(self.driver.page_source, "error_get_last_iframe.html")
            raise UnexpectedException("Not found the needed iframe")
            
        except Exception as e:
            logger.error(f"Error in getting last iframe: {str(e)}")
            raise e
            
    def _get_last_iframe_helper(
        self,
        driver: Optional[WebDriver] = None,
        stop_if_xpath: Optional[str] = None,
        max_timeout: int = 10
    ) -> int:
        """
        Navigate through nested iframes until the last one is found or stop_if_xpath is encountered.
        
        Args:
            driver: WebDriver instance to use. If None, uses self.driver
            stop_if_xpath: Optional xpath to stop navigation when found
            max_timeout: Maximum timeout for waiting for iframes
            
        Returns:
            int: Number of frames traversed
            
        Raises:
            WebDriverException: If there's an error switching between frames
        """
        frames = 0
        if not driver:
            self.driver.switch_to.default_content()
            driver = self.driver
        DEFAULT_MIN_TIMEOUT = 3
        POLL_FREQUENCY = 2
        DEFAULT_MAX_WAIT = 5
        break_while = False
        MAX_IFRAMES = 40
        try:
            while frames < MAX_IFRAMES:
                try:
                    wait = WebDriverWait(
                        driver,
                        timeout=np.random.randint(DEFAULT_MIN_TIMEOUT, max_timeout),
                        poll_frequency=POLL_FREQUENCY
                    )
                    
                    # Try to switch to the next iframe
                    wait.until(EC.frame_to_be_available_and_switch_to_it(
                        (By.XPATH, self.general_iframe_xpath)
                    ))
                    frames += 1
                    

                except (TimeoutException, WebDriverException) as e:
                    logger.info("No more iframes found after %d frames", frames)
                    break_while = True
                    break
                finally:
                    if stop_if_xpath:
                        try:
                            wait_element = WebDriverWait(driver, DEFAULT_MAX_WAIT)
                            wait_element.until(
                                EC.presence_of_element_located((By.XPATH, stop_if_xpath))
                            )
                            logger.info("Found stop xpath: %s after %d frames", stop_if_xpath, frames)
                            return (frames, True)
                        except TimeoutException:
                            if not break_while:
                                continue
                    return (frames, False)
                    
        except Exception as e:
            logger.error("Unexpected error while traversing iframes: %s", str(e))
            raise
    
    def check_if_email_code(self):
        form_pin_xpath = "//form[@id='email-pin-challenge']"
        input_pin_xpath = "//input[@id='input__email_verification_pin']"
        submit_pin_xpath = "//button[@id='email-pin-submit-button']"

        try:
            WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                EC.presence_of_element_located((By.XPATH, form_pin_xpath))
            )
            logger.info("Email verification code required")
            code = self.waiting_for_code_mail()
            if not code:
                raise UnexpectedException("Email code not received")
            input_pin = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                EC.element_to_be_clickable((By.XPATH, input_pin_xpath))
            )
            for digit in code:
                input_pin.send_keys(digit)
                time.sleep(np.random.uniform(0.1, 0.3))
            submit_pin = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                EC.element_to_be_clickable((By.XPATH, submit_pin_xpath))
            )
            ActionChains(self.driver).click(submit_pin).perform()
            logger.info("Submitted email verification code")
            return True
        except:
            logger.info("No email verification code required")
            return False

    def check_if_captcha(self, max_retries=3, base_timeout=7):
        """
        Check and handle Linkedin captcha challenge.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_timeout: Base timeout for waits
            
        Raises:
            CaptchaNeededException: If captcha needs manual intervention
            UnexpectedException: For unexpected errors
        """
        
        selectors = {
            'captcha': self.captcha_xpath,
            'verify_button': "//button[contains(., 'Verify')]",
            'challenge_image': "//img[@id='game_challengeItem_image']"
        }
        
        for attempt in range(max_retries):
            try:
                # Check for captcha presence with dynamic wait
                timeout = base_timeout * (attempt + 1)
                logger.info(f"Checking for captcha (attempt {attempt + 1}/{max_retries})")
                
                try:
                    WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.XPATH, selectors['captcha']))
                    )
                except TimeoutException:
                    logger.info("No captcha detected")
                    return
                    
                logger.warning("Captcha detected - starting resolution process")
                
                # Store original frame context
                original_frame = self.driver.current_window_handle
                
                try:
                    # Navigate to deepest iframe containing captcha
                    self.get_last_iframe(max_timeout=timeout)
                    
                    # Verify button handling
                    verify_button = WebDriverWait(self.driver, timeout).until(
                        EC.element_to_be_clickable((By.XPATH, selectors['verify_button']))
                    )
                    
                    # Click verify with retry
                    for click_attempt in range(2):
                        ActionChains(self.driver).click(verify_button).perform()
                        break
                    
                    logger.info("Clicked verify button")
                    time.sleep(np.random.uniform(0.5, 1))
                    
                    # Wait for challenge image
                    try:
                        WebDriverWait(self.driver, timeout).until(
                            EC.presence_of_element_located((By.XPATH, selectors['challenge_image']))
                        )
                        logger.info("Challenge image loaded")
                    except:
                        raise UnexpectedException("Captcha image not found after verification")
                        
                    # Handle the actual captcha resolution
                    logger.info("Starting captcha resolution")
                    self.resolve_captcha()
                    
                    # Verify captcha is resolved
                    try:
                        self.check_if_feed()
                        logger.info("Captcha successfully resolved")
                        return
                    except TimeoutException:
                        if attempt < max_retries - 1:
                            logger.warning("Captcha may not be resolved, retrying...")
                            continue
                        raise CaptchaNeededException("Failed to verify captcha resolution")
                        
                finally:
                    # Always restore original frame context
                    try:
                        self.driver.switch_to.default_content()
                        self.driver.switch_to.window(original_frame)
                    except Exception as e:
                        logger.error(f"Error restoring frame context: {str(e)}")
                        
            except Exception as e:
                logger.error(f"Error handling captcha (attempt {attempt + 1}): {str(e)}")
                self.driver.switch_to.default_content()
                self.driver.switch_to.window(original_frame)
                self.write_response(self.driver.page_source, f"error_captcha_attempt_{attempt}.html")
                
                if attempt < max_retries - 1:
                    self.driver.refresh()
                    time.sleep(np.random.uniform(2, 4) * (attempt + 1))  # Exponential backoff
                    continue
                raise

        raise CaptchaNeededException("Failed to handle captcha after max retries")

    def resolve_captcha_helper(self, message):
        self.send_email(message)

        mail_response = self.wait_for_captcha_response()
        if not mail_response:
            raise CaptchaNeededException("Captcha response not received")
        return mail_response

    
    def check_if_phone_number(self, max_retries=3):
        """
        Handle phone number verification if required by LinkedIn.
        
        Args:
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            bool: True if phone verification completed successfully
            
        Raises:
            Exception: If verification fails after max retries
        """
        selectors = {
            'phone_input': "//input[@aria-label='Please enter your phone number without country code']",
            'submit_button': "//button[@id='register-phone-submit-button']",
            'code_input': "//input[@aria-label='Please enter the 6 digit pin']",
            'error_div': "//div[contains(@class, 'body__banner body__banner--error') and not(contains(@class, 'hidden'))]"
        }

        for attempt in range(max_retries):
            try:
                # Check if phone verification is needed
                try:
                    phone_input = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                        EC.presence_of_element_located((By.XPATH, selectors['phone_input']))
                    )
                except TimeoutException:
                    logger.info("No phone verification required")
                    return False

                logger.info("Phone verification required")
                phone_number = os.getenv("PHONE_NUMBER")
                if not phone_number:
                    raise Exception("Phone number not configured in environment variables")

                # Type phone number with human-like delays
                for digit in phone_number:
                    phone_input.send_keys(digit)
                    time.sleep(np.random.uniform(0.1, 0.3))
                
                # Click submit with retry
                submit_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                    EC.element_to_be_clickable((By.XPATH, selectors['submit_button']))
                )
                
                ActionChains(self.driver).click(submit_button).perform()
                
                logger.info("Submitted phone number")

                # Check for error message
                try:
                    error_div = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                        EC.presence_of_element_located((By.XPATH, selectors['error_div']))
                    )
                    error_text = error_div.text
                    logger.warning(f"Phone verification error: {error_text}")
                    logger.warning(f"Waiting {self.waiting_before_code_retry//3600} hours before retry")
                    time.sleep(self.waiting_before_code_retry)
                    continue
                except TimeoutException:
                    pass

                # Send email requesting code
                self.send_email(
                    "Required code number, which you'll receive by sms.", 
                    "Linkedin Bot - Phone Code"
                )

                # Wait for code from email
                code = self.waiting_for_phone_code()
                if not code:
                    raise Exception("Did not receive verification code")

                logger.info(f"Received verification code: {code}")

                # Enter verification code
                code_input = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                    EC.presence_of_element_located((By.XPATH, selectors['code_input']))
                )
                
                for digit in str(code):
                    code_input.send_keys(digit)
                    time.sleep(np.random.uniform(0.1, 0.3))

                # Submit code
                submit_button = WebDriverWait(self.driver, self.get_web_driver_wait_time()).until(
                    EC.element_to_be_clickable((By.XPATH, selectors['submit_button']))
                )
                
                ActionChains(self.driver).click(submit_button).perform()

                # Verify success by waiting for error message absence
                try:
                    WebDriverWait(self.driver, self.get_web_driver_wait_time()).until_not(
                        EC.presence_of_element_located((By.XPATH, selectors['error_div']))
                    )
                    logger.info("Phone verification completed successfully")
                    return True
                except TimeoutException:
                    if attempt < max_retries - 1:
                        logger.warning("Verification may have failed, retrying...")
                        continue
                    raise Exception("Phone verification failed")

            except Exception as e:
                logger.error(f"Phone verification attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(np.random.uniform(2, 4) * (attempt + 1))
                    continue
                raise

        raise Exception(f"Phone verification failed after {max_retries} attempts")


    def resolve_captcha(self):

        """
        Handles Linkedin's captcha verification process by:
        1. Finding and clicking on captcha images
        2. Handling retry attempts if incorrect
        3. Supporting both big puzzle (3 same objects) and small puzzle (correct orientation) captchas
        
        Raises:
            CaptchaNeededException: If captcha cannot be resolved
            UnexpectedException: For unexpected errors during resolution
        """
        SELECTORS = {
            'try_again': "//button[contains(., 'Try again')]",
            'images': "//li[contains(@id, 'mage')]//a",
            'big_puzzle': "//h2[contains(., 'Pick one square that shows three of the same object')]",
            'small_puzzle': "//h2[contains(., 'Pick the image that is the correct way up')]"
        }

        message_to_send = None
        waiter = WebDriverWait(self.driver, self.get_web_driver_wait_time())

        try:
           # Wait for captcha images to load
            images = waiter.until(
                EC.presence_of_all_elements_located((By.XPATH, SELECTORS['images']))
            )
            total_images = len(images)
            logger.info(f"Found {total_images} captcha images")
            tries_captcha = 1
            MAX_CAPTCHA_RESLV = 15
            current_try = 0
            while current_try < MAX_CAPTCHA_RESLV:
                current_try += 1

                response = self.resolve_captcha_helper(message_to_send)

                if response < 1 or response > total_images:
                    message_to_send = f"Invalid image number. Choose a number between 1 and {total_images}"
                    continue

                # Click selected image
                image_xpath = f"//li[contains(@id, 'mage{response}')]//a"
                image = waiter.until(
                    EC.element_to_be_clickable((By.XPATH, image_xpath))
                )
                ActionChains(self.driver).click(image).perform()
                logger.info(f"Clicked image {response}")

                time.sleep(np.random.uniform(0.5, 1))
                try:
                    try_again = waiter.until(
                        EC.element_to_be_clickable((By.XPATH, SELECTORS["try_again"]))
                    )

                    ActionChains(self.driver).click(try_again).perform()
                    time.sleep(np.random.randint(1, 2))
                    try:
                        tries_captcha += 1
                        self.get_last_iframe(needed_xpath=SELECTORS['small_puzzle'])
                        logger.info("Retrying to resolve captcha")
                    except TimeoutException:
                        logger.info(f"Body: {self.driver.page_source}")
                        raise UnexpectedException("No small puzzle found")

                    logger.info(f"Clicked on try again button")
                    message_to_send = f"Wrong image selected ({response}). Choose another number between 1 and {total_images}"
                   

                    continue
                except TimeoutException:
                    pass
                try:
                    self.driver.switch_to.default_content()
                    waiter.until(
                        EC.visibility_of_element_located((By.XPATH, self.captcha_xpath))
                    )
                    self.get_last_iframe(needed_xpath=SELECTORS['big_puzzle'])
                    logger.info("Need to resolve captcha again")
                    self.waiting_before_check = 7
                    message_to_send = "Solve another captcha"
                    continue
                except TimeoutException:
                    logger.info("Exiting captcha resolution method")
                    return

        except Exception as e:
            logger.error(f"Error in getting images: {str(e)}")
            self.write_response(self.driver.page_source, "error_resolve_captcha.html")
            raise e
        finally:
            self.driver.switch_to.default_content()

    def save_centered_screenshot(self, padding=250):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f"screenshot_{timestamp}.png"

            

            x_center = self.viewport_width // 2
            y_center = self.viewport_height // 2
            logger.info(f"Center coordinates: {x_center}, {y_center}")
            half_width = 304 //2
            half_height = 294 // 2
            
            
            # Take full screenshot
            self.driver.save_screenshot(screenshot_path)
            
            # Open and crop image
            img = Image.open(screenshot_path)
            
            # Calculate crop coordinates with padding
            left = max(0, x_center - padding - half_width)
            top = max(0, y_center - padding - half_height)
            right = min(img.width, x_center + half_width + padding)
            bottom = min(img.height, y_center + half_height + padding)
            
            # Crop and save
            img_cropped = img.crop((left, top, right, bottom))
            img_cropped.save(screenshot_path)
            
            logger.info(f"Saved centered screenshot to {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Error saving centered screenshot: {str(e)}")
            return None

    def send_email(self, message_to_send=None, subject:str = "Linkedin Bot - Captcha to Solve", max_retries=3):
        for attempt in range(max_retries):
            try:
                self.see_all_emails_captcha()

                screenshot_path = self.save_centered_screenshot()
                if not screenshot_path:
                    logger.error("Error saving screenshot")
                    raise Exception("Error saving screenshot")

                message = MIMEMultipart()
                message["From"] = os.getenv("SENDER")
                message["To"] = os.getenv("RECEIVER")
                message["Subject"] = subject
                final_message = message_to_send or "Bot has stopped working because of captcha."

                final_message += f"\n\n--------------------------------------\n\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                message.attach(MIMEText(final_message, "plain"))

                with open(screenshot_path, 'rb') as f:
                    img_data = f.read()
                    image = MIMEImage(img_data, name=os.path.basename(screenshot_path))
                    message.attach(image)

                with smtplib.SMTP_SSL(os.getenv("SMTP_SERVER_SENDER"), os.getenv("SMTP_PORT_SENDER")) as server:
                    server.login(os.getenv("SENDER"), os.getenv("SENDER_PASS"))
                    server.sendmail(os.getenv("SENDER"), os.getenv("RECEIVER"), message.as_string())
                    logger.info("Successfully sent email")
                    return True
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.info(f"Retrying... ({attempt + 2}/{max_retries})")
                    result = check_internet_connection(logger=logger, timeout=10)
                    if not result:
                        logger.error("No internet connection")
                        time.sleep(60)
                    else:
                        logger.error(f"Error, but trying again ({attempt}): {str(e)}")
                    continue
                else:
                    logger.error(f"Error in sending email: {str(e)}")
                    raise e
            finally:
                os.remove(screenshot_path)

    def get_email_text(self, message):
        # If message is string, return directly
        if isinstance(message.get_payload(), str):
            return message.get_payload()
            
        # Handle multipart messages
        text_content = ""
        if message.is_multipart():
            # Get all parts
            for part in message.walk():
                # Check if part is text
                if part.get_content_type() == "text/plain":
                    text_content += part.get_payload()
        else:
            text_content = message.get_payload()
            
        return text_content.strip()
    def extract_number_from_message(self, message: str, regex=r'[\s+]?(\d)', group:int=1) -> int:
        try:
            # Search for single number with whitespace prefix
            match = re.search(regex, message)
            logger.info(f"Match: {str(match)}")
            if match:
                return int(match.group(group))
            logger.error("No number found in message")
            return None
        except Exception as e:
            logger.error(f"Error extracting number: {str(e)}")
            return None
        
    def see_all_emails_captcha(self):
        imap = None
        try:
            imap = imaplib.IMAP4_SSL(os.getenv("EMAIL_SERVER_HOST_SENDER"), timeout=30)
            imap.login(os.getenv("SENDER"), os.getenv("SENDER_PASS"))
            imap.select(os.getenv("SENDER_INBOX_FOLDER"))
            search_criteria = f'(UNSEEN FROM "{os.getenv("RECEIVER")}" SUBJECT "Linkedin Bot - Captcha To Solve") SINCE {datetime.now().strftime("%d-%b-%Y")}'

            _, messages = imap.search(None, search_criteria)
            if messages[0]:
                for email_id in messages[0].split():
                    _, msg = imap.fetch(email_id, "(RFC822)")
                    email_body = msg[0][1]
                    message = email.message_from_bytes(email_body)
                    subject = decode_header(message["subject"])[0][0]

                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    message = self.get_email_text(message)
                    logger.info(f"Cleaned Message: {message}")

        except (ConnectionResetError, ssl.SSLError, imaplib.IMAP4.abort) as e:
            logger.error(f"Connection error during check: {str(e)}")
        
        finally:
            if imap:
                try:
                    imap.logout()
                except:
                    pass


    def wait_for_captcha_response(self):
        max_retries = 3
        retry_delay = 30
        imap = None
        
        for attempt in range(max_retries):
            try:
                if imap:
                    try:
                        imap.logout()
                    except:
                        pass
                        
                imap = imaplib.IMAP4_SSL(os.getenv("EMAIL_SERVER_HOST_SENDER"), timeout=30)
                imap.login(os.getenv("SENDER"), os.getenv("SENDER_PASS"))
                start_time = time.time()

                while (time.time() - start_time) < self.timeout_minutes * 60:
                    try:
                        imap.select(os.getenv("SENDER_INBOX_FOLDER"))
                        search_criteria = f'(UNSEEN FROM "{os.getenv("RECEIVER")}" SUBJECT "Linkedin Bot - Captcha To Solve" SINCE {datetime.now().strftime("%d-%b-%Y")})'
                        logger.info("Waiting for captcha response")
                        _, messages = imap.search(None, search_criteria)
                        
                        if messages[0]:
                            logger.info("Captcha response received")
                            email_id = messages[0].split()[-1]
                            _, msg = imap.fetch(email_id, "(RFC822)")
                            email_body = msg[0][1]

                            message = email.message_from_bytes(email_body)
                            subject = decode_header(message["subject"])[0][0]

                            if isinstance(subject, bytes):
                                subject = subject.decode()
                            message = self.get_email_text(message)
                            number = self.extract_number_from_message(message)
                            logger.info(f"Extracted number: {number}")
                            return number
                            
                    except (ConnectionResetError, ssl.SSLError, imaplib.IMAP4.abort) as e:
                        logger.error(f"Connection error during check: {str(e)}")
                        break  # Break inner loop to trigger retry
                        
                    
                    time.sleep(self.waiting_before_check)
                    
                if attempt < max_retries - 1:
                    logger.info(f"Retrying IMAP connection, attempt {attempt + 2}/{max_retries}")
                    time.sleep(retry_delay)
                    continue
                
            except Exception as e:
                logger.error(f"Error in waiting for captcha response: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying IMAP connection, attempt {attempt + 2}/{max_retries}")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise e
            finally:
                if imap:
                    try:
                        imap.logout()
                    except:
                        pass
                        
        return None


    def waiting_for_confirmation_email(self):
        max_retries = 3
        retry_delay = 30
        imap = None

        for attempt in range(max_retries):
            try:
                if imap:
                    try:
                        imap.logout()
                    except:
                        pass
                
                imap = imaplib.IMAP4_SSL(os.getenv("EMAIL_SERVER_HOST_SENDER"), timeout=60)
                imap.login(os.getenv("SENDER"), os.getenv("SENDER_PASS"))
                start_time = time.time()

                while (time.time() - start_time) < self.timeout_minutes * 60:
                    try:
                        imap.select(os.getenv("SENDER_INBOX_FOLDER"))
                        search_criteria = f'(UNSEEN FROM "{os.getenv("RECEIVER")}" SUBJECT "Linkedin Bot - Authorization Needed" SINCE {datetime.now().strftime("%d-%b-%Y")})'
                        logger.info("Waiting for confirmation email")
                        _, messages = imap.search(None, search_criteria)

                        if messages[0]:
                            logger.info("Confirmation email received")
                            email_id = messages[0].split()[-1]
                            _, msg = imap.fetch(email_id, "(RFC822)")
                            email_body = msg[0][1]

                            message = email.message_from_bytes(email_body)
                            subject = decode_header(message["subject"])[0][0]

                            if isinstance(subject, bytes):
                                subject = subject.decode()
                            message = self.get_email_text(message)
                            return message
                    except (ConnectionResetError, ssl.SSLError, imaplib.IMAP4.abort) as e:
                        logger.error(f"Connection error during check: {str(e)}")
                        break
                    time.sleep(self.waiting_before_check)
                if attempt < max_retries - 1:
                    logger.info(f"Retrying IMAP connection, attempt {attempt + 2}/{max_retries}")
                    time.sleep(retry_delay)
                    continue
            except Exception as e:
                logger.error(f"Error in waiting for confirmation email: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying IMAP connection, attempt {attempt + 2}/{max_retries}")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise e
            finally:
                if imap:
                    try:
                        imap.logout()
                    except:
                        pass

    def waiting_for_phone_code(self):
        imap = None
        max_retries = 3
        retry_delay = 30
        for attempt in range(max_retries):
            try:
                if imap:
                    try:
                        imap.logout()
                    except:
                        pass
                imap = imaplib.IMAP4_SSL(os.getenv("EMAIL_SERVER_HOST_SENDER"), timeout=30)
                imap.login(os.getenv("SENDER"), os.getenv("SENDER_PASS"))
                start_time = time.time()

                while (time.time() - start_time) < self.timeout_minutes * 60:
                    try:
                        imap.select(os.getenv("SENDER_INBOX_FOLDER"))
                        search_criteria = f'(UNSEEN FROM "{os.getenv("RECEIVER")}" SUBJECT "Linkedin Bot - Phone Code" SINCE {datetime.now().strftime("%d-%b-%Y")})'
                        logger.info("Waiting for phone code")
                        _, messages = imap.search(None, search_criteria)
                        
                        if messages[0]:
                            logger.info("Phone code received")
                            email_id = messages[0].split()[-1]
                            _, msg = imap.fetch(email_id, "(RFC822)")
                            email_body = msg[0][1]

                            message = email.message_from_bytes(email_body)
                            subject = decode_header(message["subject"])[0][0]

                            if isinstance(subject, bytes):
                                subject = subject.decode()
                            message = self.get_email_text(message)
                            number = self.extract_number_from_message(message, regex=r'[\s+]?(\d{6})')
                            logger.info(f"Extracted number: {number}")
                            return number
                        
                    except (ConnectionResetError, ssl.SSLError, imaplib.IMAP4.abort) as e:
                        logger.error(f"Connection error during check: {str(e)}")
                        break
                    time.sleep(self.waiting_before_check)

                if attempt < max_retries - 1:
                    logger.info(f"Retrying IMAP connection, attempt {attempt + 2}/{max_retries}")
                    time.sleep(retry_delay)
                    continue
                
            except Exception as e:
                logger.error(f"Error in waiting for code response: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying IMAP connection, attempt {attempt + 2}/{max_retries}. Error: {e}")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise e
            finally:
                if imap:
                    try:
                        imap.logout()
                    except:
                        pass
        return None

    def waiting_for_code_mail(self):
        max_retries = 1
        retry_delay = 30
        imap = None
        
        for attempt in range(max_retries):
            try:
                if imap:
                    try:
                        imap.logout()
                    except:
                        pass
                        
                # Connect to Outlook IMAP server
                imap = imaplib.IMAP4_SSL(os.getenv("EMAIL_SERVER_HOST_LINKEDIN"))
                imap.login(os.getenv("LINKEDIN_USER_MAIL"), os.getenv("LINKEDIN_MAILBOX_PASS"))
                start_time = time.time()

                while (time.time() - start_time) < self.timeout_minutes * 60:
                    try:
                        imap.select(os.getenv("LINKEDIN_INBOX_FOLDER"))  # Outlook uses uppercase INBOX
                        # Outlook search criteria syntax
                        search_criteria = f'(UNSEEN FROM "{os.getenv("EMAIL_LINKEDIN_CODE")}" HEADER "X-LinkedIn-Template" "security_ato_challenge_send_pin")' #  SINCE {datetime.now().strftime("%d-%b-%Y")}
                        logger.info("Waiting for security code from Linkedin")
                        _, messages = imap.search(None, search_criteria)
                        
                        if messages[0]:
                            logger.info("Code response received from Linkedin")
                            email_id = messages[0].split()[-1]
                            _, msg = imap.fetch(email_id, "(RFC822)")
                            email_body = msg[0][1]

                            message = email.message_from_bytes(email_body)
                            subject = decode_header(message["subject"])[0][0]

                            if isinstance(subject, bytes):
                                subject = subject.decode()
                            message = self.get_email_text(message)
                            logger.info(f"Cleaned Message: {message}")
                            number = self.extract_number_from_message(message, regex=r"\s(\d{6})\s", group=1)
                            return number
                            
                    except (ConnectionResetError, ssl.SSLError, imaplib.IMAP4.abort) as e:
                        logger.error(f"Connection error during check: {str(e)}")
                        break
                        
                    time.sleep(20)
                    
                if attempt < max_retries - 1:
                    logger.info(f"Retrying IMAP connection, attempt {attempt + 2}/{max_retries}")
                    time.sleep(retry_delay)
                    continue
                
            except imaplib.IMAP4.error as e:
                logger.error(f"Outlook IMAP error: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying IMAP connection, attempt {attempt + 2}/{max_retries}")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise e
            except Exception as e:
                logger.error(f"Error in waiting for email code: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying IMAP connection, attempt {attempt + 2}/{max_retries}")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise e
            finally:
                if imap:
                    try:
                        imap.logout()
                    except:
                        pass
                        
        return None

    def human_like_mouse_move(self, element, num_control_points=3):
        """
        Moves mouse in a human-like way to element with bounds checking
        """
        def get_bezier_curve(start, end, viewport_size, num_points=50):
            """Generate bounded Bezier curve points"""
            control_points = [start]
            
            # Get viewport bounds
            viewport_width, viewport_height = viewport_size
            
            for _ in range(num_control_points):
                # Keep control points within viewport
                ctrl_x = min(max(
                    randint(min(start[0], end[0]), max(start[0], end[0])),
                    0), viewport_width
                )
                
                max_arc_height = min(abs(end[1] - start[1]) * 0.5, viewport_height // 4)
                ctrl_y = min(max(
                    randint(
                        min(start[1], end[1]) - int(max_arc_height),
                        max(start[1], end[1]) + int(max_arc_height)
                    ),
                    0), viewport_height
                )
                
                control_points.append((ctrl_x, ctrl_y))
                
            control_points.append(end)
            
            # Calculate bounded curve points
            path = []
            for t in np.linspace(0, 1, num_points):
                x = y = 0
                n = len(control_points) - 1
                
                for i, point in enumerate(control_points):
                    binom = math.comb(n, i)
                    t_i = (1 - t)**(n - i) * t**i
                    x += binom * t_i * point[0]
                    y += binom * t_i * point[1]
                
                # Ensure points stay within viewport
                x = min(max(int(x), 0), viewport_width)
                y = min(max(int(y), 0), viewport_height)
                path.append((x, y))
                
            return path

        try:
            # Get viewport dimensions
            viewport_width = self.driver.execute_script("return window.innerWidth;")
            viewport_height = self.driver.execute_script("return window.innerHeight;")
            
            # Get element location relative to viewport
            element_rect = element.rect
            viewport_x = self.driver.execute_script("return arguments[0].getBoundingClientRect().x;", element)
            viewport_y = self.driver.execute_script("return arguments[0].getBoundingClientRect().y;", element)

            # Scroll element into view if needed
            if not (0 <= viewport_y <= viewport_height):
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                    element
                )
                time.sleep(np.random.uniform(0.3, 0.7))
                
                # Recalculate viewport position
                viewport_x = self.driver.execute_script("return arguments[0].getBoundingClientRect().x;", element)
                viewport_y = self.driver.execute_script("return arguments[0].getBoundingClientRect().y;", element)

            # Calculate target point within element bounds
            padding = 5
            target_x = min(max(
                randint(
                    int(viewport_x + padding),
                    int(viewport_x + element_rect['width'] - padding)
                ),
                0), viewport_width
            )
            target_y = min(max(
                randint(
                    int(viewport_y + padding),
                    int(viewport_y + element_rect['height'] - padding)
                ),
                0), viewport_height
            )

            # Calculate start position
            start_x = max(0, min(target_x - 100, viewport_width))
            start_y = max(0, min(target_y + 100, viewport_height))

            # Generate path within viewport bounds
            path = get_bezier_curve(
                (start_x, start_y),
                (target_x, target_y),
                (viewport_width, viewport_height)
            )

            # Move mouse with dynamic speed
            actions = ActionChains(self.driver)
            current_x, current_y = start_x, start_y
            
            for idx, (x, y) in enumerate(path):
                # Calculate bounded offset
                offset_x = min(max(x - current_x, -viewport_width + 10), viewport_width-10)
                offset_y = min(max(y - current_y, -viewport_height + 10), viewport_height-10)
                
                if offset_x != 0 or offset_y != 0:  # Only move if there's a change
                    actions.move_by_offset(offset_x, offset_y)
                    current_x, current_y = x, y
                    
                    # Variable delays
                    if idx == len(path) - 1:
                        time.sleep(np.random.uniform(0.1, 0.2))
                    else:
                        time.sleep(np.random.uniform(0.001, 0.004))

            actions.perform()
            time.sleep(np.random.uniform(0.2, 0.4))

        except Exception as e:
            # Fallback to direct move if curve movement fails
            try:
                actions = ActionChains(self.driver)
                actions.move_to_element(element).perform()
            except Exception as e2:
                logger.error(f"Direct mouse movement also failed: {str(e2)}") 


    def get_web_driver_wait_time(self):
        return np.random.uniform(self.min_WDWT, self.max_WDWT)
    def close_browser(self):

        self.driver.quit()

