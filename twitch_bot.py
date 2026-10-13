import os
import requests

CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# List of streamers to track
STREAMERS = [
    "bajiru_en",
    "novaaokami",
    "gmhikaru",
    "ludwig",
    "timthetatman",
    "gothamchess",
    "vei",
    "sodapoppin",
    "summit1g",
]

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

  live_data = response.json().get("data", [])
  current_live = {stream["user_name"].lower() for stream in live_data}

  # Load previous live state
  previously_live = set()
  if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
      previously_live = set(
          line.strip().lower() for line in f if line.strip()
      )

  newly_live = current_live - previously_live

  for stream in live_data:
    name = stream["user_name"]
    if name.lower() in newly_live:
      title = stream.get("title", "No Title")
      game = stream.get("game_name", "Unknown Category")
      stream_url = f"https://twitch.tv/{name}"

      thumbnail_template = stream.get("thumbnail_url", "")
      image_url = thumbnail_template.replace("{width}", "1280").replace(
          "{height}", "720"
      )

      # Discord Embed Payload
      payload = {
          "embeds": [{
              "title": title,
              "url": stream_url,
              "color": 9520895,  # Twitch Purple (Hex #9146FF)
              "author": {"name": f"🔴 {name} is now LIVE!"},
              "fields": [{
                  "name": "Playing",
                  "value": game,
                  "inline": True,
              }],
              "image": {"url": image_url},
          }]
      }

      requests.post(WEBHOOK_URL, json=payload)
      print(f"Notification sent with preview image for {name}")

  # Save current live state
  with open(STATE_FILE, "w") as f:
    for name in current_live:
      f.write(f"{name}\n")


if __name__ == "__main__":
  main()
