import os
import re
import subprocess

MIN_FIREFOX_NEEDING_SYSTEM_ACCESS = (138, 0)
MIN_GECKODRIVER_FOR_SYSTEM_ACCESS = (0, 36)
UNKNOWN_VERSION = (0, 0)


def geckodriver_service_args(geckodriver_path):
    """Firefox 138+ only lets WebDriver open about:debugging and the Zeeschuimer panel with system access,
    which geckodriver 0.36+ grants with --allow-system-access. Older geckodrivers refuse the unknown flag."""
    if _program_version([geckodriver_path], r'geckodriver (\d+)\.(\d+)') >= MIN_GECKODRIVER_FOR_SYSTEM_ACCESS:
        return ['--allow-system-access']

    firefox_version = _program_version([os.getenv('FIREFOX_BINARY') or 'firefox'], r'Firefox (\d+)\.(\d+)')
    if firefox_version >= MIN_FIREFOX_NEEDING_SYSTEM_ACCESS:
        raise RuntimeError(f"Firefox {firefox_version[0]} needs geckodriver 0.36 or newer, found an older one at {geckodriver_path}")
    print("geckodriver older than 0.36: starting without --allow-system-access")
    return []


def _program_version(command, version_pattern):
    try:
        version_output = subprocess.run([*command, '--version'], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return UNKNOWN_VERSION
    version_match = re.search(version_pattern, version_output)
    return tuple(int(part) for part in version_match.groups()) if version_match else UNKNOWN_VERSION
