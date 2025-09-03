import discord
from discord.ext import commands
from discord import app_commands
import os
from ..valorant_api import ValorantAPI
from ..utils.ui_helpers import UIHelpers

class Rank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="rank", description="プレイヤーのValorantランク情報を表示 (デフォルト: AP)")
    @app_commands.describe(
        player="プレイヤー名#タグ (例: PlayerName#JP1)",
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
    async def rank(self, interaction: discord.Interaction, player: str, region: str = "ap"):
        # デフォルトでAPリージョンを使用
        
        # プレイヤー名とタグを分割
        if '#' not in player:
            await interaction.response.send_message(
                "正しい形式で入力してください: `プレイヤー名#タグ`",
                ephemeral=True
            )
            return
        
        name, tag = player.split('#', 1)
        await interaction.response.defer()
        
        try:
            valorant_api = ValorantAPI(os.getenv('VALORANT_API_KEY'))
            rank_data = await valorant_api.get_player_rank(region, name, tag)
            
            if not rank_data.get("data"):
                await interaction.followup.send(
                    f"プレイヤー **{name}#{tag}** のランク情報が見つかりませんでした。"
                )
                return
            
            embed = self.create_rank_embed(name, tag, rank_data["data"], region)
            await interaction.followup.send(embed=embed)
            
        except ValueError as e:
            await interaction.followup.send(str(e))
        except RuntimeError as e:
            if "制限" in str(e):
                await interaction.followup.send("API制限に達しました。少し待ってからもう一度お試しください。")
            else:
                await interaction.followup.send(f"ランク情報取得中にエラーが発生しました: {e}")
        except Exception as e:
            print(f"Rank command error: {e}")
            await interaction.followup.send("ランク情報の取得中にエラーが発生しました。")
    
    def create_rank_embed(self, name: str, tag: str, rank_data: dict, region: str) -> discord.Embed:
        """かっこいいランク情報用のEmbedを作成"""
        current = rank_data.get("current", {})
        peak = rank_data.get("peak", {})
        
        # プレイヤーの現在のランクに基づいて色を決定
        current_tier = current.get("tier", {})
        current_rank = current_tier.get("name", "Unrated")
        embed_color = UIHelpers.get_rank_color(current_rank)
        
        rank_emoji = UIHelpers.get_rank_emoji(current_rank)
        
        embed = discord.Embed(
            title=f"{rank_emoji} **{name}**#{tag}",
            color=embed_color,
            timestamp=discord.utils.utcnow()
        )
        
        if current:
            rr = current.get("rr", 0)
            
            # メインランク表示をかっこよく
            rank_display = UIHelpers.format_rank_display(current_rank, rr)
            embed.add_field(name="🎯 現在のランク", value=rank_display, inline=False)
            
            # 地域とLeaderboard順位
            region_flag = {"ap": "🏳️‍🌈", "na": "🇺🇸", "eu": "🇪🇺", "kr": "🇰🇷", "latam": "🌎", "br": "🇧🇷"}.get(region, "🌍")
            embed.add_field(name="🌍 地域", value=f"{region_flag} {region.upper()}", inline=True)
            
            leaderboard = current.get("leaderboard_placement", {})
            if leaderboard and leaderboard.get("rank"):
                embed.add_field(name="🏆 Leaderboard順位", value=f"**#{leaderboard['rank']}**", inline=True)
            else:
                embed.add_field(name="🏆 Leaderboard", value="圏外", inline=True)
            
                
        else:
            embed.description = "❌ このプレイヤーのランク情報が見つかりませんでした"
        
        # 最高ランクを豪華に表示
        if peak:
            peak_tier = peak.get("tier", {})
            peak_rank = peak_tier.get("name", "不明")
            peak_rr = peak.get("rr", 0)
            peak_emoji = UIHelpers.get_rank_emoji(peak_rank)
            
            embed.add_field(
                name="👑 最高到達ランク", 
                value=f"{peak_emoji} **{peak_rank}** ({peak_rr}RR)", 
                inline=False
            )
        
        embed.set_footer(
            text="⚡ Powered by Henrik Valorant API",
            icon_url="https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/0/smallicon.png"
        )
        
        return embed

async def setup(bot):
    await bot.add_cog(Rank(bot))