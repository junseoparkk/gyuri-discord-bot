import discord
import random
import asyncio
from discord import app_commands
from discord.ui import Button, View, Select
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
        await interaction.response.send_message(f"새 모임 '{new_channel.name}'이(가) 생성되었습니다!\n {invite.url}\n {invite_message}", ephemeral=False)

    @bot.tree.command(name='모임삭제')
    async def delete_meeting(interaction: discord.Interaction):
        """모임을 삭제합니다."""
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="모임")
        if category is None:
            await interaction.response.send_message("모임 카테고리를 찾을 수 없습니다.", ephemeral=True)
            return

        channels = category.voice_channels
        if not channels:
            await interaction.response.send_message("모임 카테고리에 음성 채널이 없습니다.", ephemeral=True)
            return

        # Select menu for choosing the channel to delete
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
        await interaction.edit_original_response(view=None)
        await reveal_raffle_result(interaction, raffle)

        if len(raffle['participants']) < total:
            await message.edit(view=None)
            await reveal_raffle_result(interaction, raffle)


        # /help 명령어 구현
        @bot.tree.command(name='help')
        async def help_command(interaction: discord.Interaction):
            """명령어 목록 출력"""
            embed = discord.Embed(title="기능 목록", color=discord.Color.blue())

            embed.add_field(
                name="1. **모임**",
                value=(
                    "1.1 **생성**: `/모임 {name}`\n"
                    "- `{name}`을 가진 모임 메시지를 출력한다.\n"
                    "- 모임은 최대 360분간 모집된다.\n"
                    "1.2 **참가**: 버튼\n"
                    "- 생성된 모임에 참가 버튼을 통해 참가할 수 있다.\n"
                    "- 다 모이거나, 360분이 지나면, 메시지와 참가자 목록을 출력한다."
                ),
                inline=False
            )

            embed.add_field(
                name="2. **짤방**",
                value=(
                    "2.1 **생성**: 어드민 생성\n"
                    "2.2 **사용**: `/짤 {name}`\n"
                    "- `{name}`으로 등록된 짤이 나온다.\n"
                    "- 없을 시 없다(나만 보이는) 메시지가 출력된다.\n"
                    "2.3 **리스트**: `/짤 리스트`\n"
                    "- 짤 목록이 담긴 메시지를 제공한다."
                ),
                inline=False
            )

            embed.add_field(
                name="3. **투표**",
                value=(
                    "3.1 **투표 생성**: `/투표 {item1} {item2} {item3}`\n"
                    "- 스페이스바(or 쉼표)로 구분된 투표 항목을 통해 투표를 생성한다.\n"
                    "- 투표 항목에 스페이스바가 들어가는 경우는 추후 수정\n"
                    "- N분 이후 투표가 마감되며 메시지를 출력한다.\n"
                    "3.2 **투표**: 버튼\n"
                    "- 생성된 투표 메시지에 참가 버튼을 통해 참가할 수 있다.\n"
                    "- N분 이후 투표 결과 메시지가 출력된다."
                ),
                inline=False
            )

            embed.add_field(
                name="4. **도움말**",
                value=(
                    "4.1 **도움말**: `/규리야`, `/귤봇손환`\n"
                    "- 도움말을 출력한다.\n"
                    "- 나만 보이는 메시지로 간략한 소개? 아니면 규리랑 DM?"
                ),
                inline=False
            )

            embed.add_field(
                name="5. **제비뽑기**",
                value=(
                    "5.1 **제비뽑기 생성**: `/제비 {name} {A} {B}`\n"
                    "- `{name}` 가진 제비뽑기를 생성한다.\n"
                    "- A명 중 B명 당첨된다.\n"
                    "5.2 **제비뽑기 참가**: 버튼\n"
                    "- 버튼으로 참가한다.\n"
                    "- 참가 인원이 다 차거나 3분이 지나면 결과를 공개한다."
                ),
                inline=False
            )

            embed.add_field(
                name="6. **주사위 굴리기**",
                value=(
                    "6.1 **주사위 굴리기**: `/굴려`, `1🎲5 = 15`\n"
                    "- 1~100까지의 추첨을 진행한다.\n"
                    "- 예시: `@chen.park 1❤️ 보이드`"
                ),
                inline=False
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)
