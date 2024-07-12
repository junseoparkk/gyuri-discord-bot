import discord
import requests
from datetime import datetime, timedelta

API_KEY = 'FiL6tauqEniSps61NiC2pZKKGE9w+sxqIAdHJ026CjcNhgGvcHSP1D84XcaoAj+tXUBp8segU7OcoFNsma+asQ=='
API_URL = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst'

def setup_weather_command(bot):
    @bot.tree.command(name='날씨')
    async def weather(interaction: discord.Interaction):
        """날씨 정보를 제공하는 명령어"""
        # await interaction.response.send_message('날씨 기능은 현재 준비중입니다.', ephemeral=False)
        await interaction.response.defer()  # 응답을 지연시켜 사용자에게 처리가 진행 중임을 알림

        # 현재 날짜와 시간을 가져옵니다.
        now = datetime.now()
        base_date = now.strftime('%Y%m%d')
        morning_time = '0500'
        base_time = (now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)).strftime('%H%M')
        # 요청할 지점 좌표를 설정합니다. 제주도 좌표를 [서류참조] 사용합니다.
        nx = '52'
        ny = '38'

        # API 요청을 보냅니다.
        params = {
            'serviceKey': API_KEY,
            'pageNo': 1,
            'numOfRows': 1000,
            'dataType': 'JSON',
            'base_date': base_date,
            'base_time': morning_time,
            'nx': nx,
            'ny': ny
        }

        response = requests.get(API_URL, params=params)
        data = response.json()
        # print(data)

        if data['response']['header']['resultCode'] != '00':
            await interaction.followup.send('날씨 정보를 가져오는 데 실패했습니다.', ephemeral=True)
            return

        items = data['response']['body']['items']['item']
        hourly_weather = {}
        rain_times = []

        for item in items:
            fcst_date = item['fcstDate']
            if fcst_date != base_date:
                continue  # base_date와 일치하지 않는 날짜의 데이터는 건너뜀
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
            alert_message = "☔️오늘 비/눈이 올 예정입니다! ☔️"
            rain_times_message = f"비/눈 오는 시간: {', '.join(rain_times)}시"
        else:
            alert_message = "😄️ 비가 오지 않습니다. 😄️   "
            rain_times_message = ""

        weather_message = (
            f"오늘의 날씨 정보:\n"
            f"🌡️ 평균 기온: {avg_temp:.2f}°C\n"
            f"☄️평균 습도: {avg_humidity:.2f}%\n"
            f"🌀️ 평균 풍속: {avg_wind_speed:.2f}m/s\n"
            f"{alert_message}\n"
            f"{rain_times_message}"
        )

        await interaction.followup.send(weather_message)


# 봇 객체를 전달하여 명령어를 설정하는 함수 호출

def setup_commands(bot):
    setup_weather_command(bot)