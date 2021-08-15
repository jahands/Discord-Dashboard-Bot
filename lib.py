from typing import Optional

from logzero import logger
from mcstatus import MinecraftServer


def get_server_formatted(ip: str, title: Optional[str]):
    try:
        online = 0 # So in case this lookup fails
        server = MinecraftServer.lookup('{0}:25565'.format(ip))
        status = server.status()
        online = status.players.online
        usersConnected = [
            user['name'] for user in status.raw['players']['sample']
        ] if 'sample' in status.raw['players'] else []
        usersConnected.sort()
        new_message = "{0}{1} Connected Player{2} on `{3}`{4}{5}".format(
            f'- **{title}:**\n' if title is not None else '',
            online,  # Count of users online
            '' if online == 1 else 's',  # Formatting
            ip,  # IP to server
            ':\n' if len(usersConnected) > 0 else '',  # Formatting
            '\n'.join([f'- {u}' for u in usersConnected]))  # Userlist
    except Exception as e:
        logger.exception(e)
        new_message = '{0} Connection Error'.format(
            f'- **{title}:**\n' if title is not None else '')

    to_return = {'fmt': new_message, 'player_count': online}
    return to_return

def get_royal_server_formatted(ip: str, title: Optional[str]):
    try:
        online = 0 # So in case this lookup fails
        server = MinecraftServer.lookup('{0}:25565'.format(ip))
        status = server.status()
        online = status.players.online
        usersConnected = [
            user['name'] for user in status.raw['players']['sample']
        ] if 'sample' in status.raw['players'] else []
        usersConnected.sort()
        new_message = "{0}{1} Connected Player{2} (out of {3}) on `{4}`{5}{6}".format(
            f'- **{title}:**\n' if title is not None else '',
            online,  # Count of users online
            '' if online == 1 else 's',  # Formatting
            status.players.max, # max players
            ip,  # IP to server
            ':\n' if len(usersConnected) > 0 else '',  # Formatting
            '\n'.join([f'- {u}' for u in usersConnected]))  # Userlist
    except Exception as e:
        logger.exception(e)
        new_message = '{0} Connection Error'.format(
            f'- **{title}:**\n' if title is not None else '')

    to_return = {'fmt': new_message, 'player_count': online}
    return to_return