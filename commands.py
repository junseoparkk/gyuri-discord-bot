import discord
import os
import random
from discord import app_commands
from discord.ui import Button, View
from utils import number_to_emoji, check_file

# 전역 변수로 투표 데이터를 관리
active_polls = {}
voice_channel_participants = {}

def setup_commands(bot):
    @bot.tree.command(name='주디')
    async def jodi(interaction: discord.Interaction):
        """사용자가 '주디'라고 입력했을 때 응답"""
        await interaction.response.send_message(f'오냐 {interaction.user.mention}', ephemeral=False)

    @bot.tree.command(name='주디야')
    @app_commands.describe(message="보낼 인사 메시지")
    async def jodi_hello(interaction: discord.Interaction, message: str):
        """사용자가 '주디야'라고 입력했을 때 응답"""
        await interaction.response.send_message(message, ephemeral=False)

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

        await interaction.response.send_message(f"새 음성 채널 '{new_channel.name}'이(가) 생성되었습니다!\n현재 참가자:\n(아직 없음)", view=view, ephemeral=False)

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

    @bot.tree.command(name='createchannel')
    @app_commands.describe(channel_name="채널 이름", channel_type="채널 유형 (text 또는 voice)")
    async def create_channel(interaction: discord.Interaction, channel_name: str, channel_type: str):
        """새 텍스트 또는 음성 채널을 생성합니다."""
        guild = interaction.guild
        if channel_type not in ['text', 'voice']:
            await interaction.response.send_message('잘못된 채널 유형입니다. "text" 또는 "voice"를 사용해주세요.', ephemeral=True)
            return

        try:
            if channel_type == 'text':
                new_channel = await guild.create_text_channel(name=channel_name)
            elif channel_type == 'voice':
                new_channel = await guild.create_voice_channel(name=channel_name)

            invite = await new_channel.create_invite(max_age=600, max_uses=1)
            await interaction.response.send_message(f"채널이 생성되었습니다: {new_channel.name}\n초대 링크: {invite.url}", ephemeral=False)
        except Exception as e:
            await interaction.response.send_message(f"채널 생성 중 오류가 발생했습니다: {e}", ephemeral=True)

    @bot.tree.command(name='ping')
    async def ping(interaction: discord.Interaction):
        """Ping 명령어"""
        await interaction.response.send_message('퐁!', ephemeral=False)

    @bot.tree.command(name='hello')
    async def hello(interaction: discord.Interaction):
        """Hello 명령어"""
        await interaction.response.send_message('안녕하세요! 🍊 나는 규리, 여러분의 귀여운 귤 친구예요! 언제나 여러분과 함께할 준비가 되어 있어요. 우리 같이 재미있는 모임을 만들고 즐거운 시간을 보내 볼까요? 어떤 모임이든, 제가 도와드릴게요!', ephemeral=False)

    @bot.tree.command(name='void')
    async def void(interaction: discord.Interaction):
        """Void 명령어"""
        image_path = 'void.png'  # 이미지 파일 경로
        if not check_file(image_path):
            await interaction.response.send_message("이미지 파일을 찾을 수 없습니다.", ephemeral=True)
            return

        try:
            await interaction.response.send_message(file=discord.File(image_path))
        except Exception as e:
            print(f"이미지 전송 중 오류가 발생했습니다: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"이미지 전송 중 오류가 발생했습니다: {e}", ephemeral=True)

    @bot.tree.command(name='void2')
    async def void2(interaction: discord.Interaction):
        """Void2 명령어"""
        image_path = 'void2.png'  # 이미지 파일 경로
        if not check_file(image_path):
            await interaction.response.send_message("이미지 파일을 찾을 수 없습니다.", ephemeral=True)
            return

        try:
            await interaction.response.send_message(file=discord.File(image_path))
        except Exception as e:
            print(f"이미지 전송 중 오류가 발생했습니다: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"이미지 전송 중 오류가 발생했습니다: {e}", ephemeral=True)
