import discord
import asyncio
from discord.ext import commands
from typing import Optional

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

active_votes = {}

class VoteButton(discord.ui.Button):
    def __init__(self, label, allow_multiple_votes, vote_tracker, title):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.votes = 0
        self.allow_multiple_votes = allow_multiple_votes
        self.vote_tracker = vote_tracker
        self.title = title

    async def callback(self, interaction: discord.Interaction):
        if self.title not in active_votes:
            await interaction.response.send_message("이미 종료된 투표에요! 🍊", ephemeral=True)
            return

        user_votes = self.vote_tracker.get(interaction.user.id, set())
        if not self.allow_multiple_votes and user_votes:
            await interaction.response.send_message("중복 투표는 안돼요! 🍊", ephemeral=True)
        elif self.label in user_votes:
            await interaction.response.send_message("이미 이 옵션에 투표하셨네요! 🍊", ephemeral=True)
        else:
            self.votes += 1
            user_votes.add(self.label)
            self.vote_tracker[interaction.user.id] = user_votes
            await interaction.response.send_message(f'{self.label}에 투표하셨어요! 🍊', ephemeral=True)

class VoteView(discord.ui.View):
    def __init__(self, options, allow_multiple_votes, time, title):
        super().__init__(timeout=time)  # View가 주어진 시간 후에 만료되도록 설정
        self.vote_tracker = {}
        self.title = title
        for option in options:
            self.add_item(VoteButton(label=option.strip(), allow_multiple_votes=allow_multiple_votes, vote_tracker=self.vote_tracker, title=title))

    def get_results(self):
        results = {button.label: button.votes for button in self.children if isinstance(button, VoteButton)}
        return results

class RemoveVoteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RemoveVoteSelect())

class RemoveVoteSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=title, value=title) for title in active_votes.keys()]
        super().__init__(placeholder="삭제할 투표를 선택하세요...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        title = self.values[0]
        if title in active_votes:
            del active_votes[title]
            await interaction.response.send_message(f"투표 '{title}'가 삭제되었어요! 🍊", ephemeral=False)
        else:
            await interaction.response.send_message("잘못된 투표 제목이에요! 🍊", ephemeral=True)

def setup_vote_command(bot):
    @bot.tree.command(name='투표')
    async def vote(
        interaction: discord.Interaction, 
        title: Optional[str] = None, 
        options: Optional[str] = None, 
        allow_multiple_votes: Optional[bool] = None, 
        time: Optional[int] = None
        ):
        """🍊 투표를 생성하는 명령어에요!"""
        if title is None or options is None or allow_multiple_votes is None or time is None:
            description = (
                "[모든 옵션을 채워주세요!! 🍊]\n"
                "제목 - 투표 제목을 입력해주세요 (예: 점심 메뉴 투표)\n"
                "항목 - 콤마로 구분하여 투표 항목을 적어주세요 (예: 한식, 중식, 일식)\n"
                "복수응답 - 복수응답 허용(True), 비허용(False)을 골라주세요\n"
                "시간 - 투표 진행 시간을 입력해주세요. 최소 10초 ~ 최대 3600초"
            )
            embed = discord.Embed(title="투표 생성 방법 🍊", description=description, color=0x00ff00)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
    
        options_list = [option.strip() for option in options.split(',')]

        if len(options_list) < 2:
            await interaction.response.send_message("투표 옵션을 두 개 이상 제공해주세요! 옵션은 콤마(,)로 구분해서 입력해주세요. 🍊", ephemeral=True)
            return
        if any(option == "" for option in options_list):
            await interaction.response.send_message("공백 옵션이 포함되어 있어요! 모든 옵션을 올바르게 입력해주세요. 🍊", ephemeral=True)
            return
        if time < 10 or time > 3600:
            await interaction.response.send_message("투표 유효 시간은 최소 10초, 최대 한 시간(3600초)에요! 🍊", ephemeral=True)
            return
        if title in active_votes:
            await interaction.response.send_message("이미 동일한 제목의 투표가 있어요! 다른 제목을 사용해주세요. 🍊", ephemeral=True)
            return

        view = VoteView(options_list, allow_multiple_votes, time, title)
        embed = discord.Embed(title=title, description="아래 버튼을 클릭해서 투표해보세요! 🍊", color=0x00ff00)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

        active_votes[title] = (interaction.channel_id, view)

        # 지정된 시간 대기 후 투표 결과 집계
        await asyncio.sleep(time)

        # 투표가 아직 활성화되어 있는지 확인
        if title in active_votes:
            results = view.get_results()
            results_str = "\n".join([f"{option}: {count} 표" for option, count in results.items()])
            result_embed = discord.Embed(title=f"{title} 결과 🍊", description=results_str, color=0xff0000)
            await interaction.followup.send(embed=result_embed, ephemeral=False)

            # 투표가 끝나면 active_votes에서 삭제
            del active_votes[title]

    @bot.tree.command(name='투표제거')
    async def remove_vote(interaction: discord.Interaction):
        """🍊 활성화된 투표 목록을 보여주고, 선택한 투표를 삭제할 수 있어요!"""
        if not active_votes:
            await interaction.response.send_message("현재 활성화된 투표가 없어요! 🍊", ephemeral=True)
            return

        view = RemoveVoteView()
        await interaction.response.send_message("삭제할 투표를 선택해주세요! 🍊", view=view, ephemeral=True)

    @bot.tree.command(name='투표수정')
    async def edit_vote(interaction: discord.Interaction, title: str, options: str = None, allow_multiple_votes: bool = None, time: int = None):
        """🍊 기존 투표를 수정하는 명령어에요!"""
        if title not in active_votes:
            await interaction.response.send_message("수정할 투표가 없어요! 🍊", ephemeral=True)
            return

        channel_id, view = active_votes[title]
        
        if options:
            options_list = [option.strip() for option in options.split(',')]
            if len(options_list) < 2:
                await interaction.response.send_message("투표 옵션을 두 개 이상 제공해주세요! 옵션은 콤마(,)로 구분해서 입력해주세요. 🍊", ephemeral=True)
                return
            if any(option == "" for option in options_list):
                await interaction.response.send_message("공백 옵션이 포함되어 있어요! 모든 옵션을 올바르게 입력해주세요. 🍊", ephemeral=True)
                return
            view.children.clear()
            for option in options_list:
                view.add_item(VoteButton(label=option, allow_multiple_votes=view.children[0].allow_multiple_votes, vote_tracker=view.vote_tracker, title=title))
        
        if allow_multiple_votes is not None:
            for button in view.children:
                button.allow_multiple_votes = allow_multiple_votes
        
        if time:
            if time < 10 or time > 3600:
                await interaction.response.send_message("투표 유효 시간은 최소 10초, 최대 한 시간(3600초)에요! 🍊", ephemeral=True)
                return
            view.timeout = time

        active_votes[title] = (channel_id, view)
        await interaction.response.send_message("투표가 성공적으로 수정되었어요! 🍊", ephemeral=True)

bot.run('YOUR_BOT_TOKEN')
