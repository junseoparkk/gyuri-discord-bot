import discord

def setup_bus_command(bot):
    @bot.tree.command(name='버스')
    async def bus(interaction: discord.Interaction):
        """버스 정보를 제공하는 명령어"""
        await interaction.response.send_message('버스 기능은 현재 준비중입니다.', ephemeral=False)