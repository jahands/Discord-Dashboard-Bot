import os
import requests
import json

import discord
import pytz
import datetime

from discord.ext import tasks
from dblog import dblog
from replit import db
from mcstatus import MinecraftServer
from logzero import logger

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

    @tasks.loop(seconds=30)
    async def update_mc_players(self):
        try:
            key = 'x:minecraft:playing_count'
            server = MinecraftServer.lookup('{0}:25565'.format(
                os.environ['MC_SERVER']))
            status = server.status()
            online = status.players.online
            if (online != db.get(key, -1)):
                new_name = 'minecraft-{0}'.format(online)
                channel = self.get_channel(int(os.environ['MC_CHANNEL_ID']))
                await channel.edit(name=new_name)
                db.set(key, online)
                logger.info(new_name)
                dblog(new_name)

        except Exception as e:
            logger.exception(e)
            dblog(e)

    @update_mc_players.before_loop
    async def before_mc_players(self):
        await self.wait_until_ready()  # wait until the bot logs in


client = MyClient()

client.run(os.environ['BOT_TOKEN'])
