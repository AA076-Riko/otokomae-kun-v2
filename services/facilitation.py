"""
ファシリテーションサービス
ツッコミと要約の生成
"""
import json
import os
from openai import OpenAI


class FacilitationService:
    """ツッコミと要約の生成"""
    
    def __init__(self, client: OpenAI, mode: str = "OTOKO☆MAEくんモード"):
        self.client = client
        self.mode = mode
        self.otokомae_prompt = self._load_prompt('prompts/otokомae_prompt.txt')
        self.yurufuwa_prompt = self._load_prompt('prompts/tsukkomi_prompt.txt')
        self.summary_prompt = self._load_prompt('prompts/summary_prompt.txt')
        self.tsukkomi_prompt = self.otokомae_prompt if mode == "OTOKO☆MAEくんモード" else self.yurufuwa_prompt
    
    def _load_prompt(self, filepath: str) -> str:
        """プロンプトファイルを読み込み"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"警告: プロンプトファイルが見つかりません: {filepath}")
            return ""
    
    def set_mode(self, mode: str):
        """ツッコミモードを変更"""
        self.mode = mode
        self.tsukkomi_prompt = self.otokомae_prompt if mode == "OTOKO☆MAEくんモード" else self.yurufuwa_prompt
        print(f"モード変更: {mode}")
        print(f"使用プロンプト: {'OTOKO☆MAEくん' if mode == 'OTOKO☆MAEくんモード' else 'OTO♡MEちゃん'}")
    
    def generate_tsukkomi(self, transcript: str) -> dict:
        """ツッコミを生成（JSON形式で返却）"""
        try:
            full_prompt = self.tsukkomi_prompt + "\n\n文字起こし:\n" + transcript
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"ツッコミ生成エラー: {str(e)}")
            return None
    
    def generate_summary(self, transcript: str) -> str:
        """会議全体の要約を生成"""
        try:
            full_prompt = self.summary_prompt + "\n\n文字起こし:\n" + transcript
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.5
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"要約生成エラー: {str(e)}"
