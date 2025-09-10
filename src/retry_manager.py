import asyncio
from typing import Dict, List
from datetime import datetime
from .rank_cache import RankCache
from .valorant_api import ValorantAPI

class RetryManager:
    """API失敗時の再試行を管理するクラス"""
    
    def __init__(self, api_key: str):
        self.cache = RankCache()
        self.api = ValorantAPI(api_key)
        self.retry_tasks = {}  # guild_id -> task
    
    async def start_retry_loop(self, guild_id: str):
        """ギルドごとの再試行ループを開始"""
        if guild_id in self.retry_tasks:
            # 既に実行中の場合はスキップ
            return
        
        self.retry_tasks[guild_id] = asyncio.create_task(self._retry_loop(guild_id))
    
    async def stop_retry_loop(self, guild_id: str):
        """ギルドごとの再試行ループを停止"""
        if guild_id in self.retry_tasks:
            self.retry_tasks[guild_id].cancel()
            del self.retry_tasks[guild_id]
    
    async def _retry_loop(self, guild_id: str):
        """2分ごとに再試行キューをチェック"""
        while True:
            try:
                await asyncio.sleep(120)  # 2分待機
                await self.process_retry_queue(guild_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in retry loop for guild {guild_id}: {e}")
    
    async def process_retry_queue(self, guild_id: str):
        """再試行キューを処理"""
        retry_entries = await self.cache.get_retry_queue(guild_id)
        
        if not retry_entries:
            return
        
        print(f"Processing {len(retry_entries)} retry entries for guild {guild_id}")
        
        for entry in retry_entries:
            player = entry['player']
            player_key = f"{player['name']}#{player['tag']}"
            
            try:
                # デフォルトリージョンを使用（または設定から取得）
                region = "ap"  # TODO: ギルドごとの設定から取得
                
                # APIから再取得を試みる
                rank_data = await self.api.get_player_rank(region, player["name"], player["tag"])
                result = {
                    "name": player["name"],
                    "tag": player["tag"],
                    **rank_data["data"]
                }
                
                # キャッシュを更新
                await self.cache.update_player_data(guild_id, player_key, result)
                print(f"Successfully updated data for {player_key}")
                
                # 成功したので再試行は不要
                await self.cache.update_retry_attempt(guild_id, player, success=True)
                
            except Exception as e:
                print(f"Retry failed for {player_key}: {e}")
                # 失敗した場合、次の再試行をスケジュール
                await self.cache.update_retry_attempt(guild_id, player, success=False)
    
    async def immediate_retry(self, guild_id: str, failed_players: List[Dict]):
        """即座に再試行を実行（初回失敗時用）"""
        if not failed_players:
            return
        
        # 2分後に再試行をスケジュール
        for player in failed_players:
            await self.cache.add_to_retry_queue(guild_id, player)
        
        # 再試行ループが開始されていない場合は開始
        await self.start_retry_loop(guild_id)