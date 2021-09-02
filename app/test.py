import discord
import os
import dotenv

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send(f'Hello to the {total_members} of you!')

@client.event
async def on_voice_state_update(member, before, after):
    print('---------------------------------------------------')
    print(f'User: {member} changed!\n')

    total_members = 0
    for guild in client.guilds:
        for channel in guild.channels:
            if type(channel) is discord.channel.VoiceChannel:
                members = channel.members
                if len(members) > 0:
                    print(f'{channel}: {len(members)}')
                for member in members:
                    print(f'{member.nick} avatar={member.avatar_url}')
                total_members += len(channel.members)
    print(f'\nTotal members online: {total_members}')
    

dotenv.load_dotenv()
token = os.getenv('DISCORD_TOKEN')
print(f'Token: {token}')
client.run(token)