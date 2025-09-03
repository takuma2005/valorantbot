# Valorant Leaderboard Discord Bot

ValorantのランクをDiscordサーバー内でLeaderboard形式で表示するPython製Discordボットです。

## 機能

- 🏆 サーバーメンバーのValorantランクLeaderboard表示
- 📝 個人アカウント登録/登録解除
- 📊 個人ランク情報表示
- 🌏 地域別サポート (AP, NA, EU, KR, LATAM, BR)

## セットアップ

### 1. Pythonとライブラリのインストール

```bash
pip install -r requirements.txt
```

または仮想環境を使用:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. 環境設定

1. `.env.example`を`.env`にコピー
2. 必要な設定値を入力:

```env
# Discord設定
DISCORD_TOKEN=あなたのDiscord Bot Token
DISCORD_GUILD_ID=テスト用ギルドID（オプション）

# Valorant API設定
VALORANT_API_KEY=Henrik Valorant APIキー

# デフォルト地域
DEFAULT_REGION=ap
```

### 3. Discord Bot作成

1. [Discord Developer Portal](https://discord.com/developers/applications)にアクセス
2. 新しいApplicationを作成
3. Bot設定で以下の権限を有効化:
   - `applications.commands` (スラッシュコマンド)
   - `bot` (基本Bot権限)
4. Bot TokenとClient IDを`.env`に設定

### 4. Valorant APIキー取得

1. [Henrik Valorant API Discord](https://discord.gg/X3GaVkX2YN)に参加
2. APIキーを取得
3. `.env`ファイルに設定

## 使用方法

### Bot起動

```bash
python bot.py
```

### コマンド

- `/register <name> <tag> [region]` - Valorantアカウントを登録
- `/leaderboard [region]` - サーバーのLeaderboard表示
- `/rank <player> [region]` - 個人ランク情報表示
- `/unregister` - 自分の登録を解除
- `/auto-leaderboard <message_id> [enable]` - 指定メッセージの5分間隔自動更新（管理者のみ）

### 使用例

```
/register PlayerName JP1
/leaderboard
/rank PlayerName#JP1
/unregister

# 自動更新設定の手順:
# 1. まずリーダーボードを表示
/leaderboard
# 2. 表示されたメッセージを右クリック→「IDをコピー」
# 3. そのメッセージIDで自動更新を有効化
/auto-leaderboard 1234567890123456789 有効にする
```

## 技術仕様

- **言語**: Python 3.8+
- **Discord API**: discord.py
- **HTTP**: aiohttp for async requests
- **データストレージ**: JSONファイル（本格運用時はデータベース推奨）

## API制限

- Basic Key: 30 requests/分
- Advanced Key: 90 requests/分

大きなサーバーでの使用時はAdvanced Keyの取得を推奨します。

## 注意事項

- このBotはRiot Games公式ではありません
- ユーザーデータの取得には同意が必要です
- レート制限を守って使用してください