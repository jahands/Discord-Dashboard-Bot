import datetime
import json
import os

import discord
import pytz
import requests
from discord.ext import tasks
from logzero import logger
from mcstatus import MinecraftServer
import redis

from lib import get_server_formatted, get_royal_server_formatted

r = redis.Redis(host=os.environ['REDISHOST'], port=os.environ['REDISPORT'],
                username=os.environ['REDISUSER'], password=os.environ['REDISPASSWORD'], db=0, decode_responses=True)


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # dblog('Starting bot!')
        self.followers_channel_id = 873251385850880111

        # start the task to run in the background
        self.update_followers.start()
        self.update_mc_players.start()

    def can_edit_channel(self, channel_name: str):
        # datetime.datetime.now().timestamp()
        key = f'x:can_edit_channel:{channel_name}'
        last_edit = datetime.datetime.fromtimestamp(r.get(key) or 0)
        now = datetime.datetime.now()
        can_edit = (now - last_edit).total_seconds() > (60 * 5 + 1)
        if (can_edit):
            logger.info(f'We can edit {channel_name}')
            r.set(key, now.timestamp())
        return can_edit

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
            data = self.get_data()
            followers_count = data['followers_count']
            if (followers_count != (r.get('x:followers_count') or -1)):
                new_name = 'Replit Followers: {0}'.format(
                    '{:,}'.format(followers_count))
                print(new_name)
                # dblog(new_name)
                channel = self.get_channel(self.followers_channel_id)
                # Only update data if count is changed
                if (self.can_edit_channel('replit_followers')):
                    await channel.edit(name=new_name)
                    # Log to logging channel
                    log_channel = self.get_channel(873253483430686810)
                    now = datetime.datetime.now(pytz.timezone('US/Central'))
                    await log_channel.send(f'{new_name} @ {now}')
                    r.set('x:followers_count', followers_count)

        except Exception as e:
            logger.exception(e)
            # dblog(e)

    @update_followers.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in

    @tasks.loop(seconds=60)
    async def update_mc_players(self):
        try:
            server = MinecraftServer.lookup('{0}:25565'.format(
                os.environ['MC_SERVER']))
            status = server.status()
            online = status.players.online
            new_name = 'minecraft-{0}'.format(online)
            channel = None
            mc_channel_name_key = 'x:minecraft:channel_name'
            if (new_name != r.get(mc_channel_name_key)):
                if (channel is None):
                    channel = self.get_channel(int(
                        os.environ['MC_CHANNEL_ID']))
                if (self.can_edit_channel('minecraft')):
                    await channel.edit(name=new_name)
                    r.set(mc_channel_name_key, new_name)
                    # dblog(new_name)

            # Update chat message with player list
            server_1 = get_server_formatted(os.environ['MC_SERVER'],
                                            'All the Mods 6')
            # example of new_message:
            # 1 Connected Player on mc.example.com:
            # - Dinnerbone

            user_list_key = 'x:minecraft:connected_players'
            status_channel_name_key = 'x:minecraft:status_channel_name'
            status_key = 'x:minecraft:status_channel_message'
            status_channel_id = 873735300566880267  # status
            status_channel_message_id = 873971100793569280
            minecraft_channel_message_id = 873728975862661232
            server_1_fmt = server_1['fmt']
            # Update #minecraft message
            if (server_1_fmt != r.get(user_list_key)):
                if (channel is None):
                    channel = self.get_channel(int(
                        os.environ['MC_CHANNEL_ID']))
                message = await channel.fetch_message(
                    minecraft_channel_message_id)
                await message.edit(content=server_1_fmt)
                r.set(user_list_key, server_1_fmt)

            # Status channel
            server_2 = get_royal_server_formatted(os.environ['MC_SERVER_2'],
                                                  'The Royal Galaxy')
            # Royal galaxy
            royal_channel_id = 874077971391086612
            royal_message_id = 874079189911879700
            royal_message_key = 'x:minecraft:royal:status_message'
            channel = None
            new_message = server_2['fmt'][2:]
            if (new_message != r.get(royal_message_key)):
                if (channel is None):
                    channel = self.get_channel(royal_channel_id)
                message = await channel.fetch_message(royal_message_id)
                await message.edit(content=f'{new_message}')
                r.set(royal_message_key, new_message)

            # my server
            servers = [server_1, server_2]
            new_message = '\n\n'.join([s['fmt'] for s in servers])
            channel = None
            # Update message with players
            if (new_message != r.get(status_key)):
                if (channel is None):
                    channel = self.get_channel(status_channel_id)
                message = await channel.fetch_message(status_channel_message_id
                                                      )
                await message.edit(content=f'**GAMES:**\n{new_message}')
                r.set(status_key, new_message)

            # count players and update status channel with count
            total_players = sum([s['player_count'] for s in servers])
            new_channel_name = f'status-{total_players}'
            if (new_channel_name != r.get(status_channel_name_key)):
                if (channel is None):
                    channel = self.get_channel(status_channel_id)
                if (self.can_edit_channel('status')):
                    await channel.edit(name=new_channel_name)
                    r.set(status_channel_name_key, new_channel_name)

        except Exception as e:
            if (e.__str__() == "Server did not respond with any information!"):
                logger.warning(
                    "Server did not respond with any information, better luck next time!"
                )
                # dblog(e)
            else:
                logger.exception(e)
                # dblog(e)

    @update_mc_players.before_loop
    async def before_mc_players(self):
        await self.wait_until_ready()  # wait until the bot logs in


client = MyClient()

client.run(os.environ['BOT_TOKEN'])
