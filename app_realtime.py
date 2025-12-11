import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime
import threading
import queue


from services.realtime_transcription import RealtimeTranscriptionService
from services.facilitation import FacilitationService

# .envファイルから環境変数を読み込み
load_dotenv()

# ページ設定
st.set_page_config(
    page_title="OTOKO★MAEくん",
    page_icon="🎤",
    layout="wide"
)

# APIキー取得
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("OpenAI APIキーが設定されていません。")
    st.stop()

client = OpenAI(api_key=api_key)

# セッション状態の初期化
if 'tsukkomi_mode' not in st.session_state:
    st.session_state.tsukkomi_mode = "OTOKO☆MAEくんモード"  # デフォルト
if 'tsukkomi_interval' not in st.session_state:
    st.session_state.tsukkomi_interval = 60  # デフォルト1分
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'transcripts' not in st.session_state:
    st.session_state.transcripts = []
if 'full_text' not in st.session_state:
    st.session_state.full_text = ""
if 'tsukkomi_list' not in st.session_state:
    st.session_state.tsukkomi_list = []
if 'summary_result' not in st.session_state:
    st.session_state.summary_result = ""
if 'last_tsukkomi_time' not in st.session_state:
    st.session_state.last_tsukkomi_time = 0
if 'realtime_service' not in st.session_state:
    st.session_state.realtime_service = None
if 'event_loop' not in st.session_state:
    st.session_state.event_loop = None
if 'result_queue' not in st.session_state:
    st.session_state.result_queue = queue.Queue()
if 'is_recording_flag' not in st.session_state:
    st.session_state.is_recording_flag = threading.Event()
if 'recording_start_time' not in st.session_state:
    st.session_state.recording_start_time = None
if 'recording_end_time' not in st.session_state:
    st.session_state.recording_end_time = None


st.title("OTOKO★MAEくん＆OTO♡MEちゃん")
st.caption("💡 リアルタイムで文字起こし＆ツッコミ生成")


with st.expander("📖 使い方", expanded=False):
    st.markdown("""
    **1.** サイドバーでキャラクターモードの選択 → **2.** 録音開始ボタンを押す → **3.** 議題を宣言して会議開始
    
    - AIが自動でツッコミ・要約を生成します（おおよそ2分間隔）
    - 要約は「会議要約を生成」ボタンでいつでも作成可能です
    """)

st.divider()

# サービスのインスタンス化
facilitation_service = FacilitationService(client, mode=st.session_state.tsukkomi_mode)

