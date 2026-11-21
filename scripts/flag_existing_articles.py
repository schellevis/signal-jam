from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

from db import Database
from functions.articles import flag_existing_articles, load_json_file

SEARCH_TERMS_PATH = Path(__file__).parent / 'source_data' / 'articles' / 'search_terms.json'


def main():
    conn = Database().conn
    flagged_count = flag_existing_articles(conn, load_json_file(SEARCH_TERMS_PATH))
    print(f"{flagged_count} articles flagged as relevant")
    conn.close()


if __name__ == '__main__':
    main()
