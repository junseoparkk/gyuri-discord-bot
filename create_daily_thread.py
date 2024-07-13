import asyncio
import datetime
from enum import Enum

from typing import Dict, Any

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import tasks

seoul_tz = datetime.timezone(datetime.timedelta(hours=9))
cronjob_dict: dict[int, tuple[tasks.Loop, tasks.Loop, tasks.Loop]] = {}
thread_dict: dict[int, discord.Thread] = {}


class DailyOperation(Enum):
    START = 0
    STOP = 1


async def setup_create_daily_thread(bot):
    async def create_cronjob(cronjob_name: str, channel: discord.TextChannel):
        @tasks.loop(
            name=cronjob_name,
            seconds=29,
            # time=[
            #     datetime.time(hour=9, minute=0, second=0, tzinfo=seoul_tz),
            # ]
        )
        async def breakfast():
            print("breakfast")

            breakfast_message = await channel.send(
                f"좋은 아침! {channel.name}"
                f"\n [출석체크 QR](https://goorm.notion.site/e9d381e31aa641499c40c72891d28a30?v=6aab6156142d4164a98b301c52763863)"
            )
            breakfast_thread = await breakfast_message.create_thread(
                name=datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S"),
            )
            thread_dict[channel.id] = breakfast_thread

        @tasks.loop(
            name=cronjob_name,
            seconds=30,
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
                content="time to lunch\n [출석체크 QR](https://goorm.notion.site/e9d381e31aa641499c40c72891d28a30?v=6aab6156142d4164a98b301c52763863)"
            )

        @tasks.loop(
            name=cronjob_name,
            seconds=31,
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
                content="time to dinner\n [출석체크 QR](https://goorm.notion.site/e9d381e31aa641499c40c72891d28a30?v=6aab6156142d4164a98b301c52763863)"
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
    @app_commands.describe(channel="데일리 받을 채널", start_or_stop="시작 or 정지")
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
