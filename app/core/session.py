"""세션 및 쿠키 관리"""

import json
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from app.core.config import COOKIE_STORAGE_DIR, COOKIE_VALIDITY_DAYS


class SessionManager:
    """세션 및 쿠키 관리"""

    def __init__(self, storage_dir: str = COOKIE_STORAGE_DIR):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.temp_sessions: Dict[str, Dict[str, Any]] = {}

    # ==================== 임시 세션 관리 ====================

    def create_session(self, username: str) -> str:
        """새 로그인 세션 생성"""
        session_id = str(uuid.uuid4())
        self.temp_sessions[session_id] = {
            "username": username,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "cookies": None
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 정보 조회"""
        return self.temp_sessions.get(session_id)

    def update_session(self, session_id: str, **kwargs):
        """세션 상태 업데이트"""
        if session_id in self.temp_sessions:
            self.temp_sessions[session_id].update(kwargs)

    def cleanup_session(self, session_id: str):
        """임시 세션 삭제"""
        self.temp_sessions.pop(session_id, None)

    # ==================== 쿠키 저장/로드 ====================

    def save_cookies(self, username: str, cookies: list):
        """로그인 쿠키를 파일로 저장"""
        cookie_file = self._get_cookie_file_path(username)
        cookie_data = {
            "username": username,
            "saved_at": datetime.now().isoformat(),
            "cookies": cookies
        }

        with open(cookie_file, "w", encoding="utf-8") as f:
            json.dump(cookie_data, f, indent=2, ensure_ascii=False)

        print(f"[INFO] 쿠키 저장 완료: {username}")

    def load_cookies(self, username: str) -> Optional[list]:
        """저장된 쿠키 로드"""
        cookie_file = self._get_cookie_file_path(username)

        if not cookie_file.exists():
            print(f"[INFO] 저장된 쿠키 없음: {username}")
            return None

        try:
            cookie_data = self._read_cookie_file(cookie_file)

            if not self._is_cookie_valid(cookie_data):
                print(f"[INFO] 쿠키 만료됨: {username}")
                return None

            print(f"[INFO] 쿠키 로드 성공: {username}")
            return cookie_data["cookies"]

        except Exception as e:
            print(f"[ERROR] 쿠키 로드 실패: {e}")
            return None

    def delete_cookies(self, username: str):
        """쿠키 파일 삭제"""
        cookie_file = self._get_cookie_file_path(username)

        if cookie_file.exists():
            cookie_file.unlink()
            print(f"[INFO] 쿠키 삭제 완료: {username}")
        else:
            print(f"[INFO] 삭제할 쿠키 없음: {username}")

    # ==================== 내부 헬퍼 메서드 ====================

    def _get_cookie_file_path(self, username: str) -> Path:
        """쿠키 파일 경로 생성"""
        return self.storage_dir / f"{username}_cookies.json"

    def _read_cookie_file(self, cookie_file: Path) -> Dict[str, Any]:
        """쿠키 파일 읽기"""
        with open(cookie_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _is_cookie_valid(self, cookie_data: Dict[str, Any]) -> bool:
        """쿠키 유효성 검사"""
        saved_at = datetime.fromisoformat(cookie_data["saved_at"])
        expiry_date = saved_at + timedelta(days=COOKIE_VALIDITY_DAYS)
        return datetime.now() < expiry_date


# 전역 세션 매니저 인스턴스
session_manager = SessionManager()
