import time
import os
import requests
import re

import asyncio
from bs4 import BeautifulSoup
from discord.ext.commands import Bot
from discord.ext import commands
from discord import Game, opus

class BlathersBot(commands.Cog):
    def __init__(self, key_store_path: str = ''):
        if not key_store_path:
            print('Keys not set, returning')
            return
        keys = []
        with open(key_store_path, 'r') as key_file:
            keys = key_file.readlines()
            for idx, key in enumerate(keys):
                keys[idx] = key.split(":")[1].strip()

        self.bot_token = keys[0]
        self.bot_id = keys[1]

        self.wiki_parser = WikiParser()
        # hard coded as do not want to dynamically acquire from wiki every time this command is called
        self.VILLAGER_STATS = [
            'Gender',
            'Personality',
            'Species',
            'Birthday',
            'Initial phrase',
            'Initial clothes',
            'Home request',
            'Skill',
            'Goal',
            'Coffee',
            'Favourite Song',
            'Appearances'
        ]

    def setup_bot(self):
        """
        Initialises the bot and sets its presence message
        """
        try:
            self.bot = commands.Bot(command_prefix='!')
            self.bot.add_cog(self)
        except Exception as err:
            print(f"Exception setting the bot {err}")
        @self.bot.event
        async def on_ready():
            # required the type argument of 1 to make the presence visible
            await self.bot.change_presence(activity=Game(name="with the wiki", type=1))
            print(f"Logged in as\n{self.bot.user.name}\n{self.bot.user.id}\n------------")

    def run(self):
        """
        Uses the bot token provided from the file to run the bot
        """
        self.bot.run(self.bot_token)

    """ 
    Each command method takes the same parameters:

    Keyword arguments:
    ctx -- message information
    args -- extra arguments passed with the message

    Command decorator arguments:
    name -- message contents required to trigger the method, along with bot_prefix
    pass_context -- allows for original message to be passed as a parameter (default True)
    no_pm -- source of message from channel or private message (default True)
    """
    @commands.command(name='ac_stats', pass_context=True, no_pm=True)
    async def get_stats(self, ctx, args=''):
        """
        Write a message !ac_stats <villager_name> <statistic> to get me to say that fact about them!

        Looks at the AC wiki page for a villager and loads the <aside> that stores
        all of their statistics. Sends a message back to the channel it is called from
        depending on what the user requested. In the format:
        !ac_stats <villager_name> <stat>
        """
        await ctx.send('Let me find that for you...')
        message_dict = self.format_split_message(ctx.message.content)
        villager_name = message_dict['args'][0]
        stat = ' '.join(message_dict['args'][1:])
        response = self.wiki_parser.request_wiki_info(stat, villager_name)
        if response:
            # response is set as a list, have to take out the first (and only) element
            await ctx.send(f'The {stat} of {villager_name} is: {response}')
            return
        await ctx.send(f'Sorry I could not find the {stat} of {villager_name} for you.')

    @commands.command(name='ac_image', pass_context=True, no_pm=True)
    async def get_profile_image(self, ctx, args=''):
        """
        Write a message !ac_image <villager_name> to get a villager's profile picture

        Uses the AC wiki page for a villager and copies the url for their profile image
        to send it back to the channel as a message
        """
        message_dict = self.format_split_message(ctx.message.content)
        villager_name = message_dict['args'][0]
        response = self.wiki_parser.request_profile_image(villager_name)
        if response:
            await ctx.send(f'Hey, this seems like a picture of someone I know...\n{response}')
            return
        await ctx.send('Hm, seems like there are not any pictures of this person I can find')

    @commands.command(name='help_characteristics', pass_context=True, no_pm=True)
    async def get_characteristics(self, ctx, args=''):
        """
        Lists all the characteristics of a given character from the set list
        """
        message = '```The available characteristics to choose from are: \n'
        message += '\n'.join([stat for stat in self.VILLAGER_STATS])
        message += '```'
        await ctx.send(message)

    @staticmethod
    def format_split_message(message):
        """
        Takes a message with multiple arguments and divides it into the command and its respective args
        
        Keyword arguments:
        message -- the discord message to split up

        Returns:
        a dictionary containing two keys:
            -- the command to run (!<command_name)
            -- a list of arguments to use with the command
        """
        split_message = message.split(' ')
        for idx, item in enumerate(split_message[1:]):
            split_message[idx+1] = item.capitalize()

        return {
            'command': split_message[0],
            'args': split_message[1:]
        }


class WikiParser():
    def __init__(self):
        self.WIKI_ROOT = 'https://animalcrossing.fandom.com/wiki/'

    def get_data_from_url(self, villager_name, tag):
        """
        Returns the raw HTML from the AC wiki, based on the name of the villager and the tag to find

        Keyword arguments:
        villager_name -- the name of the animal crossing villager to find. Must be available on the fandom wiki
        tag -- the HTML tag to search for

        Returns:
        the HTML content inside the specified tag
        """
        link = self.WIKI_ROOT + villager_name
        print(link)
        scraped_data = requests.get(link).text
        webpage_content = BeautifulSoup(scraped_data)
        return webpage_content.find_all(tag)

    def request_profile_image(self, villager_name):
        """
        Finds the href in the statistics window on the wiki to get the url of the image

        Keyword arguments:
        villager_name -- the name of the villager of which to find the image

        Returns:
        the URL of the villager's profile image
        """
        stat_tags = self.get_data_from_url(villager_name, 'figure')
        located_image = re.findall('href="(.*?)"', str(stat_tags))[0]
        # all images of characters on the wiki have /revision after the file-type of the image
        image_url = located_image.split('/revision')[0]
        return image_url

    def request_wiki_info(self, stat, villager_name):
        """
        Looks inside the <aside> tag that contains the villager stats, splitting based on each heading
        for each statistic i.e. Personality, Species etc. And from within those using regex to get the content
        between the stat tags to see what their value for that statistic is

        Keyword arguments:
        villager_name -- the name of the animal crossing villager to find. Must be available on the fandom wiki
        stat -- the specific statistic to find i.e. Personality, Species
        """
        stat_tags = self.get_data_from_url(villager_name, 'aside')
        # has to be lower to match the case in the HTML
        stat = stat.lower()
        for tag in str(stat_tags).split('<h3'):
            if stat in tag.lower():
                located_text = re.findall('>(.*?)<', tag.lower())
                print(f'Located: {located_text}')
                # should have something in the tag to return, otherwise loop again
                if stat == located_text[0]:
                    for idx, entry in enumerate(located_text[1:]):
                        if entry:
                            # have to offset as starting from 0 again, when the list is looping from 1
                            return located_text[idx+1]

if __name__ == "__main__":
    key_store_path = os.path.join(os.path.dirname(__file__), 'keys.txt')
    bot = BlathersBot(key_store_path)
    bot.setup_bot()
    bot.run()