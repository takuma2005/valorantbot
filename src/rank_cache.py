import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import asyncio

class RankCache:
    """プレイヤーのランクデータをキャッシュするクラス"""
    
    def __init__(self):
        self.cache_dir = "data/cache"
        self.cache_file = "rank_cache.json"
        self.retry_queue_file = "retry_queue.json"
        self.cache_duration = timedelta(hours=1)  # キャッシュの有効期限
        self.ensure_cache_dir()
    
    def ensure_cache_dir(self):
        """キャッシュディレクトリを作成"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_cache_path(self, guild_id: str) -> str:
        """ギルドごとのキャッシュファイルパスを取得"""
        return os.path.join(self.cache_dir, f"{guild_id}_{self.cache_file}")
    
    def get_retry_queue_path(self, guild_id: str) -> str:
        """ギルドごとの再試行キューファイルパスを取得"""
        return os.path.join(self.cache_dir, f"{guild_id}_{self.retry_queue_file}")
    
    async def load_cache(self, guild_id: str) -> Dict[str, Any]:
        """キャッシュを読み込む"""
        cache_path = self.get_cache_path(guild_id)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    async def save_cache(self, guild_id: str, cache_data: Dict[str, Any]):
        """キャッシュを保存"""
        cache_path = self.get_cache_path(guild_id)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    async def get_player_data(self, guild_id: str, player_key: str) -> Optional[Dict]:
        """プレイヤーのキャッシュデータを取得"""
        cache = await self.load_cache(guild_id)
        if player_key in cache:
            cached_data = cache[player_key]
            # タイムスタンプをチェック
            cached_time = datetime.fromisoformat(cached_data.get('timestamp', '2000-01-01'))
            if datetime.now() - cached_time < self.cache_duration:
                return cached_data.get('data')
        return None
    
    async def update_player_data(self, guild_id: str, player_key: str, data: Dict):
        """プレイヤーのデータを更新"""
        cache = await self.load_cache(guild_id)
        cache[player_key] = {
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'last_update_attempt': datetime.now().isoformat()
        }
        await self.save_cache(guild_id, cache)
    
    async def mark_update_failed(self, guild_id: str, player_key: str):
        """更新失敗をマーク（前のデータを保持）"""
        cache = await self.load_cache(guild_id)
        if player_key in cache:
            cache[player_key]['last_update_attempt'] = datetime.now().isoformat()
            cache[player_key]['failed_attempts'] = cache[player_key].get('failed_attempts', 0) + 1
            await self.save_cache(guild_id, cache)
    
    async def add_to_retry_queue(self, guild_id: str, player_info: Dict):
        """再試行キューに追加"""
        queue_path = self.get_retry_queue_path(guild_id)
        
        # 既存のキューを読み込む
        if os.path.exists(queue_path):
            with open(queue_path, 'r', encoding='utf-8') as f:
                retry_queue = json.load(f)
        else:
            retry_queue = []
        
        # プレイヤー情報と再試行時刻を追加
        retry_entry = {
            'player': player_info,
            'retry_at': (datetime.now() + timedelta(minutes=2)).isoformat(),
            'attempts': 0
        }
        
        # 既に同じプレイヤーがキューにいるかチェック
        player_key = f"{player_info['name']}#{player_info['tag']}"
        retry_queue = [item for item in retry_queue if f"{item['player']['name']}#{item['player']['tag']}" != player_key]
        retry_queue.append(retry_entry)
        
        # キューを保存
        with open(queue_path, 'w', encoding='utf-8') as f:
            json.dump(retry_queue, f, ensure_ascii=False, indent=2)
    
    async def get_retry_queue(self, guild_id: str) -> List[Dict]:
        """再試行が必要なプレイヤーのリストを取得"""
        queue_path = self.get_retry_queue_path(guild_id)
        if not os.path.exists(queue_path):
            return []
        
        with open(queue_path, 'r', encoding='utf-8') as f:
            retry_queue = json.load(f)
        
        # 現在時刻を過ぎたエントリーをフィルタ
        now = datetime.now()
        ready_for_retry = []
        remaining_queue = []
        
        for entry in retry_queue:
            retry_time = datetime.fromisoformat(entry['retry_at'])
            if retry_time <= now and entry['attempts'] < 3:  # 最大3回まで再試行
                ready_for_retry.append(entry)
            elif entry['attempts'] < 3:
                remaining_queue.append(entry)
        
        # 残りのキューを保存
        with open(queue_path, 'w', encoding='utf-8') as f:
            json.dump(remaining_queue, f, ensure_ascii=False, indent=2)
        
        return ready_for_retry
    
    async def update_retry_attempt(self, guild_id: str, player_info: Dict, success: bool):
        """再試行の結果を更新"""
        if success:
            # 成功した場合はキューから削除（既に削除されているはず）
            return
        
        queue_path = self.get_retry_queue_path(guild_id)
        if not os.path.exists(queue_path):
            return
        
        with open(queue_path, 'r', encoding='utf-8') as f:
            retry_queue = json.load(f)
        
        player_key = f"{player_info['name']}#{player_info['tag']}"
        
        for entry in retry_queue:
            if f"{entry['player']['name']}#{entry['player']['tag']}" == player_key:
                entry['attempts'] += 1
                entry['retry_at'] = (datetime.now() + timedelta(minutes=2)).isoformat()
                break
        
        with open(queue_path, 'w', encoding='utf-8') as f:
            json.dump(retry_queue, f, ensure_ascii=False, indent=2)
    
    async def get_all_cached_data(self, guild_id: str) -> Dict[str, Any]:
        """すべてのキャッシュデータを取得（古いデータも含む）"""
        cache = await self.load_cache(guild_id)
        result = {}
        for player_key, cached_data in cache.items():
            if 'data' in cached_data:
                result[player_key] = cached_data['data']
        return result