import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from commands import setup_commands

# .env 파일에서 환경 변수를 로드
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

if TOKEN is None:
    raise ValueError("DISCORD_TOKEN이 환경 변수로 설정되지 않았습니다.")

# 인텐트를 설정
intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='/', intents=intents)

    async def setup_hook(self):
        # 슬래시 명령어 동기화
        for guild in self.guilds:
            self.tree.copy_global_to(guild=guild)
        await self.tree.sync()

bot = MyBot()

# 명령어 설정
setup_commands(bot)

@bot.event
async def on_ready():
    print(f'{bot.user}로 로그인했습니다!')
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("대기중"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("해당 명령어를 찾을 수 없습니다.", delete_after=10)
    else:
        await ctx.send(f"명령어 실행 중 오류가 발생했습니다: {error}", delete_after=10)

bot.run(TOKEN)