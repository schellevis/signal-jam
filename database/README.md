# Database

This folder contains the PostgreSQL schema for Signal Jam. You can use this schema to initialize the database of your choice.

## Schema Overview

The database consists of seven tables and one view:

### `accounts`
Stores social media accounts that are being tracked.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial | Primary key |
| `platform` | enum | twitter, tiktok, facebook, or instagram |
| `username` | varchar | Handle/username (unique per platform) |
| `account_url` | text | URL to the account profile (optional) |
| `display_name` | varchar | Display name (optional) |
| `is_watched` | boolean | True when the account is on the scrape list. Managed on the Instellingen page of the dashboard (logged-in users only); the scrapers read it at the start of each run |
| `is_approved` | boolean | True once the account has 3 posts labeled as misinformation. Set by a trigger on `posts`, never by hand. Approved accounts get all their posts scraped; candidates only posts matching the theme filter terms |
| `created_at` | timestamptz | When we added this account |

### `posts`
Stores all scraped posts across platforms.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial | Primary key |
| `url` | text | URL of the post (unique per platform) |
| `platform` | enum | twitter, tiktok, facebook, or instagram |
| `account_id` | integer | Foreign key to accounts |
| `content` | text | Post text content |
| `post_type` | enum | original, reply, repost, or quote |
| `parent_post_id` | integer | References original post (for replies/reposts/quotes) |
| `posted_at` | timestamptz | When the post was published |
| `scraped_at` | timestamptz | When we scraped the post |
| `likes` | integer | Like/favorite count |
| `reposts` | integer | Retweet/share count |
| `comments` | integer | Comment/reply count |
| `is_checked` | boolean | Whether the post has been reviewed |
| `is_relevant` | boolean | Moderation flag: false when a moderator marked the post as not belonging in the database |
| `relevant_for_signal_jam_theme` | boolean | Whether the post matches the theme filter terms (always true for term-search results) |
| `contains_misinformation` | boolean | Whether misinformation was found |
| `notes` | text | Free-text notes on the post (optional) |
| `frame_id` | integer | Foreign key to frames (optional) |
| `platform_data` | jsonb | Platform-specific metadata |

### `post_reposts`
Who reposted a post, and when. Plain reposts (retweets, shares without own text) have no content or label of their own, so they get a row here instead of a duplicate in `posts`. Quote posts add commentary and are stored in `posts` with `post_type = 'quote'`. A repost is only recorded when the original post is already in `posts`.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial | Primary key |
| `post_id` | integer | The reposted post, foreign key to posts (deleted with it) |
| `account_id` | integer | The account that reposted it, foreign key to accounts |
| `reposted_at` | timestamptz | When it was reposted |
| `url` | text | URL of the repost (optional) |

Unique per `(post_id, account_id)`.

### `scrape_terms`
Search and filter terms per platform, managed on the Instellingen page of the dashboard (logged-in users only). The scrapers read them at the start of each run.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial | Primary key |
| `platform` | enum | twitter, tiktok, facebook, or instagram |
| `kind` | enum | `search`: term the scraper searches for on the platform. `filter`: word that flags a post as relevant for the theme (`relevant_for_signal_jam_theme`) |
| `term` | text | The term. Search terms are used as-is in the search URL (so `%22rt.com%22` searches for the exact phrase) |
| `created_at` | timestamptz | When the term was added |

Unique per `(platform, kind, term)`.

### `account_review_queue` (view)
Watched accounts that still need labeling, used by the labeling page. One row per account that is not yet approved, has unreviewed theme posts, and has enough own posts (confirmed + unreviewed) to reach the three needed for approval. Reposts are not counted, since they have no label of their own.

| Column | Type | Description |
|--------|------|-------------|
| `account_id`, `platform`, `username`, `account_url`, `display_name` | | The account |
| `confirmed_count` | bigint | Posts labeled as misinformation |
| `unreviewed_count` | bigint | Theme posts not yet reviewed |

### `frames`
Central misinformation themes that posts can be tagged with.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial | Primary key |
| `name` | varchar | Unique frame name |
| `description` | text | Description of the frame (optional) |
| `created_at` | timestamptz | When the frame was created |

### `articles`
Articles scraped from Russian state media (RT, TASS, Lenta, Gazeta) and propaganda sites (Pravda NL). These are not social media posts, so they live outside of `posts`/`accounts`. The weekly propaganda summary in `summaries` is generated from them.

| Column | Type | Description |
|--------|------|-------------|
| `url` | text | Primary key, the URL of the article |
| `title` | text | Article title |
| `source` | text | Name of the outlet (e.g. `Tass`) |
| `author` | text | Author (optional) |
| `language` | varchar | ISO 639-1 code of the article, set per source in the source files (e.g. `en`, `ru`, `nl`) |
| `summary` | text | Summary as published in the feed (optional) |
| `content` | text | Full article text (optional) |
| `title_en` | text | English translation of the title (optional, filled by the translation step) |
| `content_en` | text | English translation of the start of the content, about 250 characters (optional, filled by the translation step) |
| `published_at` | timestamptz | When the article was published |
| `scraped_at` | timestamptz | When we scraped the article |
| `relevant_for_signal_jam_theme` | boolean | Whether the title, summary or content matches the filter terms in `search_terms.json`. Every article is stored, the dashboard hides unflagged ones by default |

