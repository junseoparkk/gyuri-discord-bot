import discord
import aiohttp
import json
import asyncio
from discord import app_commands
from datetime import datetime, timedelta

bus_icon = ":bus:"

# 숙소
start_stations = [
    {'id': '405000405', 'name': '**(숙소 - 교육장) 월성마을회관 정류장**'},
    {'id': '405000176', 'name': '**(숙소 - 교육장) 월구마을 정류장**'},
    {'id': '405000662', 'name': '**(숙소 - 교육장) 월성마을 정류장**'},
]

bus_start_routes = {
    '405000405': [
        { 'routeId': '466', 'type': '환승', 'transfer': {'routeNum': '315', 'stationNm': '남서광마을입구 정류장', 'possible_routes': ['316', '317', '318']}, 'start_walk': 12, 'bus_ride': 20, 'end_walk': 18, 'totalTime': 50 },
        { 'routeId': '315', 'type': '직행', 'arrive': '제주지방법원(아라방면) 정류장', 'start_walk': 12, 'end_walk': 18, 'bus_ride': 40, 'totalTime': 70 },
        { 'routeId': '360', 'type': '직행', 'arrive': '제주지방법원(아라방면) 정류장', 'start_walk': 12, 'end_walk': 18, 'bus_ride': 12, 'totalTime': 42 },
    ],
    '405000176': [
        { 'routeId': '360', 'type': '직행', 'arrive': '제주지방법원(아라방면) 정류장', 'start_walk': 9, 'end_walk': 18, 'bus_ride': 12, 'totalTime': 39 },
        { 'routeId': '335', 'type': '직행', 'arrive': '제주지방법원(아라방면) 정류장', 'start_walk': 9, 'end_walk': 18, 'bus_ride': 12, 'totalTime': 39 },
        { 'routeId': '358', 'type': '직행', 'arrive': '제주지방법원(아라방면) 정류장', 'start_walk': 9, 'end_walk': 18, 'bus_ride': 12, 'totalTime': 39 },
    ],
    '405000662': [
        { 'routeId': '365', 'type': '직행', 'arrive': '제주지방법원(아라방면) 정류장', 'start_walk': 9, 'end_walk': 18, 'bus_ride': 12, 'totalTime': 39 },
        { 'routeId': '370', 'type': '직행', 'arrive': '제주지방법원(아라방면) 정류장', 'start_walk': 9, 'end_walk': 18, 'bus_ride': 12, 'totalTime': 39 },
        { 'routeId': '455', 'type': '직행', 'arrive': '제주지방법원(아라방면) 정류장', 'start_walk': 9, 'end_walk': 18, 'bus_ride': 12, 'totalTime': 39 },
    ],
}

