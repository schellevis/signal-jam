"""Temporary helper: log a Firefox profile into Facebook from the command line, so the scrapers can use it."""
import argparse
import getpass
import os
import shutil
import time
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

load_dotenv(Path(__file__).parent.parent / '.env')

SCRAPING_TOOLS_DIR = Path(__file__).parent / 'scraping_tools'
DEFAULT_PROFILE_DIR = SCRAPING_TOOLS_DIR / 'firefox-profile'
SCREENSHOT_PATH = SCRAPING_TOOLS_DIR / 'facebook-login.png'

LOGIN_URL = 'https://www.facebook.com/login/'
SESSION_COOKIE_NAME = 'c_user'
COOKIE_BUTTON_TEXTS = [
    'Decline optional cookies',
    'Only allow essential cookies',
    'Optionele cookies weigeren',
    'Alleen essentiële cookies toestaan',
]
COOKIE_BUTTON_XPATH = " | ".join(
    f"//*[(self::button or @role='button') and .//text()[normalize-space()='{text}']]"
    for text in COOKIE_BUTTON_TEXTS
)
EMAIL_SELECTOR = 'input[name="email"]'
PASSWORD_SELECTOR = 'input[name="pass"]'
CODE_INPUT_SELECTOR = 'input[type="text"], input[type="tel"], input[type="number"]'
PAGE_SETTLE_SECONDS = 3
SESSION_WAIT_SECONDS = 20


def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path,
                        default=Path(os.getenv('FIREFOX_PROFILE_PATH') or DEFAULT_PROFILE_DIR),
                        help='Firefox profile directory to log in (default: FIREFOX_PROFILE_PATH or scraping_tools/firefox-profile)')
    parser.add_argument('--headed', action='store_true', help='Show the browser window (needs a display)')
    parser.add_argument('--check', action='store_true', help='Only open the login form and report, without logging in')
    return parser.parse_args()


def start_browser(profile_dir, is_headed):
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_dir.chmod(0o700)

    options = Options()
    options.add_argument('-profile')
    options.add_argument(str(profile_dir))
    if not is_headed:
        options.add_argument('-headless')
    if os.getenv('FIREFOX_BINARY'):
        options.binary_location = os.getenv('FIREFOX_BINARY')

    geckodriver_path = shutil.which('geckodriver') or str(SCRAPING_TOOLS_DIR / 'geckodriver')
    return webdriver.Firefox(service=Service(geckodriver_path), options=options)


def is_logged_in(driver):
    return driver.get_cookie(SESSION_COOKIE_NAME) is not None


def find_visible(driver, selector, by=By.CSS_SELECTOR):
    visible_elements = [element for element in driver.find_elements(by, selector) if element.is_displayed()]
    return visible_elements[0] if visible_elements else None


def dismiss_cookie_banner(driver):
    button = find_visible(driver, COOKIE_BUTTON_XPATH, By.XPATH)
    if button:
        button.click()
        print("Declined optional cookies.")
        time.sleep(PAGE_SETTLE_SECONDS)


def find_login_form(driver):
    email_input = find_visible(driver, EMAIL_SELECTOR)
    password_input = find_visible(driver, PASSWORD_SELECTOR)
    if not (email_input and password_input):
        raise NoSuchElementException(f"Login form not found on {driver.current_url}, see {save_screenshot(driver)}")
    return email_input, password_input


def submit_credentials(email_input, password_input):
    email_input.send_keys(input('Facebook email or phone: ').strip())
    password_input.send_keys(getpass.getpass('Facebook password: '))
    password_input.send_keys(Keys.RETURN)


def save_screenshot(driver):
    driver.save_screenshot(str(SCREENSHOT_PATH))
    return SCREENSHOT_PATH


def wait_for_session(driver, seconds):
    deadline = time.time() + seconds
    while time.time() < deadline:
        if is_logged_in(driver):
            return True
        time.sleep(1)
    return False


def enter_code(driver, code):
    code_input = find_visible(driver, CODE_INPUT_SELECTOR)
    if not code_input:
        print("No code field found on this page.")
        return
    code_input.clear()
    code_input.send_keys(code)
    code_input.send_keys(Keys.RETURN)


def complete_extra_steps(driver):
    """Handle two-factor codes and approvals until the session cookie appears or the user stops."""
    while not wait_for_session(driver, SESSION_WAIT_SECONDS):
        dismiss_cookie_banner(driver)
        print(f"\nNot logged in yet. Page: {driver.title!r} ({driver.current_url})")
        print(f"Screenshot: {save_screenshot(driver)}")
        answer = input("Enter a code from Facebook, press Enter to check again after approving elsewhere, or q to stop: ").strip()
        if answer.lower() == 'q':
            return False
        if answer:
            enter_code(driver, answer)
    return True


def log_in(driver, is_check_only):
    driver.get(LOGIN_URL)
    time.sleep(PAGE_SETTLE_SECONDS)
    dismiss_cookie_banner(driver)

    if is_logged_in(driver):
        print("This profile is already logged in to Facebook.")
        return True

    email_input, password_input = find_login_form(driver)
    if is_check_only:
        print(f"Login form found on {driver.current_url}. Check only, not logging in. Screenshot: {save_screenshot(driver)}")
        return True

    submit_credentials(email_input, password_input)
    return complete_extra_steps(driver)


def main():
    arguments = parse_arguments()
    print(f"Using Firefox profile {arguments.profile}")
    driver = start_browser(arguments.profile, arguments.headed)
    try:
        is_successful = log_in(driver, arguments.check)
    finally:
        driver.quit()

    if is_successful and not arguments.check:
        print(f"Logged in. Set FIREFOX_PROFILE_PATH={arguments.profile} in .env so the scrapers use this profile.")
    if not is_successful:
        print("Login not completed.")


if __name__ == '__main__':
    main()
