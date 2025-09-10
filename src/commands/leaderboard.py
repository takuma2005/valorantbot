import discord
from discord.ext import commands
from discord import app_commands
import os
from ..valorant_api import ValorantAPI
from ..data_manager import DataManager
from ..utils.ui_helpers import UIHelpers
from ..retry_manager import RetryManager

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.retry_manager = RetryManager(os.getenv('VALORANT_API_KEY'))
    
    @app_commands.command(name="leaderboard", description="ValorantランキングでサーバーLeaderboardを表示 (デフォルト: AP)")
    @app_commands.describe(
        region="地域を変更する場合のみ指定 (デフォルト: AP)"
    )
    @app_commands.choices(region=[
        app_commands.Choice(name="Asia Pacific", value="ap"),
        app_commands.Choice(name="North America", value="na"),
        app_commands.Choice(name="Europe", value="eu"),
        app_commands.Choice(name="Korea", value="kr"),
        app_commands.Choice(name="Latin America", value="latam"),
        app_commands.Choice(name="Brazil", value="br"),
    ])
    async def leaderboard(self, interaction: discord.Interaction, region: str = "ap"):
        # デフォルトでAPリージョンを使用
        
        await interaction.response.defer()
        
        # 同じチャンネル内の古いリーダーボードを削除
        await self.cleanup_old_leaderboards(interaction.channel)
        
        try:
            valorant_api = ValorantAPI(os.getenv('VALORANT_API_KEY'))
            data_manager = DataManager()
            
            # 登録されたプレイヤーを取得
            registered_players = await data_manager.get_guild_players(str(interaction.guild_id))
            
            if not registered_players:
                await interaction.followup.send(
                    "このサーバーに登録されたプレイヤーがいません。`/register`コマンドで登録してください。"
                )
                return
            
            # プレイヤーリストを準備
            player_list = [{"name": p["name"], "tag": p["tag"]} for p in registered_players]
            
            # Leaderboardデータを取得（キャッシュ付き）
            leaderboard_data, failed_players = await valorant_api.get_leaderboard_data(
                region, player_list, str(interaction.guild_id)
            )
            sorted_data = valorant_api.sort_by_rank(leaderboard_data)
            
            # 失敗したプレイヤーがいる場合、再試行をスケジュール
            if failed_players:
                await self.retry_manager.immediate_retry(str(interaction.guild_id), failed_players)
                print(f"Scheduled retry for {len(failed_players)} players")
            
            # Embedを作成
            embed = self.create_leaderboard_embed(sorted_data, region, len(registered_players))
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"Leaderboard command error: {e}")
            await interaction.followup.send(
                "Leaderboard取得中にエラーが発生しました。後でもう一度お試しください。"
            )
    
    def create_leaderboard_embed(self, sorted_data: list, region: str, total_players: int) -> discord.Embed:
        """かっこいいLeaderboard用のEmbedを作成"""
        # 紫色を使用
        embed_color = 0x8A2BE2
        
        embed = discord.Embed(
            title=UIHelpers.create_leaderboard_title(region),
            color=embed_color,
            timestamp=discord.utils.utcnow()
        )
        
        
        if not sorted_data:
            embed.description = "🚫 データを取得できたプレイヤーがいませんでした\n💡 API制限またはサーバーエラーの可能性があります"
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
            text=f"⚡ {len(sorted_data)}/{total_players} 名表示 • 🔄 最終更新: たった今"
        )
        
        return embed
    
    async def cleanup_old_leaderboards(self, channel):
        """チャンネル内の古いリーダーボードを削除（2個以上ある場合）"""
        try:
            leaderboard_messages = []
            
            # 過去100件のメッセージを確認
            async for message in channel.history(limit=100):
                if (message.author == self.bot.user and 
                    message.embeds and 
                    len(message.embeds) > 0 and 
                    message.embeds[0].title and 
                    "ランキング" in message.embeds[0].title):
                    leaderboard_messages.append(message)
            
            # 1個以上ある場合、全て削除（新しいのが後で作成される）
            if len(leaderboard_messages) >= 1:
                # 全て削除
                for old_message in leaderboard_messages:
                    try:
                        await old_message.delete()
                    except discord.Forbidden:
                        print(f"Cannot delete message {old_message.id} - no permission")
                    except discord.NotFound:
                        print(f"Message {old_message.id} already deleted")
                    except Exception as e:
                        print(f"Error deleting message {old_message.id}: {e}")
                        
        except Exception as e:
            print(f"Error during leaderboard cleanup: {e}")

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))