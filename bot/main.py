import discord
from discord.ext import commands
from mcrcon import MCRcon
import asyncio
import logging
from config import DISCORD_TOKEN, RCON_HOST, RCON_PORT, RCON_PASSWORD
from datetime import datetime

# 로깅 설정
def setup_logging():
   log_filename = f'bot_{datetime.now().strftime("%Y%m%d")}.log'
   
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s [%(levelname)s] %(message)s',
       handlers=[
           logging.FileHandler(log_filename, encoding='utf-8'),
           logging.StreamHandler()
       ]
   )
   return logging.getLogger('discord_bot')

logger = setup_logging()

# 봇 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!좀보이드 ', intents=intents)

async def send_rcon_command(command):
   try:
       logger.info(f'RCON 명령어 전송: {command}')
       with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as client:
           response = client.command(command)
           logger.info(f'RCON 응답: {response}')
           return response if response else "명령어가 실행되었지만 응답이 없습니다."
   except Exception as e:
       logger.error(f'RCON 오류 발생: {str(e)}', exc_info=True)
       return f"RCON 오류: {e}"

@bot.event
async def on_ready():
   logger.info(f'{bot.user.name} 봇이 시작되었습니다.')

@bot.command(name="플레이어")
async def players(ctx):
   """접속 중인 플레이어 목록을 확인합니다."""
   logger.info(f'플레이어 명령어 실행 - 요청자: {ctx.author}')
   response = await send_rcon_command("players")
   await ctx.send(f"```{response}```")

@bot.command(name="아이템")
@commands.has_role("Admin")
async def add_item(ctx, player: str, item: str, count: int = 1):
   """플레이어에게 아이템을 지급합니다."""
   logger.info(f'아이템 지급 명령어 실행 - 요청자: {ctx.author}, 대상: {player}, 아이템: {item}, 개수: {count}')
   if not item.startswith("Base."):
       item = f"Base.{item}"
   response = await send_rcon_command(f'additem "{player}" "{item}" {count}')
   await ctx.send(f"```{response}```")

@bot.command(name="권한")
@commands.has_role("Admin")
async def set_access_level(ctx, player: str, level: str):
   """플레이어의 권한 레벨을 설정합니다."""
   logger.info(f'권한 설정 명령어 실행 - 요청자: {ctx.author}, 대상: {player}, 레벨: {level}')
   response = await send_rcon_command(f'setaccesslevel "{player}" {level}')
   await ctx.send(f"```{response}```")

@bot.command(name="공지")
@commands.has_role("Admin")
async def server_message(ctx, *, message: str):
   """서버 전체 공지를 전송합니다."""
   logger.info(f'공지 명령어 실행 - 요청자: {ctx.author}, 메시지: {message}')
   response = await send_rcon_command(f'servermsg "{message}"')
   await ctx.send(f"공지를 전송했습니다: {message}")

@bot.command(name="텔레포트")
@commands.has_role("Admin")
async def teleport(ctx, player1: str, player2: str = None):
   """플레이어를 텔레포트시킵니다."""
   if player2:
       logger.info(f'텔레포트 명령어 실행 - 요청자: {ctx.author}, 대상1: {player1}, 대상2: {player2}')
       command = f'teleport "{player1}" "{player2}"'
   else:
       logger.info(f'텔레포트 명령어 실행 - 요청자: {ctx.author}, 대상: {player1}')
       command = f'teleport "{player1}"'
   response = await send_rcon_command(command)
   await ctx.send(f"```{response}```")

@bot.command(name="비내리기")
@commands.has_role("Admin")
async def start_rain(ctx):
   """비를 내리게 합니다."""
   logger.info(f'비내리기 명령어 실행 - 요청자: {ctx.author}')
   response = await send_rcon_command("startrain")
   await ctx.send("비가 내리기 시작했습니다.")

@bot.command(name="비그치기")
@commands.has_role("Admin")
async def stop_rain(ctx):
   """비를 멈추게 합니다."""
   logger.info(f'비그치기 명령어 실행 - 요청자: {ctx.author}')
   response = await send_rcon_command("stoprain")
   await ctx.send("비가 그쳤습니다.")

@bot.command(name="시간")
async def server_time(ctx):
   """서버의 현재 시간을 확인합니다."""
   logger.info(f'서버시간 명령어 실행 - 요청자: {ctx.author}')
   response = await send_rcon_command("servertime")
   await ctx.send(f"서버 시간: ```{response}```")

@bot.command(name="도움말")
async def help_command(ctx):
   """사용 가능한 명령어 목록을 보여줍니다."""
   logger.info(f'도움말 명령어 실행 - 요청자: {ctx.author}')
   help_text = """
**좀보이드 서버 명령어 목록**
`!좀보이드 플레이어` - 접속 중인 플레이어 목록 확인
`!좀보이드 시간` - 서버 시간 확인
`!좀보이드 아이템 [플레이어] [아이템] [개수]` - 아이템 지급 (관리자)
`!좀보이드 권한 [플레이어] [레벨]` - 권한 설정 (관리자)
`!좀보이드 공지 [메시지]` - 전체 공지 (관리자)
`!좀보이드 텔레포트 [플레이어1] [플레이어2]` - 텔레포트 (관리자)
`!좀보이드 비내리기` - 비 내리기 (관리자)
`!좀보이드 비그치기` - 비 그치기 (관리자)
"""
   await ctx.send(help_text)

@bot.event
async def on_command_error(ctx, error):
   """에러 처리 및 로깅"""
   error_message = ""
   
   if isinstance(error, commands.MissingRole):
       error_message = "이 명령어를 사용할 권한이 없습니다."
       logger.warning(f'권한 없음 - 사용자: {ctx.author}, 명령어: {ctx.command}, 필요한 역할: Admin')
   elif isinstance(error, commands.MissingRequiredArgument):
       error_message = "필요한 인자가 누락되었습니다. `!좀보이드 도움말`을 참고해주세요."
       logger.warning(f'인자 누락 - 사용자: {ctx.author}, 명령어: {ctx.command}, 누락된 인자: {error.param.name}')
   else:
       error_message = f"오류가 발생했습니다: {error}"
       logger.error(f'예상치 못한 오류 발생 - 사용자: {ctx.author}, 명령어: {ctx.command}', exc_info=error)

   await ctx.send(error_message)

@bot.event
async def on_error(event, *args, **kwargs):
   logger.error(f'글로벌 에러 발생 - 이벤트: {event}', exc_info=True)

try:
   bot.run(DISCORD_TOKEN)
except Exception as e:
   logger.critical(f'봇 실행 실패: {str(e)}', exc_info=True)