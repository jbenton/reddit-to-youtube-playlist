import os
import json
import base64
import re
import praw
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- Function Definitions ---
def get_reddit_client():
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=os.environ["REDDIT_USERNAME"],
        password=os.environ["REDDIT_PASSWORD"],
        user_agent=os.environ["REDDIT_USER_AGENT"]
    )
    return reddit

def fetch_youtube_ids_from_subreddit(reddit_client, subreddit_name, post_limit):
    subreddit = reddit_client.subreddit(subreddit_name)
    posts = subreddit.hot(limit=post_limit)
    yt_ids = set()
    for post in posts:
        url = post.url
        logging.info(f"Checking: {post.title} → {url}")
        match = re.search(r"(?:youtu\.be/|youtube\.com/watch\?v=)([\w-]{11})", url)
        if match:
            vid = match.group(1).lower()
            yt_ids.add(vid)
    logging.info(f"✅ Found {len(yt_ids)} YouTube video(s) from r/{subreddit_name}")
    return yt_ids

def get_youtube_service():
    try:
        client_secret = json.loads(base64.b64decode(os.environ["CLIENT_SECRET_JSON"]))
    except KeyError:
        logging.error("Error: CLIENT_SECRET_JSON is missing.")
        return None, None
    except base64.binascii.Error:
        logging.error("Error: CLIENT_SECRET_JSON is not valid base64.")
        return None, None
    except json.JSONDecodeError:
        logging.error("Error: CLIENT_SECRET_JSON is not valid JSON.")
        return None, None

    try:
        token_info = json.loads(base64.b64decode(os.environ["TOKEN_JSON"]))
    except KeyError:
        logging.error("Error: TOKEN_JSON is missing.")
        return None, None
    except base64.binascii.Error:
        logging.error("Error: TOKEN_JSON is not valid base64.")
        return None, None
    except json.JSONDecodeError:
        logging.error("Error: TOKEN_JSON is not valid JSON.")
        return None, None

    try:
        playlist_id = os.environ["PLAYLIST_ID"]
    except KeyError:
        logging.error("Error: PLAYLIST_ID environment variable is missing.")
        return None, None

    creds = Credentials.from_authorized_user_info(token_info)
    youtube = build("youtube", "v3", credentials=creds)
    return youtube, playlist_id

def get_existing_playlist_video_ids(youtube_service, playlist_id):
    existing_yt_ids = set()
    next_page_token = None
    while True:
        pl_request = youtube_service.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        pl_response = pl_request.execute()
        for item in pl_response.get('items', []):
            existing_yt_ids.add(item['contentDetails']['videoId'].lower())
        next_page_token = pl_response.get('nextPageToken')
        if not next_page_token:
            break
    logging.info(f"Found {len(existing_yt_ids)} videos already in the playlist.")
    return existing_yt_ids

def prune_playlist(youtube, playlist_id, max_items=500):
    logging.info(f"🔍 Checking playlist size for pruning (limit: {max_items})")
    items_to_delete = []
    nextPageToken = None
    while True:
        response = youtube.playlistItems().list(
            part="id,snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=nextPageToken
        ).execute()
        items = response.get("items", [])
        items_to_delete.extend(items)
        nextPageToken = response.get("nextPageToken")
        if not nextPageToken:
            break
    total = len(items_to_delete)
    logging.info(f"📦 Playlist currently has {total} items")
    if total <= max_items:
        logging.info("✅ No pruning needed.")
        return
    items_to_delete.sort(key=lambda x: x["snippet"]["publishedAt"])
    to_remove = items_to_delete[:total - max_items]
    logging.info(f"🗑 Removing {len(to_remove)} oldest items...")
    for item in to_remove:
        try:
            youtube.playlistItems().delete(id=item["id"]).execute()
            logging.info(f"❌ Removed: {item['snippet']['title']}")
        except Exception as e:
            logging.warning(f"⚠️ Failed to remove item: {e}")

def add_videos_to_playlist(youtube_service, playlist_id, video_ids_to_add, existing_video_ids):
    added_count = 0
    for vid in video_ids_to_add:
        if vid.lower() in existing_video_ids:
            logging.info(f"ℹ️ Video {vid} already in playlist. Skipping.")
            continue
        try:
            youtube_service.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": vid
                        }
                    }
                }
            ).execute()
            logging.info(f"✅ Added: {vid}")
            added_count += 1
        except Exception as e:
            logging.error(f"⚠️ Failed to add {vid}: {e}")
    logging.info(f"Successfully added {added_count} new video(s) to the playlist.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    reddit_client = get_reddit_client()
    subreddit_name_env = os.environ.get("SUBREDDIT_NAME", "listentothis")
    try:
        post_limit_env = int(os.environ.get("POST_LIMIT", "20"))
    except ValueError:
        logging.warning("⚠️ Warning: Invalid POST_LIMIT. Defaulting to 20.")
        post_limit_env = 20
    yt_ids_from_reddit = fetch_youtube_ids_from_subreddit(reddit_client, subreddit_name_env, post_limit_env)
    if not yt_ids_from_reddit:
        logging.info("No YouTube videos found from Reddit. Exiting.")
        exit(0)
    youtube_service, playlist_id_env = get_youtube_service()
    if not youtube_service:
        logging.error("Failed to initialize YouTube service. Exiting.")
        exit(1)
    existing_playlist_ids = get_existing_playlist_video_ids(youtube_service, playlist_id_env) or set()
    prune_playlist(youtube_service, playlist_id_env, max_items=500)
    add_videos_to_playlist(youtube_service, playlist_id_env, yt_ids_from_reddit, existing_playlist_ids)
    