# 교육장
end_stations = [
    {'id': '405000153', 'name': '**(교육장 - 숙소) 수선화아파트 정류장**'}
]
bus_end_routes = {
    '405000153': [
        { 'routeId': '332', 'type': '환승', 'transfer': {'routeNum': '500', 'stationNm': '환승 정류장', 'possible_routes': ['501', '502', '503']}, 'start_walk': 12, 'bus_ride': 20, 'end_walk': 18, 'totalTime': 50 },
        { 'routeId': '432', 'type': '직행', 'start_walk': 12, 'bus_ride': 40, 'end_walk': 18, 'totalTime': 70 },
        { 'routeId': '336', 'type': '직행', 'start_walk': 12, 'bus_ride': 45, 'end_walk': 18, 'totalTime': 75 },
    ]
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
                        if any(route['routeId'] == routeId for route in bus_start_routes.get(station_id, [])) or any(route['routeId'] == routeId for route in bus_end_routes.get(station_id, [])):  # 관심 있는 버스만 필터링
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

async def fetch_transfer_bus_info(station_id, routeNum):
    url = f"http://bus.jeju.go.kr/api/searchArrivalInfoList.do?station_id={station_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                print(f"Transfer API Response for station {station_id}: {text}")
                try:
                    data = json.loads(text)
                    for item in data:
                        if item['ROUTE_NUM'] == routeNum:
                            predictTravTm = int(item['PREDICT_TRAV_TM'])
                            arrival_time = (datetime.now() + timedelta(minutes=predictTravTm)).strftime('%H:%M')
                            return predictTravTm, arrival_time
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error (Transfer): {e}")
                    return None, None
            else:
                print(f"Transfer API request failed with status: {response.status}")
                return None, None

async def fetch_route_info(routeId, station_id, route_type):
    # 버스 경로 정보를 반환하는 부분입니다.
    if route_type == 'start':
        return [route for route in bus_start_routes.get(station_id, []) if route['routeId'] == routeId]
    elif route_type == 'end':
        return [route for route in bus_end_routes.get(station_id, []) if route['routeId'] == routeId]
    return []

async def monitor_buses(channel):
    while True:
        current_time_str = datetime.now().strftime('%H:%M')
        if '07:30' <= current_time_str <= '21:00':
            stations = start_stations
            route_type = 'start'
            direction_message = "07:30-21:00 5분마다 교육장으로 가는"
        elif '21:30' <= current_time_str <= '23:00':
            stations = end_stations
            route_type = 'end'
            direction_message = "21:30-23:00 5분마다 숙소로 향하는"
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
                    route_info_list = await fetch_route_info(routeId, station_id, route_type)
                    for route_info in route_info_list:
                        if route_info['type'] == '직행':
                            message += f"{bus_icon} **{routeId}번 버스** - {predictTravTm}분 뒤 도착 **(직행)** {bus_icon}\n\t\t{leftStation} 정류장 전 / 도착 시각 **{arrival_time}**\n"
                            message += f"\t\t소요시간 : {route_info['totalTime']}분\n\t\t(숙소-정류장) {route_info['start_walk']}분 걷기\n\t\t(버스) {route_info['bus_ride']}분\n\t\t(정류장-교육장) {route_info['end_walk']}분 걷기\n\n"
                        elif route_info['type'] == '환승':
                            transfer = route_info['transfer']
                            transfer_predictTravTm, transfer_arrival_time = await fetch_transfer_bus_info(station_id, transfer['routeNum'])
                            possible_routes = ", ".join(transfer['possible_routes'])
                            message += f"{bus_icon} **{routeId}번 버스** - {predictTravTm}분 뒤 도착 **(환승)** {bus_icon}\n\t\t{leftStation} 정류장 전 / 도착 시각 **{arrival_time}**\n"
                            message += f"\t\t**환승정보** : {transfer['stationNm']} {transfer['routeNum']}번 {transfer_predictTravTm}분 뒤 도착 ({possible_routes}도 가능)\n"
                            message += f"\t\t**소요시간** : {route_info['totalTime']}분\n\t\t(숙소-정류장) {route_info['start_walk']}분 걷기\n\t\t(버스) {route_info['bus_ride']}분\n\t\t(환승) {transfer['stationNm']}\n\t\t(버스) {transfer['routeNum']} {route_info['bus_ride']}분\n\t\t(정류장-교육장) {route_info['end_walk']}분 걷기\n\n"
            
        message += "🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿\n"
        message += f"규리가 매일 {direction_message} 버스 정보를 알려드립니다! 🍊\n"    
        await channel.send(message)

        await asyncio.sleep(300)  # 5분마다 실행

def setup_bus_command(bot):
    @bot.tree.command(name='버스숙소')

    async def bus_sookso(interaction: discord.Interaction):
        """교육장으로 향하는 실시간 숙소 근처 버스 정보를 알려드립니다."""
        station_id = start_stations[0]['id']
        station_name = start_stations[0]['name']
        bus_info = await fetch_bus_arrival_info(station_id)
        
        message = "🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿\n"
        current_time = datetime.now().strftime('%H:%M')
        message += f"🍊 {station_name} 버스 정보 {current_time} 🍊\n\n"
        if not bus_info:
            message += f"🌿**도착 예정 버스가 없습니다 ㅠㅠ** 🌿\n\n"
        else:
            message += f"🌿**버스가 곧 도착합니다!** 🌿\n\n"
            for predictTravTm, routeId, arrival_time, leftStation in bus_info:
                route_info_list = await fetch_route_info(routeId, station_id, 'start')
                for route_info in route_info_list:
                    if route_info['type'] == '직행':
                        message += f"{bus_icon} **{routeId}번 버스** - {predictTravTm}분 뒤 도착 **(직행)** {bus_icon}\n\t\t{leftStation} 정류장 전 / 도착 시각 **{arrival_time}**\n"
                        message += f"\t\t소요시간 : {route_info['totalTime']}분\n\t\t(숙소-정류장) {route_info['start_walk']}분 걷기\n\t\t(버스) {route_info['bus_ride']}분\n\t\t(정류장-교육장) {route_info['end_walk']}분 걷기\n\n"
                    elif route_info['type'] == '환승':
                        transfer = route_info['transfer']
                        transfer_predictTravTm, transfer_arrival_time = await fetch_transfer_bus_info(station_id, transfer['routeNum'])
                        possible_routes = ", ".join(transfer['possible_routes'])
                        message += f"{bus_icon} **{routeId}번 버스** - {predictTravTm}분 뒤 도착 **(환승)** {bus_icon}\n\t\t{leftStation} 정류장 전 / 도착 시각 **{arrival_time}**\n"
                        message += f"\t\t**환승정보** : {transfer['stationNm']} {transfer['routeNum']}번 {transfer_predictTravTm}분 뒤 도착 ({possible_routes}도 가능)\n"
                        message += f"\t\t**소요시간** : {route_info['totalTime']}분\n\t\t(숙소-정류장) {route_info['start_walk']}분 걷기\n\t\t(버스 {routeId}) {route_info['bus_ride']}분\n\t\t(환승) {transfer['stationNm']}\n\t\t(버스 {transfer['routeNum']}) {route_info['bus_ride']}분\n\t\t(정류장-교육장) {route_info['end_walk']}분 걷기\n\n"
            
        await interaction.response.send_message(message, ephemeral=False)

    @bot.tree.command(name='버스교육장')
    async def bus_gyoyukjang(interaction: discord.Interaction):
        """숙소로 향하는 실시간 교육장 근처 버스 정보를 알려드립니다."""
        station_id = end_stations[0]['id']
        station_name = end_stations[0]['name']
        bus_info = await fetch_bus_arrival_info(station_id)
        
        message = "🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿\n"
        current_time = datetime.now().strftime('%H:%M')
        message = f"🍊 {station_name} 버스 정보 {current_time} 🍊\n\n"
        if not bus_info:
            message += f"🌿 **도착 예정 버스가 없습니다 ㅠㅠ** 🌿\n\n"
            await interaction.response.send_message(message, ephemeral=False)
        else:             
            message += f"🌿 **버스가 곧 도착합니다!** 🌿\n\n"
            for predictTravTm, routeId, arrival_time, leftStation in bus_info:
                route_info_list = await fetch_route_info(routeId, station_id, 'end')
                for route_info in route_info_list:
                    if route_info['type'] == '직행':
                        message += f"{bus_icon} **{routeId}번 버스** - {predictTravTm}분 뒤 도착 **(직행)** {bus_icon}\n\t\t{leftStation} 정류장 전 / 도착 시각 **{arrival_time}**\n"
                        message += f"\t\t소요시간 : {route_info['totalTime']}분\n\t\t(숙소-정류장) {route_info['start_walk']}분 걷기\n\t\t(버스) {route_info['bus_ride']}분\n\t\t(정류장-교육장) {route_info['end_walk']}분 걷기\n\n"
                    elif route_info['type'] == '환승':
                        transfer = route_info['transfer']
                        transfer_predictTravTm, transfer_arrival_time = await fetch_transfer_bus_info(station_id, transfer['routeNum'])
                        possible_routes = ", ".join(transfer['possible_routes'])
                        message += f"{bus_icon} **{routeId}번 버스** - {predictTravTm}분 뒤 도착 **(환승)** {bus_icon}\n\t\t{leftStation} 정류장 전 / 도착 시각 **{arrival_time}**\n"
                        message += f"\t\t**환승정보** : {transfer['stationNm']} {transfer['routeNum']}번 {transfer_predictTravTm}분 뒤 도착 ({possible_routes}도 가능)\n"
                        message += f"\t\t**소요시간** : {route_info['totalTime']}분\n\t\t(숙소-정류장) {route_info['start_walk']}분 걷기\n\t\t(버스 {routeId}) {route_info['bus_ride']}분\n\t\t(환승) {transfer['stationNm']}\n\t\t(버스 {transfer['routeNum']}) {route_info['bus_ride']}분\n\t\t(정류장-교육장) {route_info['end_walk']}분 걷기\n\n"
        
        message += "🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿🌿\n"
        message += f"규리가 매일 21:30-23:00 5분마다 숙소로 향하는 버스 정보를 알려드립니다! 🍊\n"    
        await interaction.response.send_message(message, ephemeral=False)
