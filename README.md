
## Requirements

### Software
- Python 3.10 or higher  
- Redis (local or remote)  
- Firefox  
- Geckodriver (must match your Firefox version)  
- FFmpeg  
- Discord server with permission to add bots

### Python Packages
Install dependencies:
```bash
pip install discord.py redis selenium google-auth google-auth-oauthlib google-api-python-client psutil pywin32
Setup
1. Redis
Start Redis locally:

bash
Copy code
redis-server
If Redis is hosted remotely, edit these variables in head_bot.py and ss_bot.py:

python
Copy code
REDIS_HOST = "localhost"
REDIS_PORT = 6379
2. Create Discord Bots
You need one master bot (the “head”) and one or more slave bots (recorders).

Go to https://discord.com/developers/applications

Create new bots:
HeadBot
RecorderBot1, RecorderBot2, etc.
Under Bot → Token, copy each token.

In head_bot.py, set your token and server ID:

python
Copy code
TOKEN = "YOUR_HEAD_BOT_TOKEN". The bot token can be found on discord.com/developers/application
SERVER_ID = "YOUR_SERVER_ID"
Invite all bots to your Discord server with Administrator permissions.

3. Firefox Profiles for Recording Bots
Each ss_bot.py instance uses a unique Firefox profile logged into a Discord bot account.

Steps:

Open Firefox and go to about:profiles
You need to create a new profile for each bot, this is the only way to not have to keep on logging in each time the browser gets closed.
Click “Create a New Profile”

Log into the bot’s Discord account

Note the profile path (for example:
C:\Users\<you>\AppData\Roaming\Mozilla\Firefox\Profiles\abc123.default-release)

Update the profile_path in ss_bot.py:

python
Copy code
profile_path = r"firefox_profiles\abc123.default-release"
4. Get Bot ID from Firefox
Run:

bash
Copy code
python get_bot_id.py
This reads the bot’s Discord ID from the Firefox profile and prints it, for example:

yaml
Copy code
Found bot ID: 1281044001104859270
5. Start the Master Bot
Run:

bash
Copy code
python head_bot.py
Expected output:

csharp
Copy code
logged in as HeadBot#1234
[MASTER] Waiting for bots...
6. Set Up Roles and Channels in Discord
In your Discord server, use the following text commands:

Command	Description
!init_category <category>	Register all voice channels in a category
!init_channel <voice_channel>	Add a single voice channel
!set_waiting_channel <voice_channel>	Set where idle bots wait
!set_human_role <role>	Define which role represents users who can stream
!init_bot @Bot <bot_role>	Register a recording bot

Example:

diff
Copy code
!init_category StreamRooms
!set_waiting_channel WaitingRoom
!set_human_role Streamers
!init_bot @RecorderBot @BotRole
7. Run Recording Bots
Each ss_bot.py instance should run in its own terminal:

bash
Copy code
python ss_bot.py
When it connects successfully, you’ll see:

csharp
Copy code
[1281044001104859270] Listening for commands...
8. Automatic Recording
When a user with the designated human role starts screen sharing:

The head bot detects the stream.

It assigns a free recording bot.

The recording bot joins the same voice channel.

The bot clicks “Watch Stream.”

FFmpeg begins recording.

Recordings are saved to:

php-template
Copy code
recordings/<BOT_ID>/<timestamp>_stream.mp4
