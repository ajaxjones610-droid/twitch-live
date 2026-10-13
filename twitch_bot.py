import os
import requests

CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# List of streamers to track based on their Twitch profile URLs
STREAMERS = [
    "bajiru_en",
    "novaaokami",
    "gmhikaru",
    "ludwig",
    "timthetatman",
    "gothamchess",
    "vei",
    "sodapoppin",
]

# File to remember who is currently live between GitHub Actions runs
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

  # Twitch API allows checking multiple usernames at once using query parameters
  params = [("user_login", s) for s in STREAMERS]

  response = requests.get(
      "https://api.twitch.tv/helix/streams", headers=headers, params=params
  )
  if response.status_code != 200:
    print(f"Failed to fetch streams: {response.text}")
    return

  # Grab anyone currently live from the API response
  live_data = response.json().get("data", [])
  current_live = {stream["user_name"].lower() for stream in live_data}

  # Load previous live state from file
  previously_live = set()
  if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
      previously_live = set(
          line.strip().lower() for line in f if line.strip()
      )

  # Find streamers who just went live (they are live now, but weren't last time)
  newly_live = current_live - previously_live

  for stream in live_data:
    name = stream["user_name"]
    if name.lower() in newly_live:
      title = stream.get("title", "")
      game = stream.get("game_name", "")
      payload = {
          "content": (
              f"🔴 **{name}** is now live playing **{game}**!\nTitle: {title}\n"
              f"🔗 https://twitch.tv/{name}"
          )
      }
      requests.post(WEBHOOK_URL, json=payload)
      print(f"Notification sent for {name}")

  # Save the current live state back to the file for the next 5-minute check
  with open(STATE_FILE, "w") as f:
    for name in current_live:
      f.write(f"{name}\n")


if __name__ == "__main__":
  main()
