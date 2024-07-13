import discord

def setup_vote_command(bot):
    @bot.tree.command(name='투표')
    async def vote(interaction: discord.Interaction):
        """투표를 생성하는 명령어"""
        await interaction.response.send_message('투표 기능은 현재 준비중입니다.', ephemeral=False)