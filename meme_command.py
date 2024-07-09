import discord

def setup_meme_command(bot):
    @bot.tree.command(name='짤')
    async def meme(interaction: discord.Interaction):
        """랜덤 짤을 제공하는 명령어"""
        await interaction.response.send_message('짤 기능은 현재 준비중입니다.', ephemeral=False)