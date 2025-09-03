import discord
from discord.ext import commands
from discord import app_commands

class DeleteLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="delete-leaderboard", description="指定したメッセージIDのリーダーボードを削除")
    @app_commands.describe(
        message_id="削除するリーダーボードのメッセージID"
    )
    async def delete_leaderboard(self, interaction: discord.Interaction, message_id: str):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # メッセージIDの妥当性チェック
            try:
                message_id_int = int(message_id)
            except ValueError:
                await interaction.followup.send("無効なメッセージIDです。数字のみで入力してください。")
                return
            
            # メッセージが存在するかチェック
            try:
                message = await interaction.channel.fetch_message(message_id_int)
                
                # ボットのメッセージかチェック
                if message.author != self.bot.user:
                    await interaction.followup.send("指定されたメッセージはこのBotのメッセージではありません。")
                    return
                
                # リーダーボードメッセージかチェック（タイトルで判定）
                if (message.embeds and 
                    len(message.embeds) > 0 and 
                    message.embeds[0].title and 
                    "ランキング" in message.embeds[0].title):
                    
                    # メッセージを削除
                    await message.delete()
                    
                    embed = discord.Embed(
                        title="✅ リーダーボード削除完了",
                        description=f"メッセージID `{message_id}` のリーダーボードを削除しました。",
                        color=0x00FF00,
                        timestamp=discord.utils.utcnow()
                    )
                    await interaction.followup.send(embed=embed)
                
                else:
                    await interaction.followup.send("指定されたメッセージはリーダーボードではありません。")
                    return
                    
            except discord.NotFound:
                await interaction.followup.send("指定されたメッセージが見つかりませんでした。")
                return
            except discord.Forbidden:
                await interaction.followup.send("メッセージを削除する権限がありません。")
                return
                
        except Exception as e:
            print(f"Delete leaderboard error: {e}")
            await interaction.followup.send("削除中にエラーが発生しました。")

async def setup(bot):
    await bot.add_cog(DeleteLeaderboard(bot))