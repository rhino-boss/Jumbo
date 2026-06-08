from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# 🔴 請把下方雙引號內的文字，換成你在 BotFather 拿到、被你紅線槓起來的那串 Token
TOKEN = "你的_TELEGRAM_BOT_TOKEN"


async def echo_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """測試函式：收到什麼文字，機器人就秒讀秒回覆一樣的文字"""
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    user_name = update.message.from_user.full_name

    # 這行會在你的電腦黑色視窗（終端機）印出記錄
    print(f"成功收到來自 {user_name} 的訊息: {user_text}")

    # 讓機器人在 Telegram 上回覆對方
    await update.message.reply_text(f"🤖 機器人收到並覆誦：{user_text}")


if __name__ == "__main__":
    print("正在啟動機器人中...")

    # 初始化機器人
    app = Application.builder().token(TOKEN).build()

    # 讓機器人監聽所有「純文字訊息」，並交給 echo_test 函式處理
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_test))

    print("🎉 機器人已成功上線！(按下 Ctrl + C 可以關閉程式)")
    app.run_polling()
