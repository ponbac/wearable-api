import discord

class DiscordClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}')

    async def on_voice_state_update(self, member, before, after):
        print('---------------------------------------------------')
        print(f'User: {member} changed!\n')

        total_members = 0
        for guild in self.guilds:
            for channel in guild.channels:
                if type(channel) is discord.channel.VoiceChannel:
                    members = channel.members
                    if len(members) > 0:
                        print(f'{channel}: {len(members)}')
                    for member in members:
                        print(f'{member.nick} avatar={member.avatar_url}')
                    total_members += len(channel.members)
        print(f'\nTotal members online: {total_members}')
