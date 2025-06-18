import requests
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
import base58
import os

# === 配置 ===
API_KEY = "c57fa371-56a2-4d82-93e8-f65e2c3d0de4"
TELEGRAM_BOT_TOKEN = "7287406874:AAGXHItho1d0DMwckq7Hcfp0YptPnLKnB6k"
TELEGRAM_CHAT_ID = "-1002395300592"  # 群组 ID
MONITORED_ADDRESSES = [
    "TRX25SH76THQCBmaQoJCHFKEpZAo666666",
]

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# === 保存已处理交易哈希（持久化） ===
PROCESSED_FILE = "processed.txt"


def load_processed():
    try:
        with open(PROCESSED_FILE, "r") as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()


def save_processed(tx_hash):
    with open(PROCESSED_FILE, "a") as f:
        f.write(tx_hash + "\n")


processed_tx_hashes = load_processed()


# === 获取最新交易 ===
def fetch_latest_incoming_tx(address):
    url = f"https://api.trongrid.io/v1/accounts/{address}/transactions"
    headers = {"TRON-PRO-API-KEY": API_KEY}
    params = {"only_to": "true", "limit": 1, "sort": "-timestamp"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=25)
        resp.raise_for_status()
        data = resp.json()
        if "data" in data and data["data"]:
            return data["data"][0]
    except Exception as e:
        print(f"[错误] 获取地址 {address} 的交易失败：{e}")
    return None


# === 解析交易并播报 ===
async def parse_and_send_report(tx, address):
    tx_hash = tx.get("txID")
    if tx_hash in processed_tx_hashes:
        return

    raw_amount = tx.get("raw_data", {}).get("contract", [{}])[0].get("parameter", {}).get("value", {}).get("amount", 0)
    trx_amount = raw_amount / 1_000_000

    energy_map = {3: 65000, 6: 131000,9:195000,12:260000,15:325000}
    energy_amount = energy_map.get(int(trx_amount))
    if energy_amount is None:
        return

    order_no = str(int(tx_hash[:16], 16))[:8]
    from_address = tx.get("raw_data", {}).get("contract", [{}])[0].get("parameter", {}).get("value", {}).get("owner_address")
    if not from_address:
        return

    try:
        if len(from_address) == 42 and from_address.startswith("41"):
            from_address_bytes = bytes.fromhex(from_address)
            from_address_b58 = base58.b58encode_check(from_address_bytes).decode()
        else:
            from_address_b58 = "[地址解析失败]"
    except Exception:
        from_address_b58 = "[地址错误]"

    short_sender = f"{from_address_b58[:6]}...{from_address_b58[-6:]}"
    short_hash = f"{tx_hash[:6]}...{tx_hash[-6:]}"
    hash_link = f"{tx_hash}"

    msg = (
        "✅能量闪租 订单完成\n"
        "➖➖➖➖➖➖➖➖\n"
        f"订单号：{order_no}\n"
        f"能量数量：{energy_amount}\n"
        f"有效时间：1小时\n"
        f"接收地址：`{short_sender}`\n"
        f"交易HASH：[{short_hash} ]({hash_link})"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅U换TRX", url="https://t.me/DJTRX07bot?start=shandui"), InlineKeyboardButton("🔋3TRX闪租", url="https://t.me/DJTRX07bot?start=3trx")],
        [InlineKeyboardButton("💥笔数套餐", url="https://t.me/DJTRX07bot?start=bishu"), InlineKeyboardButton("🛎手动笔数", url="https://t.me/DJTRX07bot?start=zhiling")],
        [InlineKeyboardButton("✈️飞机会员", url="https://t.me/DJTRX07bot?start=huiyuan"), InlineKeyboardButton("🎁赠送闪租", url="https://t.me/DJTRX07bot?start=zengsong")],
        [InlineKeyboardButton("🧑🏻‍💻联系客服", url="https://t.me/KX686")],
        [InlineKeyboardButton("👇点击关注机器人", url="https://t.me/DJTRX07bot")]
    ])

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=msg,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        print(f"[播报] 已发送消息: {tx_hash}")
        processed_tx_hashes.add(tx_hash)
        save_processed(tx_hash)
    except Exception as e:
        print(f"[发送失败] Telegram 超时或网络异常：{e}")


# === 主循环 ===
async def main_loop():
    print("启动监控...")
    while True:
        for address in MONITORED_ADDRESSES:
            tx = fetch_latest_incoming_tx(address)
            if tx:
                await parse_and_send_report(tx, address)
        await asyncio.sleep(15)


if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except Exception as e:
        print(f"[主循环崩溃] 错误信息：{e}")

from aiohttp import web
import asyncio

async def handle(request):
    return web.Response(text="OK")

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

async def main_loop():
    # 启动http服务器和监控任务并行
    await start_web_server()
    print("启动监控...")
    while True:
        for address in MONITORED_ADDRESSES:
            tx = fetch_latest_incoming_tx(address)
            if tx:
                await parse_and_send_report(tx, address)
        await asyncio.sleep(15)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except Exception as e:
        print(f"[主循环崩溃] 错误信息：{e}")
