# Reddit to YouTube Playlist Importer

This script fetches YouTube videos shared in a specified subreddit and adds them to a YouTube playlist. It checks for duplicates before adding new videos.

## Features

*   Fetches top posts from a configurable subreddit.
*   Extracts YouTube video IDs from post URLs.
*   Connects to the YouTube API to manage a playlist.
*   Checks for existing videos in the playlist to avoid duplicates.
*   Configurable via environment variables.
*   Uses logging for informative output.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url> # Replace <repository_url> with the actual URL
    cd <repository_directory>   # Replace <repository_directory> with the folder name
    ```

2.  **Install dependencies:**
    Ensure you have Python 3.x installed. Then, install the required Python packages using `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment Variables:**
    The script requires several environment variables to be set for it to function correctly. These include API credentials for both Reddit and YouTube, and settings for script behavior. See the "Configuration" section below for details.

## Configuration

The script uses the following environment variables for configuration:

### Reddit API Credentials (Mandatory)
These are required to access the Reddit API. You'll need to create a Reddit application at [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps).
*   `REDDIT_CLIENT_ID`: Your Reddit application client ID.
*   `REDDIT_CLIENT_SECRET`: Your Reddit application client secret.
*   `REDDIT_USERNAME`: Your Reddit username (the account that owns the app).
*   `REDDIT_PASSWORD`: Your Reddit password.
*   `REDDIT_USER_AGENT`: A unique user agent string for your Reddit application (e.g., "RedditToYouTubePlaylist/1.0 by u/YourUsername").

### YouTube API Credentials (Mandatory)
These are required to access the YouTube Data API. You'll need a Google Cloud Platform project with the YouTube Data API v3 enabled.
*   `CLIENT_SECRET_JSON`: Your Google Cloud project's client secret JSON content, **base64 encoded**. You can download this JSON file from the "Credentials" page of your GCP project. After downloading, encode its entire content to base64.
*   `TOKEN_JSON`: The OAuth 2.0 token JSON for YouTube API access, **base64 encoded**. This token is typically generated the first time you authorize the application to access your YouTube account. The script (if run interactively for the first time with appropriate OAuth setup) would guide you through this, or you might need a separate script/process to generate this if you followed a guide like the one for `google-auth-oauthlib`. Ensure the generated JSON content is base64 encoded.
*   `PLAYLIST_ID`: The ID of the YouTube playlist where videos will be added. You can find this in the URL of your playlist (e.g., `PLxxxxxxxxxxxxxxxxxxxx`).

### Script Behavior (Optional)
*   `SUBREDDIT_NAME`: The name of the subreddit to fetch posts from (e.g., "listentothis", "videos").
    *   Defaults to: `"listentothis"` if not set.
*   `POST_LIMIT`: The number of posts to fetch from the subreddit.
    *   Defaults to: `20` if not set. Must be a valid integer.

## Running the Script

Once the setup is complete and environment variables are configured, you can run the script:

```bash
python add_from_reddit.py
```

The script will log its actions to the console, including posts checked, videos found, and videos added to the playlist.

## How to Base64 Encode Credentials

For `CLIENT_SECRET_JSON` and `TOKEN_JSON`, you need to provide their content as base64 encoded strings.

**Example (Linux/macOS):**

1.  If your client secret is in a file named `client_secret.json`:
    ```bash
    export CLIENT_SECRET_JSON=$(base64 -w 0 client_secret.json)
    ```
2.  If your token is in a file named `token.json`:
    ```bash
    export TOKEN_JSON=$(base64 -w 0 token.json)
    ```

**Example (Python):**
You can use a Python interpreter to get the base64 string:
```python
import base64

# For CLIENT_SECRET_JSON
with open('client_secret.json', 'rb') as f:
    client_secret_content = f.read()
encoded_client_secret = base64.b64encode(client_secret_content).decode('utf-8')
print(f"CLIENT_SECRET_JSON='{encoded_client_secret}'")

# For TOKEN_JSON
with open('token.json', 'rb') as f:
    token_content = f.read()
encoded_token = base64.b64encode(token_content).decode('utf-8')
print(f"TOKEN_JSON='{encoded_token}'")
```
Ensure no newlines are introduced if copying from terminal output. The `-w 0` flag in the `base64` command for Linux/macOS helps prevent this.
