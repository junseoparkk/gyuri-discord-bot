import discord
import os
import random
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('DISCORD_GUILD_ID')  # 서버 ID

if TOKEN is None:
    raise ValueError("DISCORD_TOKEN이 환경 변수로 설정되지 않았습니다.")

if GUILD_ID is None:
    raise ValueError("DISCORD_GUILD_ID가 환경 변수로 설정되지 않았습니다.")

# 인텐트를 설정
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True  # 음성 상태 인텐트 활성화


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='/', intents=intents)
        self.guild = discord.Object(id=GUILD_ID)

    async def setup_hook(self):
        # 슬래시 명령어 동기화
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)


bot = MyBot()

# 전역 변수로 투표 데이터를 관리
active_polls = {}
voice_channel_participants = {}


@bot.event
async def on_ready():
    print(f'Logged on as {bot.user}!')
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("대기중"))


@bot.tree.command(name='주디')
async def jodi(interaction: discord.Interaction):
    """사용자가 '주디'라고 입력했을 때 응답"""
    await interaction.response.send_message(f'오냐 {interaction.user.mention}', ephemeral=False)


@bot.tree.command(name='주디야')
@app_commands.describe(message="보낼 인사 메시지")
async def jodi_hello(interaction: discord.Interaction, message: str):
    """사용자가 '주디야'라고 입력했을 때 응답"""
    await interaction.response.send_message(message, ephemeral=False)


def number_to_emoji(number):
    num_to_emoji = {
        '0': ':zero:',
        '1': ':one:',
        '2': ':two:',
        '3': ':three:',
        '4': ':four:',
        '5': ':five:',
        '6': ':six:',
        '7': ':seven:',
        '8': ':eight:',
        '9': ':nine:'
    }
    return ''.join(num_to_emoji[digit] for digit in str(number))


@bot.tree.command(name='굴려')
async def roll_dice(interaction: discord.Interaction):
    """1부터 100까지의 숫자 중 하나를 무작위로 반환합니다."""
    roll = random.randint(1, 100)
    roll_emoji = number_to_emoji(roll)
    await interaction.response.send_message(f'🎲 {interaction.user.mention} : {roll_emoji}', ephemeral=False)


class VoteButton(Button):
    def __init__(self, label, count_dict):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.count_dict = count_dict

    async def callback(self, interaction: discord.Interaction):
        self.count_dict[self.label] += 1
        await interaction.response.send_message(f'{self.label}에 투표하셨습니다.', ephemeral=True)


@bot.tree.command(name='투표')
@app_commands.describe(topic="투표 주제", options="투표 옵션들 (쉼표로 구분)")
async def create_poll(interaction: discord.Interaction, topic: str, options: str):
    """새로운 투표를 생성합니다."""
    options_list = options.split(',')
    if len(options_list) < 2:
        await interaction.response.send_message("투표 항목을 두 개 이상 제공해야 합니다.", ephemeral=True)
        return

    count_dict = {option: 0 for option in options_list}
    active_polls[interaction.channel_id] = count_dict  # 현재 채널의 투표 데이터 저장

    view = View()
    for option in options_list:
        view.add_item(VoteButton(option, count_dict))

    await interaction.response.send_message(f'**{topic}**에 대한 투표를 시작합니다!', view=view, ephemeral=False)


@bot.tree.command(name='투표결과')
async def poll_results(interaction: discord.Interaction):
    """투표 결과를 보여줍니다."""
    if interaction.channel_id not in active_polls:
        await interaction.response.send_message("현재 활성화된 투표가 없습니다.", ephemeral=True)
        return

    count_dict = active_polls[interaction.channel_id]
    results = "\n".join([f"{option}: {count}" for option, count in count_dict.items()])
    await interaction.response.send_message(f'투표 결과:\n{results}', ephemeral=False)


class JoinButton(Button):
    def __init__(self, channel_id):
        super().__init__(label="참가하기", style=discord.ButtonStyle.success)
        self.channel_id = channel_id

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        if user not in voice_channel_participants[self.channel_id]:
            voice_channel_participants[self.channel_id].append(user)
            await interaction.response.send_message(f"{user.mention}이(가) 음성 채널에 참가했습니다.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user.mention}님은 이미 참가했습니다.", ephemeral=True)

        participant_list = "\n".join([user.mention for user in voice_channel_participants[self.channel_id]])
        await interaction.message.edit(content=f"현재 참가자:\n{participant_list}", view=self.view)


@bot.tree.command(name='음성채널생성')
@app_commands.describe(channel_name="생성할 음성 채널의 이름")
async def create_voice_channel(interaction: discord.Interaction, channel_name: str):
    """새 음성 채널을 생성합니다."""
    guild = interaction.guild
    category = discord.utils.get(guild.categories, name="주디팟 채널")
    if category is None:
        category = await guild.create_category("주디팟 채널")

    existing_channel = discord.utils.get(category.voice_channels, name=channel_name)
    if existing_channel is not None:
        await interaction.response.send_message(f"'{channel_name}' 채널이 이미 존재합니다.", ephemeral=True)
        return

    new_channel = await category.create_voice_channel(name=channel_name)
    voice_channel_participants[new_channel.id] = []

    view = View()
    join_button = JoinButton(new_channel.id)
    view.add_item(join_button)

    await interaction.response.send_message(f"새 음성 채널 '{new_channel.name}'이(가) 생성되었습니다!\n현재 참가자:\n(아직 없음)", view=view,
                                            ephemeral=False)


@bot.tree.command(name='음성채널참가')
@app_commands.describe(channel_name="참가할 음성 채널의 이름")
async def join_voice_channel(interaction: discord.Interaction, channel_name: str):
    """기존 음성 채널에 참가하는 버튼을 생성합니다."""
    guild = interaction.guild
    category = discord.utils.get(guild.categories, name="주디팟 채널")
    if category is None:
        await interaction.response.send_message("주디팟 채널 카테고리를 찾을 수 없습니다.", ephemeral=True)
        return

    channel = discord.utils.get(category.voice_channels, name=channel_name)
    if channel is None:
        await interaction.response.send_message(f"'{channel_name}' 음성 채널을 찾을 수 없습니다.", ephemeral=True)
        return

    view = View()
    join_button = JoinButton(channel.id)
    view.add_item(join_button)

    participant_list = "\n".join([user.mention for user in voice_channel_participants.get(channel.id, [])])
    await interaction.response.send_message(f"현재 참가자:\n{participant_list}", view=view, ephemeral=False)


@bot.tree.command(name='채팅채널생성')
@app_commands.describe(channel_name="생성할 채팅 채널의 이름")
async def create_text_channel(interaction: discord.Interaction, channel_name: str):
    """새 채팅 채널을 생성합니다."""
    guild = interaction.guild
    category = discord.utils.get(guild.categories, name="채팅채널")
    if category is None:
        category = await guild.create_category("채팅채널")

    existing_channel = discord.utils.get(category.text_channels, name=channel_name)
    if existing_channel is not None:
        await interaction.response.send_message(f"'{channel_name}' 채널이 이미 존재합니다.", ephemeral=True)
        return

    new_channel = await category.create_text_channel(name=channel_name)
    await interaction.response.send_message(f"새 채팅 채널 '{new_channel.name}'이(가) 생성되었습니다!", ephemeral=False)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("해당 명령어를 찾을 수 없습니다.", delete_after=10)
    else:
        await ctx.send(f"명령어 실행 중 오류가 발생했습니다: {error}", delete_after=10)


bot.run(TOKEN)
