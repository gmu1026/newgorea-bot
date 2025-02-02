import discord
from discord.ext import commands
from rcon.source import Client
import asyncio
from config import DISCORD_TOKEN, RCON_HOST, RCON_PORT, RCON_PASSWORD

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!좀보이드 ', intents=intents)

async def send_rcon_command(command):
    try:
        with Client(RCON_HOST, RCON_PORT, passwd=RCON_PASSWORD) as client:
            response = client.run(command)
            return response
    except Exception as e:
        print(f"RCON 오류: {e}")
        return None

# 기존 명령어들은 유지하고 새로운 명령어 추가

@bot.command(name="아이템")
@commands.has_role("Admin")
async def add_item(ctx, player: str, item: str, count: int = 1):
    try:
        # 아이템 이름에 Base. 접두사가 없으면 추가
        if not item.startswith("Base."):
            item = f"Base.{item}"
        
        response = await send_rcon_command(f'additem "{player}" "{item}" {count}')
        await ctx.send(f"{player}님에게 {item} {count}개를 지급했습니다.")
    except Exception as e:
        await ctx.send(f"아이템 지급 중 오류가 발생했습니다: {e}")

@bot.command(name="비내리기")
@commands.has_role("Admin")
async def start_rain(ctx):
    try:
        response = await send_rcon_command("startrain")
        await ctx.send("비가 내리기 시작했습니다.")
    except Exception as e:
        await ctx.send(f"날씨 변경 중 오류가 발생했습니다: {e}")

@bot.command(name="비그치기")
@commands.has_role("Admin")
async def stop_rain(ctx):
    try:
        response = await send_rcon_command("stoprain")
        await ctx.send("비가 그쳤습니다.")
    except Exception as e:
        await ctx.send(f"날씨 변경 중 오류가 발생했습니다: {e}")

@bot.command(name="텔레포트")
@commands.has_role("Admin")
async def teleport(ctx, player1: str, player2: str = None):
    try:
        if player2:
            # 플레이어1을 플레이어2에게 텔레포트
            response = await send_rcon_command(f'teleport "{player1}" "{player2}"')
            await ctx.send(f"{player1}님을 {player2}님의 위치로 텔레포트했습니다.")
        else:
            # 단일 플레이어 텔레포트
            response = await send_rcon_command(f'teleport "{player1}"')
            await ctx.send(f"{player1}님을 텔레포트했습니다.")
    except Exception as e:
        await ctx.send(f"텔레포트 중 오류가 발생했습니다: {e}")

@bot.command(name="도움말")
async def help_command(ctx):
    help_text = """
**좀보이드 서버 명령어 목록**
- !좀보이드 플레이어 - 접속 중인 플레이어 목록 확인
- !좀보이드 서버시간 - 현재 서버 시간 확인
- !좀보이드 아이템 [플레이어] [아이템] [개수] - 플레이어에게 아이템 지급 (관리자 전용)
- !좀보이드 킥 [플레이어] - 플레이어 킥 (관리자 전용)
- !좀보이드 공지 [메시지] - 서버 공지 전송 (관리자 전용)
- !좀보이드 저장 - 서버 저장 (관리자 전용)
- !좀보이드 비내리기 - 비 내리기 시작 (관리자 전용)
- !좀보이드 비그치기 - 비 그치기 (관리자 전용)
- !좀보이드 텔레포트 [플레이어1] [플레이어2] - 텔레포트 (관리자 전용)
- !좀보이드 치트 - 치트 사용 확인 (관리자 전용)

관리자 전용 명령어는 해당 권한이 있는 사용자만 실행할 수 있습니다.
"""
    await ctx.send(help_text)

bot.run(DISCORD_TOKEN)