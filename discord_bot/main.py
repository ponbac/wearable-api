import os
import dotenv

from client import DiscordClient


dotenv.load_dotenv()
token = os.getenv('DISCORD_TOKEN')
print(f'Token: {token}')

client = DiscordClient()
client.run(token)
