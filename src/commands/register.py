import discord
from discord.ext import commands
from discord import app_commands
import os
from ..valorant_api import ValorantAPI
from ..data_manager import DataManager
from ..utils.ui_helpers import UIHelpers
from datetime import datetime

class Register(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="register", description="Valorantアカウントをleaderboardに登録 (デフォルト: AP)")
    @app_commands.describe(
        player="プレイヤー名#タグ (例: PlayerName#JP1) または分割入力",
        tag="プレイヤータグ (例: JP1) - playerに#が含まれない場合のみ使用",
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
    async def register(self, interaction: discord.Interaction, player: str, tag: str = None, region: str = "ap"):
        # プレイヤー名とタグを分析
        if '#' in player:
            # PlayerName#TAG形式の場合
            name, player_tag = player.split('#', 1)
        elif tag:
            # 分割入力の場合
            name, player_tag = player, tag
        else:
            await interaction.response.send_message(
                "正しい形式で入力してください:\n"
                "• `PlayerName#TAG` 形式\n"
                "• または `player: PlayerName` と `tag: TAG` を両方指定",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            valorant_api = ValorantAPI(os.getenv('VALORANT_API_KEY'))
            
            # アカウントの存在確認
            account_data = await valorant_api.get_account(name, player_tag)
            if not account_data.get("data"):
                await interaction.followup.send(
                    f"プレイヤー **{name}#{player_tag}** が見つかりませんでした。名前とタグを確認してください。"
                )
                return
            
            # ランク情報を取得して登録確認に表示
            rank_data = await valorant_api.get_player_rank(region, name, player_tag)
            
            # プレイヤーデータを保存
            data_manager = DataManager()
            await data_manager.store_player_data(
                str(interaction.guild_id), 
                str(interaction.user.id), 
                {
                    "name": name,
                    "tag": player_tag,
                    "region": region,
                    "puuid": account_data["data"].get("puuid"),
                    "registered_at": datetime.now().isoformat()
                }
            )
            
            # 登録確認Embedを豪華に作成
            current_data = rank_data.get("data", {}).get("current", {})
            current_tier = current_data.get("tier", {})
            current_rank = current_tier.get("name", "Unrated")
            rr = current_data.get("rr", 0)
            
            rank_emoji = UIHelpers.get_rank_emoji(current_rank)
            rank_color = UIHelpers.get_rank_color(current_rank)
            region_flag = {"ap": "🏳️‍🌈", "na": "🇺🇸", "eu": "🇪🇺", "kr": "🇰🇷", "latam": "🌎", "br": "🇧🇷"}.get(region, "🌍")
            
            embed = discord.Embed(
                title="🎉 **LEADERBOARD登録完了！**",
                description=f"```ansi\n\u001b[1;32m🚀 {name}#{player_tag} が参戦！\u001b[0m\n```",
                color=rank_color,
                timestamp=discord.utils.utcnow()
            )
            
            # ランク情報を豪華に表示
            rank_display = UIHelpers.format_rank_display(current_rank, rr)
            embed.add_field(name="🎯 現在のランク", value=rank_display, inline=False)
            
            embed.add_field(name="🌍 地域", value=f"{region_flag} {region.upper()}", inline=True)
            
            # Leaderboard順位があれば表示
            leaderboard = current_data.get("leaderboard_placement", {})
            if leaderboard and leaderboard.get("rank"):
                embed.add_field(name="🏆 順位", value=f"**#{leaderboard['rank']}**", inline=True)
            else:
                embed.add_field(name="🏆 順位", value="集計中...", inline=True)
            
            await interaction.followup.send(embed=embed)
            
        except ValueError as e:
            # プレイヤーが見つからない場合
            await interaction.followup.send(str(e))
        except RuntimeError as e:
            # API制限やその他のAPIエラー
            if "制限" in str(e):
                await interaction.followup.send("API制限に達しました。少し待ってからもう一度お試しください。")
            else:
                await interaction.followup.send(f"登録中にエラーが発生しました: {e}")
        except Exception as e:
            print(f"Registration error: {e}")
            await interaction.followup.send("登録中にエラーが発生しました。後でもう一度お試しください。")

async def setup(bot):
    await bot.add_cog(Register(bot))