import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 설정 변수
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
RCON_HOST = os.getenv('RCON_HOST')
RCON_PORT = int(os.getenv('RCON_PORT', 27015))
RCON_PASSWORD = os.getenv('RCON_PASSWORD')