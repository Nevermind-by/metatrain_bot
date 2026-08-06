from aiogram import Bot
from app.config.settings import settings

def main():
  bot = Bot(token=settings.bot_token)
  print("MetaTrain initialization completed.")
  
if __name__   == "__main__":
  main()