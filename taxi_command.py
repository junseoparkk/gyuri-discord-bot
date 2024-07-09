import discord

def setup_taxi_command(bot):
    @bot.tree.command(name='택시')
    async def taxi(interaction: discord.Interaction):
        """택시 관련 정보를 제공하는 명령어"""
        await interaction.response.send_message('택시 기능은 현재 준비중입니다.', ephemeral=False)