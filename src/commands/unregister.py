import discord
from discord.ext import commands
from discord import app_commands
from ..data_manager import DataManager

class Unregister(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="unregister", description="Leaderboardから自分のアカウントを削除")
    @app_commands.describe(
        player="削除するプレイヤー名#タグ (例: PlayerName#TAG)"
    )
    async def unregister(self, interaction: discord.Interaction, player: str):
        await interaction.response.defer(ephemeral=True)
        
        # プレイヤー名とタグを分析
        if '#' not in player:
            await interaction.followup.send(
                "正しい形式で入力してください: `PlayerName#TAG`"
            )
            return
        
        name, tag = player.split('#', 1)
        
        try:
            data_manager = DataManager()
            
            # 全プレイヤーから該当アカウントを検索
            guild_players = await data_manager.get_guild_players(str(interaction.guild_id))
            target_player = None
            
            for player_data in guild_players:
                if player_data.get("name") == name and player_data.get("tag") == tag:
                    target_player = player_data
                    break
            
            if not target_player:
                await interaction.followup.send(
                    f"プレイヤー **{name}#{tag}** は登録されていません。"
                )
                return
            
            # puuidを使用してプレイヤーデータを削除
            file_path = data_manager._get_guild_file_path(str(interaction.guild_id))
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    guild_data = json.load(f)
                
                puuid = target_player.get("puuid")
                if puuid and puuid in guild_data.get("players", {}):
                    del guild_data["players"][puuid]
                    
                    # ファイルに保存
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(guild_data, f, ensure_ascii=False, indent=2)
                    
                    embed = discord.Embed(
                        title="👋 **LEADERBOARD退出**",
                        description=f"```ansi\n\u001b[1;31m🚪 {name}#{tag} が退出しました\u001b[0m\n```",
                        color=0xFF6B6B,
                        timestamp=discord.utils.utcnow()
                    )
                    embed.add_field(
                        name="📊 ステータス", 
                        value="✅ データ削除完了\n🔄 Leaderboard更新済み", 
                        inline=False
                    )
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send("登録解除中にエラーが発生しました。")
                    
            except Exception as e:
                print(f"File operation error: {e}")
                await interaction.followup.send("登録解除中にエラーが発生しました。")
                
        except Exception as e:
            print(f"Unregister error: {e}")
            await interaction.followup.send("登録解除中にエラーが発生しました。")

async def setup(bot):
    await bot.add_cog(Unregister(bot))