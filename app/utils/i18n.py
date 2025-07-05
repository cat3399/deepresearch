# Simple i18n support for fixed generator outputs
from config.base_config import APP_LANG

_MESSAGES = {
    'start_deep_research': {
        'zh': "🔍 **开始深度研究搜索...**\n\n",
        'en': "🔍 **Start deep research search...**\n\n",
    },
    'initial_search': {
        'zh': "📋 **初始搜索获取参考信息**\n",
        'en': "📋 **Initial search to gather references**\n",
    },
    'initial_done': {
        'zh': "✅ 初始搜索完成\n\n",
        'en': "✅ Initial search complete\n\n",
    },
    'generate_first_plan': {
        'zh': "📌 **生成第一个搜索计划**\n",
        'en': "📌 **Generate first search plan**\n",
    },
    'first_plan_fail': {
        'zh': "⚠️ 第一个搜索计划未能生成。\n\n",
        'en': "⚠️ Failed to generate first search plan.\n\n",
    },
    'deep_end': {
        'zh': "🏁 **深度研究结束**\n\n",
        'en': "🏁 **Deep research finished**\n\n",
    },
    'exec_first_plan': {
        'zh': "🔄 **执行第一个搜索计划**\n",
        'en': "🔄 **Execute first search plan**\n",
    },
    'exec_plan': {
        'zh': "🔄 **执行搜索计划{num}**\n",
        'en': "🔄 **Execute search plan {num}**\n",
    },
    'plan_exec_done': {
        'zh': "✅ 搜索计划{num}执行完成\n\n",
        'en': "✅ Search plan {num} executed\n\n",
    },
    'plans_executed': {
        'zh': "📊 **已执行的搜索计划数量：** {num}/{max}\n",
        'en': "📊 **Executed search plans:** {num}/{max}\n",
    },
    'next_plan': {
        'zh': "📌 **步骤{num}：生成下一个搜索计划**\n",
        'en': "📌 **Step {num}: generate next search plan**\n",
    },
    'no_new_plan': {
        'zh': "🏁 **未能生成新的搜索计划，信息获取完毕，深度研究提前完成**\n\n",
        'en': "🏁 **No new plans generated, research finished early**\n\n",
    },
    'no_plan_executed': {
        'zh': "🏁 **未能执行任何搜索计划，深度研究结束**\n\n",
        'en': "🏁 **No search plans executed, research finished**\n\n",
    },
    'deep_finished': {
        'zh': "🏁 **深度研究完成**\n\n",
        'en': "🏁 **Deep research completed**\n\n",
    },
    'deep_search_done': {
        'zh': "✅ **深度研究搜索完成**\n",
        'en': "✅ **Deep research search done**\n",
    },
    'deep_error': {
        'zh': "🚫 **研究过程出现意外,强行终止**",
        'en': "🚫 **Unexpected error, research aborted**",
    },
    'search_start': {
        'zh': "🔍 **开始搜索...**\n\n",
        'en': "🔍 **Start searching...**\n\n",
    },
    'search_keyword_fail': {
        'zh': "❌ **搜索关键词生成失败！**",
        'en': "❌ **Failed to generate search keywords!**",
    },
    'search_done': {
        'zh': "✅ **搜索完成**\n",
        'en': "✅ **Search completed**\n",
    },
    'no_urls': {
        'zh': "📝 **未查看任何网页内容**\n",
        'en': "📝 **No page content viewed**\n",
    },
    'search_purpose': {
        'zh': "🎯 **搜索预期：** {text}\n",
        'en': "🎯 **Search purpose:** {text}\n",
    },
    'search_restrictions': {
        'zh': "⭕ **结果限制：** {text}\n",
        'en': "⭕ **Restrictions:** {text}\n",
    },
    'search_keywords': {
        'zh': "🔍 **搜索关键词：**\n",
        'en': "🔍 **Search keywords:**\n",
    },
    'viewed_urls': {
        'zh': "🌐 **已查看 {num} 个网页：**\n",
        'en': "🌐 **Viewed {num} pages:**\n",
    },
    'fetching_url': {
        'zh': "我正在获取 {url} 网页的内容\n",
        'en': "Fetching content of {url}\n",
    },
    'request_failed': {
        'zh': "请求失败",
        'en': "Request failed",
    },
}


def i18n(key: str, **kwargs) -> str:
    lang = APP_LANG if APP_LANG in ('zh', 'en') else 'zh'
    msg = _MESSAGES.get(key, {}).get(lang, '')
    if kwargs:
        try:
            msg = msg.format(**kwargs)
        except Exception:
            pass
    return msg
