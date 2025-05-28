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
    """Initializes and returns a PRAW Reddit client instance."""
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=os.environ["REDDIT_USERNAME"],
        password=os.environ["REDDIT_PASSWORD"],
        user_agent=os.environ["REDDIT_USER_AGENT"]
    )
    return reddit

def fetch_youtube_ids_from_subreddit(reddit_client, subreddit_name, post_limit):
    """Fetches posts from a subreddit and extracts YouTube video IDs."""
    subreddit = reddit_client.subreddit(subreddit_name)
    posts = subreddit.hot(limit=post_limit)  # or .top("day"), .new(limit=20), etc.

    yt_ids = set()
    for post in posts:
        url = post.url
        logging.info(f"Checking: {post.title} → {url}")
        match = re.search(r"(?:youtu\.be/|youtube\.com/watch\?v=)([\w-]{11})", url)
        if match:
            vid = match.group(1)
            yt_ids.add(vid)
    
    logging.info(f"✅ Found {len(yt_ids)} YouTube video(s) from r/{subreddit_name}")
    return yt_ids

def get_youtube_service():
    """Initializes and returns the YouTube API service and playlist ID."""
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
    """Fetches and returns a set of video IDs from the given YouTube playlist."""
    existing_yt_ids = set()
    next_page_token = None
    while True:
        pl_request = youtube_service.playlistItems().list(
            part='contentDetails', # we only need videoId
            playlistId=playlist_id,
            maxResults=50, # Max allowed by API
            pageToken=next_page_token
        )
        pl_response = pl_request.execute()

        for item in pl_response.get('items', []):
            existing_yt_ids.add(item['contentDetails']['videoId'])
        
        next_page_token = pl_response.get('nextPageToken')
        if not next_page_token:
            break
    logging.info(f"Found {len(existing_yt_ids)} videos already in the playlist.")
    return existing_yt_ids

def add_videos_to_playlist(youtube_service, playlist_id, video_ids_to_add, existing_video_ids):
    """Adds new videos to the YouTube playlist, skipping duplicates."""
    added_count = 0
    for vid in video_ids_to_add:
        if vid in existing_video_ids:
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
    
    # Reddit part
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

    # YouTube part
    youtube_service, playlist_id_env = get_youtube_service()
    if not youtube_service:
        logging.error("Failed to initialize YouTube service. Exiting.")
        exit(1) # Exit with error code if YouTube service failed

    existing_playlist_ids = get_existing_playlist_video_ids(youtube_service, playlist_id_env)
    
    add_videos_to_playlist(youtube_service, playlist_id_env, yt_ids_from_reddit, existing_playlist_ids)
