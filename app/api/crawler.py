from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.schemas import CoursesResponse, Course
from app.core.browser import browser_manager
from app.core.session import session_manager

router = APIRouter(prefix="/courses", tags=["Courses"])
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    토큰 검증 (간단한 구현)
    실제 서비스에서는 JWT 검증 로직 필요
    """
    token = credentials.credentials

    # 간단한 토큰 검증 (token_sessionid 형식)
    if not token.startswith("token_"):
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

    return token


@router.get("/{username}", response_model=CoursesResponse)
async def get_courses_by_username(
    username: str,
    token: str = Depends(verify_token)
):
    """
    특정 사용자의 강의 목록 조회
    - 저장된 쿠키를 사용하여 강의 목록 크롤링
    - Authorization 헤더에 Bearer 토큰 필요
    """
    try:
        # 강의 목록 크롤링
        courses_data = await browser_manager.crawl_courses(username)

        courses = [
            Course(
                id=course["id"],
                name=course["name"],
                professor=course.get("professor"),
                semester=course.get("semester"),
                year=course.get("year")
            )
            for course in courses_data
        ]

        return CoursesResponse(courses=courses)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"강의 목록 조회 중 오류: {str(e)}")
