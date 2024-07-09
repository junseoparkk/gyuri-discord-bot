import discord

def setup_greet_command(bot):
    @bot.tree.command(name='인사')
    async def greet(interaction: discord.Interaction):
        """인사 명령어"""
        await interaction.response.send_message('안녕하세요! 🍊 저는 규리, 여러분의 귀여운 귤 친구예요! 무엇을 도와드릴까요?', ephemeral=False)