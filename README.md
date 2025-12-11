# 🎤 OTOKO★MAE くん＆OTO♡ME ちゃん

**Streamlit + カスタムコンポーネント**で実現する、リアルタイム AI 会議ファシリテーターです。ブラウザで録音し、指定時間ごとに自動で文字起こし・ツッコミ・要約を生成します。

## ✨ 特徴

- **ブラウザ録音**: MediaRecorder API を使用したシンプルな録音
- **自動チャンク送信**: 30〜180 秒ごとに音声を自動送信・処理
- **リアルタイム文字起こし**: OpenAI Whisper API で即座に文字起こし
- **AI ツッコミ**: 会議の進行を AI がサポート
  - **OTOKO☆MAE くんモード**: 関西弁でテンポよくツッコミ 🔥
  - **OTO♡ME ちゃんモード**: 優しく丁寧なサポート 🐰
- **会議要約**: 会議全体の要約を自動生成
- **Streamlit のみで完結**: 追加のサーバー不要、デプロイが簡単！

## 🚀 セットアップ

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

または `.env` ファイルを作成：

```
OPENAI_API_KEY=your_api_key_here
```

#### Streamlit Cloud の場合

Streamlit Cloud のダッシュボードで Secrets に `OPENAI_API_KEY` を設定してください。

## 💻 使い方

### アプリの起動

```bash
streamlit run app.py
```

ブラウザが自動的に開き、アプリが表示されます（通常は `http://localhost:8501`）。

### 会議のファシリテート

1. **サイドバーでキャラクター選択**（OTOKO☆MAE くん / OTO♡ME ちゃん）
2. **チャンク長を設定**（30〜180 秒、デフォルト 60 秒）
3. **🎤 録音開始ボタン**を押す
4. **今日の議題を宣言**してから会話を開始
5. AI が自動で：
   - 設定した時間ごとに文字起こし
   - チャンクごとにツッコミを生成
   - 会議全体を記録
6. **⏹️ 録音停止ボタン**で終了
7. **📊 要約を生成ボタン**で会議全体の要約を作成

## 📁 プロジェクト構造

```
otokomae-kun-1/
├── app.py                          # メインアプリケーション
├── requirements.txt                # Python依存関係（streamlit, openai, python-dotenv）
├── components/
│   └── audio_recorder/             # カスタム録音コンポーネント
│       ├── __init__.py             # Pythonインターフェース
│       └── frontend/
│           └── index.html          # ブラウザ録音UI（MediaRecorder API）
├── prompts/
│   ├── otokомae_prompt.txt         # OTOKO★MAEくんプロンプト
│   ├── tsukkomi_prompt.txt         # OTO♡MEちゃんプロンプト
│   └── summary_prompt.txt          # 要約生成プロンプト
└── image/                          # 画像素材
```

## 🌐 Streamlit Cloud でのデプロイ

1. GitHub リポジトリを Streamlit Cloud に接続
2. メインファイルパスを `app.py` に設定
3. Secrets に `OPENAI_API_KEY` を追加
4. デプロイ完了！

## 🛠️ 必要な環境

- Python 3.8 以上
- OpenAI API キー（[OpenAI Platform](https://platform.openai.com/)で取得）
  - Whisper API と GPT-4 へのアクセス
- インターネット接続
- マイク（音声入力用）
- モダンブラウザ（Chrome, Firefox, Edge 等）

## ❓ トラブルシューティング

### API キーエラーが表示される場合

- 環境変数 `OPENAI_API_KEY` が正しく設定されているか確認
- `.env` ファイルに API キーが設定されているか確認

### 録音ができない場合

- ブラウザのマイク権限を確認
- HTTPS または localhost で実行されているか確認（MediaRecorder API の要件）

### 文字起こしが表示されない場合

- インターネット接続を確認
- ブラウザの開発者コンソールでエラーメッセージを確認
- マイクの音量が適切か確認

## ライセンス

MIT License
