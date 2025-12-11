import streamlit as st
import io
import os
import json
import re
from openai import OpenAI
from datetime import datetime
from audio_recorder_streamlit import audio_recorder

# OpenAIクライアント初期化
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# プロンプト読み込み
def load_prompt(filename):
    """プロンプトファイルを読み込む"""
    try:
        with open(f"prompts/{filename}", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        st.error(f"プロンプト読み込みエラー: {e}")
        return ""

# 音声を文字起こし
def transcribe_audio(audio_bytes):
    """音声バイトデータをWhisperで文字起こし"""
    try:
        # 音声ファイルとして送信
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"
        
        # Whisper APIで文字起こし
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="ja"
        )
        
        return transcript.text
    except Exception as e:
        st.error(f"文字起こしエラー: {e}")
        return None

# ツッコミ生成
def generate_tsukkomi(transcript_text, prompt_type="otokomae"):
    """文字起こしテキストからツッコミを生成"""
    try:
        # プロンプト選択
        prompt_file = "otokомae_prompt.txt" if prompt_type == "otokomae" else "tsukkomi_prompt.txt"
        system_prompt = load_prompt(prompt_file)
        
        if not system_prompt:
            return "プロンプトが読み込めませんでした。"
        
        # GPT-4でツッコミ生成
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"会議テキスト:\n{transcript_text}"}
            ],
            temperature=0.8
        )
        
        response_text = response.choices[0].message.content
        
        # JSONをパースして整形
        try:
            # JSONブロックを抽出（```json...```の形式に対応）
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 生のJSONの場合
                json_str = response_text
            
            data = json.loads(json_str)
            
            # should_speakがfalseの場合
            if not data.get("should_speak", True):
                return None
            
            # replyの内容を整形して返す
            reply = data.get("reply", {})
            tsukkomi = reply.get("tsukkomi", "")
            
            # ツッコミがある場合のみ返す
            if tsukkomi:
                return tsukkomi
            else:
                return None
                
        except (json.JSONDecodeError, KeyError, AttributeError):
            # JSONパースに失敗した場合は生のテキストを返す
            return response_text
        
    except Exception as e:
        st.error(f"ツッコミ生成エラー: {e}")
        return None

# 要約生成
def generate_summary(transcript_text):
    """文字起こしテキストから要約を生成"""
    try:
        summary_prompt = load_prompt("summary_prompt.txt")
        
        if not summary_prompt:
            return "要約プロンプトが読み込めませんでした。"
        
        # GPT-4で要約生成
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": summary_prompt},
                {"role": "user", "content": transcript_text}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"要約生成エラー: {e}")
        return None


