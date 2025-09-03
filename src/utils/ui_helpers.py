import discord
from typing import Dict, Any

class UIHelpers:
    @staticmethod
    def get_rank_icon_url(rank_name: str) -> str:
        """ランクに対応するアイコンURLを取得"""
        rank_tier_mapping = {
            "Radiant": 27,
            "Immortal 3": 26, "Immortal 2": 25, "Immortal 1": 24,
            "Ascendant 3": 23, "Ascendant 2": 22, "Ascendant 1": 21,
            "Diamond 3": 20, "Diamond 2": 19, "Diamond 1": 18,
            "Platinum 3": 17, "Platinum 2": 16, "Platinum 1": 15,
            "Gold 3": 14, "Gold 2": 13, "Gold 1": 12,
            "Silver 3": 11, "Silver 2": 10, "Silver 1": 9,
            "Bronze 3": 8, "Bronze 2": 7, "Bronze 1": 6,
            "Iron 3": 5, "Iron 2": 4, "Iron 1": 3,
            "Unrated": 0
        }
        
        tier_id = rank_tier_mapping.get(rank_name, 0)
        return f"https://media.valorant-api.com/competitivetiers/03621f52-342b-cf4e-4f86-9350a49c6d04/{tier_id}/smallicon.png"
    
    @staticmethod
    def get_rank_emoji(rank_name: str) -> str:
        """ランクに対応する絵文字を取得"""
        # カスタム絵文字ID
        custom_rank_emojis = {
            "Radiant": "<:valorantradiant:1309884284760490054>",
            "Immortal 3": "<:valorantimmortal3:1309884281966956618>",
            "Immortal 2": "<:valorantimmortal2:1309884246869147749>",
            "Immortal 1": "<:valorantimmortal1:1309884245447147591>",
            "Immortal": "<:valorantimmortal3:1309884281966956618>",
            "Ascendant 3": "<:valorantascendant3:1309884249683525673>",
            "Ascendant 2": "<:valorantascendant2:1309884292704505887>",
            "Ascendant 1": "<:valorantascendant1:1309884267148476476>",
            "Ascendant": "<:valorantascendant3:1309884249683525673>",
            "Diamond 3": "<:valorantdiamond3:1309884243668762634>",
            "Diamond 2": "<:valorantdiamond2:1309884256444616885>",
            "Diamond 1": "<:valorantdiamond1:1309884275193020487>",
            "Diamond": "<:valorantdiamond3:1309884243668762634>",
            "Platinum 3": "<:valorantplatinum3:1309884620916920390>",
            "Platinum 2": "<:valorantplatinum2:1309884251314982922>",
            "Platinum 1": "<:valorantplatinum1:1309884276690387004>",
            "Platinum": "<:valorantplatinum3:1309884620916920390>",
            "Gold 3": "<:valorantgold3:1309884252451508285>",
            "Gold 2": "<:valorantgold2:1309884238069235803>",
            "Gold 1": "<:valorantgold1:1309884278192083065>",
            "Gold": "<:valorantgold3:1309884252451508285>",
            "Silver 3": "<:valorantsilver3:1309884499751866388>",
            "Silver 2": "<:valorantsilver2:1309884556874223616>",
            "Silver 1": "<:valorantsilver1:1309884522351038504>",
            "Silver": "<:valorantsilver3:1309884499751866388>",
            "Bronze 3": "<:valorantbronze3:1309884241739382886>",
            "Bronze 2": "<:valorantbronze2:1309884263461552188>",
            "Bronze 1": "<:valorantbronze1:1309884259997192192>",
            "Bronze": "<:valorantbronze3:1309884241739382886>",
            "Iron 3": "<:valorantiron3:1309884248274112543>",
            "Iron 2": "<:valorantiron2:1309884288434569236>",
            "Iron 1": "<:valorantiron1:1309884239369736232>",
            "Iron": "<:valorantiron3:1309884248274112543>",
            "Unrated": "<:valorant_unranked:1378116951607345172>"
        }
        
        # フォールバック用の通常絵文字
        fallback_emojis = {
            "Radiant": "✨",
            "Immortal": "💎",
            "Ascendant": "🌟",
            "Diamond": "💍",
            "Platinum": "🔷",
            "Gold": "🏅",
            "Silver": "🥈",
            "Bronze": "🥉",
            "Iron": "⚡",
            "Unrated": "❓"
        }
        
        # まず完全一致を試す（例: "Immortal 3"）
        if rank_name in custom_rank_emojis:
            return custom_rank_emojis[rank_name]
        
        # 完全一致がない場合、ランク名の最初の単語で試す（例: "Immortal"）
        rank_base = rank_name.split()[0] if rank_name and " " in rank_name else rank_name
        if rank_base in custom_rank_emojis:
            return custom_rank_emojis[rank_base]
        
        # フォールバック
        return fallback_emojis.get(rank_base, "❓")
    
    @staticmethod
    def get_rank_color(rank_name: str) -> int:
        """ランクに対応する色を取得"""
        rank_colors = {
            "Radiant": 0xFFFFFF,      # 白
            "Immortal": 0x8A2BE2,     # 紫
            "Ascendant": 0x00FF7F,    # 緑
            "Diamond": 0x87CEEB,      # 水色
            "Platinum": 0x40E0D0,     # ターコイズ
            "Gold": 0xFFD700,         # 金
            "Silver": 0xC0C0C0,       # 銀
            "Bronze": 0xCD7F32,       # 銅
            "Iron": 0x808080,         # 灰色
            "Unrated": 0x36393F       # 暗い灰色
        }
        
        rank_base = rank_name.split()[0] if rank_name and " " in rank_name else rank_name
        return rank_colors.get(rank_base, 0xFA4454)  # デフォルト（Valorant赤）
    
    @staticmethod
    def create_progress_bar(current_rr: int, max_rr: int = 100, length: int = 10) -> str:
        """RRプログレスバーを作成"""
        if max_rr <= 0:
            return "▱" * length
        
        filled = int((current_rr / max_rr) * length)
        filled = min(filled, length)  # 最大値を超えないように
        
        bar = "▰" * filled + "▱" * (length - filled)
        return f"{bar} {current_rr}/{max_rr}RR"
    
    @staticmethod
    def create_relative_progress_bar(player_rr: int, top_player_rr: int, bottom_player_rr: int, length: int = 15) -> str:
        """1位を100%、最下位を0%とした相対プログレスバーを作成"""
        if top_player_rr <= 0 or player_rr <= 0:
            return "▱" * length + " 0%"
        
        # 最下位を0%、1位を100%とした相対計算
        if top_player_rr == bottom_player_rr:
            # 全員同じRRの場合は100%
            percentage = 100.0
        else:
            rr_range = top_player_rr - bottom_player_rr
            player_offset = player_rr - bottom_player_rr
            percentage = (player_offset / rr_range) * 100
        
        percentage = max(0, min(percentage, 100))  # 0-100%の範囲に制限
        filled = int((percentage / 100) * length)
        filled = min(filled, length)
        
        bar = "▰" * filled + "▱" * (length - filled)
        return f"{bar} {percentage:.0f}%"
    
    @staticmethod
    def get_position_emoji(position: int) -> str:
        """順位に応じた特別な絵文字を取得"""
        position_emojis = {
            1: "👑",    # 王冠
            2: "🥈",    # 銀メダル
            3: "🥉",    # 銅メダル
            4: "🔸",
            5: "🔹"
        }
        
        if position <= 5:
            return position_emojis.get(position, "🔸")
        elif position <= 10:
            return "⭐"
        else:
            return "🔵"
    
    @staticmethod
    def format_rank_display(rank_name: str, rr: int) -> str:
        """ランク表示をフォーマット"""
        rank_emoji = UIHelpers.get_rank_emoji(rank_name)
        
        # Immortal/Radiantの場合は特別な表示
        if "Immortal" in rank_name or "Radiant" in rank_name:
            return f"{rank_emoji} **{rank_name}** `{rr}RR`"
        else:
            # 通常のランクはプログレスバー付き
            progress = UIHelpers.create_progress_bar(rr, 100, 8)
            return f"{rank_emoji} **{rank_name}**\n`{progress}`"
    
    
    @staticmethod
    def create_leaderboard_title(region: str, is_auto: bool = False) -> str:
        """リーダーボードのタイトルを作成"""
        auto_text = " (最新)" if not is_auto else " (自動更新)"
        title = f"サーバー内ランキング{auto_text}"
        # 中央揃えのためのスペースを計算（おおよそ）
        padding = " " * ((50 - len(title)) // 2)
        return f"{padding}{title}"