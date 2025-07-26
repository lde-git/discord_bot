# Discord Sound & Utility Bot

A custom Discord bot built with `discord.py` that provides some utility commands, primarily focused on playing sounds in voice channels and making random choices.

## Features

- **`!choose <option1>, <option2>, ...`**: Randomly picks one option from a comma-separated list.
- **`!heart` / `!broken_heart` / `💔`**: A command to express "pity". It randomly selects a user from a predefined list, joins the command author's voice channel, and plays a corresponding name sound.
  - Using the `💔` alias will play an additional random sound after the first one.
  - *Note: The text message functionality for this command is currently commented out in `bat.py`.*
- **`!hot_face` / `🥵`**: Joins the user's voice channel and plays a specific sound (`bust.mp3`).

## Setup and Installation

Follow these steps to get the bot running on your own server.

### 1. Prerequisites

- Python 3.8 or newer
- FFmpeg (must be installed and available in your system's PATH for voice functionality)

### 2. Clone the Repository

```bash
git clone <your-repository-url>
cd discord_wheel_bot
```

### 3. Create a Virtual Environment

```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate
```

### 4. Install Dependencies

Install the required Python libraries from `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 5. Configure the Bot

Create a file named `.env` in the root of the project directory. This file will hold your secret bot token.

```
DISCORD_TOKEN=YOUR_BOT_TOKEN_HERE
```

### 6. Add Sound Files

### 7. Run the Bot

```bash
python bat.py
```

## Customization

You can easily customize the bot by editing `bat.py`:
- **`!heart` command names**: Modify the `names_to_pity` list to change the users the command can select.
- **`!heart` command messages**: The `arena_pity_texts` list is currently commented out. You can uncomment it and the `await ctx.send(final_message)` line in the `heart_command` to enable sending text messages.