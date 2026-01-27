from fastapi import APIRouter, HTTPException
from app.models.schemas import LoginRequest, LoginResponse, OTPRequest
from app.core.browser import browser_manager
from app.core.session import session_manager

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    로그인 시작
    - 아이디/비밀번호 입력
    - OTP 필요시 session_id 반환
    - OTP 불필요시 바로 로그인 완료
    """
    try:
        # 세션 생성
        session_id = session_manager.create_session(request.username)

        # 로그인 시도
        result = await browser_manager.start_login(
            session_id=session_id,
            username=request.username,
            password=request.password
        )

        if result["status"] == "otp_required":
            # OTP 필요
            session_manager.update_session(session_id, status="otp_pending")
            return LoginResponse(
                status="otp_required",
                session_id=session_id,
                message=result["message"]
            )

        elif result["status"] == "success":
            # 바로 로그인 성공
            session_manager.update_session(session_id, status="authenticated")
            # 실제 서비스에서는 JWT 토큰 생성
            token = f"token_{session_id}"

            # 컨텍스트 정리
            await browser_manager.close_context(session_id)
            session_manager.cleanup_session(session_id)

            return LoginResponse(
                status="success",
                token=token,
                message=result["message"]
            )

        else:
            # 로그인 실패
            await browser_manager.close_context(session_id)
            session_manager.cleanup_session(session_id)

            raise HTTPException(status_code=401, detail=result["message"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그인 처리 중 오류: {str(e)}")


@router.post("/submit-otp", response_model=LoginResponse)
async def submit_otp(request: OTPRequest):
    """
    OTP 제출
    - 로그인 과정에서 받은 session_id와 OTP 코드 전송
    """
    try:
        # 세션 확인
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

        if session["status"] != "otp_pending":
            raise HTTPException(status_code=400, detail="잘못된 세션 상태입니다")

        # OTP 제출
        result = await browser_manager.submit_otp(
            session_id=request.session_id,
            otp=request.otp,
            username=session["username"]
        )

        if result["status"] == "success":
            # 로그인 성공
            session_manager.update_session(request.session_id, status="authenticated")
            # 실제 서비스에서는 JWT 토큰 생성
            token = f"token_{request.session_id}"

            # 컨텍스트 정리
            await browser_manager.close_context(request.session_id)
            session_manager.cleanup_session(request.session_id)

            return LoginResponse(
                status="success",
                token=token,
                message=result["message"]
            )

        else:
            # OTP 인증 실패
            raise HTTPException(status_code=401, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OTP 처리 중 오류: {str(e)}")


@router.delete("/logout/{username}")
async def logout(username: str):
    """
    로그아웃 (저장된 쿠키 삭제)
    """
    try:
        session_manager.delete_cookies(username)
        return {"status": "success", "message": "로그아웃 완료"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그아웃 처리 중 오류: {str(e)}")
