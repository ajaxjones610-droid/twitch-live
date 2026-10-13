import os
import requests

CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Add the Twitch usernames you want to track here
STREAMERS = ["streamer_one", "streamer_two"]

# A simple file to remember who is currently live between runs
STATE_FILE = "live_state.txt"


def get_app_token():
  res = requests.post(
      "https://id.twitch.tv/oauth2/token",
      data={
          "client_id": CLIENT_ID,
          "client_secret": CLIENT_SECRET,
          "grant_type": "client_credentials",
      },
  ).json()
  return res.get("access_token")


def main():
  if not CLIENT_ID or not CLIENT_SECRET or not WEBHOOK_URL:
    print("Error: Missing environment variables.")
    return

  token = get_app_token()
  headers = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {token}"}
  params = [("user_login", s) for s in STREAMERS]

  response = requests.get(
      "https://api.twitch.tv/helix/streams", headers=headers, params=params
  )
  if response.status_code != 200:
    print(f"Failed to fetch streams: {response.text}")
    return

  current_live = {
      stream["user_name"] for stream in response.json().get("data", [])
  }

  # Load previous live state
  previously_live = set()
  if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
      previously_live = set(line.strip() for line in f if line.strip())

  # Find streamers who just went live
  newly_live = current_live - previously_live
  for stream in response.json().get("data", []):
    name = stream["user_name"]
    if name in newly_live:
      title = stream.get("title", "")
      game = stream.get("game_name", "")
      requests.post(
          WEBHOOK_URL,
          json={
              "content": (
                  f"🔴 **{name}** is now live playing **{game}**!\nTitle:"
                  f" {title}"
              )
          },
      )
      print(f"Notification sent for {name}")

  # Save current state for the next run
  with open(STATE_FILE, "w") as f:
    for name in current_live:
      f.write(f"{name}\n")


if __name__ == "__main__":
  main()
