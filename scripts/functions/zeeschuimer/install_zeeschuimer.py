import shutil
import subprocess

from .zeeschuimer_source import ZEESCHUIMER_DIR, load_zeeschuimer_source, installed_zeeschuimer_commit


def install_zeeschuimer():
    """Check out the pinned Zeeschuimer commit into scraping_tools/zeeschuimer. Does nothing when it is already there."""
    source = load_zeeschuimer_source()
    if installed_zeeschuimer_commit() == source['commit']:
        print(f"Zeeschuimer {source['commit'][:8]} is already installed in {ZEESCHUIMER_DIR}")
        return

    shutil.rmtree(ZEESCHUIMER_DIR, ignore_errors=True)
    ZEESCHUIMER_DIR.mkdir(parents=True)
    for git_arguments in (
        ['init', '--quiet'],
        ['fetch', '--quiet', '--depth', '1', source['repository'], source['commit']],
        ['checkout', '--quiet', '--detach', 'FETCH_HEAD'],
    ):
        _run_git(git_arguments)

    if installed_zeeschuimer_commit() != source['commit']:
        raise RuntimeError(f"Checked out the wrong commit in {ZEESCHUIMER_DIR}, expected {source['commit']}")
    print(f"Installed Zeeschuimer {source['commit'][:8]} from {source['repository']} in {ZEESCHUIMER_DIR}")


def _run_git(git_arguments):
    subprocess.run(['git', '-C', str(ZEESCHUIMER_DIR), *git_arguments], check=True)
