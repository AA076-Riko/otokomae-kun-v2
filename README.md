# 🎤 OTOKO★MAE くん＆OTO♡ME ちゃん

OpenAI Realtime API を使用した**リアルタイム会議ファシリテーター**です。会議音声をリアルタイムで文字起こしし、AI が自動でツッコミ・要約を生成します。

## 機能

- リアルタイム音声認識（OpenAI Realtime API）
- AI による自動ツッコミ生成（2 分間隔）
- 2 つのキャラクターモード
  - **OTOKO☆MAE くんモード**：関西弁でテンポよくツッコミ 🔥
  - **OTO♡ME ちゃんモード**：優しく丁寧なサポート 🐰
- 会議要約の自動生成
- 会議時間の自動計測
- 文字起こし・要約のダウンロード機能

## セットアップ

### 1. 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. OpenAI API キーの設定

#### ローカル環境の場合

環境変数を設定：

```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY="your_api_key_here"

# Windows (コマンドプロンプト)
set OPENAI_API_KEY=your_api_key_here

# Mac/Linux
export OPENAI_API_KEY=your_api_key_here
```

または `.streamlit/secrets.toml` ファイルを編集：

```toml
OPENAI_API_KEY = "your_api_key_here"
```

#### Streamlit Cloud の場合

Streamlit Cloud のダッシュボードで Secrets に `OPENAI_API_KEY` を設定してください。

## 使い方

### アプリの起動

```bash
streamlit run app_realtime.py
```

ブラウザが自動的に開き、アプリが表示されます（通常は `http://localhost:8501`）。

### 会議のファシリテート

1. **サイドバーでキャラクター選択**（OTOKO☆MAE くん / OTO♡ME ちゃん）
2. **🎙️ 録音開始ボタン**を押す
3. **今日の議題を宣言**してから会話を開始
4. AI が自動で：
   - リアルタイムに文字起こし
   - 2 分ごとにツッコミを生成
   - 必要に応じて会議要約を作成
5. **⏹️ 録音停止ボタン**で終了

## 必要な環境

- Python 3.8 以上
- OpenAI API キー（[OpenAI Platform](https://platform.openai.com/)で取得）
  - Realtime API へのアクセス権が必要
- インターネット接続
- マイク（音声入力用）

## トラブルシューティング

### API キーエラーが表示される場合

- 環境変数 `OPENAI_API_KEY` が正しく設定されているか確認
- `.env` ファイルに API キーが設定されているか確認
- Realtime API へのアクセス権があるか確認

### 録音ができない場合

- マイクが正しく接続されているか確認
- OS のマイク権限設定を確認
- PyAudio が正しくインストールされているか確認

### 文字起こしが表示されない場合

- インターネット接続を確認
- ターミナルのログでエラーメッセージを確認
- マイクの音量が適切か確認

## ライセンス

MIT License
