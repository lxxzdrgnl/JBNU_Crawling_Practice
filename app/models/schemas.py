from pydantic import BaseModel
from typing import Optional, List, Dict, Any


# 로그인 요청
class LoginRequest(BaseModel):
    username: str
    password: str


# OTP 제출 요청
class OTPRequest(BaseModel):
    session_id: str
    otp: str


# 로그인 응답
class LoginResponse(BaseModel):
    status: str  # "otp_required", "success", "error"
    session_id: Optional[str] = None
    token: Optional[str] = None
    message: Optional[str] = None


# 강의 정보
class Course(BaseModel):
    id: str
    name: str
    professor: Optional[str] = None
    semester: Optional[str] = None
    year: Optional[int] = None


# 강의 목록 응답
class CoursesResponse(BaseModel):
    courses: List[Course]


# 과제 정보
class Assignment(BaseModel):
    id: str
    title: str
    course_name: str
    due_date: Optional[str] = None
    status: Optional[str] = None  # "submitted", "pending", etc.


# 과제 목록 응답
class AssignmentsResponse(BaseModel):
    assignments: List[Assignment]


# 공지사항 정보
class Notice(BaseModel):
    id: str
    title: str
    course_name: str
    created_at: Optional[str] = None
    content: Optional[str] = None


# 공지사항 목록 응답
class NoticesResponse(BaseModel):
    notices: List[Notice]
