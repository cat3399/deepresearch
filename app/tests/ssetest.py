import os
import requests

url = "https://api.x.ai/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer xai-zUSXyGazvmor4VIZszm9xpej6EU9sFBJhgCQeRgxGCmia0VJRIqTdh8Zn2T4y2uCnMIxgeFZRIMEpC7k"
}

docs = """
以下参数直接位于 search_parameters 对象内部：
mode (字符串，必需)
描述：控制搜索行为
可选值：
"off": 禁用搜索，模型不访问外部数据源
"auto" (默认): 模型可以使用实时搜索，并自动决定是否执行
"on": 强制启用实时搜索
return_citations (布尔值，可选)
描述：是否在响应中返回数据源的引用链接
默认值：false (不返回)
设置为 true 以返回引用
注意：流式传输时，引用信息 (citations 字段，包含URL字符串列表) 仅在最后一个响应数据块中返回
from_date (字符串，可选)
描述：限制搜索数据的起始日期 (包含此日期)
格式："YYYY-MM-DD" (ISO 8601)
示例："2025-01-01"
to_date (字符串，可选)
描述：限制搜索数据的结束日期 (包含此日期)
格式："YYYY-MM-DD" (ISO 8601)
示例："2025-12-31"
注意：from_date 和 to_date 可独立使用仅 from_date 表示从该日期到今天；仅 to_date 表示截至该日期的所有数据
max_search_results (整数，可选)
描述：限制查询时考虑的数据源最大数量
默认值：20
数据源配置 (sources)
sources 是一个对象列表，用于指定具体使用哪些数据源及其参数如果未提供 sources，则默认使用 "web" 和 "x" 作为数据源
每个数据源对象包含一个 type 字段来指定源类型，以及该类型支持的其他参数
type 值	描述	支持的参数 (parameter: 说明)
"web"	网站搜索	<ul><li>country (字符串): ISO alpha-2 国家代码，限制搜索到特定国家/地区</li><li>excluded_websites (字符串数组): 要排除的网站域名列表 (最多5个)</li><li>safe_search (布尔值): 是否启用安全搜索 (默认 true)</li></ul>
"x"	X (原Twitter) 帖子搜索	<ul><li>x_handles (字符串数组): 仅搜索指定的 X 用户账号的帖子</li></ul>
"news"	新闻源搜索	<ul><li>country (字符串): ISO alpha-2 国家代码，限制搜索到特定国家/地区</li><li>excluded_websites (字符串数组): 要排除的新闻网站域名列表 (最多5个)</li><li>safe_search (布尔值): 是否启用安全搜索 (默认 true)</li></ul>
"rss"	RSS 源数据检索	<ul><li>links (字符串数组): RSS feed URL 列表 (目前仅支持提供1个URL)</li></ul>
参数详解：
country: (用于 "web", "news") 指定 ISO alpha-2 国家代码 (例如 "CH" 代表瑞士)，以获取特定区域的结果
excluded_websites: (用于 "web", "news") 提供一个最多包含5个网站域名的列表，这些网站将被排除在搜索结果之外 (例如 ["wikipedia.org"])
safe_search: (用于 "web", "news") 默认为 true (开启)设置为 false 可禁用安全搜索，可能返回成人内容
x_handles: (用于 "x") 提供一个 X 用户名列表 (不含 @，例如 ["grok"])，搜索将仅限于这些用户的帖子
links: (用于 "rss") 提供一个包含 RSS feed URL 的列表 (例如 ["https://status.x.ai/feed.xml"])目前仅支持列表中的一个链接
示例 search_parameters 结构：
{
  "search_parameters": {
    "mode": "auto",
    "return_citations": true,
    "from_date": "2024-01-01",
    "max_search_results": 20,
    "sources": [
      {
        "type": "web",
        "country": "US",
        "excluded_websites": ["example.com"],
        "safe_search": true
      },
      {
        "type": "x",
        "x_handles": ["username"]
      },
      {
        "type": "news"
      },
      {
        "type": "rss",
        "links": ["https://blog.x.ai/feed.xml"]
      }
    ]
  }
}
Json
"""

payload = {
    "messages": [
        {
            "role": "user",
            "content": "玩偶姐姐在x上最近发了什么消息,最新的一条是什么"
        }
    ],
    "search_parameters": {
        "mode": "on",
        "sources": [
          { "type": "x" }
        ]
    },
    "model": "grok-3-latest"
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())