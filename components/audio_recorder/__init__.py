import streamlit.components.v1 as components


def audio_recorder(chunk_duration=60, key=None):
    """
    ブラウザで音声を録音し、指定された秒数ごとに音声チャンクをPython側に送信するカスタムコンポーネント
    
    Parameters:
    -----------
    chunk_duration : int
        録音チャンクの長さ（秒）。デフォルトは60秒
    key : str
        Streamlitコンポーネントのキー
    
    Returns:
    --------
    dict or None
        音声データを含む辞書。形式: {"audio": base64_encoded_audio, "timestamp": timestamp}
    """
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                margin: 0;
                padding: 10px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}
            .controls {{
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
            }}
            button {{
                padding: 10px 20px;
                font-size: 14px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 500;
            }}
            #startBtn {{
                background-color: #4CAF50;
                color: white;
            }}
            #stopBtn {{
                background-color: #f44336;
                color: white;
            }}
            button:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
            }}
            .status {{
                padding: 10px;
                border-radius: 4px;
                font-size: 13px;
                margin-bottom: 10px;
            }}
            .status.recording {{
                background-color: #ffebee;
                color: #c62828;
            }}
            .status.idle {{
                background-color: #e8f5e9;
                color: #2e7d32;
            }}
            .info {{
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="controls">
            <button id="startBtn">🎤 録音開始</button>
            <button id="stopBtn" disabled>⏹️ 録音停止</button>
        </div>
        <div id="status" class="status idle">待機中...</div>
        <div class="info">
            <p>📝 {chunk_duration}秒ごとに自動送信 | チャンク数: <span id="chunkCount">0</span></p>
        </div>

        <script>
            let mediaRecorder = null;
            let audioChunks = [];
            let chunkTimer = null;
            let chunkCount = 0;
            let isRecording = false;

            function sendDataToParent(audioData) {{
                const reader = new FileReader();
                reader.onloadend = function() {{
                    const base64data = reader.result.split(',')[1];
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        value: {{
                            audio: base64data,
                            timestamp: Date.now(),
                            chunk_number: chunkCount
                        }}
                    }}, '*');
                }};
                reader.readAsDataURL(audioData);
            }}

            function updateStatus(message, type = 'idle') {{
                const statusEl = document.getElementById('status');
                statusEl.className = `status ${{type}}`;
                statusEl.textContent = message;
            }}

            function processChunk() {{
                if (audioChunks.length > 0) {{
                    const audioBlob = new Blob(audioChunks, {{ type: 'audio/webm' }});
                    audioChunks = [];
                    chunkCount++;
                    document.getElementById('chunkCount').textContent = chunkCount;
                    updateStatus(`録音中... (チャンク #${{chunkCount}} 送信中)`, 'recording');
                    sendDataToParent(audioBlob);
                }}
            }}

            async function startRecording() {{
                try {{
                    const stream = await navigator.mediaDevices.getUserMedia({{
                        audio: {{
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true
                        }}
                    }});

                    mediaRecorder = new MediaRecorder(stream, {{ mimeType: 'audio/webm' }});
                    
                    mediaRecorder.ondataavailable = (event) => {{
                        if (event.data.size > 0) {{
                            audioChunks.push(event.data);
                        }}
                    }};

                    mediaRecorder.onstop = () => {{
                        processChunk();
                        stream.getTracks().forEach(track => track.stop());
                    }};

                    mediaRecorder.start();
                    isRecording = true;
                    chunkCount = 0;
                    document.getElementById('chunkCount').textContent = chunkCount;
                    
                    updateStatus(`録音中... ({chunk_duration}秒ごとに自動送信)`, 'recording');
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = false;

                    chunkTimer = setInterval(() => {{
                        if (isRecording && mediaRecorder && mediaRecorder.state === 'recording') {{
                            mediaRecorder.stop();
                            setTimeout(() => {{
                                if (isRecording) {{
                                    mediaRecorder.start();
                                }}
                            }}, 100);
                        }}
                    }}, {chunk_duration * 1000});

                }} catch (error) {{
                    console.error('録音エラー:', error);
                    updateStatus('エラー: マイクアクセス拒否', 'idle');
                }}
            }}

            function stopRecording() {{
                isRecording = false;
                if (chunkTimer) {{
                    clearInterval(chunkTimer);
                    chunkTimer = null;
                }}
                if (mediaRecorder && mediaRecorder.state !== 'inactive') {{
                    mediaRecorder.stop();
                }}
                updateStatus('録音停止', 'idle');
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
            }}

            document.getElementById('startBtn').addEventListener('click', startRecording);
            document.getElementById('stopBtn').addEventListener('click', stopRecording);

            // Streamlitに準備完了を通知
            window.parent.postMessage({{
                type: 'streamlit:componentReady',
                height: 150
            }}, '*');
        </script>
    </body>
    </html>
    """
    
    component_value = components.html(html_code, height=150, scrolling=False)
    return component_value
