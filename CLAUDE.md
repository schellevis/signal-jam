# Project Context

When working with this codebase, prioritize readability and clean code over cleverness. Ask clarifying questions before making architectural changes.

## About This Project

_Signal Jam_ is a software suite to track disinformation in the online sphere. It consists of a scraping part to gather information, and a dashboard to label it and display it to the public. The codebase is written in a modular fashion, it is _provider agnostic_ by design. 

## Key Directories

- `dashboard/` - The Vue code for the dashboard.
- `database/` - The sql structure and instructions for the database part. 
- `scripts/` - The python scripts to gather the information from social media. 

## MCP servers
Always use Context7 MCP when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask. 

## Standards

My coding standard is heavily focused on clean, modular code. Avoid long files and put explanations in READMEs rather then in the code itself. I prefer provider agnostic code, where functionality is implemented in a way that there is an abstraction layer on top which allows you to switch providers easily when it comes to things such as databases, deployment etc. 

### Naming variables and functions
- Use descriptive and meaningful names 
- For variables and properties: Nouns or short phrases with adjectives
- For functions and methods: verbs short phrases with adjectives
- For classes: nouns
- For booleans: yes/no questions (like isValid) 

### General clean code principles
- Limit the number of parameters in functions
- Functions should be small and do one thing. Avoid mixing levels of abstraction, but also avoid redundant splitting
- Use small classes with a single responsibility and with high cohesion
- Stay DRY: do not repeat yourself. Put functionality in different files and load them in different parts of the code if needed
- Avoid unexpected side effects
- Prefer positive checks
- Avoid deep nesting. Use the law of Demeter for "real objects" 
- Use the SOLID principles, especially SRP and OCP. 

### Folder and file structure
- When using python, place functions in a functions/ folder and if needed, subfolders for functions in a common category.
- When using python, place common variables in a .env file (and always a .env.example equivalent) and use python-dotenv
- When using javascript, place functions in separate js files if it makes files less readable otherwise
- When using javascript frameworks, stick to component structures but avoid long functions in component files (put these in separate js files)

### Comments
- Avoid comments as much as possible, use clear variable naming and clean code instead
- If more elaborate explanation feels necessary, create a README file or add some explanation there
- Comments are acceptable for legal stuff, warnings, helpful explanations (i.e. with regex) or todo's

## Notes

### Running and testing
- `uv run --with-requirements scripts/requirements.txt <script>` - run a script without a venv (there is no pyproject.toml); use Python 3.11
- `python install_zeeschuimer.py` (in `scripts/`) - check out the pinned Zeeschuimer fork commit (`scripts/zeeschuimer_source.json`) into `scripts/scraping_tools/zeeschuimer`; scrapers refuse to start without it
- `setup_selenium(platform_stats_id)` - stats ids are `twittercom`, `tiktokcom`, `instagramcom`, `facebookcom`; it stops when the loaded Zeeschuimer lacks that module
- Local test stack: Postgres + `database/schema.sql`, PostgREST with the `anon` role from `database/README.md`, dashboard with `VITE_DB_PROVIDER=postgrest`
- `vite build` needs `VITE_APP_TITLE`, `VITE_APP_DESCRIPTION` and `VITE_APP_URL`, otherwise it fails with "URI malformed"
- `ndjson_to_db` sleeps `RATE_LIMIT_REST_SECONDS` (120) after every capture; set it to 0 in tests
- Test parsers offline on a saved Zeeschuimer ndjson capture before doing live scrapes; live runs use real accounts

### Gotchas
- Firefox 138+ needs geckodriver 0.36+ with `--allow-system-access` (handled in `functions/utils/geckodriver_service_args.py`)
- Facebook: automated logins get a puzzle and a session moved between browsers is invalidated; log in by hand in Firefox and copy the profile (`scripts/tmp_login_facebook.py` is a CLI fallback)
- Facebook captures are ~170 KB per post; the parser stores a compact `platform_data` and must skip malformed records one by one
- `package.json` pins Yarn 1 but `yarn.lock` is Berry; a `yarn install` may rewrite `yarn.lock` and `.yarnrc.yml`, don't commit those changes by accident
- `database/.gitignore` ignores `*.sql`, so put migration SQL in `database/README.md` ("Updating an existing database"), not in new `.sql` files
- The Docker image does not install Zeeschuimer and is untested; cloud configs only run `scrape_x.py`

### Sensitive data
- `scripts/scraping_tools/` (logged-in Firefox profile) and `scripts/data/` (captures with real users' posts) are gitignored and dockerignored; never commit them or copy them elsewhere
- Share captures with external tools or review agents only as aggregates (counts, key names), not post text, names or URLs
