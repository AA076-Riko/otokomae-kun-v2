"""
文字起こしサービス
WhisperまたはRealtimeAPIを使った音声文字起こし
"""
import pyaudio
import wave
from openai import OpenAI

# 録音設定
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
WAVE_OUTPUT_FILENAME = "temp_audio.wav"


class TranscriptionService:
    """将来RealtimeAPIに切り替え可能な設計"""
    
    def __init__(self, client: OpenAI, mode="whisper"):
        self.mode = mode
        self.client = client
    
    def record_audio(self, duration: int) -> bool:
        """指定秒数の音声を録音"""
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            frames = []
            
            for i in range(0, int(RATE / CHUNK * duration)):
                data = stream.read(CHUNK)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # WAVファイルとして保存
            wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            return True
        except Exception as e:
            p.terminate()
            print(f"録音エラー: {str(e)}")
            return False
    
    def transcribe(self, filename: str) -> str:
        """音声ファイルを文字起こし"""
        if self.mode == "whisper":
            return self._whisper_transcribe(filename)
        # elif self.mode == "realtime":
        #     return self._realtime_transcribe(filename)  # 将来実装
    
    def _whisper_transcribe(self, filename: str) -> str:
        """Whisper APIで文字起こし"""
        try:
            with open(filename, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                )
                return transcription.text
        except Exception as e:
            return f"エラー: {str(e)}"
