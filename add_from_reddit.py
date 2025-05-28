import os, json, base64, re, requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Decode and load credentials
client_secret = json.loads(base64.b64decode(os.environ['CLIENT_SECRET_JSON']))
token_info = json.loads(base64.b64decode(os.environ['TOKEN_JSON']))
playlist_id = os.environ['PLAYLIST_ID']

# Authenticate
creds = Credentials.from_authorized_user_info(token_info)
youtube = build("youtube", "v3", credentials=creds)

# Fetch top Reddit posts
headers = {
    "User-Agent": "reddit-to-yt-script by u/jbentonbot",  # use a real-looking Reddit UA
}

res = requests.get("https://www.reddit.com/r/listentothis/hot.json?limit=20", headers=headers)

# Debug: check what we actually got back
print("Reddit status code:", res.status_code)
print("Reddit response (first 200 chars):", res.text[:200])

res.raise_for_status()  # will show clearer error if it failed

posts = res.json()["data"]["children"]

# Extract YouTube video IDs
yt_ids = set()
for post in posts:
    url = post["data"]["url"]
    match = re.search(r"(?:youtu\.be/|youtube\.com/watch\?v=)([\w-]{11})", url)
    if match:
        yt_ids.add(match.group(1))

# Add each video to playlist
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
