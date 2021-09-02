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
        total_members = 0
        for guild in client.guilds:
            for channel in guild.channels:
                if type(channel) is discord.channel.VoiceChannel:
                    members = channel.members
                    print(f'{channel}: {len(members)}')
                    for member in members:
                        print(f'{member.nick} avatar={member.avatar_url}')
                    total_members += len(channel.members)
        await message.channel.send(f'Hello to the {total_members} of you!')

dotenv.load_dotenv()
token = os.getenv('DISCORD_TOKEN')
print(f'Token: {token}')
client.run(token)