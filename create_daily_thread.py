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
            minutes=20,
            seconds=0
            # time=[
            #     datetime.time(hour=9, minute=0, second=0, tzinfo=seoul_tz),
            # ]
        )
        async def breakfast():
            print("breakfast")

            breakfast_message = await channel.send(
                f"좋은 아침! {channel.name}\n"
                f"{get_mention_message(channel)}\n"
                f"[출석체크 QR](https://goorm.notion.site/e9d381e31aa641499c40c72891d28a30?v=6aab6156142d4164a98b301c52763863)"
            )
            breakfast_thread = await breakfast_message.create_thread(
                name=datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S"),
            )
            thread_dict[channel.id] = breakfast_thread

        @tasks.loop(
            name=cronjob_name,
            minutes=20,
            seconds=1
            # time=[
            #     datetime.time(hour=13, minute=0, second=0, tzinfo=seoul_tz),
            # ]
        )
        async def lunch():

            if channel.id not in thread_dict:
                print("lunch but no breakfast")
                return

            print("lunch")
            await thread_dict[channel.id].send(
                content="time to lunch\n"
                        "[출석체크 QR](https://goorm.notion.site/e9d381e31aa641499c40c72891d28a30?v=6aab6156142d4164a98b301c52763863)"
            )

        @tasks.loop(
            name=cronjob_name,
            minutes=20,
            seconds=2
            # time=[
            #     datetime.time(hour=18, minute=0, second=0, tzinfo=seoul_tz),
            # ]
        )
        async def dinner():
            if channel.id not in thread_dict:
                print("dinner but no breakfast")
                return

            print("dinner")
            await thread_dict[channel.id].send(
                content="time to dinner\n"
                        "[출석체크 QR](https://goorm.notion.site/e9d381e31aa641499c40c72891d28a30?v=6aab6156142d4164a98b301c52763863)"
            )

        return breakfast, lunch, dinner

    async def start_daily(interaction: discord.Interaction, channel: discord.TextChannel):
        if channel.id in cronjob_dict:
            return await interaction.response.send_message(
                f"{interaction.channel.name} 데일리 시작할 수 없습니다.\n 이미 존재하는 데일리입니다."
            )

        cronjob_tuple = await create_cronjob(f"daily_cronjob : {channel.id}", channel)
        for cronjob in cronjob_tuple:
            cronjob.start()
        cronjob_dict[channel.id] = cronjob_tuple

        await interaction.response.send_message(f"{channel.name} 데일리 시작")

    async def stop_daily(interaction: discord.Interaction, channel: discord.TextChannel = None):
        if not channel.id in cronjob_dict:
            return await interaction.response.send_message(
                f"{channel.name} 데일리 정지할 수 없습니다.\n 존재하지 않는 데일리입니다."
            )

        cronjob_tuple = cronjob_dict[channel.id]
        for cronjob in cronjob_tuple:
            cronjob.cancel()
        del cronjob_dict[channel.id]

        await interaction.response.send_message(f"{channel.name} 데일리 정지")

    @bot.tree.command(name="데일리", description="데일리 시작")
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
            print(f"{channel} 시작 req")
            await start_daily(interaction, channel)
        else:
            print(f"{channel.name} 정지 req")
            await stop_daily(interaction, channel)

    @bot.tree.command(name="데일리_태그", description="데일리 태그 사람 추가")
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
        await interaction.response.send_message(f"추가되었습니다 :{[member.mention for member in members]}")

    async def delete_members(members: list[discord.User], interaction: discord.Interaction):
        # 처음 추가하는 경우
        if interaction.channel.id not in user_ids_dict:
            return
        # 사람을 이전에 추가한 경우
        else:
            for member in members:
                if member.id in user_ids_dict[interaction.channel.id]:
                    print(f"사람 삭제 : {member.name}")
                    user_ids_dict[interaction.channel.id].remove(member.id)
        await interaction.response.send_message(f"삭제되었습니다 :{','.join([member.mention for member in members])}")

    def get_mention_message(channel: discord.TextChannel):
        if channel.id not in user_ids_dict:
            return ""
        return ",".join(mention_user(user_id) for user_id in user_ids_dict[channel.id])

    def mention_user(user_id: int):
        return f'<@{user_id}>'
