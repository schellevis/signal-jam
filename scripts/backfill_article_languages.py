from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

from db import Database
from functions.articles import backfill_article_languages, load_json_file

SOURCES_DIR = Path(__file__).parent / 'source_data' / 'articles'
SOURCE_FILE_NAMES = ('russian_feeds.json', 'pravda_sources.json')


def load_configured_sources():
    """The sources of every configured source file; files that are not set up are skipped."""
    source_paths = [SOURCES_DIR / name for name in SOURCE_FILE_NAMES if (SOURCES_DIR / name).exists()]
    return [source for path in source_paths for source in load_json_file(path)]


def main():
    conn = Database().conn
    updated_count = backfill_article_languages(conn, load_configured_sources())
    print(f"Language set on {updated_count} articles")
    conn.close()


if __name__ == '__main__':
    main()
