from greet_command import setup_greet_command
from help_command import setup_help_command
from roll_command import setup_roll_command
from weather_command import setup_weather_command
from bus_command import setup_bus_command
from taxi_command import setup_taxi_command
from meme_command import setup_meme_command
from vote_command import setup_vote_command
from meeting_command import setup_meeting_command
from create_daily_thread import setup_create_daily_thread
from feedback_command import setup_feedback_command  # 추가

async def setup_commands(bot):
    """
    모든 명령어를 설정합니다.
    """
    # 인사 명령어 설정
    setup_greet_command(bot)
    
    # 도움말 명령어 설정
    setup_help_command(bot)
    
    # 주사위 굴리기 명령어 설정
    setup_roll_command(bot)
    
    # 날씨 정보 명령어 설정
    setup_weather_command(bot)
    
    # 버스 정보 명령어 설정 및 자동 모니터링
    setup_bus_command(bot)
    
    # 택시 정보 명령어 설정
    await setup_taxi_command(bot)
    
    # 랜덤 짤 명령어 설정
    setup_meme_command(bot)
    
    # 투표 생성 명령어 설정
    setup_vote_command(bot)
    
    # 모임 생성 및 관리 명령어 설정
    setup_meeting_command(bot)
    
    # 피드백 명령어 설정
    await setup_feedback_command(bot)  # 추가

    await setup_create_daily_thread(bot)
