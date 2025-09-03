import json
import os
import asyncio
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

class DataManager:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(exist_ok=True)
    
    def _get_guild_file_path(self, guild_id: str) -> Path:
        """ギルドのデータファイルパスを取得"""
        return self.data_dir / f"{guild_id}.json"
    
    async def get_guild_players(self, guild_id: str) -> List[Dict]:
        """ギルドの全プレイヤーデータを取得"""
        file_path = self._get_guild_file_path(guild_id)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                guild_data = json.load(f)
            
            # puuidをキーとしたplayersデータを配列形式に変換
            players = []
            for puuid, player_data in guild_data.get("players", {}).items():
                player_data["puuid"] = puuid  # puuidを明示的に追加
                players.append(player_data)
            
            return players
            
        except (FileNotFoundError, json.JSONDecodeError):
            # データディレクトリを作成
            os.makedirs(self.data_dir, exist_ok=True)
            return []
        except Exception as e:
            print(f"Error reading guild data: {e}")
            return []
    
    
    async def store_player_data(self, guild_id: str, user_id: str, player_data: Dict):
        """プレイヤーデータを保存（puuidをキーとして使用）"""
        file_path = self._get_guild_file_path(guild_id)
        
        # 既存データを読み込み
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                guild_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            guild_data = {}
        
        # プレイヤーデータを更新（puuidをキーとして使用）
        if "players" not in guild_data:
            guild_data["players"] = {}
        
        player_data["updated_at"] = datetime.now().isoformat()
        
        # puuidをキーとして保存
        puuid = player_data.get("puuid")
        if puuid:
            guild_data["players"][puuid] = player_data
        
        # ファイルに保存
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(guild_data, f, ensure_ascii=False, indent=2)
    
    async def remove_player_data(self, guild_id: str, user_id: str) -> bool:
        """プレイヤーデータを削除（そのDiscordユーザーの最新アカウント）"""
        file_path = self._get_guild_file_path(guild_id)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                guild_data = json.load(f)
            
            if "players" not in guild_data:
                return False
            
            # Discord IDに紐づく最新のプレイヤーを検索
            target_puuid = None
            latest_time = ""
            
            for puuid, player_data in guild_data["players"].items():
                if player_data.get("discord_user_id") == user_id:
                    updated_at = player_data.get("updated_at", "")
                    if updated_at > latest_time:
                        latest_time = updated_at
                        target_puuid = puuid
            
            if target_puuid:
                del guild_data["players"][target_puuid]
                
                # ファイルに保存
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(guild_data, f, ensure_ascii=False, indent=2)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error removing player data: {e}")
            return False
    
    async def store_auto_update_config(self, guild_id: str, config: Dict):
        """自動更新設定を保存"""
        file_path = self._get_guild_file_path(guild_id)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                guild_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            guild_data = {}
        
        guild_data["auto_update"] = config
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(guild_data, f, ensure_ascii=False, indent=2)
    
    async def get_auto_update_config(self, guild_id: str) -> Optional[Dict]:
        """自動更新設定を取得"""
        file_path = self._get_guild_file_path(guild_id)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                guild_data = json.load(f)
            return guild_data.get("auto_update")
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    async def get_all_auto_update_configs(self) -> Dict[str, Dict]:
        """すべてのギルドの自動更新設定を取得"""
        configs = {}
        
        for file_path in self.data_dir.glob("*.json"):
            guild_id = file_path.stem
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    guild_data = json.load(f)
                
                auto_update = guild_data.get("auto_update")
                if auto_update:
                    configs[guild_id] = auto_update
                    
            except (json.JSONDecodeError, FileNotFoundError):
                continue
        
        return configs