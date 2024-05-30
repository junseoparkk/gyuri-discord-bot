import discord
import random
import asyncio
from discord import app_commands
from discord.ui import Button, View, Select
from utils import check_file

# 전역 변수로 투표 데이터를 관리
active_polls = {}
voice_channel_participants = {}

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

def setup_commands(bot):
    @bot.tree.command(name='안녕')
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
            await interaction.response.defer()
            await interaction.followup.send(file=discord.File(image_path))
        except Exception as e:
            print(f"이미지 전송 중 오류가 발생했습니다: {e}")
            try:
                await interaction.followup.send(f"이미지 전송 중 오류가 발생했습니다: {e}", ephemeral=True)
            except Exception as followup_error:
                print(f"후속 메시지 전송 중 오류가 발생했습니다: {followup_error}")

    @bot.tree.command(name='void2')
    async def void2(interaction: discord.Interaction):
        """Void2 명령어"""
        image_path = 'void2.png'  # 이미지 파일 경로
        if not check_file(image_path):
            await interaction.response.send_message("이미지 파일을 찾을 수 없습니다.", ephemeral=True)
            return

        try:
            await interaction.response.defer()
            await interaction.followup.send(file=discord.File(image_path))
        except Exception as e:
            print(f"이미지 전송 중 오류가 발생했습니다: {e}")
            try:
                await interaction.followup.send(f"이미지 전송 중 오류가 발생했습니다: {e}", ephemeral=True)
            except Exception as followup_error:
                print(f"후속 메시지 전송 중 오류가 발생했습니다: {followup_error}")

    @bot.tree.command(name='규리')
    async def gyuri(interaction: discord.Interaction):
        """규리 명령어"""
        image_path = '규리.png'  # 이미지 파일 경로
        if not check_file(image_path):
            await interaction.response.send_message("이미지 파일을 찾을 수 없습니다.", ephemeral=True)
            return

        try:
            await interaction.response.defer()
            await interaction.followup.send(file=discord.File(image_path))
        except Exception as e:
            print(f"이미지 전송 중 오류가 발생했습니다: {e}")
            try:
                await interaction.followup.send(f"이미지 전송 중 오류가 발생했습니다: {e}", ephemeral=True)
            except Exception as followup_error:
                print(f"후속 메시지 전송 중 오류가 발생했습니다: {followup_error}")

    @bot.tree.command(name='머스크형')
    async def musk(interaction: discord.Interaction):
        """머스크형 명령어"""
        image_path = '머스크형.png'  # 이미지 파일 경로
        if not check_file(image_path):
            await interaction.response.send_message("이미지 파일을 찾을 수 없습니다.", ephemeral=True)
            return

        try:
            await interaction.response.defer()
            await interaction.followup.send(file=discord.File(image_path))
        except Exception as e:
            print(f"이미지 전송 중 오류가 발생했습니다: {e}")
            try:
                await interaction.followup.send(f"이미지 전송 중 오류가 발생했습니다: {e}", ephemeral=True)
            except Exception as followup_error:
                print(f"후속 메시지 전송 중 오류가 발생했습니다: {followup_error}")

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
            await interaction.response.send_message(f"'{name}' 모임이 이미 존재합니다.", ephemeral=True)
            return

        new_channel = await category.create_voice_channel(name=name)
        voice_channel_participants[new_channel.id] = []

        invite = await new_channel.create_invite(max_age=21600, max_uses=0)  # 6시간 유효
        await interaction.response.send_message(f"모임 '{new_channel.name}'이(가) 생성되었습니다!\n {invite.url}\n {invite_message}", ephemeral=False)

    @bot.tree.command(name='모임제거')
    async def delete_meeting(interaction: discord.Interaction):
        """모임을 제거합니다."""
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="모임")
        if category is None:
            await interaction.response.send_message("모임 카테고리를 찾을 수 없습니다.", ephemeral=True)
            return

        channels = category.voice_channels
        if not channels:
            await interaction.response.send_message("모임 카테고리에 음성 채널이 없습니다.", ephemeral=True)
            return

        options = [discord.SelectOption(label=channel.name, value=str(channel.id)) for channel in channels]

        class DeleteChannelSelect(Select):
            def __init__(self):
                super().__init__(placeholder="삭제할 모임 채널을 선택하세요", min_values=1, max_values=1, options=options)

            async def callback(self, interaction: discord.Interaction):
                channel_id = int(self.values[0])
                channel = discord.utils.get(guild.voice_channels, id=channel_id)
                if channel:
                    await channel.delete(reason="관리자에 의한 수동 삭제")
                    await interaction.response.send_message(f"모임 '{channel.name}'이(가) 삭제되었습니다.", ephemeral=False)
                else:
                    await interaction.response.send_message("채널을 찾을 수 없습니다.", ephemeral=True)

        view = View()
        view.add_item(DeleteChannelSelect())
        await interaction.response.send_message("삭제할 모임 채널을 선택하세요:", view=view, ephemeral=True)

    class RaffleButton(discord.ui.Button):
        def __init__(self, raffle):
            super().__init__(label="참가", style=discord.ButtonStyle.primary)
            self.raffle = raffle

        async def callback(self, interaction: discord.Interaction):
            user = interaction.user
            if user not in self.raffle['participants']:
                self.raffle['participants'].append(user)
                await interaction.response.send_message(f"{user.name}님이 참가했습니다!", ephemeral=True)
            else:
                await interaction.response.send_message("이미 참가하셨습니다!", ephemeral=True)

    class RaffleView(discord.ui.View):
        def __init__(self, raffle):
            super().__init__()
            self.raffle = raffle
            self.add_item(RaffleButton(raffle))

    async def reveal_raffle_result(interaction: discord.Interaction, raffle):
        if len(raffle['participants']) < raffle['winners']:
            await interaction.followup.send(f"참가자가 충분하지 않습니다. 제비뽑기 '{raffle['name']}'를 취소합니다.")
            return

        winners = random.sample(raffle['participants'], raffle['winners'])
        winner_names = ", ".join([winner.name for winner in winners])
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

        view = RaffleView(raffle)

        await interaction.response.send_message(
            f"제비뽑기 '{name}'가 생성되었습니다!\n참가자는 총 {total}명 중 {winners}명이 당첨됩니다.\n참가 가능 시간: 3분",
            view=view
        )

        await asyncio.sleep(180)
        await interaction.edit_original_response(view=None)
        await reveal_raffle_result(interaction, raffle)

    async def roll_dice(interaction: discord.Interaction):
        """1부터 100까지의 숫자 중 하나를 무작위로 반환합니다."""
        roll = random.randint(1, 100)
        roll_emoji = number_to_emoji(roll)
        await interaction.response.send_message(f'🎲 {interaction.user.mention} : {roll_emoji}', ephemeral=False)

    @bot.tree.command(name='굴려')
    async def roll_command(interaction: discord.Interaction):
        """주사위 굴리기"""
        await roll_dice(interaction)

    @bot.tree.command(name='도움말')
    async def help_command(interaction: discord.Interaction):
        """명령어 목록 출력"""
        embed = discord.Embed(title="기능 목록", color=discord.Color.blue())

        embed.add_field(
            name="1. **안녕**",
            value="규리와 인사를 나눌 수 있어요! 🍊 `/안녕` 명령어를 사용해보세요!🍊",
            inline=False
        )

        embed.add_field(
            name="2. **Void**",
            value="먹고 씻고 연애하는건? `/Void` 명령어를 사용하세요!🍊",
            inline=False
        )

        embed.add_field(
            name="3. **Void2**",
            value="세침떼기(?) 인생네컷 보이드 짤을 채팅방에 보냅니다. `/Void2` 명령어를 사용하세요!🍊",
            inline=False
        )

        embed.add_field(
            name="4. **규리**",
            value="귀여운 🍊규리🍊 의 사진을 전송합니다. `/규리` 명령어를 사용하세요!🍊",
            inline=False
        )

        embed.add_field(
            name="5. **머스크형**",
            value="머스크형의 명언, 당신은 100시간을 코딩하셔야...아니 보이드였다. `/머스크형` 명령어를 사용하세요!🍊",
            inline=False
        )

        embed.add_field(
            name="6. **모임**",
            value="새로운 모임을 만들 수 있어요! `/모임 {name} {invite_message}`를 사용해보세요!🍊",
            inline=False
        )

        embed.add_field(
            name="7. **모임제거**",
            value="모임을 삭제할 수 있어요! `/모임제거` 명령어를 사용해보세요!🍊",
            inline=False
        )

        embed.add_field(
            name="8. **제비**",
            value="제비뽑기를 할 수 있어요! `/제비 {name} {total} {winners}`를 사용해보세요!🍊",
            inline=False
        )

        embed.add_field(
            name="9. **굴려**",
            value="1부터 100까지 숫자 중 하나를 무작위로 반환합니다! `/굴려` 명령어를 사용해보세요!🍊",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
