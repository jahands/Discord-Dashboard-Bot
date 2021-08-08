import os
import requests
import json

import discord
import pytz
import datetime
import time

from discord.ext import tasks
from dblog import dblog
from replit import db
from mcstatus import MinecraftServer
from logzero import logger

from lib import get_server_formatted


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dblog('Starting bot!')
        self.followers_channel_id = 873251385850880111

        # start the task to run in the background
        self.update_followers.start()
        self.update_mc_players.start()

    def get_data(self):
        headers = {
            'user-agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.67'
        }
        url = 'https://mlmcounts.herokuapp.com/twitter/api/?name=replit'
        response = requests.get(url, headers=headers)
        if (not response.ok):
            raise Exception('Could not get account details')
        data = json.loads(response.text)
        return data

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    @tasks.loop(minutes=30)
    async def update_followers(self):
        try:
            channel = self.get_channel(self.followers_channel_id)
            data = self.get_data()
            followers_count = data['followers_count']
            new_name = 'Replit Followers: {0}'.format(
                '{:,}'.format(followers_count))
            print(new_name)
            dblog(new_name)
            if (followers_count != db.get('x:followers_count', -1)):
                # Only update data if count is changed
                await channel.edit(name=new_name)
                # Log to logging channel
                log_channel = self.get_channel(873253483430686810)
                now = datetime.datetime.now(pytz.timezone('US/Central'))
                await log_channel.send(f'{new_name} @ {now}')
                db.set('x:followers_count', followers_count)

        except Exception as e:
            logger.exception(e)
            dblog(e)

    @update_followers.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in

    @tasks.loop(seconds=15)
    async def update_mc_players(self):
        channel_name = 'x:minecraft:channel_name'
        try:
            server = MinecraftServer.lookup('{0}:25565'.format(
                os.environ['MC_SERVER']))
            status = server.status()
            online = status.players.online
            new_name = 'minecraft-{0}'.format(online)
            channel = self.get_channel(int(os.environ['MC_CHANNEL_ID']))
            if (new_name != channel.name):
                logger.info('updating #minecraft channel name')
                await channel.edit(name=new_name)
                logger.info(new_name)
                dblog(new_name)

            # Update chat message with player list
            server_1 = get_server_formatted(os.environ['MC_SERVER'],
                                            'All the Mods 6')
            # example of new_message:
            # 1 Connected Player on mc.example.com:
            # - Dinnerbone

            user_list_key = 'x:minecraft:connected_players'
            status_channel_id = 873735300566880267  #status
            status_channel_message_id = 873971100793569280
            minecraft_channel_message_id = 873728975862661232
            server_1_fmt = server_1['fmt']
            if (server_1_fmt != db.get(user_list_key, '')):
                logger.info(server_1_fmt)
                message = await channel.fetch_message(
                    minecraft_channel_message_id)
                await message.edit(content=server_1_fmt)
                db.set(user_list_key, server_1_fmt)

            # Status channel
            server_2 = get_server_formatted(os.environ['MC_SERVER_2'],
                                            'The Royal Galaxy')
            servers = [server_1, server_2]
            new_message = '\n\n'.join([s['fmt'] for s in servers])
            status_key = 'x:minecraft:status_channel_message'
            channel = self.get_channel(status_channel_id)
            # Update message with players
            if (new_message != db.get(status_key, '')):
                message = await channel.fetch_message(status_channel_message_id
                                                      )
                await message.edit(content=f'**GAMES:**\n{new_message}')
                db.set(status_key, new_message)

            # count players and update status channel with count
            total_players = sum([s['player_count'] for s in servers])
            new_channel_name = f'status-{total_players}'
            if (new_channel_name != channel.name):
                logger.info('Updating #status channel name')
                await channel.edit(name=new_channel_name)

        except Exception as e:
            if (e.__str__() == "Server did not respond with any information!"):
                logger.warning(
                    "Server did not respond with any information, better luck next time!"
                )
                dblog(e)
            else:
                logger.exception(e)
                dblog(e)

    @update_mc_players.before_loop
    async def before_mc_players(self):
        await self.wait_until_ready()  # wait until the bot logs in


client = MyClient()

client.run(os.environ['BOT_TOKEN'])
