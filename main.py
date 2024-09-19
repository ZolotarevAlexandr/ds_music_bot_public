import logging

import dotenv
dotenv.load_dotenv()

from global_variables import client, TOKEN

logging.basicConfig(
    filename='logs.log',
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    level=logging.WARNING
)

client.load_extension("music_cog")
print('Bot is started')
client.run(TOKEN)
