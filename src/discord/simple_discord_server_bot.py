import discord
import asyncio
import json

TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
FORUM_CHANNEL_ID = 0
ACCEPTED_CLIENTS = ['127.0.0.1'] # add your ip here 
PORT = 5000

intents = discord.Intents.default()
bot = discord.Client(intents=intents)

clients = {}

class Client:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.ip = writer.get_extra_info('peername')[0]
        self.port = writer.get_extra_info('peername')[1]
        self.nickname = f"{self.ip}:{self.port}"

    async def get_message(self):
        return (await self.reader.read()).decode('utf8')

async def handle_client(reader, writer):
    ip = writer.get_extra_info('peername')[0]
    if ip not in ACCEPTED_CLIENTS:
        writer.write('Unauthorized Connection'.encode('utf8'))
        await writer.drain()
        writer.close()
        return

    client = Client(reader, writer)
    task = asyncio.create_task(client_listener(client))
    clients[task] = client
    task.add_done_callback(lambda t: disconnect_client(t, client))

def disconnect_client(task, client):
    if client in clients.values():
        client.writer.write('quit'.encode('utf8'))
        client.writer.close()
        del clients[task]

async def client_listener(client):
    while True:
        message = await client.get_message()
        if not message:
            break
        data = json.loads(message)
        if data.get("type") == "URL":
            broadcast_to_others(message.encode('utf8'), client)
        elif data.get("type") == "DISCORD_FORUM":
            await post_to_discord(data)

def broadcast_to_others(message, sender):
    for other_client in clients.values():
        if other_client != sender:
            other_client.writer.write(message)

async def post_to_discord(data):
    await bot.wait_until_ready()
    forum = bot.get_channel(FORUM_CHANNEL_ID)
    if not isinstance(forum, discord.ForumChannel):
        print("Forum channel not found or not valid.")
        return

    title = data['title']
    user = data['user']
    runtime = data['runtime']
    memory = data['memory']
    code = data['code']
    time_taken = data['time_taken']
    url_slug = data['url_slug']

    embed = discord.Embed(title=f'Code by {user}', color=0x2ecc71)
    embed.description = f'```py\n{code}```'
    embed.set_footer(text=f'Runtime: {runtime}, Memory: {memory}, Time taken: {time_taken}')

    thread = discord.utils.get(forum.threads, name=title)
    if not thread:
        await forum.create_thread(name=title, content=f'<https://leetcode.com/problems/{url_slug}>', embed=embed)
    else:
        await thread.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    server = await asyncio.start_server(handle_client, '0.0.0.0', PORT)
    print(f'Socket server running on port {PORT}')
    asyncio.create_task(server.serve_forever())

bot.run(TOKEN)
