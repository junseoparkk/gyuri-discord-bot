import discord
import aiohttp
import json
import asyncio
from discord import app_commands
from datetime import datetime, timedelta, time
import pytz  # 시간대를 처리하기 위해 추가

bus_icon = ":bus:"
korea_timezone = pytz.timezone('Asia/Seoul')  # 한국 시간대 설정

def generate_times(start_hour, start_minute, end_hour, end_minute, interval_minutes):
    times = []
    
    current_time = datetime.now(korea_timezone).replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    end_time = datetime.now(korea_timezone).replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
    
    while current_time <= end_time:
        times.append(current_time.time())
        current_time += timedelta(minutes=interval_minutes)
    
    return times

# 7시 30분부터 8시 30분까지 5분 간격으로 시간 생성
morning_times = generate_times(7, 30, 8, 30, 5)
print(morning_times)

# 21시 50분부터 22시 30분까지 5분 간격으로 시간 생성
evening_times = generate_times(21, 50, 22, 30, 5)
print(evening_times)

# 출발 정류장 목록
start_stations = [
    {'id': '405000405', 'name': '월성마을회관'},
    {'id': '405000662', 'name': '월성마을'},
]

# 출발 정류장별 버스 경로
bus_start_routes = {
    '405000405': [ # 월성마을회관
        {'routeId': '315', 'type': '환승', 'transfer': '제주버스터미널', 'arrive': '수선화아파트', 'totalTime': 30},
        {'routeId': '315', 'type': '환승', 'transfer': '남서광마을입구', 'arrive': '제주지방법원(아라방면)', 'totalTime': 40},
        {'routeId': '331', 'type': '환승', 'transfer': '제주버스터미널', 'arrive': '수선화아파트', 'totalTime': 30},
        {'routeId': '331', 'type': '환승', 'transfer': '제주시청(아라방면)', 'arrive': '이도초등학교', 'totalTime': 33},
        {'routeId': '331', 'type': '환승', 'transfer': '남서광마을입구', 'arrive': '제주지방법원(아라방면)', 'totalTime': 40},
    ],
    '405000662': [ # 월성마을
        {'routeId': '365', 'type': '직행', 'arrive': '제주지방법원(아라방면)', 'totalTime': 49},
        {'routeId': '370', 'type': '직행', 'arrive': '제주지방법원(아라방면)', 'totalTime': 49},
    ],
}

# 도착 정류장 목록
end_stations = [
    {'id': '405000108', 'name': '수선화아파트'},
    {'id': '405001973', 'name': '이도초등학교'}
]

# 도착 정류장별 버스 경로
bus_end_routes = {
    '405000108': [ # 수선화아파트
        {'routeId': '436', 'type': '환승', 'transfer': '한국병원', 'arrive': '월성마을회관', 'totalTime': 30},
        {'routeId': '436', 'type': '환승', 'transfer': '제주버스터미널', 'arrive': '월성마을회관', 'totalTime': 30},
        {'routeId': '356', 'type': '환승', 'transfer': '제주도청 신제주로터리', 'arrive': '월성마을회관', 'totalTime': 35},        
        {'routeId': '357', 'type': '환승', 'transfer': '제주도청 신제주로터리', 'arrive': '월성마을회관', 'totalTime': 35},        
        {'routeId': '436', 'type': '환승', 'transfer': '제주버스터미널', 'arrive': '명신마을', 'totalTime': 32},
    ],
    '405001973': [ # 이도초등학교
        {'routeId': '431', 'type': '환승', 'transfer': '제주버스터미널', 'arrive': '월성마을회관', 'totalTime': 33},
    ],
}

# 정류장의 버스 도착 정보를 가져오는 함수
async def fetch_bus_arrival_info(station_id):
    url = f"http://bus.jeju.go.kr/api/searchArrivalInfoList.do?station_id={station_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                try:
                    data = json.loads(text)
                    bus_list = []
                    for item in data:
                        predictTravTm = int(item['PREDICT_TRAV_TM'])
                        routeId = item['ROUTE_NUM']
                        if any(route['routeId'] == routeId for route in bus_start_routes.get(station_id, [])) or any(route['routeId'] == routeId for route in bus_end_routes.get(station_id, [])):
                            leftStation = item['REMAIN_STATION'] if 'REMAIN_STATION' in item else "정보 없음"
                            arrival_time = (datetime.now(korea_timezone) + timedelta(minutes=predictTravTm)).strftime('%H:%M')
                            bus_list.append((predictTravTm, routeId, arrival_time, leftStation))
                    return sorted(bus_list, key=lambda x: x[0])
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error: {e}")
                    return []
            else:
                print(f"API request failed with status: {response.status}")
                return []

# 환승 버스 정보를 가져오는 함수
async def fetch_transfer_bus_info(station_id, routeNum):
    url = f"http://bus.jeju.go.kr/api/searchArrivalInfoList.do?station_id={station_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                try:
                    data = json.loads(text)
                    for item in data:
                        if item['ROUTE_NUM'] == routeNum:
                            predictTravTm = int(item['PREDICT_TRAV_TM'])
                            arrival_time = (datetime.now(korea_timezone) + timedelta(minutes=predictTravTm)).strftime('%H:%M')
                            return predictTravTm, arrival_time
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error (Transfer): {e}")
                    return None, None
            else:
                print(f"Transfer API request failed with status: {response.status}")
                return None, None

