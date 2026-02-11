"""
크롤러 모듈
각 사이트별 크롤러를 제공합니다.
"""
from .base import BaseCrawler
from .csai_crawler import CSAICrawler
from .eng_crawler import EngCrawler
from .jbnu_crawler import JbnuCrawler
from .swuniv_crawler import SwunivCrawler

__all__ = [
    "BaseCrawler",
    "CSAICrawler",
    "EngCrawler",
    "JbnuCrawler",
    "SwunivCrawler"
]

# 크롤러 타입 매핑
CRAWLER_MAP = {
    "csai": CSAICrawler,
    "eng": EngCrawler,
    "jbnu": JbnuCrawler,
    "swuniv": SwunivCrawler,
}
