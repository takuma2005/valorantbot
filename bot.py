import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# トークンを取得
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    print("Error: DISCORD_TOKEN not found in .env file")
    exit(1)

# 環境変数を直接設定
os.environ['VALORANT_API_KEY'] = 'HDEV-a6371732-b2b9-467c-92d0-47b438225d48'
os.environ['DEFAULT_REGION'] = 'ap'

class ValorantBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
    
    async def setup_hook(self):
        """Bot起動時の初期化処理"""
        print("Loading commands...")
        
        # コマンドを読み込み
        await self.load_extension('src.commands.leaderboard')
        await self.load_extension('src.commands.register')
        await self.load_extension('src.commands.rank')
        await self.load_extension('src.commands.unregister')
        await self.load_extension('src.commands.auto_update')
        await self.load_extension('src.commands.delete_leaderboard')
        
        print("Commands loaded successfully")
        
        # スラッシュコマンドを同期
        guild_id = os.getenv('DISCORD_GUILD_ID')
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Slash commands synced to guild {guild_id}")
        else:
            await self.tree.sync()
            print("Slash commands synced globally")
    
    async def on_ready(self):
        """Bot準備完了時"""
        print(f"Bot logged in as {self.user}")
        print(f"Serving {len(self.guilds)} guilds")
        
        # アクティビティを設定
        activity = discord.Game(name="Valorant Rankings")
        await self.change_presence(activity=activity)
        
        # 自動更新タスクを開始
        from src.commands.auto_update import AutoUpdate
        auto_update_cog = self.get_cog('AutoUpdate')
        if auto_update_cog and not auto_update_cog.auto_leaderboard_update.is_running():
            auto_update_cog.auto_leaderboard_update.start()

async def main():
    """メイン関数"""
    # 環境変数の確認
    required_vars = ['DISCORD_TOKEN', 'VALORANT_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return
    
    # Botを起動
    bot = ValorantBot()
    
    try:
        await bot.start(TOKEN)
    except discord.LoginFailure:
        print("Invalid Discord token")
    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
