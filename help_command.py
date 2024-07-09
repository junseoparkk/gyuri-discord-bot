import discord

def setup_help_command(bot):
    @bot.tree.command(name='도움말')
    async def help_command(interaction: discord.Interaction):
        """도움말 명령어"""
        await interaction.response.send_message('도움말 준비중입니다.', ephemeral=False)