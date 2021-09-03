import discord
from deta import Deta
from config import settings

class DiscordClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}')

    async def on_voice_state_update(self, member, before, after):
        #print('---------------------------------------------------')
        #print(f'Before: {before}\nAfter: {after}')
        
        if after.channel is None:
            deta = Deta(settings.DETA_PROJECT_KEY)
            db = deta.Base('members')
            print(f'{member.nick} left the voice channel!')
            user = next(db.fetch({"nick": member.nick}))[0]
            db.delete(user['key'])
        elif before.channel == after.channel or before.channel is not None:
            print(f'{member.nick} state changed')
        else:
            deta = Deta(settings.DETA_PROJECT_KEY)
            db = deta.Base('members')
            print(f'{member.nick} joined {after.channel} avatar={str(member.avatar_url)}')
            db.insert({'nick': member.nick, 'avatar': str(member.avatar_url)})
        
# total_members = 0
#         for guild in self.guilds:
#             for channel in guild.channels:
#                 if type(channel) is discord.channel.VoiceChannel:
#                     members = channel.members
#                     if len(members) > 0:
#                         print(f'{channel}: {len(members)}')
#                     for member in members:
#                         print(f'{member.nick} avatar={member.avatar_url}')
#                     total_members += len(channel.members)
#         print(f'\nTotal members online: {total_members}')