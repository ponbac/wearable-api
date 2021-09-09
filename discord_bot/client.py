import discord
from deta import Deta
from config import settings


class DiscordClient(discord.Client):
    def create_db_connection(self):
        deta = Deta(settings.DETA_PROJECT_KEY)
        return deta.Base('members')

    async def on_ready(self):
        print(f'Logged in as {self.user}')

    async def on_voice_state_update(self, member, before, after):
        #print('---------------------------------------------------')
        #print(f'Member:  {member}\nBefore: {before}\nAfter: {after}')

        if after.channel is None:
            db = self.create_db_connection()
            print(f'{member.nick} left the voice channel!')
            db.delete(str(member.id))
        else:
            db = self.create_db_connection()
            if member.nick is None:
                print('NO NICK!')
                member.nick = member.name.split('#')[0]
                print(member.nick)
            print(
                f'{member.nick} updated, in channel {after.channel} avatar={str(member.avatar_url)}')
            db_object = {'nick': member.nick, 'avatar': str(
                member.avatar_url_as(size=256)), 'channelId': str(after.channel.id), 'channelName': str(after.channel.name), 'isStreaming': bool(after.self_stream)}
            #print(db_object)
            db.put(db_object, str(member.id))

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
