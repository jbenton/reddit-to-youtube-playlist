import os
import json
import base64
import re
import praw
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- Reddit setup via praw ---
reddit = praw.Reddit(
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    username=os.environ["REDDIT_USERNAME"],
    password=os.environ["REDDIT_PASSWORD"],
    user_agent=os.environ["REDDIT_USER_AGENT"]
)

subreddit = reddit.subreddit("listentothis")
posts = subreddit.hot(limit=20)  # or .top("day"), .new(limit=20), etc.

yt_ids = set()
for post in posts:
    url = post.url
    print(f"Checking: {post.title} → {url}")
    match = re.search(r"(?:youtu\.be/|youtube\.com/watch\?v=)([\w-]{11})", url)
    if match:
        vid = match.group(1)
        yt_ids.add(vid)

print(f"✅ Found {len(yt_ids)} YouTube video(s)")

# --- YouTube setup ---
client_secret = json.loads(base64.b64decode(os.environ["CLIENT_SECRET_JSON"]))
token_info = json.loads(base64.b64decode(os.environ["TOKEN_JSON"]))
playlist_id = os.environ["PLAYLIST_ID"]

creds = Credentials.from_authorized_user_info(token_info)
youtube = build("youtube", "v3", credentials=creds)

# --- Push to playlist ---
for vid in yt_ids:
    try:
        youtube.playlistItems().insert(
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
        print(f"✅ Added: {vid}")
    except Exception as e:
        print(f"⚠️ Failed to add {vid}: {e}")
