import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import json
import os

FEEDBACK_FILE = 'feedback.json'

def save_feedback(feedback_data):
    """피드백 데이터를 JSON 파일에 저장합니다."""
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    data.append(feedback_data)

    with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def setup_feedback_command(bot):
    @app_commands.command(name="피드백", description="피드백을 남겨주세요! 🍊")
    @app_commands.describe(
        내용="피드백 내용을 입력하세요"
    )
    async def feedback(interaction: discord.Interaction, 내용: str):
        user = interaction.user
        username = user.name
        user_account = f"{user.name}#{user.discriminator}"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        feedback_data = {
            "시간": current_time,
            "사용자 이름": username,
            "사용자 계정": user_account,
            "내용": 내용
        }

        save_feedback(feedback_data)

        await interaction.response.send_message("피드백이 성공적으로 저장되었습니다. 🍊", ephemeral=True)

    # 명령어를 봇에 등록합니다
    bot.tree.add_command(feedback)

def setup(bot):
    bot.loop.create_task(setup_feedback_command(bot))
