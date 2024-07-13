import discord
from discord.ext import tasks
import requests
from datetime import datetime, timedelta
import os
import logging
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
API_URL = os.getenv('API_URL')
CHANNEL_ID = os.getenv('DISCORD_CID')

if CHANNEL_ID is None:
    raise ValueError("CHANNEL_ID is not set in the environment variables")

def get_weather_message():
    def fetch_weather_data(base_date, base_time, nx, ny):
        params = {
            'serviceKey': API_KEY,
            'pageNo': 1,
            'numOfRows': 1000,
            'dataType': 'JSON',
            'base_date': base_date,
            'base_time': base_time,
            'nx': nx,
            'ny': ny
        }

        response = requests.get(API_URL, params=params)
        data = response.json()
        return data

    def process_weather_data(data, target_date):
        if data['response']['header']['resultCode'] != '00':
            return None, []

        items = data['response']['body']['items']['item']
        hourly_weather = {}
        rain_times = []

        for item in items:
            fcst_date = item['fcstDate']
            if fcst_date != target_date:
                continue
            fcst_time = item['fcstTime']
            if fcst_time not in hourly_weather:
                hourly_weather[fcst_time] = {}
            hourly_weather[fcst_time][item['category']] = item['fcstValue']
            if item['category'] == 'PTY' and item['fcstValue'] != '0':
                rain_times.append(fcst_time)

        total_temp = 0
        total_humidity = 0
        total_wind_speed = 0
        count = 0

        for weather in hourly_weather.values():
            total_temp += float(weather.get('TMP', 0))
            total_humidity += float(weather.get('REH', 0))
            total_wind_speed += float(weather.get('WSD', 0))
            count += 1

        avg_temp = total_temp / count if count else 0
        avg_humidity = total_humidity / count if count else 0
        avg_wind_speed = total_wind_speed / count if count else 0

        if rain_times:
            alert_message = "☔️ 비/눈이 올 예정입니다! ☔️"
            rain_times_message = f"비/눈 오는 시간: {', '.join(rain_times)}시"
        else:
            alert_message = "😄️ 비가 오지 않습니다. 😄️   "
            rain_times_message = ""

        weather_message = (
            f"🌡️ 평균 기온: {avg_temp:.2f}°C\n"
            f"☄️ 평균 습도: {avg_humidity:.2f}%\n"
            f"🌀️ 평균 풍속: {avg_wind_speed:.2f}m/s\n"
            f"{alert_message}\n"
            f"{rain_times_message}"
        )

        return weather_message

    now = datetime.now()
    base_date = now.strftime('%Y%m%d')
    morning_time = '0500'
    nx = '52'
    ny = '38'

    # 제주도 날씨 Fetch
    data = fetch_weather_data(base_date, morning_time, nx, ny)

    # 당일 날씨 정보
    weather_today = process_weather_data(data, base_date)

    # 내일 날씨 정보
    next_day = (now + timedelta(days=1)).strftime('%Y%m%d')
    weather_next_day = process_weather_data(data, next_day)

    # 내일 모래 날씨 정보
    day_after_next = (now + timedelta(days=2)).strftime('%Y%m%d')
    weather_day_after_next = process_weather_data(data, day_after_next)

    weather_message = (
        f"오늘의 날씨 정보:\n{weather_today}\n\n"
        f"내일의 날씨 정보:\n{weather_next_day}\n\n"
        f"이틀 후 날씨 정보:\n{weather_day_after_next}"
    )

    return weather_message

class WeatherScheduler:
    def __init__(self, bot):
        self.bot = bot

    def start(self):
        self.daily_weather_update.start()

    @tasks.loop(seconds=60)
    async def daily_weather_update(self):
        now = datetime.now()
        if now.hour == 8 and now.minute == 0:
            try:
                channel = await self.bot.fetch_channel(int(CHANNEL_ID))
                if channel is None:
                    logging.error(f"Channel with ID {CHANNEL_ID} not found.")
                    return

                weather_message = get_weather_message()
                if weather_message:
                    await channel.send(weather_message)
                else:
                    logging.error("Failed to get weather message.")
            except Exception as e:
                logging.error(f"Error in daily_weather_update: {e}")


    @daily_weather_update.before_loop
    async def before_daily_weather_update(self):
        await self.bot.wait_until_ready()

def setup_weather_command(bot):
    @bot.tree.command(name='날씨')
    async def weather(interaction: discord.Interaction):
        """날씨 정보를 제공하는 명령어"""
        await interaction.response.defer()
        weather_message = get_weather_message()
        if weather_message:
            await interaction.followup.send(weather_message)
        else:
            await interaction.followup.send('날씨 정보를 가져오는 데 실패했습니다.', ephemeral=True)

    scheduler = WeatherScheduler(bot)
    bot.scheduler = scheduler

