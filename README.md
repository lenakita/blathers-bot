# Blathers-Bot
This is Blathers-Bot, the one stop wiki scraping shop for dynamically accessing information on animal crossing villagers from the comfort of your discord channel! Please read below for details:

### Features
This discord bot provides an interactive interface to the Animal Crossing Wiki, giving details on any villager! The commands it currently has are:

- !ac_stats villager_name statistic: returns that statistic about the villager, such as personality or species
- !ac_image villager_name: gets the profile image of the villager and displays it in the channel

### Dependencies
- Python 3.6 or above
- Python modules listed in requirements.txt

### How to run
Navigate to the directory in command line and type:

- Windows: python discord_bot.py
- Linux: python3 discord_bot.py

If you want to run this bot yourself using this method, you will need to generate a keys.txt file in the format:
token: insert bot token from discord developer portal/application/bot page
id: insert the ID from the discord developer portal/application page
And place it in the root directory of this project along with the .py script

Please follow the instructions available [here](https://discordpy.readthedocs.io/en/latest/discord.html) on how to create a bot.