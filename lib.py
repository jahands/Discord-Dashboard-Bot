import os
from typing import Optional
from mcstatus import MinecraftServer


def get_server_formatted(ip: str, title: Optional[str]):
    server = MinecraftServer.lookup('{0}:25565'.format(ip))
    status = server.status()
    online = status.players.online
    usersConnected = [
        user['name'] for user in status.raw['players']['sample']
    ] if 'sample' in status.raw['players'] else []
    usersConnected.sort()
    new_message = "{0}{1} Connected Player{2} on `{3}`{4}\n{5}".format(
        f'- **{title}:**\n' if title is not None else '',
        online,  # Count of users online
        '' if online == 1 else 's',  # Formatting
        ip,  # IP to server
        ':' if len(usersConnected) > 0 else '',  # Formatting
        '\n'.join([f'- {u}' for u in usersConnected]))  # Userlist
    return new_message
