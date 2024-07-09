import discord

def setup_weather_command(bot):
    @bot.tree.command(name='날씨')
    async def weather(interaction: discord.Interaction):
        """날씨 정보를 제공하는 명령어"""
        await interaction.response.send_message('날씨 기능은 현재 준비중입니다.', ephemeral=False)