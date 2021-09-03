import discord
from deta import Deta
from config import settings

class DiscordClient(discord.Client):
    deta = Deta(settings.DETA_PROJECT_KEY)
    db = deta.Base('members')

    async def on_ready(self):
        print(f'Logged in as {self.user}')

    async def on_voice_state_update(self, member, before, after):
        #print('---------------------------------------------------')
        #print(f'Before: {before}\nAfter: {after}')
        
        if after.channel is None:
            print(f'{member.nick} left the voice channel!')
            user = next(DiscordClient.db.fetch({"nick": member.nick}))[0]
            DiscordClient.db.delete(user['key'])
        elif before.channel == after.channel or before.channel is not None:
            print(f'{member.nick} state changed')
        else:
            print(f'{member.nick} joined {after.channel} avatar={str(member.avatar_url)}')
            DiscordClient.db.insert({'nick': member.nick, 'avatar': str(member.avatar_url)})
        
