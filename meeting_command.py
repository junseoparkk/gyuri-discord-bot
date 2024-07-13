import discord
from discord import app_commands
from discord.ui import Select, View

voice_channel_participants = {}

def setup_meeting_command(bot):
    @bot.tree.command(name='모임')
    @app_commands.describe(name="모임 이름", invite_message="초대 메시지")
    async def create_meeting(interaction: discord.Interaction, name: str, invite_message: str):
        """🍊 규리가 소모임을 음성 채널을 만드려드려요!"""
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
        """🍊 여러분이 만든 모임을 규리가 치워드릴게요!"""
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