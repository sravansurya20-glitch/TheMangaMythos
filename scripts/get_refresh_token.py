import requests
import urllib.parse

print("=== The Manga Mythos - YouTube Authorization Helper ===")
client_id = input("Enter your YOUTUBE_CLIENT_ID: ").strip()
client_secret = input("Enter your YOUTUBE_CLIENT_SECRET: ").strip()

# Generate authorization URL
params = {
    "client_id": client_id,
    "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
    "response_type": "code",
    "scope": "https://www.googleapis.com/auth/youtube.upload",
    "access_type": "offline",
    "prompt": "consent"
}
auth_url = "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)

print("\n1. Copy and paste this URL into your browser:")
print("-" * 80)
print(auth_url)
print("-" * 80)
print("2. Log in with your YouTube Google account.")
print("   IMPORTANT: Select 'The Manga Mythos' brand channel when prompted!")
print("3. Click 'Allow' and copy the authorization code shown on the screen.")

auth_code = input("\nEnter the authorization code: ").strip()

# Exchange for tokens
print("\nExchanging code for refresh token...")
resp = requests.post("https://oauth2.googleapis.com/token", data={
    "code": auth_code,
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
    "grant_type": "authorization_code"
}, timeout=30)

if resp.status_code == 200:
    data = resp.json()
    print("\nSUCCESS!")
    print("-" * 80)
    print(f"YOUTUBE_REFRESH_TOKEN: {data.get('refresh_token')}")
    print("-" * 80)
    print("Copy this refresh token and add it to your GitHub secrets!")
else:
    print(f"\nFailed to exchange code: {resp.status_code}")
    print(resp.text)
