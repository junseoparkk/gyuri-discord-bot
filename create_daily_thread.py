import datetime
from enum import Enum

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import tasks

seoul_tz = datetime.timezone(datetime.timedelta(hours=9))
cronjob_dict: dict[int, tuple[tasks.Loop, tasks.Loop, tasks.Loop]] = {}
thread_dict: dict[int, discord.Thread] = {}
user_ids_dict: dict[int, list[int]] = {}


def get_current_time():
    return datetime.datetime.now(tz=seoul_tz)


def is_weekday():
    return datetime.datetime.now(tz=seoul_tz).weekday() < 5


class DailyOperation(Enum):
    START = 0
    STOP = 1


class DailyMemberOperation(Enum):
    ADD = 0
    DELETE = 1


async def setup_create_daily_thread(bot):
    async def create_cronjob(cronjob_name: str, channel: discord.TextChannel):
        @tasks.loop(
            name=cronjob_name,
            time=[
                datetime.time(hour=9, minute=0, second=0, tzinfo=seoul_tz),
            ]
        )
        async def breakfast():
            if not is_weekday():
                return

            print(f"breakfast - {channel.name}")

            breakfast_message = await channel.send(
                f"좋은 아침이에요!☀️ QR 잊지마세요! 🍊\n"
                f"{get_mention_message(channel)}\n",
                file=discord.File("./meme/qr.png", filename="qr.png")
            )
            breakfast_thread = await breakfast_message.create_thread(
                name=datetime.datetime.now().strftime("%y/%m/%d"),
            )
            thread_dict[channel.id] = breakfast_thread

        @tasks.loop(
            name=cronjob_name,
            time=[
                datetime.time(hour=13, minute=0, second=0, tzinfo=seoul_tz),
            ]
        )
        async def lunch():
            if channel.id not in thread_dict:
                print("lunch but no breakfast")
                return

            if not is_weekday():
                return

            print("lunch")

            await thread_dict[channel.id].send(
                content="점심 맛있게 드셨나요? QR도 잊지마세요! 🍊\n"
                        f"{get_mention_message(channel)}\n",
                file=discord.File("./meme/qr.png", filename="qr.png")
            )

        @tasks.loop(
            name=cronjob_name,
            time=[
                datetime.time(hour=18, minute=0, second=0, tzinfo=seoul_tz),
            ]
        )
        async def dinner():
            if channel.id not in thread_dict:
                print("dinner but no breakfast")
                return

            if not is_weekday():
                return

            print("dinner")
            await thread_dict[channel.id].send(
                content="오늘 하루도 고생많으셨어요!👋🏻\n 퇴실 QR도 잊지마세요! 🍊\n"
                        f"{get_mention_message(channel)}\n",
                file=discord.File("./meme/qr.png", filename="qr.png")
            )

        return breakfast, lunch, dinner

    async def start_daily(interaction: discord.Interaction, channel: discord.TextChannel):
        if channel.id in cronjob_dict:
            return await interaction.response.send_message(
                f"{channel.name}(은)는 이미 일일 스레드를 생성하고 있던 곳이에요. 🍊"
            )

        cronjob_tuple = await create_cronjob(f"daily_cronjob : {channel.id}", channel)
        for cronjob in cronjob_tuple:
            cronjob.start()
        cronjob_dict[channel.id] = cronjob_tuple

        await interaction.response.send_message(f"{channel.name} 에서 일일 스레드를 만들게요! 🍊")

    async def stop_daily(interaction: discord.Interaction, channel: discord.TextChannel = None):
        if not channel.id in cronjob_dict:
            return await interaction.response.send_message(
                f"{channel.name}(은)는 일일 스레드 목록에 없어요. 🍊"
            )

        cronjob_tuple = cronjob_dict[channel.id]
        for cronjob in cronjob_tuple:
            cronjob.cancel()
        del cronjob_dict[channel.id]

        await interaction.response.send_message(f"이제 {channel.name} 에서 더 이상 일일 스레드를 만들지 않아요! 🍊")

    async def add_members(members: list[discord.User], interaction: discord.Interaction):
        # 처음 추가하는 경우
        if interaction.channel.id not in user_ids_dict:
            user_ids_dict[interaction.channel.id] = [member.id for member in members]
        # 사람을 이전에 추가한 경우
        else:
            for member in members:
                if member.id not in user_ids_dict[interaction.channel.id]:
                    print(f"사람 추가 : {member.name}")
                    user_ids_dict[interaction.channel.id].append(member.id)
        await interaction.response.send_message(f"{','.join([member.mention for member in members])} 에게 알림을 드릴게요! 🍊")

    async def delete_members(members: list[discord.User], interaction: discord.Interaction):
        # 이미 일전에 추가한 경우
        if interaction.channel.id in user_ids_dict:
            for member in members:
                if member.id in user_ids_dict[interaction.channel.id]:
                    print(f"사람 삭제 : {member.name}")
                    user_ids_dict[interaction.channel.id].remove(member.id)
        await interaction.response.send_message(
            f"{','.join([member.mention for member in members])} 에게 더이상 알림 드리지 않아요! 🍊")

    def get_mention_message(channel: discord.TextChannel):
        if channel.id not in user_ids_dict:
            return ""
        return ",".join(mention_user(user_id) for user_id in user_ids_dict[channel.id])

    def mention_user(user_id: int):
        return f'<@{user_id}>'

    @bot.tree.command(name="데일리", description="🍊 규리가 데일리 스레드를 만들게요!")
    @app_commands.describe(start_or_stop="시작 or 정지", channel="텍스트 채널", )
    @app_commands.choices(start_or_stop=[
        app_commands.Choice(name="시작", value=DailyOperation.START.value),
        app_commands.Choice(name="정지", value=DailyOperation.STOP.value)
    ])
    async def daily(
            interaction: discord.Interaction,
            start_or_stop: Choice[int],
            channel: discord.TextChannel,
    ):
        if start_or_stop.value == DailyOperation.START.value:
            print(f"## {channel} 데일리 시작 req")
            await start_daily(interaction, channel)
        else:
            print(f"## {channel.name} 데일리 정지 req")
            await stop_daily(interaction, channel)

    @bot.tree.command(name="데일리_태그", description="🍊 알림에 맨션할 사람을 추가해요!")
    @app_commands.choices(add_or_delete=[
        app_commands.Choice(name="추가", value=DailyMemberOperation.ADD.value),
        app_commands.Choice(name="삭제", value=DailyMemberOperation.DELETE.value)
    ])
    async def add_user_to_daily(
            interaction: discord.Interaction,
            add_or_delete: Choice[int],
            user: discord.User,
            user1: discord.User = None,
            user2: discord.User = None,
            user3: discord.User = None,
            user4: discord.User = None,
    ):
        arg_users = [user, user1, user2, user3, user4]
        members = []
        for arg_user in arg_users:
            if arg_user is not None:
                members.append(arg_user)

        # 추가
        if add_or_delete.value == DailyMemberOperation.ADD.value:
            print("추가")
            await add_members(members, interaction)
        # 삭제
        else:
            print("삭제")
            await delete_members(members, interaction)