# 특정 경로 정보를 가져오는 함수
async def fetch_route_info(routeId, station_id, route_type):
    if route_type == 'start':
        return [route for route in bus_start_routes.get(station_id, []) if route['routeId'] == routeId]
    elif route_type == 'end':
        return [route for route in bus_end_routes.get(station_id, []) if route['routeId'] == routeId]
    return []

# 메시지를 생성하는 함수
async def generate_message(stations, route_type):
    current_time_str = datetime.now(korea_timezone).strftime('%Y/%m/%d %H:%M')
    message = ""
    
    buses_within_10_minutes = 0
    buses_within_30_minutes = 0
    bus_info_present = False
    
    all_bus_info = []

    for station in stations:
        station_id = station['id']
        station_name = station['name']
        bus_info = await fetch_bus_arrival_info(station_id)
        
        if bus_info:
            bus_info_present = True
        
        for predictTravTm, routeId, arrival_time, leftStation in bus_info:
            if predictTravTm <= 10:
                buses_within_10_minutes += 1
            if predictTravTm <= 30:
                buses_within_30_minutes += 1

            route_info_list = await fetch_route_info(routeId, station_id, route_type)
            for route_info in route_info_list:
                all_bus_info.append((predictTravTm, routeId, arrival_time, leftStation, route_info, station_name))

    all_bus_info.sort(key=lambda x: x[0])

    for predictTravTm, routeId, arrival_time, leftStation, route_info, station_name in all_bus_info:
        if route_info['type'] == '직행':
            if predictTravTm == 0:
                message += f"{bus_icon} **{routeId}번 (직행) {route_info['totalTime']}분 소요**\n"
                message += f"**`곧 도착` {station_name} ({arrival_time}) / {leftStation} 정류장 전**\n"
            else:
                message += f"{bus_icon} **{routeId}번 (직행) {route_info['totalTime']}분 소요**\n"
                message += f"**`{predictTravTm}분뒤` {station_name} 도착 ({arrival_time}) / {leftStation} 정류장 전**\n"
            message += f"({station_name}-{route_info['arrive']})\n\n"
        elif route_info['type'] == '환승':
            transfer = route_info['transfer']
            if predictTravTm == 0:
                message += f"{bus_icon} **{routeId}번 (환승) {route_info['totalTime']}분 소요**\n"
                message += f"**`곧 도착` {station_name} ({arrival_time}) / {leftStation} 정류장 전**\n"
            else:
                message += f"{bus_icon} **{routeId}번 (환승) {route_info['totalTime']}분 소요**\n"
                message += f"**`{predictTravTm}분뒤` {station_name} 도착 ({arrival_time}) / {leftStation} 정류장 전**\n"
            message += f"({station_name}-{transfer}-{route_info['arrive']})\n\n"

    if buses_within_10_minutes > 0:
        message = f"🌿 **서두르세요! 10분 내 버스 {buses_within_10_minutes}개 도착 예정** 🌿\n🕒 **현재시각** {current_time_str} \n\n" + message
    elif buses_within_30_minutes == 0:
        message = f"🌿 **천천히 준비하세요. 30분 내 버스 없음** 🌿\n🕒 **현재시각** {current_time_str} \n\n" + message
    elif not bus_info_present:
        message = f"🌿 **버스 없음..ㅠㅠ** 🌿\n🕒 **현재시각** {current_time_str} \n\n" + message
    else :
        message = f"🌿 **곧 버스가 도착할거예요!** 🌿\n🕒 **현재시각** {current_time_str} \n\n" + message
    
    if bus_info_present:
        message += f"🍊 **어서 버스에 탑승하세요!** 🍊\n\n"
    else:
        message += f"🍊 **죄송합니다.. 버스가 없네요** 🍊\n\n"
    
    return message

# 버스를 모니터링하는 함수
async def monitor_buses(channel):
    while True:
        current_time = datetime.now(korea_timezone).time()
        current_hour_minute = time(current_time.hour, current_time.minute)
        
        if any(current_hour_minute == t for t in morning_times):
            stations = start_stations
            route_type = 'start'
        elif any(current_hour_minute == t for t in evening_times):
            stations = end_stations
            route_type = 'end'
        else:
            await asyncio.sleep(60)  # 1분마다 확인
            continue

        message = await generate_message(stations, route_type)
        await channel.send(message)
        
        # 아침의 마지막 시간 이후 메시지
        if current_hour_minute == morning_times[-1]:
            await channel.send("😘 **오늘 아침 버스 방송을 종료합니다. 모두 힘찬 하루 보내세요!** 🍀")

        # 저녁의 마지막 시간 이후 메시지
        if current_hour_minute == evening_times[-1]:
            await channel.send("😘 **모두들 숙소에 잘 들어가셨나요? 내일 또 만나요!** 🍀")

        await asyncio.sleep(60)

# 디스코드 봇 명령어 설정
def setup_bus_command(bot):
    @bot.tree.command(name='버스교육장')
    async def bus_sookso(interaction: discord.Interaction):
        """🚌 교육장으로 향하는 실시간 숙소 근처 버스 정보를 알려드립니다."""
        message = await generate_message(start_stations, 'start')
        await interaction.response.send_message(message, ephemeral=False)

    @bot.tree.command(name='버스숙소')
    async def bus_gyoyukjang(interaction: discord.Interaction):
        """🚌 숙소로 향하는 실시간 교육장 근처 버스 정보를 알려드립니다."""
        message = await generate_message(end_stations, 'end')
        await interaction.response.send_message(message, ephemeral=False)
