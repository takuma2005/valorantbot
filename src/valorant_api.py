import aiohttp
import asyncio
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote
from .rank_cache import RankCache

class ValorantAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.henrikdev.xyz/valorant"
        self.headers = {"Authorization": api_key}
        self.cache = RankCache()
    
    async def get_account(self, name: str, tag: str) -> Dict:
        """アカウント情報をRiot IDで取得"""
        url = f"{self.base_url}/v2/account/{quote(name)}/{quote(tag)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise ValueError(f"プレイヤー {name}#{tag} が見つかりませんでした")
                elif response.status == 429:
                    raise RuntimeError("API制限に達しました")
                else:
                    raise RuntimeError(f"APIエラー: {response.status}")
    
    async def get_player_rank(self, region: str, name: str, tag: str, season: Optional[str] = None) -> Dict:
        """プレイヤーの競合ランク情報を取得"""
        url = f"{self.base_url}/v3/mmr/{region}/pc/{quote(name)}/{quote(tag)}"
        params = {"season": season} if season else {}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise ValueError(f"プレイヤー {name}#{tag} のランク情報が見つかりませんでした")
                elif response.status == 429:
                    raise RuntimeError("API制限に達しました")
                else:
                    raise RuntimeError(f"APIエラー: {response.status}")
    
    async def get_leaderboard_data(self, region: str, players: List[Dict[str, str]], guild_id: str = None) -> Tuple[List[Dict], List[Dict]]:
        """複数プレイヤーのランク情報を一括取得（キャッシュ付き）
        Returns: (成功したデータのリスト, 失敗したプレイヤーのリスト)
        """
        success_results = []
        failed_players = []
        
        async def get_single_player(player):
            player_key = f"{player['name']}#{player['tag']}"
            
            # キャッシュから取得を試みる
            if guild_id:
                cached_data = await self.cache.get_player_data(guild_id, player_key)
                if cached_data:
                    print(f"Using cached data for {player_key}")
                    return cached_data, False  # (data, is_from_api)
            
            # APIから取得
            try:
                rank_data = await self.get_player_rank(region, player["name"], player["tag"])
                result = {
                    "name": player["name"],
                    "tag": player["tag"],
                    **rank_data["data"]
                }
                
                # キャッシュに保存
                if guild_id:
                    await self.cache.update_player_data(guild_id, player_key, result)
                
                return result, True  # (data, is_from_api)
            except Exception as e:
                print(f"Failed to get rank for {player_key}: {e}")
                
                # API制限エラーの場合、キャッシュから古いデータを使用
                if guild_id and "API制限" in str(e):
                    cached_data = await self.cache.get_player_data(guild_id, player_key)
                    if cached_data:
                        print(f"Using stale cached data for {player_key} due to API limit")
                        await self.cache.mark_update_failed(guild_id, player_key)
                        return cached_data, False
                    
                    # キャッシュもない場合、全キャッシュから取得を試みる
                    all_cache = await self.cache.get_all_cached_data(guild_id)
                    if player_key in all_cache:
                        print(f"Using old cached data for {player_key}")
                        return all_cache[player_key], False
                
                return None, False
        
        # API制限を考慮して並列実行数を制限
        semaphore = asyncio.Semaphore(3)  # 同時実行数3に制限
        
        async def bounded_request(player):
            async with semaphore:
                return await get_single_player(player)
        
        tasks = [bounded_request(player) for player in players]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果を分類
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_players.append(players[i])
            elif result is not None:
                data, is_from_api = result
                if data is not None:
                    success_results.append(data)
                else:
                    failed_players.append(players[i])
                    if guild_id:
                        # 再試行キューに追加
                        await self.cache.add_to_retry_queue(guild_id, players[i])
        
        return success_results, failed_players
    
    def sort_by_rank(self, players_data: List[Dict]) -> List[Dict]:
        """ランクでプレイヤーをソート（高いランクから低いランクへ）"""
        rank_order = {
            "Radiant": 8,
            "Immortal": 7, 
            "Ascendant": 6,
            "Diamond": 5,
            "Platinum": 4,
            "Gold": 3,
            "Silver": 2,
            "Bronze": 1,
            "Iron": 0,
            "Unrated": -1
        }
        
        def get_rank_value(player):
            current = player.get("current", {})
            tier = current.get("tier", {})
            current_tier = tier.get("name", "Unrated")
            
            if current_tier == "Unrated":
                return (-1, 0, 0)
            
            # ランク名の最初の部分を取得 (例: "Immortal 3" -> "Immortal")
            rank_name = current_tier.split()[0] if " " in current_tier else current_tier
            rank_value = rank_order.get(rank_name, -2)
            
            # 同じランク種類内でのティア番号を取得 (例: "Ascendant 2" -> 2)
            tier_number = 0
            if " " in current_tier:
                try:
                    tier_number = int(current_tier.split()[1])
                except (ValueError, IndexError):
                    tier_number = 0
            
            # 同じランク内でのRRでソート
            rr = current.get("rr", 0)
            return (rank_value, tier_number, rr)
        
        return sorted(players_data, key=get_rank_value, reverse=True)