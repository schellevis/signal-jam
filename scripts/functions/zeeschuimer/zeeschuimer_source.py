import json
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent
SOURCE_PATH = SCRIPTS_DIR / 'zeeschuimer_source.json'
ZEESCHUIMER_DIR = SCRIPTS_DIR / 'scraping_tools' / 'zeeschuimer'


def load_zeeschuimer_source():
    """The pinned repository and commit of the Zeeschuimer build the scrapers load."""
    return json.loads(SOURCE_PATH.read_text(encoding='utf-8'))


def installed_zeeschuimer_commit():
    """The commit checked out in ZEESCHUIMER_DIR, or None when nothing is installed."""
    if not (ZEESCHUIMER_DIR / '.git').exists():
        return None
    result = subprocess.run(['git', '-C', str(ZEESCHUIMER_DIR), 'rev-parse', 'HEAD'],
                            capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None
