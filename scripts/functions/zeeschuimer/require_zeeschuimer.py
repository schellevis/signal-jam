from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from .zeeschuimer_source import ZEESCHUIMER_DIR, load_zeeschuimer_source, installed_zeeschuimer_commit

PLATFORM_ROW_WAIT_SECONDS = 10


def require_installed_zeeschuimer():
    """Stop with instructions when scraping_tools/zeeschuimer is missing or not the pinned commit."""
    pinned_commit = load_zeeschuimer_source()['commit']
    installed_commit = installed_zeeschuimer_commit()
    if installed_commit != pinned_commit:
        raise RuntimeError(
            f"Zeeschuimer in {ZEESCHUIMER_DIR} is {installed_commit or 'not installed'}, expected {pinned_commit}. "
            "Run `python install_zeeschuimer.py` in the scripts folder."
        )


def require_platform_module(driver, platform_stats_id):
    """Stop when the loaded Zeeschuimer has no module for the platform, instead of scraping without capturing anything.

    Zeeschuimer's panel adds its platform rows asynchronously, so this waits for the row."""
    try:
        WebDriverWait(driver, PLATFORM_ROW_WAIT_SECONDS).until(
            expected_conditions.presence_of_element_located((By.ID, f'stats-{platform_stats_id}'))
        )
    except TimeoutException:
        raise RuntimeError(f"The loaded Zeeschuimer has no '{platform_stats_id}' module. Run `python install_zeeschuimer.py`.")
