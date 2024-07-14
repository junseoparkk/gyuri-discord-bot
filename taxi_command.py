import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import asyncio
import json
import os
import random
import string

DATA_FILE = 'taxi_events.json'

class TaxiView(discord.ui.View):
    def __init__(self, bot, guild_id, author, destination, time, max_participants, message_id=None, participants=None, created_at=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.author = author
        self.destination = destination
        self.time = time
        self.max_participants = max_participants
        self.participants = participants if participants else [author]
        self.thread = None
        self.deleted = False
        self.message_id = message_id
        self.is_full = False
        self.is_departed = False
        self.created_at = created_at if created_at else datetime.now()

    @discord.ui.button(label="참가", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.deleted:
            await interaction.response.send_message("이 모집은 삭제되었어요! 🍊", ephemeral=True)
            return

        if self.is_departed:
            await interaction.response.send_message("이미 출발했어요! 🍊", ephemeral=True)
            return

        if interaction.user in self.participants:
            await interaction.response.send_message("이미 참가하셨네요! 🍊", ephemeral=True)
        elif len(self.participants) >= self.max_participants:
            await interaction.response.send_message("모집이 다 찼어요! 🍊", ephemeral=True)
        else:
            self.participants.append(interaction.user)
            await interaction.response.send_message(f"{interaction.user.name}님이 참가하셨어요! 🍊", ephemeral=True)
            await interaction.message.edit(embed=self.get_embed(), view=self)
            if self.thread:
                await self.thread.send(f"{interaction.user.mention}님이 참가하셨어요! 🍊")
                await interaction.message.edit(view=self)
            if len(self.participants) == self.max_participants:
                self.is_full = True
                if self.thread:
                    await self.thread.send(embed=self.get_complete_embed())
                    mentions = ' '.join([p.mention for p in self.participants])
                    await self.thread.send(f"{mentions} 모두 모였어요! 🍊")
                self.schedule_departure_alert()
            self.save_event()

    @discord.ui.button(label="참가취소", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.deleted:
            await interaction.response.send_message("이 모집은 삭제되었어요! 🍊", ephemeral=True)
            return

        if self.is_departed:
            await interaction.response.send_message("이미 출발했어요! 🍊", ephemeral=True)
            return

        if interaction.user not in self.participants:
            await interaction.response.send_message("참가하지 않으셨네요! 🍊", ephemeral=True)
        elif interaction.user == self.author:
            await interaction.response.send_message("모임장은 참가를 취소할 수 없어요! 🍊", ephemeral=True)
        else:
            self.participants.remove(interaction.user)
            self.is_full = False
            await interaction.response.send_message(f"{interaction.user.name}님이 참가를 취소하셨어요! 🍊", ephemeral=True)
            await interaction.message.edit(embed=self.get_embed(), view=self)
            if self.thread:
                await self.thread.send(f"{interaction.user.mention}님이 참가를 취소하셨어요! 🍊")
                await interaction.message.edit(view=self)
            self.save_event()

    @discord.ui.button(label="출발", style=discord.ButtonStyle.blurple)
    async def depart(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.deleted:
            await interaction.response.send_message("이 모집은 삭제되었어요! 🍊", ephemeral=True)
            return

        if self.is_departed:
            await interaction.response.send_message("이미 출발했어요! 🍊", ephemeral=True)
            return

        if interaction.user != self.author:
            await interaction.response.send_message("모임장만 출발을 할 수 있어요! 🍊", ephemeral=True)
            return

        self.is_departed = True
        await interaction.response.send_message("택시가 출발했습니다! 🍊", ephemeral=True)
        if self.thread:
            mentions = ' '.join([p.mention for p in self.participants])
            await self.thread.send(f"{mentions} 택시가 출발했습니다! 🍊")
        
        # 참가 및 취소 버튼 비활성화
        self.children[0].disabled = True  # 참가 버튼
        self.children[1].disabled = True  # 참가취소 버튼
        await interaction.message.edit(view=self)
        self.save_event()

    def get_embed(self):
        """택시 모집 정보를 포함한 임베드를 생성합니다."""
        embed = discord.Embed(title="택시 모집 🍊", color=0x00ff00)
        embed.add_field(name="목적지", value=self.destination, inline=False)
        embed.add_field(name="출발 시간", value=format_time(self.time), inline=False)
        embed.add_field(name="모집자", value=self.author.mention if self.author else "Unknown", inline=False)
        embed.add_field(name="모집 인원", value=f"{len(self.participants)}/{self.max_participants}", inline=False)
        participant_mentions = '\n'.join([f"- {p.mention}" for p in self.participants])
        embed.add_field(name="참가자", value=participant_mentions if participant_mentions else "없음", inline=False)
        return embed

    def get_complete_embed(self):
        """택시 모집 완료 정보를 포함한 임베드를 생성합니다."""
        embed = discord.Embed(title="택시 모집 완료! 🍊", color=0x00ff00)
        embed.add_field(name="목적지", value=self.destination, inline=False)
        embed.add_field(name="출발 시간", value=format_time(self.time), inline=False)
        embed.add_field(name="모집자", value=self.author.mention if self.author else "Unknown", inline=False)
        participant_mentions = '\n'.join([f"- {p.mention}" for p in self.participants])
        embed.add_field(name="참가자", value=participant_mentions, inline=False)
        return embed

    def schedule_departure_alert(self):
        """출발 알림을 스케줄링합니다."""
        time_format = "%H%M"
        departure_time = datetime.strptime(self.time, time_format)
        now = datetime.now()

        if departure_time.time() <= now.time():
            departure_time += timedelta(days=1)

        intervals = [10, 5, 3, 1]
        for minutes in intervals:
            alert_time = departure_time - timedelta(minutes=minutes)
            delay = (alert_time - now).total_seconds()
            if delay > 0:
                self.bot.loop.create_task(self.send_departure_alert(delay, minutes))

    async def send_departure_alert(self, delay, minutes):
        """출발 알림을 보냅니다."""
        await asyncio.sleep(delay)
        mentions = ' '.join([p.mention for p in self.participants])
        if self.thread:
            await self.thread.send(f"{mentions} 출발 시간이 {minutes}분 남았어요! 🍊")

    def save_event(self):
        """택시 모집 정보를 파일에 저장합니다."""
        event_data = {
            'guild_id': self.guild_id,
            'author': self.author.id if self.author else None,
            'destination': self.destination,
            'time': self.time,
            'max_participants': self.max_participants,
            'participants': [p.id for p in self.participants],
            'message_id': self.message_id,
            'created_at': self.created_at.isoformat(),
            'is_full': self.is_full,
            'is_departed': self.is_departed,
            'deleted': self.deleted
        }
        
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        else:
            data = {}

        data[self.message_id] = event_data

        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    @staticmethod
    async def load_events(bot):
        """파일에서 택시 모집 정보를 불러옵니다."""
        if not os.path.exists(DATA_FILE):
            return

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}

        for message_id, event_data in data.items():
            author = await bot.fetch_user(event_data['author']) if event_data['author'] else None
            participants = [await bot.fetch_user(user_id) for user_id in event_data['participants']]
            created_at = datetime.fromisoformat(event_data['created_at'])
            view = TaxiView(
                bot,
                event_data['guild_id'],
                author,
                event_data['destination'],
                event_data['time'],
                event_data['max_participants'],
                message_id=message_id,
                participants=participants,
                created_at=created_at
            )
            view.is_full = event_data['is_full']
            view.is_departed = event_data['is_departed']
            view.deleted = event_data['deleted']
            bot.taxi_events[message_id] = view

class TaxiListView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.update_view()

    def update_view(self):
        """택시 목록 뷰를 업데이트합니다."""
        self.clear_items()
        for event_id, view in self.bot.taxi_events.items():
            if view.message_id and view.thread and not view.is_full and not view.is_departed and not view.deleted:
                button = discord.ui.Button(label=f"{view.destination} - {format_time(view.time)}", style=discord.ButtonStyle.link, url=f"https://discord.com/channels/{view.guild_id}/{view.thread.id}/{view.message_id}")
                self.add_item(button)

def parse_time(time_input):
    """입력된 시간 문자열을 파싱하여 표준 형식으로 변환합니다."""
    if time_input.isdigit():
        if len(time_input) == 4:
            return time_input
        elif len(time_input) <= 2:
            hour = int(time_input)
            if 0 <= hour <= 23:
                return f"{hour:02d}00"
    try:
        time = datetime.strptime(time_input, "%H:%M")
        return time.strftime("%H%M")
    except ValueError:
        return None

def format_time(time_str):
    """시간 문자열을 포맷팅합니다."""
    time = datetime.strptime(time_str, "%H%M")
    return time.strftime("%H시 %M분")

def generate_unique_id():
    """고유한 ID를 생성합니다."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

async def setup_taxi_command(bot):
    @app_commands.command(name="택시", description="🍊 택시 모집! 함께 가요!")
    @app_commands.describe(
        목적지="목적지를 선택해주세요",
        시간="출발 시간 (오전 8시 입력하기 : 8, 0800, 08:00)",
        모집인원="모집 인원 (2-4명)"
    )
    @app_commands.choices(
        목적지=[
            app_commands.Choice(name="숙소", value="숙소"),
            app_commands.Choice(name="교육장", value="교육장"),
            app_commands.Choice(name="기타", value="기타")
        ],
        모집인원=[
            app_commands.Choice(name="2명", value=2),
            app_commands.Choice(name="3명", value=3),
            app_commands.Choice(name="4명", value=4)
        ]
    )
    async def taxi(interaction: discord.Interaction, 목적지: str, 시간: str, 모집인원: int):
        """택시 모집을 생성합니다."""
        for view in bot.taxi_events.values():
            if view.author == interaction.user and not view.deleted and datetime.strptime(view.time, "%H%M") > datetime.now():
                await interaction.response.send_message(f"{interaction.user.name}님, 이미 활성화된 택시 파티가 있어요! 먼저 삭제해주세요. 🍊", ephemeral=True)
                return
        
        parsed_time = parse_time(시간)
        if parsed_time is None:
            await interaction.response.send_message("올바른 시간 형식이 아니에요. 출발 시간은 다음과 같이 입력해주세요:\n"
                                                    "- 8 입력 시 오전 8시\n"
                                                    "- 0800 입력 시 오전 8시\n"
                                                    "- 08:00 입력 시 오전 8시\n"
                                                    "🍊", ephemeral=True)
            return

        # 현재 시간보다 이전 시간인지 확인
        current_time = datetime.now()
        input_time = datetime.strptime(parsed_time, "%H%M")
        if input_time.time() < current_time.time():
            await interaction.response.send_message("현재 시간보다 이전 시간으로 택시를 잡을 수 없어요! 🍊", ephemeral=True)
            return
        
        event_id = generate_unique_id()
        view = TaxiView(bot, interaction.guild_id, interaction.user, 목적지, parsed_time, 모집인원)
        bot.taxi_events[event_id] = view
        
        await interaction.response.send_message(embed=view.get_embed(), view=view)
        try:
            original_response = await interaction.original_response()
            view.message_id = original_response.id
            unique_id = generate_unique_id()
            thread_name = f"택시 모집 - {unique_id}"
            thread = await original_response.create_thread(name=thread_name, auto_archive_duration=60)
            view.thread = thread
            await thread.send(f"택시 모집 스레드가 생성되었어요!🍊 출발 시간: {format_time(parsed_time)} 🍊", view=view)
            view.save_event()
        except Exception as e:
            await interaction.followup.send("스레드 생성에 실패했어요. 관리자에게 문의하세요. 🍊", ephemeral=True)
            print(f"Failed to create thread: {e}")

    @app_commands.command(name="택시조회", description="🍊 생성된 택시 모집을 조회해요!")
    async def view_taxi(interaction: discord.Interaction):
        """생성된 택시 모집을 조회합니다."""
        active_events = {k: v for k, v in bot.taxi_events.items() if not v.is_full and not v.is_departed and not v.deleted}
        if not active_events:
            await interaction.response.send_message("현재 참가 가능한 택시 모집이 없어요! 🍊", ephemeral=True)
            return

        embeds = [discord.Embed(title="택시 모집 조회", description=f"목적지: {view.destination}\n출발 시간: {format_time(view.time)}\n모집자: {view.author.mention if view.author else 'Unknown'}", color=0x00ff00) for view in active_events.values()]
        view = TaxiListView(bot)
        await interaction.response.send_message(embeds=embeds, view=view, ephemeral=True)

    @app_commands.command(name="택시참여", description="🍊 내가 참여한 택시 모집을 조회해요!")
    async def view_my_taxi_participation(interaction: discord.Interaction):
        """사용자가 참여한 택시 모집을 조회합니다."""
        my_events = [view for view in bot.taxi_events.values() if interaction.user in view.participants and not view.deleted]
        if not my_events:
            await interaction.response.send_message("현재 참여한 택시 모집이 없어요! 🍊", ephemeral=True)
            return

        embeds = []
        for view in my_events:
            embed = discord.Embed(title="내가 참여한 택시 모집", color=0x00ff00)
            embed.add_field(name="목적지", value=view.destination, inline=False)
            embed.add_field(name="출발 시간", value=format_time(view.time), inline=False)
            embed.add_field(name="모집자", value=view.author.mention if view.author else "Unknown", inline=False)
            embed.add_field(name="참가자", value='\n'.join([p.mention for p in view.participants]), inline=False)
            embeds.append(embed)

        await interaction.response.send_message(embeds=embeds, ephemeral=True)

    @app_commands.command(name="택시삭제", description="🍊 내가 만든 택시 모집을 삭제할게요!")
    async def delete_taxi(interaction: discord.Interaction):
        """사용자가 생성한 가장 최근의 택시 모집을 삭제합니다."""
        user_events = [event_id for event_id, view in bot.taxi_events.items() if view.author == interaction.user and not view.deleted]
        if not user_events:
            await interaction.response.send_message("삭제할 택시 모집을 찾을 수 없어요! 🍊", ephemeral=True)
            return

        # 가장 최근에 생성된 택시 모집을 찾습니다
        latest_event_id = max(user_events, key=lambda x: bot.taxi_events[x].created_at)
        view = bot.taxi_events[latest_event_id]
        
        view.deleted = True
        if view.thread is not None:
            mentions = ' '.join([p.mention for p in view.participants])
            await view.thread.send(f"{mentions}\n택시 모집이 삭제되었어요! 🍊")
        view.save_event()
        await interaction.response.send_message("가장 최근에 생성한 택시 모집이 삭제되었어요! 🍊", ephemeral=True)

    # 모든 명령어를 봇에 등록합니다
    bot.tree.add_command(taxi)
    bot.tree.add_command(view_taxi)
    bot.tree.add_command(view_my_taxi_participation)
    bot.tree.add_command(delete_taxi)

    await TaxiView.load_events(bot)

def load_taxi_events(bot):
    """파일에서 택시 모집 정보를 불러옵니다."""
    TaxiView.load_events(bot)

def save_taxi_events(bot):
    """파일에 택시 모집 정보를 저장합니다."""
    for view in bot.taxi_events.values():
        view.save_event()
