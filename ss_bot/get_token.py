from google_auth_oauthlib.flow import InstalledAppFlow

# Scope for managing and streaming YouTube broadcasts
SCOPES = ["https://www.googleapis.com/auth/youtube"]

flow = InstalledAppFlow.from_client_secrets_file(
    "ss_bot\client_secret_852886386845-lnsat0uit1ei6fb5n0rv5v4po8uhtsta.apps.googleusercontent.com.json",  # your downloaded file
    SCOPES
)
creds = flow.run_local_server(port=0)

# Save credentials to file
with open("token.json", "w") as token:
    token.write(creds.to_json())

print("✅ Token saved to token.json")
