"""
RealtimeAPI用の文字起こしサービス
WebSocketでリアルタイム音声認識
"""
import asyncio
import json
import base64
import pyaudio
from openai import OpenAI
import websockets
import os

# 録音設定
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000  # RealtimeAPIは24kHz
WAVE_OUTPUT_FILENAME = "temp_audio.wav"


class RealtimeTranscriptionService:
    """RealtimeAPIを使ったリアルタイム文字起こし"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.websocket = None
        self.is_recording = False
        self.transcription_queue = asyncio.Queue()
        
    async def connect(self):
        """WebSocket接続を確立"""
        url = "wss://api.openai.com/v1/realtime?model=gpt-realtime"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        self.websocket = await websockets.connect(url, additional_headers=headers)
        print(f"[RealtimeAPI] WebSocket接続完了")
        
        # セッション更新（日本語音声認識設定）
        await self.websocket.send(json.dumps({
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "あなたは日本語の会議音声を文字起こしするアシスタントです。全ての音声は日本語です。",
                "input_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1",
                    "language": "ja"  # 日本語
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                }
            }
        }))
        
    async def start_recording(self):
        """音声録音とストリーミングを開始"""
        self.is_recording = True
        
        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
        
        print(f"[RealtimeAPI] 録音開始")
        
        try:
            # 音声送信タスクとレスポンス受信タスクを並行実行
            await asyncio.gather(
                self._send_audio(stream),
                self._receive_transcription()
            )
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            self.is_recording = False
            print(f"[RealtimeAPI] 録音停止")
    
    async def _send_audio(self, stream):
        """音声データをWebSocketで送信"""
        while self.is_recording:
            try:
                audio_data = stream.read(CHUNK, exception_on_overflow=False)
                
                # Base64エンコード
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                # 音声データを送信
                await self.websocket.send(json.dumps({
                    "type": "input_audio_buffer.append",
                    "audio": audio_base64
                }))
                
                await asyncio.sleep(0.01)  # 少し待機
                
            except Exception as e:
                print(f"[RealtimeAPI] 音声送信エラー: {e}")
                break
    
    async def _receive_transcription(self):
        """文字起こし結果を受信"""
        async for message in self.websocket:
            try:
                data = json.loads(message)
                event_type = data.get("type")
                
                # 文字起こし結果を取得
                if event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = data.get("transcript", "")
                    if transcript:
                        print(f"[RealtimeAPI] 文字起こし: {transcript}")
                        await self.transcription_queue.put({
                            'text': transcript,
                            'timestamp': data.get("item_id")
                        })
                
                # エラーハンドリング
                elif event_type == "error":
                    error = data.get("error", {})
                    print(f"[RealtimeAPI] エラー: {error}")
                    
            except json.JSONDecodeError as e:
                print(f"[RealtimeAPI] JSON解析エラー: {e}")
            except Exception as e:
                print(f"[RealtimeAPI] 受信エラー: {e}")
    
    async def get_transcription(self):
        """文字起こし結果を取得（キューから）"""
        return await self.transcription_queue.get()
    
    async def stop(self):
        """録音停止とクリーンアップ"""
        self.is_recording = False
        if self.websocket:
            await self.websocket.close()
            print(f"[RealtimeAPI] WebSocket切断")
