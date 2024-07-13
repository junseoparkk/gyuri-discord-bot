import discord
import aiohttp
import json
import asyncio
from discord import app_commands
from datetime import datetime, timedelta

# 숙소
start_stations = [
    {'id': '405000405', 'name': '**(숙소 - 교육장) 월성마을회관 정류장**'},
    {'id': '405000401', 'name': '**(숙소 - 교육장) 월성마을회관2 정류장**'}
]
bus_start_routes = {
    '405000405': {
        '466': { 'type': '환승', 'transfer': {'routeNum': '500', 'stationNm': '환승 정류장'}, 'totalTime': 60 },
        '315': { 'type': '직행', 'totalTime': 40 },
        '331': { 'type': '직행', 'totalTime': 45 }
    },
    '405000401': {
        '466': { 'type': '환승', 'transfer': {'routeNum': '500', 'stationNm': '환승 정류장'}, 'totalTime': 60 },
        '315': { 'type': '직행', 'totalTime': 40 },
        '331': { 'type': '직행', 'totalTime': 45 }
    },
}

# 교육장
end_stations = [
    {'id': '405000153', 'name': '**(교육장 - 숙소) 수선화아파트 정류장**'}
]
bus_end_routes = {
    '405000153': {
        '332': { 'type': '환승', 'transfer': {'routeNum': '500', 'stationNm': '환승 정류장'}, 'totalTime': 60 },
        '432': { 'type': '직행', 'totalTime': 40 },
        '336': { 'type': '직행', 'totalTime': 45 }
    }
}

async def fetch_bus_arrival_info(station_id):
    url = f"http://bus.jeju.go.kr/api/searchArrivalInfoList.do?station_id={station_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                print(f"API Response for station {station_id}: {text}")
                try:
                    data = json.loads(text)
                    bus_list = []
                    for item in data:
                        predictTravTm = int(item['PREDICT_TRAV_TM'])
                        routeId = item['ROUTE_NUM']
                        if routeId in bus_start_routes.get(station_id, {}) or routeId in bus_end_routes.get(station_id, {}):  # 관심 있는 버스만 필터링
                            leftStation = item['REMAIN_STATION'] if 'REMAIN_STATION' in item else "정보 없음"
                            arrival_time = (datetime.now() + timedelta(minutes=predictTravTm)).strftime('%H:%M')
                            bus_list.append((predictTravTm, routeId, arrival_time, leftStation))
                    return bus_list
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error: {e}")
                    return []
            else:
                print(f"API request failed with status: {response.status}")
                return []

async def fetch_route_info(routeId, station_id, route_type):
    # 버스 경로 정보를 반환하는 부분입니다.
    if route_type == 'start':
        return bus_start_routes.get(station_id, {}).get(routeId, {})
    elif route_type == 'end':
        return bus_end_routes.get(station_id, {}).get(routeId, {})
    return {}

async def monitor_buses(channel):
    bus_icon = ":bus:"
    while True:
        current_time_str = datetime.now().strftime('%H:%M')
        if '07:30' <= current_time_str <= '13:30':
            stations = start_stations
            route_type = 'start'
            direction_message = "07:30-08:30 5분마다 교육장으로 가는"
        elif '21:00' <= current_time_str <= '23:00':
            stations = end_stations
            route_type = 'end'
            direction_message = "21:00-23:00 5분마다 숙소로 향하는"
        else:
            await asyncio.sleep(300)
            continue

        message = "🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿\n"
        for station in stations:
            station_id = station['id']
            station_name = station['name']
            bus_info = await fetch_bus_arrival_info(station_id)
            
            current_time = datetime.now().strftime('%H:%M')
            message += f"🍊 {station_name} 버스 정보 {current_time} 🍊\n\n"
            if not bus_info:
                message += f"🌿 **도착 예정 버스가 없습니다 ㅠㅠ** 🌿\n\n"
            else:
                message += f"🌿 **버스가 곧 도착합니다!** 🌿\n\n"
                for predictTravTm, routeId, arrival_time, leftStation in bus_info:
                    if routeId in bus_start_routes.get(station_id, {}) or routeId in bus_end_routes.get(station_id, {}):
                        message += f"{bus_icon} **{routeId}번 버스** - {predictTravTm}분 뒤 도착 \n\t\t도착 시각 **{arrival_time}** \n\t\t{leftStation} 정류장 전\n"
                        route_info = await fetch_route_info(routeId, station_id, route_type)
                        if route_info:
                            if route_info.get('type') == '직행':
                                message += f"\t\t🚏 (직행) 소요시간 : {route_info['totalTime']}분\n\n"
                            elif route_info.get('type') == '환승':
                                transfer = route_info['transfer']
                                message += f"\t\t🚏 (환승 - {transfer['routeNum']}번 {transfer['stationNm']}) 소요시간 : {route_info['totalTime']}분\n\n"
            
        message += "🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿\n"
        message += f"규리가 매일 {direction_message} 버스 정보를 알려드립니다! 🍊\n"    
        await channel.send(message)

        await asyncio.sleep(300)  # 5분마다 실행