# Streamlitアプリのメイン
def main():
    st.set_page_config(
        page_title="OTOKO★MAEくん",
        page_icon="🎤",
        layout="wide"
    )
    
    st.title("OTOKO★MAEくん＆OTO♡MEちゃん")
    st.caption("💡 音声録音で文字起こし＆ツッコミ生成")
    
    with st.expander("📖 使い方", expanded=False):
        st.markdown("""
        **1.** サイドバーでキャラクターモード選択 → **2.** 録音ボタンを押して会話 → **3.** 停止ボタンで処理
        
        - 録音するたびにAIが文字起こし・ツッコミを生成します
        - 要約は「会議要約を生成」ボタンでいつでも作成可能です
        
        ### ⚠️ 注意事項（デプロイ版の制限）
        - **手動録音のみ**: マイクボタンを押して録音開始・停止を行ってください
        - **録音時間**: 最大5分まで（それ以上は自動停止します）
        - ファイルサイズが大きすぎる場合はエラーになります
        - 文字起こし、ツッコミの表示はリアルタイムでは行えません。録音停止後に処理されます
        - マイクボタンの色で状態確認: 🔴赤=録音中 / 🔵青=待機中
        """)
    
    st.divider()
    
    # セッション状態の初期化
    if "transcripts" not in st.session_state:
        st.session_state.transcripts = []
    if "tsukkomi_history" not in st.session_state:
        st.session_state.tsukkomi_history = []
    if "full_transcript" not in st.session_state:
        st.session_state.full_transcript = ""
    if "chunk_counter" not in st.session_state:
        st.session_state.chunk_counter = 0
    if "last_audio_hash" not in st.session_state:
        st.session_state.last_audio_hash = None
    if "is_recording" not in st.session_state:
        st.session_state.is_recording = False
    if "meeting_start_time" not in st.session_state:
        st.session_state.meeting_start_time = None
    if "meeting_end_time" not in st.session_state:
        st.session_state.meeting_end_time = None
    if "meeting_start_time" not in st.session_state:
        st.session_state.meeting_start_time = None
    if "meeting_end_time" not in st.session_state:
        st.session_state.meeting_end_time = None
    
    # サイドバー設定
    with st.sidebar:
        st.header("設定")
        
        # キャラクター選択
        character = st.radio(
            "キャラクター選択",
            ["OTOKO☆MAEくんモード", "OTO♡MEちゃんモード"],
            index=0,
            help="OTOKO☆MAEくんモード：関西弁でテンポよくツッコミ 🔥  \nOTO♡MEちゃんモード：優しく丁寧なサポート 🐰"
        )
        prompt_type = "otokomae" if "OTOKO☆MAE" in character else "otome"
        
        st.divider()
        
        # 要約ボタン
        if st.button("📋 会議要約を生成", width="stretch", disabled=len(st.session_state.full_transcript) == 0):
            with st.spinner("要約を生成中..."):
                summary = generate_summary(st.session_state.full_transcript)
                st.session_state.summary_result = summary
            st.success("要約完了！")
            st.rerun()
        
        # クリアボタン
        if st.button("🗑️ すべてクリア", width="stretch"):
            st.session_state.transcripts = []
            st.session_state.tsukkomi_history = []
            st.session_state.full_transcript = ""
            st.session_state.chunk_counter = 0
            st.session_state.last_audio_hash = None
            st.session_state.meeting_start_time = None
            st.session_state.meeting_end_time = None
            if hasattr(st.session_state, 'summary_result'):
                del st.session_state.summary_result
            st.rerun()
        
        st.divider()
        st.markdown(f"**処理済みチャンク:** {st.session_state.chunk_counter}")
        st.markdown(f"**総文字数:** {len(st.session_state.full_transcript)}")
    
    # メインエリア（2:3の比率）
    col1, col2 = st.columns([2, 3])
    
    with col1:
        # === ツッコミエリア ===
        st.subheader("💬 AIツッコミ")
  
        
        if st.session_state.tsukkomi_history:
            # 最新のツッコミを取得
            latest_tsukkomi = st.session_state.tsukkomi_history[-1]
            timestamp = latest_tsukkomi['time']
            tsukkomi_text = latest_tsukkomi['text']
            is_no_tsukkomi = latest_tsukkomi.get('no_tsukkomi', False)
            
            # キャラクター画像と吹き出し
            char_col, bubble_col = st.columns([1, 2])
            
            with char_col:
                # キャラクター画像
                if "OTO♡ME" in character:
                    image_path = "image/otome_chan.jpg"
                else:
                    image_path = "image/otoko_mae_kun.png"
                
                # 画像が存在する場合のみ表示
                if os.path.exists(image_path):
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.image(image_path, use_container_width=True)
            
            with bubble_col:
                # カスタムCSS（色をツッコミ有無で変更）
                if is_no_tsukkomi:
                    gradient = "background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);"
                else:
                    gradient = "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"
                
                st.markdown(f"""
                <style>
                .tsukkomi-bubble {{
                    {gradient}
                    color: white;
                    padding: 20px;
                    border-radius: 20px;
                    margin: 10px 0;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .tsukkomi-time {{
                    font-size: 0.85em;
                    opacity: 0.9;
                    margin-bottom: 8px;
                }}
                .tsukkomi-text {{
                    font-size: 1.1em;
                    font-weight: bold;
                    margin: 10px 0;
                }}
                </style>
                """, unsafe_allow_html=True)
                
                # 最新のツッコミを表示
                st.markdown(f"""
                <div class="tsukkomi-bubble">
                    <div class="tsukkomi-time">🕐 {timestamp}</div>
                    <div class="tsukkomi-text">{tsukkomi_text}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 過去のツッコミ履歴
            if len(st.session_state.tsukkomi_history) > 1:
                with st.expander(f"📜 過去のツッコミ履歴 ({len(st.session_state.tsukkomi_history) - 1}件)"):
                    for tsukkomi_item in reversed(st.session_state.tsukkomi_history[:-1]):
                        past_timestamp = tsukkomi_item['time']
                        past_text = tsukkomi_item['text']
                        
                        st.markdown(f"**🕐 {past_timestamp}**")
                        st.write(f"💬 {past_text}")
                        
        else:
            st.info("💬 マイクボタンを押して録音を停止するとその地点までのツッコミが表示されます")
    
    with col2:
        st.subheader("📝 文字起こし履歴")
        
        # 録音コンポーネントの説明
        st.info("🎤 マイクボタンを押して録音開始 → もう一度押して停止（最大5分）")
        
        # 音声録音コンポーネント（手動制御モード、5分制限）
        audio_bytes = audio_recorder(
            text="",
            recording_color="#e74c3c",
            neutral_color="#3498db",
            icon_name="microphone",
            icon_size="2x",
            energy_threshold=(-1.0, 1.0),  # 自動音声検出を無効化
            pause_threshold=300.0,  # 5分で自動停止（ファイルサイズ制限対策）
        )
        
        # 音声データを受信した場合
        if audio_bytes:
            # ファイルサイズチェック（Whisper APIは25MB制限）
            audio_size_mb = len(audio_bytes) / (1024 * 1024)
            if audio_size_mb > 24:  # 24MBで制限（余裕を持たせる）
                st.error(f"⚠️ 音声ファイルが大きすぎます（{audio_size_mb:.1f}MB）。録音時間を短くしてください（最大5分程度）。")
            else:
                # ハッシュを計算して重複処理を防ぐ
                import hashlib
                audio_hash = hashlib.md5(audio_bytes).hexdigest()
                
                if audio_hash != st.session_state.last_audio_hash:
                    st.session_state.last_audio_hash = audio_hash
                    st.session_state.chunk_counter += 1
                    chunk_num = st.session_state.chunk_counter
                    
                    with st.spinner(f"🎵 チャンク #{chunk_num} を処理中..."):
                        # 文字起こし
                        transcript = transcribe_audio(audio_bytes)
                    
                    if transcript:
                        # 記録
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        st.session_state.transcripts.append({
                            "chunk": chunk_num,
                            "time": timestamp,
                            "text": transcript
                        })
                        st.session_state.full_transcript += f"\n[{timestamp}] {transcript}"
                        
                        # 最初のチャンクで会議開始時刻を記録
                        if st.session_state.meeting_start_time is None:
                            import time
                            st.session_state.meeting_start_time = time.time()
                        
                        # ツッコミ生成
                        with st.spinner("ツッコミを生成中..."):
                            tsukkomi = generate_tsukkomi(st.session_state.full_transcript, prompt_type)
                            
                            if tsukkomi:
                                st.session_state.tsukkomi_history.append({
                                    "chunk": chunk_num,
                                    "time": timestamp,
                                    "text": tsukkomi,
                                    "no_tsukkomi": False
                                })
                            else:
                                # ツッコミ不要の場合も履歴に記録
                                st.session_state.tsukkomi_history.append({
                                    "chunk": chunk_num,
                                    "time": timestamp,
                                    "text": "ツッコミは不要みたい！",
                                    "no_tsukkomi": True
                                })
                        
                        st.success(f"✅ チャンク #{chunk_num} の文字起こし完了！")
                        st.rerun()
        
        # 文字起こし表示
        if st.session_state.transcripts:
            # 最新が上に来るように逆順で結合
            transcript_items = [f"[{item['time']}] {item['text']}" for item in st.session_state.transcripts]
            reversed_text = "\n\n".join(reversed(transcript_items))
            st.text_area(
                "文字起こし履歴",
                reversed_text,
                height=300,
                key=f"transcript_display_{len(st.session_state.transcripts)}",
                label_visibility="collapsed"
            )


        
        # ダウンロードボタン
        if st.session_state.full_transcript:
            st.download_button(
                label="📥 文字起こしをダウンロード",
                data=st.session_state.full_transcript,
                file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    # === 要約エリア（下部全体） ===
    st.divider()
    st.subheader("📋 会議要約")
    
    if hasattr(st.session_state, 'summary_result') and st.session_state.summary_result:
        with st.expander("要約を表示", expanded=True):
            st.markdown(st.session_state.summary_result)
            
            st.download_button(
                label="📥 要約をダウンロード",
                data=st.session_state.summary_result,
                file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    else:
        st.info("サイドバーの「会議要約を生成」ボタンを押してください")


if __name__ == "__main__":
    main()