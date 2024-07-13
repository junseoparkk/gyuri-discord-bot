import discord

def setup_help_command(bot):
    @bot.tree.command(name='도움말')
    async def help_command(interaction: discord.Interaction):
        """🍊 규리를 어떻게 사용하는 지 도움을 드려요!!"""
        await interaction.response.send_message('도움말 준비중입니다.', ephemeral=False)