def setup_bus_command(bot):
    @app_commands.command(name="버스숙소", description=":bus: 교육장-숙소 실시간 버스 정보를 알려드려요.")
    async def bus_sookso(interaction: discord.Interaction):
        station_id = start_stations[0]['id']
        station_name = start_stations[0]['name']
        bus_info = await fetch_bus_arrival_info(station_id)
        
        message = "🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿\n"
        current_time = datetime.now().strftime('%H:%M')
        message += f"🍊 {station_name} 버스 정보 {current_time} 🍊\n\n"
        if not bus_info:
            message += f"🌿 **도착 예정 버스가 없습니다 ㅠㅠ** 🌿\n\n"
        else:
            bus_icon = ":bus:"
            message += f"🌿 **버스가 곧 도착합니다!** 🌿\n\n"
            for predictTravTm, routeId, arrival_time, leftStation in bus_info:
                if routeId in bus_start_routes.get(station_id, {}):
                    message += f"{bus_icon} **{routeId}번 버스** - {predictTravTm}분 뒤 도착 \n\t\t도착 시각 **{arrival_time}** \n\t\t{leftStation} 정류장 전\n"
                    route_info = await fetch_route_info(routeId, station_id, 'start')
                    if route_info:
                        if route_info.get('type') == '직행':
                            message += f"\t\t🚏 (직행) 소요시간 : {route_info['totalTime']}분\n\n"
                        elif route_info.get('type') == '환승':
                            transfer = route_info['transfer']
                            message += f"\t\t🚏 (환승 - {transfer['routeNum']}번 {transfer['stationNm']}) 소요시간 : {route_info['totalTime']}분\n\n"
            
        message += "🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿\n"
        message += f"규리가 매일 07:30-08:30 5분마다 교육장으로 가는 버스 정보를 알려드립니다! 🍊\n"    
        await interaction.response.send_message(message, ephemeral=False)

    @app_commands.command(name="버스교육장", description=":bus: 숙소-교육장 실시간 버스 정보를 알려드립니다.")
    async def bus_gyoyukjang(interaction: discord.Interaction):
        station_id = end_stations[0]['id']
        station_name = end_stations[0]['name']
        bus_info = await fetch_bus_arrival_info(station_id)
        
        message = "🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿\n"
        current_time = datetime.now().strftime('%H:%M')
        message += f"🍊 {station_name} 버스 정보 {current_time} 🍊\n\n"
        if not bus_info:
            message += f"🌿 **도착 예정 버스가 없습니다 ㅠㅠ** 🌿\n\n"
            await interaction.response.send_message(message, ephemeral=False)
        else:
            bus_icon = ":bus:"
            message += f"🌿 **버스가 곧 도착합니다!** 🌿\n\n"
            for predictTravTm, routeId, arrival_time, leftStation in bus_info:
                if routeId in bus_end_routes.get(station_id, {}):
                    message += f"{bus_icon} **{routeId}번 버스** - {predictTravTm}분 뒤 도착 \n\t\t도착 시각 **{arrival_time}** \n\t\t{leftStation} 정류장 전\n"
                    route_info = await fetch_route_info(routeId, station_id, 'end')
                    if route_info:
                        if route_info.get('type') == '직행':
                            message += f"\t\t🚏 (직행) 소요시간 : {route_info['totalTime']}분\n\n"
                        elif route_info.get('type') == '환승':
                            transfer = route_info['transfer']
                            message += f"\t\t🚏 (환승 - {transfer['routeNum']}번 {transfer['stationNm']}) 소요시간 : {route_info['totalTime']}분\n\n"
        
        message += "🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿\n"
        message += f"규리가 매일 21:00-23:00 5분마다 숙소로 향하는 버스 정보를 알려드립니다! 🍊\n"    
        await interaction.response.send_message(message, ephemeral=False)
