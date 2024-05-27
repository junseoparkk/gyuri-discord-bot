import discord
import random
import asyncio
from discord import app_commands
from discord.ui import Button, View
from utils import check_file

# 전역 변수로 투표 데이터를 관리
active_polls = {}
voice_channel_participants = {}

def setup_commands(bot):
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
                await interaction.followup.send(f"이미지 전송 중 오류가 발생했습니다: {e}", ephemeral=True)

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
                await interaction.followup.send(f"이미지 전송 중 오류가 발생했습니다: {e}", ephemeral=True)

    @bot.tree.command(name='모임')
    @app_commands.describe(name="모임 이름", invite_message="초대 메시지")
    async def create_meeting(interaction: discord.Interaction, name: str, invite_message: str):
        """모임을 생성합니다."""
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="모임")
        if category is None:
            category = await guild.create_category("모임")

        existing_channel = discord.utils.get(category.voice_channels, name=name)
        if existing_channel is not None:
            await interaction.response.send_message(f"'{name}' 채널이 이미 존재합니다.", ephemeral=True)
            return

        new_channel = await category.create_voice_channel(name=name)
        voice_channel_participants[new_channel.id] = []

        invite = await new_channel.create_invite(max_age=21600, max_uses=0)  # 6시간 유효
        await interaction.response.send_message(f"새 모임 음성 채널 '{new_channel.name}'이(가) 생성되었습니다!\n초대 링크: {invite.url}\n초대 메시지: {invite_message}", ephemeral=False)

    class RaffleButton(Button):
        def __init__(self, raffle):
            super().__init__(label="참가", style=discord.ButtonStyle.primary)
            self.raffle = raffle

        async def callback(self, interaction: discord.Interaction):
            user = interaction.user
            if user not in self.raffle['participants']:
                self.raffle['participants'].append(user)
                await interaction.response.send_message(f"{user.name}님이 참가했습니다!", ephemeral=True)
                if len(self.raffle['participants']) >= self.raffle['total']:
                    await self.raffle['message'].edit(view=None)
                    await reveal_raffle_result(interaction, self.raffle)
            else:
                await interaction.response.send_message("이미 참가하셨습니다!", ephemeral=True)

    async def reveal_raffle_result(interaction: discord.Interaction, raffle):
        if len(raffle['participants']) < raffle['winners']:
            await interaction.followup.send(f"참가자가 충분하지 않습니다. 제비뽑기 '{raffle['name']}'를 취소합니다.")
            return

        winners_list = random.sample(raffle['participants'], raffle['winners'])
        winner_names = ", ".join([winner.name for winner in winners_list])
        await interaction.followup.send(f"제비뽑기 '{raffle['name']}'의 당첨자는: {winner_names}입니다!")

    @bot.tree.command(name='제비')
    @app_commands.describe(name="제비뽑기 이름", total="참가자 수", winners="당첨자 수")
    async def create_raffle(interaction: discord.Interaction, name: str, total: int, winners: int):
        """제비뽑기를 생성합니다."""
        raffle = {
            'name': name,
            'total': total,
            'winners': winners,
            'participants': [],
            'message': None
        }

        view = View()
        button = RaffleButton(raffle)
        view.add_item(button)

        # Send the initial message and store the message object
        message = await interaction.response.send_message(
            f"제비뽑기 '{name}'가 생성되었습니다!\n참가자는 총 {total}명 중 {winners}명이 당첨됩니다.\n참가 가능 시간: 3분",
            view=view,
            wait=True
        )
        raffle['message'] = message

        # Wait for 3 minutes or until participants are full
        await asyncio.sleep(180)
        if len(raffle['participants']) < total:
            await message.edit(view=None)
            await reveal_raffle_result(interaction, raffle)
