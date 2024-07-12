import discord
import os
from discord.ext import commands

# def setup_meme_command(bot):
#     @bot.tree.command(name='짤')
#     async def meme(interaction: discord.Interaction):
#         """랜덤 짤을 제공하는 명령어"""
#         await interaction.response.send_message('짤 기능은 현재 준비중입니다.', ephemeral=False)


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# meme 폴더에서 이미지 파일 목록을 가져오기
meme_folder = './meme'
meme_images = {file_name: os.path.join(meme_folder, file_name) for file_name in os.listdir(meme_folder) if os.path.isfile(os.path.join(meme_folder, file_name))}

class MemeSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=name, value=name) for name in meme_images.keys()]
        super().__init__(placeholder="출력할 짤을 선택하세요...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_meme = self.values[0]
        file_path = meme_images[selected_meme]
        file = discord.File(file_path, filename=selected_meme)
        await interaction.response.send_message(file=file)

class MemeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MemeSelect())

def setup_meme_command(bot):
    @bot.tree.command(name='짤')
    async def meme(interaction: discord.Interaction):
        """랜덤 짤을 제공하는 명령어"""
        if not meme_images:
            await interaction.response.send_message('사용 가능한 짤이 없습니다.', ephemeral=True)
            return

        view = MemeView()
        await interaction.response.send_message('출력할 짤을 선택하세요:', view=view, ephemeral=True)