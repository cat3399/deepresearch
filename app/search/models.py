import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from config.base_config import MAX_SEARCH_RESULTS

class QueryKeys:
    """查询键类，用于存储搜索关键词和语言"""
    
    def __init__(self, key: str = "", language: str = ""):
        self.key = key
        self.language = language
    def __str__(self):
        return f"QueryKeys(key={self.key},language={self.language})"
    def __repr__(self):
        return f"QueryKeys(key={self.key},language={self.language})"
    
class SearchRequest:
    """搜索请求数据类，包含搜索查询的基本参数"""
    
    def __init__(self, query_keys: List[QueryKeys] = [QueryKeys()], time_page: list[int] = [0,0,0], search_purpose: str = "", search_restrictions: str = "", max_search_results: int = MAX_SEARCH_RESULTS):

            
        # 确保时间范围格式正确，如果为空或格式错误则使用默认值
        if not time_page or not isinstance(time_page, list) or len(time_page) != 3:
            self.time_page = [0, 0, 0]  # 默认值
        else:
            # 确保time_page中的每个元素都是整数
            try:
                self.time_page = [int(time) for time in time_page]
            except (ValueError, TypeError):
                self.time_page = [0, 0, 0]  # 转换失败时使用默认值
        # self.keys = [query_key.key for query_key in self.query_keys]
        # self.language = [query_key.language for query_key in self.query_keys]
        self.search_purpose = search_purpose
        self.search_restrictions = search_restrictions
        self.query_keys = query_keys
        self.max_search_results = max_search_results if max_search_results else MAX_SEARCH_RESULTS
    
    def __str__(self) -> str:
        return f"SearchRequest(query_keys='{[query_key for query_key in self.query_keys]}', time_page={self.time_page})"
    
    def __repr__(self) -> str:
        return f"SearchRequest(query_keys={[query_key for query_key in self.query_keys]}, time_page={self.time_page})"
    
class SearchResult:
    """搜索结果类，表示单个搜索结果项"""
    
    def __init__(
        self,
        url: Optional[str] = None,
        title: Optional[str] = None,
        content: str = "",
        score: float = 0,
    ):
        self.url = url          # 相关URL
        self.title = title      # 标题
        self.content = content  # 搜索结果内容
        self.score = score      # 相关性分数


    def __str__(self) -> str:
        return (f"SearchResult(title='{self.title}', "
                f"score={self.score}, "
                f"url='{self.url}')")
    def __repr__(self) -> str:
        content_repr = self.content[:47] + "..."
        return (f"SearchResult(url={self.url}, "
                f"title={self.title}, "
                f"content={content_repr}, "
                f"score={self.score})")

    def to_dict(self) -> Dict[str, Any]:
        """将搜索结果转换为字典形式"""
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
        }


class SearchResults:
    """搜索结果集合类，表示一组搜索结果"""
    
    def __init__(self, search_request:SearchRequest = SearchRequest(), results: Optional[List[SearchResult]] = []):
        self.search_request = search_request
        self.results = results or []
    
    def __str__(self) -> str:
        return (f"SearchResults(search_request='{self.search_request}', "
                f"results=[<{(self.results)} SearchResult objects>], ")
    def __repr__(self) -> str:
        return (f"SearchResults(search_request={self.search_request}, "
                f"results=[<{(self.results)} SearchResult objects>], ")

    def get_urls(self) -> list[str]:
        return [result.url for result in self.results if result.url]

    def get_search_surpose(self) -> str:
        """获取搜索目的"""
        return self.search_request.search_purpose

    def add_result(self, result: SearchResult) -> None:
        """添加一个搜索结果"""
        self.results.append(result)
    
    def sort_by_score(self) -> None:
        """按相关性分数排序结果"""
        self.results.sort(key=lambda x: x.score, reverse=True)
    
    def to_list(self) -> list[Dict]:
        """将整个搜索结果集转换为字典"""
        return [result.to_dict() for result in self.results]
    
    def to_str(self) -> list[Dict]:
        """将整个搜索结果集转换为字符串"""
        return str({f"网页{i+1}":result for i,result in enumerate(self.to_list())})
    def to_dict(self) -> list[Dict]:
        """将整个搜索结果集转换为字典类型"""
        return {f"网页{i+1}":result for i,result in enumerate(self.to_list())}
    def merge(self, other: 'SearchResults', remove_duplicates: bool = True) -> None:
        """合并另一个SearchResults对象的结果到当前对象
        
        Args:
            other: 要合并的另一个SearchResults对象
            remove_duplicates: 是否移除URL重复的结果，默认为True
        """
        if not isinstance(other, SearchResults):
            raise TypeError("只能与SearchResults类型的对象合并")
        
        # 处理结果合并
        if remove_duplicates:
            # 获取现有URL列表
            existing_urls = self.get_urls()
            # 只添加URL不重复的结果
            for result in other.results:
                if result.url not in existing_urls:
                    self.add_result(result)
                    existing_urls.append(result.url)
        else:
            # 直接添加所有结果
            self.results.extend(other.results)
