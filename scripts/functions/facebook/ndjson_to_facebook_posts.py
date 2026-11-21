import json
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from classes import Account, Post

FACEBOOK_PLATFORM = 'facebook'
FACEBOOK_URL_BASE = 'https://www.facebook.com/'
CAPTURE_METADATA_KEYS = ('id', 'item_id', 'source_platform', 'source_platform_url', 'timestamp_collected')
NESTED_STORY_PATH = ('comet_sections', 'content', 'story')
NESTED_CREATION_TIME_PATH = ('comet_sections', 'timestamp', 'story', 'creation_time')
FEEDBACK_PATH = (
    'comet_sections', 'feedback', 'story', 'story_ufi_container', 'story',
    'feedback_context', 'feedback_target_with_context',
)


def ndjson_to_facebook_posts(ndjson_path):
    results = []
    skipped_count = 0
    with open(ndjson_path, 'r', encoding='utf-8') as ndjson_file:
        for line in ndjson_file:
            if not line.strip():
                continue
            parsed = _parse_line_safely(line)
            if parsed:
                results.append(parsed)
            else:
                skipped_count += 1
    if skipped_count:
        print(f"  [skipped] {skipped_count} Facebook records without a usable post or author")
    return results


def _parse_line_safely(line):
    """One malformed field must not cost the rest of the capture, since the importer only runs after parsing."""
    try:
        return _parse_line(line)
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None


def _parse_line(line):
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        return None
    story = entry.get('data') if isinstance(entry, dict) else None
    if not isinstance(story, dict):
        return None

    account = _build_account(_first_actor(story))
    url = story.get('permalink_url') or _dig(story, NESTED_STORY_PATH + ('wwwURL',))
    if not account or not url:
        return None
    return account, _build_post(entry, story, url)


def _first_actor(story):
    actors = story.get('actors')
    first_actor = actors[0] if isinstance(actors, list) and actors else None
    return first_actor if isinstance(first_actor, dict) else {}


def _build_account(actor):
    actor_id = actor.get('id')
    username = facebook_username_from_url(actor.get('url')) or actor_id
    if not username:
        return None
    return Account(
        platform=FACEBOOK_PLATFORM,
        username=str(username),
        account_url=actor.get('url') or f"{FACEBOOK_URL_BASE}profile.php?id={actor_id}",
        display_name=str(actor.get('name') or '').strip() or None,
    )


def facebook_username_from_url(profile_url):
    """The page or profile name from a Facebook URL, or the numeric id for profile.php?id= and /people/<name>/<id>/ URLs."""
    if not profile_url:
        return None
    parsed_url = urlparse(profile_url)
    path_segments = parsed_url.path.strip('/').split('/')
    if path_segments[0] == 'profile.php':
        return (parse_qs(parsed_url.query).get('id') or [None])[0]
    if path_segments[0] == 'people':
        return path_segments[2] if len(path_segments) > 2 else None
    return path_segments[0] or None


def _build_post(entry, story, url):
    shared_story = _shared_story(story)
    own_text = _message_text(story)
    feedback = _dig(story, FEEDBACK_PATH) or {}
    return Post(
        platform=FACEBOOK_PLATFORM,
        account_id=None,
        posted_at=_posted_at(story),
        url=url,
        content=own_text or _message_text(shared_story),
        post_type=_post_type(shared_story, own_text),
        parent_url=(shared_story or {}).get('permalink_url'),
        likes=_find_count(feedback, 'reaction_count'),
        reposts=_find_count(feedback, 'share_count'),
        comments=_find_comment_count(feedback),
        platform_data=_compact_platform_data(entry, story, own_text),
    )


def _shared_story(story):
    shared_story = story.get('attached_story')
    return shared_story if isinstance(shared_story, dict) else None


def _message_text(story):
    if not story:
        return None
    message = _dig(story, NESTED_STORY_PATH + ('message',)) or story.get('message')
    return message.get('text') if isinstance(message, dict) else None


def _post_type(shared_story, own_text):
    if not shared_story:
        return 'original'
    return 'quote' if own_text else 'repost'


def _posted_at(story):
    for unix_seconds in (story.get('creation_time'), _dig(story, NESTED_CREATION_TIME_PATH)):
        try:
            return datetime.fromtimestamp(int(unix_seconds), tz=timezone.utc)
        except (TypeError, ValueError, OverflowError, OSError):
            continue
    return datetime.now(tz=timezone.utc)


def _find_count(feedback, key):
    """The first {key: {'count': n}} in the feedback tree, skipping the previewed comments."""
    for value in _walk_values(feedback, key):
        if isinstance(value, dict) and isinstance(value.get('count'), int):
            return value['count']
    return 0


def _find_comment_count(feedback):
    for comments in _walk_values(feedback, 'comments'):
        if isinstance(comments, dict) and isinstance(comments.get('total_count'), int):
            return comments['total_count']
    return 0


def _walk_values(node, key):
    if isinstance(node, dict):
        for child_key, child in node.items():
            if child_key == 'interesting_top_level_comments':
                continue
            if child_key == key:
                yield child
            yield from _walk_values(child, key)
    elif isinstance(node, list):
        for child in node:
            yield from _walk_values(child, key)


def _walk_strings(node, key):
    return (value for value in _walk_values(node, key) if isinstance(value, str))


def _dig(node, path):
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


def _compact_platform_data(entry, story, own_text):
    """The capture without Facebook's rendering data, which runs to ~170 KB per post.

    Keeps 'data' with the links in the post, since contains_search_term searches it for expanded URLs."""
    compact = {key: entry.get(key) for key in CAPTURE_METADATA_KEYS}
    attachment_links = _walk_strings(story.get('attachments'), 'url')
    message_links = _walk_strings(story, 'external_url')
    compact['data'] = {
        'id': story.get('id'),
        'post_id': story.get('post_id'),
        'permalink_url': story.get('permalink_url'),
        'creation_time': story.get('creation_time'),
        'actors': [_compact_actor(actor) for actor in story.get('actors') or [] if isinstance(actor, dict)],
        'message': own_text,
        'links': sorted(set(attachment_links) | set(message_links)),
        'shared_post_url': (_shared_story(story) or {}).get('permalink_url'),
    }
    return compact


def _compact_actor(actor):
    return {key: actor.get(key) for key in ('id', 'name', 'url')}