# ======================
# RealtimeAPI処理スレッド
# ======================
def realtime_worker(api_key, result_queue, is_recording_flag, facilitation_service, tsukkomi_interval):
    """リアルタイム文字起こし"""
    try:
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        service = RealtimeTranscriptionService(api_key)
        
        async def run():
            await service.connect()
            

            recording_task = asyncio.create_task(service.start_recording())
            
            # 最後のツッコミ時刻
            last_tsukkomi_time = 0
            full_text_buffer = ""
            
            # 文字起こし結果を処理
            while is_recording_flag.is_set():
                try:
                    result = await asyncio.wait_for(
                        service.get_transcription(),
                        timeout=1.0
                    )
          
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    text = result['text']
                    entry = f"[{timestamp}] {text}"
                    
                    full_text_buffer += ("\n\n" if full_text_buffer else "") + entry
                    
                    print(f"[{timestamp}] 文字起こし: {text}")
                    
          
                    result_queue.put({
                        'type': 'transcript',
                        'entry': entry
                    })
                    
                    # ツッコミ生成（ユーザー設定の間隔）
                    import time
                    current_time = time.time()
                    if current_time - last_tsukkomi_time > tsukkomi_interval and full_text_buffer:
                        print(f"[{timestamp}] ツッコミ生成開始...")
                        tsukkomi_result = facilitation_service.generate_tsukkomi(full_text_buffer)
                        
                        # 生成したら時刻を更新（should_speakに関わらず）
                        last_tsukkomi_time = current_time
                        
                        if tsukkomi_result and tsukkomi_result.get('should_speak', False):
                            result_queue.put({
                                'type': 'tsukkomi',
                                'timestamp': timestamp,
                                'data': tsukkomi_result
                            })
                            print(f"[{timestamp}] ツッコミ生成完了 - 表示")
                        else:
                            print(f"[{timestamp}] ツッコミ生成完了 - スキップ（ツッコむ必要なし）")
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"処理エラー: {e}")
                    break
            
            service.is_recording = False
            await service.stop()
        
        loop.run_until_complete(run())
        
    except Exception as e:
        print(f"RealtimeAPIエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        is_recording_flag.clear()

# ======================
# サイドバー
# ======================
with st.sidebar:
    st.header("設定")

    # ツッコミモード選択

    mode = st.radio(
        "キャラクター選択",
        ["OTOKO☆MAEくんモード", "OTO♡MEちゃんモード"],
        index=0 if st.session_state.tsukkomi_mode == "OTOKO☆MAEくんモード" else 1,
        help="OTOKO☆MAEくんモード：関西弁でテンポよくツッコミ 🔥  \nOTO♡MEちゃんモード：優しく丁寧なサポート 🐰",
        disabled=st.session_state.recording  # 録音中は変更不可
    )
    
    # モード変更時の処理
    if mode != st.session_state.tsukkomi_mode:
        st.session_state.tsukkomi_mode = mode
        facilitation_service.set_mode(mode)
        st.rerun()  
    
    # ツッコミ生成頻度の選択
    interval_options = {
        "1分": 60,
        "2分": 120,
        "5分": 300,
        "10分": 600
    }
    
    selected_interval = st.selectbox(
        "ツッコミ生成頻度",
        options=list(interval_options.keys()),
        index=list(interval_options.values()).index(st.session_state.tsukkomi_interval),
        help="AIがツッコミを生成する間隔を選択できます",
        disabled=st.session_state.recording  # 録音中は変更不可
    )
    
    st.session_state.tsukkomi_interval = interval_options[selected_interval]

    st.divider()
    
    # 開始/停止ボタン
    st.text("ボタンを​押し、​今日の​議題を​宣言してから​会話を​開始してください")
    if not st.session_state.recording:
        if st.button("🎙️ 録音開始", type="primary", width="stretch"):
            st.session_state.recording = True
            st.session_state.is_recording_flag.set()
            
            # 録音開始時刻を記録
            import time
            st.session_state.recording_start_time = time.time()
            
            # RealtimeAPIスレッド起動
            thread = threading.Thread(
                target=realtime_worker, 
                args=(api_key, st.session_state.result_queue, st.session_state.is_recording_flag, facilitation_service, st.session_state.tsukkomi_interval),
                daemon=True
            )
            thread.start()
            
            st.rerun()
    else:
        if st.button("⏹️ 録音停止", type="secondary", width="stretch"):
            st.session_state.recording = False
            st.session_state.is_recording_flag.clear()
            
            # 録音終了時刻を記録
            import time
            st.session_state.recording_end_time = time.time()
            
            st.rerun()
    
    # ステータス表示
    if st.session_state.recording:
        st.success("🔴 録音中...")
    else:
        st.info("⚫ 停止中")
    
    st.divider()
    
    # 要約ボタン
    if st.button("📋 会議要約を生成", width="stretch", disabled=len(st.session_state.full_text) == 0):
        with st.spinner("要約を生成中..."):
            summary = facilitation_service.generate_summary(st.session_state.full_text)
            st.session_state.summary_result = summary
        st.success("要約完了！")
        st.rerun()
    
    # クリアボタン
    if st.button("🗑️ すべてクリア", width="stretch"):
        st.session_state.transcripts = []
        st.session_state.full_text = ""
        st.session_state.tsukkomi_list = []
        st.session_state.summary_result = ""
        st.session_state.recording_start_time = None
        st.session_state.recording_end_time = None
        st.rerun()
    
    st.divider()
    

# ======================
# キューから結果を取得
# ======================
queue_count = 0
while not st.session_state.result_queue.empty():
    try:
        result = st.session_state.result_queue.get_nowait()
        queue_count += 1
        
        print(f"[メイン] キューから取得: {result['type']}")
        
        if result['type'] == 'transcript':
            st.session_state.transcripts.append(result['entry'])
            st.session_state.full_text += ("\n\n" if st.session_state.full_text else "") + result['entry']
            # print(f"[メイン] 文字起こし追加: 合計{len(st.session_state.transcripts)}件")
        
        elif result['type'] == 'tsukkomi':
            st.session_state.tsukkomi_list.append({
                'timestamp': result['timestamp'],
                'data': result['data']
            })
            import time
            st.session_state.last_tsukkomi_time = time.time()
            print(f"[メイン] ツッコミ追加: 合計{len(st.session_state.tsukkomi_list)}件")
    
    except queue.Empty:
        break

if queue_count > 0:
    print(f"[メイン] キュー処理完了: {queue_count}件")
if st.session_state.recording:
    print(f"[メイン] 録音中 - フラグ: {st.session_state.is_recording_flag.is_set()}")

# ======================
# メインエリア（1:2の比率）
# ======================
# 会議の経過時間表示
if st.session_state.recording and st.session_state.recording_start_time:
    # 録音中：リアルタイムで経過時間を表示
    import time
    elapsed_seconds = int(time.time() - st.session_state.recording_start_time)
    hours = elapsed_seconds // 3600
    minutes = (elapsed_seconds % 3600) // 60
    seconds = elapsed_seconds % 60
    
    if hours > 0:
        time_display = f"⏱️ **会議時間: {hours:02d}:{minutes:02d}:{seconds:02d}**"
    else:
        time_display = f"⏱️ **会議時間: {minutes:02d}:{seconds:02d}**"
    
    st.markdown(time_display)
elif st.session_state.recording_start_time and st.session_state.recording_end_time:
    # 録音停止後：固定された最終時間を表示
    elapsed_seconds = int(st.session_state.recording_end_time - st.session_state.recording_start_time)
    hours = elapsed_seconds // 3600
    minutes = (elapsed_seconds % 3600) // 60
    seconds = elapsed_seconds % 60
    
    if hours > 0:
        time_display = f"⏱️ **会議時間: {hours:02d}:{minutes:02d}:{seconds:02d}** (終了)"
    else:
        time_display = f"⏱️ **会議時間: {minutes:02d}:{seconds:02d}** (終了)"
    
    st.markdown(time_display)

col1, col2 = st.columns([2, 3])

with col1:
    # === ツッコミエリア（上部） ===
    st.subheader("💬 AIツッコミ")
    
    if len(st.session_state.tsukkomi_list) > 0:
        # 最新のツッコミを取得
        latest_tsukkomi = st.session_state.tsukkomi_list[-1]
        timestamp = latest_tsukkomi['timestamp']
        data = latest_tsukkomi['data']
        reply = data.get('reply', {})
        
        
        char_col, tsukkomi_col = st.columns([1, 2])
        
        with char_col:
            # キャラクター画像エリア
            if st.session_state.tsukkomi_mode == "OTO♡MEちゃんモード":
                image_path = "image/otome_chan.jpg"
                gradient = "background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);"
            else:
                image_path = "image/otoko_mae_kun.png"
                gradient = "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.image(image_path, width="stretch")
        
        with tsukkomi_col:

            # カスタムCSS
            st.markdown("""
            <style>
            .tsukkomi-bubble {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 20px;
                margin: 10px 0;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .tsukkomi-time {
                font-size: 0.85em;
                opacity: 0.9;
                margin-bottom: 8px;
            }
            .tsukkomi-text {
                font-size: 1.1em;
                font-weight: bold;
                margin: 10px 0;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # 最新のツッコミを表示
            st.markdown(f"""
            <div class="tsukkomi-bubble">
                <div class="tsukkomi-time">🕐 {timestamp}</div>
                <div class="tsukkomi-text">{reply.get('tsukkomi', '')}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # スペース
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 詳細情報（常に表示）
            st.write(f"**理由:** {data.get('reason', '')}")
            st.write(f"**要約:** {reply.get('summary', '')}")
            st.write(f"**次のアクション:** {reply.get('next_action', '')}")
            st.write(f"**重要度:** {'⭐' * data.get('severity', 1)}")
        
        # 過去のツッコミ履歴（トグル）
        if len(st.session_state.tsukkomi_list) > 1:
            with st.expander(f"📜 過去のツッコミ履歴 ({len(st.session_state.tsukkomi_list) - 1}件)"):
                for tsukkomi_item in reversed(st.session_state.tsukkomi_list[:-1]):
                    past_timestamp = tsukkomi_item['timestamp']
                    past_data = tsukkomi_item['data']
                    past_reply = past_data.get('reply', {})
                    
                    st.markdown(f"**🕐 {past_timestamp}**")
                    st.write(f"💬 {past_reply.get('tsukkomi', '')}")
                    st.caption(f"理由: {past_data.get('reason', '')} | 要約: {past_reply.get('summary', '')} | 重要度: {'⭐' * past_data.get('severity', 1)}")
                    st.divider()
    else:
        st.info("ツッコミが必要な場面で自動的に表示されます")
    
    
    

with col2:
    st.subheader("📝 文字起こし履歴（リアルタイム）")
    
    if st.session_state.transcripts:
        # 最新が上に来るように逆順で結合
        reversed_text = "\n\n".join(reversed(st.session_state.transcripts))
        st.text_area(
            "文字起こし履歴",
            reversed_text,
            height=400,
            key=f"transcript_display_{len(st.session_state.transcripts)}"
        )
    else:
        st.info("録音を開始すると、リアルタイムで文字起こしが表示されます。")
    
    # ステータス表示
    if st.session_state.recording:
        st.success(f"🔴 リアルタイム録音中...")
    
    # ダウンロードボタン
    if st.session_state.full_text:
        st.download_button(
            label="📥 文字起こしテキストをダウンロード",
            data=st.session_state.full_text,
            file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            width="stretch"
        )


# === 要約エリア（下部全体） ===
st.divider()
st.subheader("📋 会議要約")

if st.session_state.summary_result:
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
# 自動リロード（録音中のみ）
if st.session_state.recording:
    import time
    time.sleep(2)
    st.rerun()