### `summaries`
Weekly AI-generated summaries of tracked content.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial | Primary key |
| `week_start` | date | Monday of the summary week (unique) |
| `week_end` | date | Sunday of the summary week |
| `content` | text | Generated summary text |
| `propaganda_channels_content` | text | Summary of the week's articles from Russian propaganda channels. `NULL` until checked, an empty string when the week had no matching articles |
| `llm_provider` | varchar | Which LLM generated the summary (optional) |
| `generated_at` | timestamptz | When the summary was generated |

## Setup by Provider

### Supabase (recommended)

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to the SQL Editor in your dashboard
3. Paste the contents of `schema.sql` and run it
4. Edit your RLS policies, so that public access to the tables is limited to reading them, except for the accounts and terms tables. Make sure to only allow authenticated users to write to those.
5. Find your connection string under Settings > Database > Connection string
6. Add to your `.env`:
   ```
   DATABASE_URL=postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
   ```

### Neon

1. Create a new project at [neon.tech](https://neon.tech)
2. Open the SQL Editor from your dashboard
3. Paste the contents of `schema.sql` and run it
4. Copy your connection string from the dashboard
5. Add to your `.env`:
   ```
   DATABASE_URL=postgresql://[user]:[password]@[host].neon.tech/[database]?sslmode=require
   ```

### Railway

1. Create a new project at [railway.app](https://railway.app)
2. Add a PostgreSQL database to your project
3. Connect using the provided credentials and run `schema.sql`
4. Copy the connection string from the Variables tab
5. Add to your `.env`:
   ```
   DATABASE_URL=postgresql://postgres:[password]@[host].railway.app:5432/railway
   ```

### Local PostgreSQL

1. Make sure PostgreSQL is installed and running
2. Create a new database:
   ```bash
   createdb signaljam
   ```
3. Run the schema:
   ```bash
   psql -d signaljam -f schema.sql
   ```
4. Add to your `.env`:
   ```
   DATABASE_URL=postgresql://localhost:5432/signaljam
   ```

### Neon, Railway, and local PostgreSQL — dashboard access via PostgREST

The dashboard runs in the browser and can't connect to a raw PostgreSQL database directly. Supabase handles this transparently via its built-in [PostgREST](https://postgrest.org) layer. For all other providers you need to run PostgREST yourself and set `VITE_DB_PROVIDER=postgrest` in the dashboard.

**Quick setup (Docker):**
```bash
docker run --rm -p 3000:3000 \
  -e PGRST_DB_URI="postgresql://user:password@host:5432/database" \
  -e PGRST_DB_SCHEMA="public" \
  -e PGRST_DB_ANON_ROLE="anon" \
  postgrest/postgrest
```

Then in `dashboard/.env`:
```
VITE_DB_PROVIDER=postgrest
VITE_POSTGREST_URL=http://localhost:3000
```

For production, deploy PostgREST as a container alongside your database and set `VITE_POSTGREST_URL` to its public URL. If you want to restrict access, configure a JWT secret in PostgREST and set `VITE_POSTGREST_ANON_KEY` to a signed anon token.

The `PGRST_DB_ANON_ROLE` must be a PostgreSQL role that can read the tables the dashboard shows, and write what the labeling workflow (`posts`, `frames`) and the Instellingen page (`accounts`, `scrape_terms`) change. Create the role and grant permissions after running the schema:

```sql
CREATE ROLE anon NOLOGIN;
GRANT SELECT ON accounts, posts, summaries, frames, articles, post_reposts, scrape_terms, account_review_queue TO anon;
GRANT UPDATE, DELETE ON posts TO anon;
GRANT INSERT, UPDATE, DELETE ON accounts, frames TO anon;
GRANT INSERT, DELETE ON scrape_terms TO anon;
GRANT USAGE ON SEQUENCE accounts_id_seq, frames_id_seq, scrape_terms_id_seq TO anon;
```

> These grants let anyone who can reach PostgREST label posts and change what is scraped. For a public dashboard, give the write grants to a separate role for logged-in users and enable PostgREST's JWT authentication, like the Supabase setup does with RLS policies.

## Updating an existing database

`schema.sql` is for new databases. Articles gained a language, an English translation and a theme flag later; on a database from before that, run:

```sql
ALTER TABLE articles ADD COLUMN IF NOT EXISTS language VARCHAR(10);
ALTER TABLE articles ADD COLUMN IF NOT EXISTS title_en TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS content_en TEXT;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS relevant_for_signal_jam_theme BOOLEAN NOT NULL DEFAULT FALSE;
```

Then fill them with `python flag_existing_articles.py` and `python backfill_article_languages.py` in `scripts/` (see the [scripts README](../scripts/README.md#articles-russian-news-outlets)). Compare other tables with `schema.sql` the same way.

## Notes

- Adding a new platform to an existing database: the `platform` and `post_type` columns are Postgres enums, so new values need a migration rather than re-running `schema.sql`. For example, to add Instagram: `ALTER TYPE platform ADD VALUE 'instagram';` (run outside a transaction block; Postgres requires this for `ADD VALUE`).
- The `platform_data` JSONB column can store any platform-specific fields (e.g., video duration for TikTok, hashtags, media URLs)
- Posts are uniquely identified by `(platform, url)` to prevent duplicates
- Accounts are uniquely identified by `(platform, username)`
- The `contains_misinformation` field is nullable: `NULL` means not yet determined, `FALSE` means checked and clean, `TRUE` means flagged
- The `is_relevant` field defaults to `TRUE`; set to `FALSE` to exclude posts from analysis without deleting them
