import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from ..valorant_api import ValorantAPI
from ..data_manager import DataManager
from ..utils.ui_helpers import UIHelpers
from ..retry_manager import RetryManager

class AutoUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = DataManager()
        self.retry_manager = RetryManager(os.getenv('VALORANT_API_KEY'))
        
    def cog_unload(self):
        """Cogがアンロードされる時にタスクを停止"""
        self.auto_leaderboard_update.cancel()
    
    @app_commands.command(name="auto-leaderboard", description="5分間隔でリーダーボードの自動更新を設定")
    @app_commands.describe(
        message_id="更新するメッセージのID（まず/leaderboardでメッセージを作成してIDを取得）",
        enable="自動更新を有効/無効にする"
    )
    @app_commands.choices(enable=[
        app_commands.Choice(name="有効にする", value="true"),
        app_commands.Choice(name="無効にする", value="false")
    ])
    async def auto_leaderboard(self, interaction: discord.Interaction, 
                             message_id: str, enable: str = "true"):
        
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            guild_id = str(interaction.guild_id)
            
            if enable == "true":
                # メッセージIDの妥当性チェック
                try:
                    message_id_int = int(message_id)
                except ValueError:
                    await interaction.followup.send("無効なメッセージIDです。数字のみで入力してください。")
                    return
                
                # メッセージが存在するかチェック
                try:
                    # 現在のチャンネルでメッセージを検索
                    message = await interaction.channel.fetch_message(message_id_int)
                    if message.author != self.bot.user:
                        await interaction.followup.send("指定されたメッセージはこのBotのメッセージではありません。")
                        return
                except discord.NotFound:
                    await interaction.followup.send("指定されたメッセージが見つかりませんでした。")
                    return
                
                # 自動更新を有効化
                await self.data_manager.store_auto_update_config(guild_id, {
                    "enabled": True,
                    "message_id": message_id_int,
                    "channel_id": interaction.channel_id,
                    "region": "ap"
                })
                
                # タスクを開始（まだ開始されていない場合）
                if not self.auto_leaderboard_update.is_running():
                    self.auto_leaderboard_update.start()
                
                embed = discord.Embed(
                    title="✅ 自動更新設定完了",
                    description=f"メッセージID `{message_id}` が5分間隔で自動更新されます。",
                    color=0x00FF00,
                    timestamp=discord.utils.utcnow()
                )
                
            else:
                # 自動更新を無効化
                await self.data_manager.store_auto_update_config(guild_id, {
                    "enabled": False,
                    "message_id": None,
                    "channel_id": None,
                    "region": "ap"
                })
                
                embed = discord.Embed(
                    title="🛑 自動更新停止",
                    description="リーダーボードの自動更新を停止しました。",
                    color=0xFF6B6B,
                    timestamp=discord.utils.utcnow()
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"Auto-update configuration error: {e}")
            await interaction.followup.send("設定中にエラーが発生しました。")
    
    @tasks.loop(minutes=5)
    async def auto_leaderboard_update(self):
        """5分間隔でリーダーボードを更新"""
        try:
            # 自動更新が有効なすべてのギルドを取得
            configs = await self.data_manager.get_all_auto_update_configs()
            
            for guild_id, config in configs.items():
                if not config.get("enabled"):
                    continue
                
                message_id = config.get("message_id")
                channel_id = config.get("channel_id")
                region = config.get("region", "ap")
                
                if not message_id or not channel_id:
                    continue
                
                try:
                    # チャンネルとメッセージを取得
                    channel = self.bot.get_channel(channel_id)
                    if not channel:
                        print(f"Channel {channel_id} not found for guild {guild_id}")
                        continue
                    
                    try:
                        message = await channel.fetch_message(message_id)
                    except discord.NotFound:
                        print(f"Message {message_id} not found in guild {guild_id}")
                        # メッセージが見つからない場合は自動更新を無効化
                        await self.data_manager.store_auto_update_config(guild_id, {
                            "enabled": False,
                            "message_id": None,
                            "channel_id": None,
                            "region": region
                        })
                        continue
                    
                    # プレイヤーデータを取得
                    registered_players = await self.data_manager.get_guild_players(guild_id)
                    if not registered_players:
                        # プレイヤーがいない場合はメッセージに表示
                        embed = discord.Embed(
                            title=f"🏆 Valorant Leaderboard ({region.upper()}) - 自動更新",
                            description="登録されたプレイヤーがいません。",
                            color=0xFA4454,
                            timestamp=discord.utils.utcnow()
                        )
                        await message.edit(embed=embed)
                        continue
                    
                    # リーダーボードを生成（キャッシュ付き）
                    valorant_api = ValorantAPI(os.getenv('VALORANT_API_KEY'))
                    player_list = [{"name": p["name"], "tag": p["tag"]} for p in registered_players]
                    leaderboard_data, failed_players = await valorant_api.get_leaderboard_data(
                        region, player_list, guild_id
                    )
                    sorted_data = valorant_api.sort_by_rank(leaderboard_data)
                    
                    # 失敗したプレイヤーがいる場合、再試行をスケジュール
                    if failed_players:
                        await self.retry_manager.immediate_retry(guild_id, failed_players)
                        print(f"Auto-update: Scheduled retry for {len(failed_players)} players in guild {guild_id}")
                    
                    # Embedを作成して既存メッセージを完全上書き
                    embed = self.create_auto_leaderboard_embed(sorted_data, region, len(registered_players))
                    await message.edit(content="", embed=embed, attachments=[])
                    
                except Exception as e:
                    print(f"Auto-update error for guild {guild_id}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Auto-update task error: {e}")
    
    @auto_leaderboard_update.before_loop
    async def before_auto_update(self):
        """タスク開始前にボットの準備を待つ"""
        await self.bot.wait_until_ready()
    
    def create_auto_leaderboard_embed(self, sorted_data: list, region: str, total_players: int) -> discord.Embed:
        """自動更新用のかっこいいLeaderboard Embedを作成"""
        # 紫色を使用
        embed_color = 0x8A2BE2
        
        embed = discord.Embed(
            title=UIHelpers.create_leaderboard_title(region, is_auto=True),
            color=embed_color,
            timestamp=discord.utils.utcnow()
        )
        
        if not sorted_data:
            embed.description = "🚫 データを取得できたプレイヤーがいませんでした\n🔄 次回更新: 5分後"
            return embed
        
        description = ""
        display_limit = min(len(sorted_data), 20)
        
        for i in range(display_limit):
            player = sorted_data[i]
            current = player.get("current", {})
            tier = current.get("tier", {})
            rank = tier.get("name", "Unrated")
            rr = current.get("rr", 0)
            
            position_emoji = UIHelpers.get_position_emoji(i + 1)
            rank_emoji = UIHelpers.get_rank_emoji(rank)
            
            # プレイヤー情報（強調表示）
            player_name = f"**{player['name']}#{player['tag']}**"
            
            # ランク名を日本語化
            rank_jp = {
                "Radiant": "レディアント",
                "Immortal 3": "イモータル 3", 
                "Immortal 2": "イモータル 2",
                "Immortal 1": "イモータル 1",
                "Ascendant 3": "アセンダント 3",
                "Ascendant 2": "アセンダント 2", 
                "Ascendant 1": "アセンダント 1",
                "Diamond 3": "ダイヤモンド 3",
                "Diamond 2": "ダイヤモンド 2",
                "Diamond 1": "ダイヤモンド 1",
                "Platinum 3": "プラチナ 3",
                "Platinum 2": "プラチナ 2",
                "Platinum 1": "プラチナ 1",
                "Gold 3": "ゴールド 3",
                "Gold 2": "ゴールド 2", 
                "Gold 1": "ゴールド 1",
                "Silver 3": "シルバー 3",
                "Silver 2": "シルバー 2",
                "Silver 1": "シルバー 1",
                "Bronze 3": "ブロンズ 3",
                "Bronze 2": "ブロンズ 2",
                "Bronze 1": "ブロンズ 1",
                "Iron 3": "アイアン 3",
                "Iron 2": "アイアン 2",
                "Iron 1": "アイアン 1"
            }.get(rank, rank)
            
            # リスト形式で表示
            if i == 0:
                description += f"🏅 1位: {player_name}\n"
            elif i == 1:
                description += f"🥈 2位: {player_name}\n"
            elif i == 2:
                description += f"🥉 3位: {player_name}\n"
            else:
                description += f"{i+1}位: {player_name}\n"
            
            description += f"{rank_emoji} {rank_jp} | {rr} RR\n"
            
            # プレイヤー間に余白を追加
            if i < display_limit - 1:
                description += "\n"
        
        # 最下位の下に余白追加
        description += "\n"
        
        # 追加統計情報
        if len(sorted_data) > 20:
            description += f"\n🔽 **他 {len(sorted_data) - 20} 名のプレイヤー**"
        
        embed.description = description
        
        # フッターに詳細情報（日本語）
        embed.set_footer(
            text=f"🔄 自動更新中 • {len(sorted_data)}/{total_players} 名表示"
        )
        
        return embed

async def setup(bot):
    await bot.add_cog(AutoUpdate(bot))