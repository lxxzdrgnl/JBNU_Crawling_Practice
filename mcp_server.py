"""JBNU LMS Crawler MCP Server

Claude가 전북대 LMS를 크롤링할 수 있도록 하는 MCP 서버

사용법:
    uv run python mcp_server.py
"""

import asyncio
from typing import Optional
from fastmcp import FastMCP

from app.core.browser import browser_manager
from app.core.session import session_manager

# MCP 서버 생성
mcp = FastMCP("JBNU LMS Crawler")


@mcp.tool()
async def login_to_lms(username: str, password: str) -> dict:
    """
    전북대 LMS에 로그인을 시작합니다.

    Args:
        username: 전북대 포털 ID (학번/사번)
        password: 비밀번호

    Returns:
        로그인 결과 (OTP 필요 여부 포함)
    """
    session_id = session_manager.create_session(username)
    result = await browser_manager.start_login(session_id, username, password)

    # 세션 ID를 함께 반환 (OTP 제출 시 필요)
    if result["status"] == "otp_required":
        result["session_id"] = session_id

    return result


@mcp.tool()
async def submit_otp(session_id: str, otp: str) -> dict:
    """
    Google OTP를 제출하여 로그인을 완료합니다.

    Args:
        session_id: login_to_lms에서 받은 세션 ID
        otp: Google Authenticator 6자리 코드

    Returns:
        로그인 완료 결과
    """
    # 세션에서 username 가져오기
    session = session_manager.get_session(session_id)
    if not session:
        return {"status": "error", "message": "세션을 찾을 수 없습니다"}

    username = session["username"]
    result = await browser_manager.submit_otp(session_id, otp, username)

    # 로그인 완료 후 세션 정리
    if result["status"] == "success":
        await browser_manager.close_context(session_id)
        session_manager.cleanup_session(session_id)

    return result


@mcp.tool()
async def get_lms_courses(username: str) -> dict:
    """
    사용자의 강의 목록을 조회합니다.
    저장된 로그인 쿠키를 사용하므로 먼저 로그인이 필요합니다.

    Args:
        username: 전북대 포털 ID (학번/사번)

    Returns:
        강의 목록 (강의명, 교수명, 학기 정보)
    """
    courses = await browser_manager.crawl_courses(username)

    if not courses:
        return {
            "status": "error",
            "message": "강의 목록을 가져올 수 없습니다. 먼저 로그인해주세요.",
            "courses": []
        }

    return {
        "status": "success",
        "courses": courses,
        "count": len(courses)
    }


@mcp.tool()
def logout_from_lms(username: str) -> dict:
    """
    저장된 로그인 세션을 삭제합니다.

    Args:
        username: 전북대 포털 ID (학번/사번)

    Returns:
        로그아웃 결과
    """
    session_manager.delete_cookies(username)
    return {
        "status": "success",
        "message": f"{username}의 로그인 세션이 삭제되었습니다"
    }


@mcp.tool()
def check_login_status(username: str) -> dict:
    """
    저장된 로그인 세션이 있는지 확인합니다.

    Args:
        username: 전북대 포털 ID (학번/사번)

    Returns:
        로그인 상태 정보
    """
    cookies = session_manager.load_cookies(username)

    if cookies:
        return {
            "status": "logged_in",
            "message": f"{username}의 로그인 세션이 유효합니다",
            "has_cookies": True
        }
    else:
        return {
            "status": "not_logged_in",
            "message": f"{username}의 로그인 세션이 없습니다",
            "has_cookies": False
        }


if __name__ == "__main__":
    # MCP 서버 실행
    mcp.run()
