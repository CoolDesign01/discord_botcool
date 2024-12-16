import os 
import discord
import asyncio
from discord.ext import commands, tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, time

from myserver import server_on

import json
import platform

# แก้ปัญหา Event Loop บน Windows
if platform.system() == "Windows":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ตั้งค่า intents และสร้าง bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# โหลดและบันทึกข้อมูลใน config.json
def load_config():
    with open("config.json", "r", encoding="utf-8") as file:
        return json.load(file)

def save_config(config):
    with open("config.json", "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=4)

# โหลด config
config = load_config()

# ฟังก์ชันแจ้งเตือน
async def send_announcement(message, title="การแจ้งเตือน", image_url=None, color=discord.Color.green()):
    channel = bot.get_channel(config["announcement_channel_id"])
    if channel:
        embed = discord.Embed(
            title=title,
            description=message,
            color=color
        )
        if image_url:  # หากมีการกำหนด URL รูปภาพ
            embed.set_image(url=image_url)

        embed.set_footer(text="ข้อความนี้ส่งโดยบอท")
        await channel.send(embed=embed)

# ระบบแจ้งเตือนอัตโนมัติ
@tasks.loop(minutes=1)
async def check_schedule():
    now = datetime.now().strftime("%H:%M")
    schedule = config["schedule"]

    # แจ้งเตือนเปิดร้าน
    if now == schedule["daily_open"]:
        await send_announcement(
            config["shop_open_message"],
            title="📢 เปิดร้านแล้ว!",
            image_url="https://cdn.discordapp.com/attachments/1094275872959246366/1317852648895942730/Free_Simple_Modern_Circle_Design_Studio_Logo.png?ex=6760316c&is=675edfec&hm=11d5ed9a0a0dd40ad8e98d9fe921d72c8d4f649562e01a7aaa2e547696da1df4&",  # ใส่ URL รูปภาพที่ต้องการ
            color=discord.Color.from_rgb(114,137,218)
        )

    # แจ้งเตือนปิดร้าน
    elif now == schedule["daily_close"]:
        await send_announcement(
            config["shop_close_message"],
            title="🔔 ปิดร้านแล้ว!!",
            image_url="https://cdn.discordapp.com/attachments/1094275872959246366/1317852648895942730/Free_Simple_Modern_Circle_Design_Studio_Logo.png?ex=6760316c&is=675edfec&hm=11d5ed9a0a0dd40ad8e98d9fe921d72c8d4f649562e01a7aaa2e547696da1df4&",  # ใส่ URL รูปภาพที่ต้องการ
            color=discord.Color.from_rgb(114,137,218)  
        )
    # แจ้งเตือนแบบกำหนดเอง
    for custom in schedule["custom_announcements"]:
        if now == custom["time"]:
            await send_announcement(custom["message"])

# คำสั่งปรับเวลาแจ้งเตือน
@bot.command(name="ตั้งเวลา")
async def set_schedule(ctx, time_type: str, new_time: str):
    if time_type in ["เปิดร้าน", "ปิดร้าน"]:
        key = "daily_open" if time_type == "เปิดร้าน" else "daily_close"
        config["schedule"][key] = new_time
        save_config(config)
        await ctx.send(f"ตั้งเวลา {time_type} เป็น {new_time} เรียบร้อย!")
    else:
        await ctx.send("กรุณาระบุประเภทเวลา: เปิดร้าน หรือ ปิดร้าน")

# คำสั่งเพิ่มประกาศแบบกำหนดเวลา
@bot.command(name="เพิ่มการแจ้งเตือน")
async def add_custom_announcement(ctx, time: str, *, message: str):
    config["schedule"]["custom_announcements"].append({"time": time, "message": message})
    save_config(config)
    await ctx.send(f"เพิ่มการแจ้งเตือน: '{message}' เวลา {time} เรียบร้อย!")

# คำสั่งดูตารางแจ้งเตือน
@bot.command(name="ดูตาราง")
async def view_schedule(ctx):
    schedule = config["schedule"]
    daily_open = schedule["daily_open"]
    daily_close = schedule["daily_close"]
    custom_announcements = schedule["custom_announcements"]
    response = f"**ตารางแจ้งเตือน**\n- เปิดร้าน: {daily_open}\n- ปิดร้าน: {daily_close}\n"
    if custom_announcements:
        response += "\n**การแจ้งเตือนแบบกำหนดเอง:**\n"
        for custom in custom_announcements:
            response += f"- เวลา {custom['time']}: {custom['message']}\n"

    await ctx.send(response)

# คำสั่งทั่วไป
@bot.command()
async def hello(ctx):
    await ctx.send(f"สวัสดี {ctx.author.mention}!")  # ตอบกลับผู้ที่ใช้คำสั่ง

@bot.command()
async def add(ctx, a: int, b: int):
    result = a + b
    await ctx.send(f"ผลรวมของ {a} และ {b} คือ {result}")

@bot.command()
async def info(ctx):
    embed = discord.Embed(title="ข้อมูลบอท", description="นี่คือบอทตัวอย่าง", color=discord.Color.blue())
    embed.add_field(name="คำสั่ง", value="`!hello`, `!add`, `!info`", inline=False)
    embed.set_footer(text="สร้างโดย Atichat")
    await ctx.send(embed=embed)

@bot.command()
async def secret(ctx):
    if ctx.author.guild_permissions.administrator:
        await ctx.send("คุณเป็นแอดมิน! มีสิทธิ์ใช้งานคำสั่งนี้!")
    else:
        await ctx.send("คำสั่งนี้เฉพาะสำหรับแอดมินเท่านั้น!")

@bot.command()
async def test(ctx):
    await ctx.send("ทดสอบ! บอททำงานแล้ว 🚀")

# Event เมื่อบอทออนไลน์
@bot.event
async def on_ready():
    print(f'บอทออนไลน์แล้วในฐานะ {bot.user}')
    check_schedule.start()  # เริ่มระบบเช็คแจ้งเตือน

# Event เมื่อมีข้อความใหม่
@bot.event
async def on_message(message):
    print(f"รับข้อความ: {message.content} จาก: {message.author}")
    await bot.process_commands(message)

server_on()


bot.run(os.getenv('TOKEN'))
