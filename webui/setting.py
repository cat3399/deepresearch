# env_editor_bp.py

import os
from pathlib import Path
import sys
from flask import Blueprint, render_template, request, redirect, url_for, flash
from dotenv import set_key, dotenv_values

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
env_path = ROOT_DIR.joinpath(".env")

from config import base_config as config
from config.logging_config import logger
from app.utils.test_api import get_available_tests, run_single_test

env_editor_bp = Blueprint('setting', __name__, template_folder='templates')


def get_comments_from_env(filepath):
    """
    从 .env 文件中解析出每个键上方的注释。
    返回一个字典 {'KEY': 'comment'}
    """
    comments = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            last_comment_lines = []
            for line in f:
                line = line.strip()
                if line.startswith('#'):
                    last_comment_lines.append(line.lstrip('# ').strip())
                elif '=' in line:
                    key = line.split('=', 1)[0].strip()
                    if key and last_comment_lines:
                        comments[key] = ' '.join(last_comment_lines)
                    last_comment_lines = []
                else:
                    last_comment_lines = []
    except FileNotFoundError:
        pass
    return comments

# --- 核心优化：结构化配置生成函数 ---
def get_structured_config(env_path):
    """
    将 .env 文件的内容构造成前端需要的分组结构。
    新增了 type, placeholder, options 等元数据，用于驱动前端生成更智能的控件。
    """
    # 1. 定义分组规则和元数据 (核心改动：增加了 test_name 字段)
    group_definitions = [
        {
            "title": "核心配置", "icon": "fa-key",
            "vars": [
                {"key": "API_KEY", "type": "password", "placeholder": "用于访问本项目API的密钥"},
                {"key": "ALL_IN_GEMINI_KEY", "type": "textarea", "placeholder": "用逗号分隔多个Gemini Key"},
                {"key": "APP_LANG", "type": "select", "options": ["", "zh", "en"], "placeholder": "zh"},
                {"key": "MAX_SEARCH_RESULTS", "type": "number", "min": 1, "max": 1000, "placeholder": "默认 6"},
                {"key": "MAX_DEEPRESEARCH_RESULTS", "type": "number", "min": 1, "max": 1000, "placeholder": "默认 3"},
                {"key": "MAX_STEPS_NUM", "type": "number", "min": 1, "max": 1000, "placeholder": "默认 12"},
            ]
        },
        {
            "title": "搜索引擎配置", "icon": "fa-search", "test_name": "search_api_worker_test",
            "vars": [
                {"key": "SEARXNG_URL", "type": "text", "placeholder": "例如: https://sousuo.emoe.top/search"},
                {"key": "TAVILY_KEY", "type": "password", "placeholder": "Tavily API Key (可选, SearXNG优先)"},
                {"key": "TAVILY_MAX_NUM", "type": "number", "min": 5, "max": 50, "placeholder": "默认 20"},
                {"key": "SEARCH_API_LIMIT", "type": "number", "min": 1, "max": 10, "placeholder": "并发限制 默认 5"},
            ]
        },
        {
            "title": "网页爬虫配置", "icon": "fa-spider", "test_name": "url_to_markdown_test",
            "vars": [
                {"key": "FIRECRAWL_API_URL", "type": "text", "placeholder": "本地部署地址或留空使用官方API"},
                {"key": "FIRECRAWL_API_KEY", "type": "password", "placeholder": "使用官方API时需要填写"},
                {"key": "CRAWL4AI_API_URL", "type": "text", "placeholder": "本地部署的 Crawl4AI 地址"},
                {"key": "JINA_API_URL", "type": "text", "placeholder": "默认 https://r.jina.ai"},
                {"key": "JINA_API_KEY", "type": "password", "placeholder": "Jina Reader API Key (jina_...)"},
                {"key": "CRAWL_THREAD_NUM", "type": "number", "min": 1, "max": 20, "placeholder": "建议 3-10"},
            ]
        },
        {
            "title": "基础对话模型", "icon": "fa-comments",
            "vars": [
                {"key": "BASE_CHAT_API_KEY", "type": "password", "placeholder": "留空则使用ALL_IN_GEMINI_KEY"},
                {"key": "BASE_CHAT_API_URL", "type": "text", "placeholder": "API-URL, 例如: https://api.openai.com/v1"},
                {"key": "BASE_CHAT_MODEL", "type": "text", "placeholder": "模型名称, 例如: o3"},
            ]
        },
        {
            "title": "搜索关键词生成模型", "icon": "fa-lightbulb", "test_name": "search_plan_test",
            "vars": [
                {"key": "SEARCH_KEYWORD_API_KEY", "type": "password", "placeholder": "留空则继承基础对话模型配置"},
                {"key": "SEARCH_KEYWORD_API_URL", "type": "text", "placeholder": "留空则继承基础对话模型配置"},
                {"key": "SEARCH_KEYWORD_MODEL", "type": "text", "placeholder": "留空则继承基础对话模型配置"},
            ]
        },
        {
            "title": "评估模型", "icon": "fa-check-double", "test_name": "evaluate_single_batch_test",
            "vars": [
                {"key": "EVALUATE_THREAD_NUM", "type": "number", "min": 1, "max": 20, "placeholder": "默认 5"},
                {"key": "EVALUATE_API_KEY", "type": "password", "placeholder": "留空则继承基础对话模型配置"},
                {"key": "EVALUATE_API_URL", "type": "text", "placeholder": "留空则继承基础对话模型配置"},
                {"key": "EVALUATE_MODEL", "type": "text", "placeholder": "留空则继承基础对话模型配置"},
            ]
        },
        {
            "title": "内容压缩模型", "icon": "fa-compress-arrows-alt", "test_name": "compress_url_content_test",
            "vars": [
                {"key": "COMPRESS_API_TYPE", "type": "select", "options": ["", "OPENAI", "GEMINI"], "placeholder": "留空默认GEMINI"},
                {"key": "COMPRESS_API_KEY", "type": "password", "placeholder": "留空则继承基础对话模型配置"},
                {"key": "COMPRESS_API_URL", "type": "text", "placeholder": "留空则继承基础对话模型配置"},
                {"key": "COMPRESS_MODEL", "type": "text", "placeholder": "留空则继承基础对话模型配置"},
            ]
        },
        {
            "title": "总结模型", "icon": "fa-file-alt", "test_name": "summary_test",
            "vars": [
                {"key": "SUMMARY_API_TYPE", "type": "select", "options": ["", "OPENAI"], "placeholder": "留空默认OPENAI"},
                {"key": "SUMMARY_API_KEY", "type": "password", "placeholder": "留空则继承基础对话模型配置"},
                {"key": "SUMMARY_API_URL", "type": "text", "placeholder": "留空则继承基础对话模型配置"},
                {"key": "SUMMARY_MODEL", "type": "text", "placeholder": "留空则继承基础对话模型配置"},
            ]
        },
        {
            "title": "杂项", "icon": "fa-sliders-h",
            "vars": [
                {"key": "HEARTBEAT_TIMEOUT", "type": "number", "min": 10, "placeholder": "单位:秒"},
            ]
        }
    ]

    # 2. 读取.env文件的键值对和注释
    env_vars = dotenv_values(env_path)
    env_comments = get_comments_from_env(env_path)

    # 3. 构建最终的数据结构
    config_data = []
    processed_keys = set()
    
    for group_def in group_definitions:
        section = {"title": group_def["title"], "icon": group_def["icon"], "vars": [], "test_name": group_def.get("test_name")}
        for var_def in group_def.get("vars", []):
            key = var_def["key"]
            var_data = {
                "key": key,
                "value": env_vars.get(key, ''),
                "comment": env_comments.get(key, ""),
                "type": var_def.get("type", "text"),
                "placeholder": var_def.get("placeholder", ""),
                "options": var_def.get("options", []),
                "min": var_def.get("min"),
                "max": var_def.get("max"),
            }
            section["vars"].append(var_data)
            processed_keys.add(key)
        
        if section["vars"]:
            config_data.append(section)

    # 4. 处理未被分组的 "孤儿" 配置项
    unclassified_vars = []
    for key, value in env_vars.items():
        if key not in processed_keys:
            unclassified_vars.append({
                "key": key,
                "value": value,
                "comment": env_comments.get(key, "无说明"),
                "type": "text", "placeholder": "", "options": [], "min": None, "max": None
            })
    
    if unclassified_vars:
        config_data.append({
            "title": "未分类配置",
            "icon": "fa-question-circle",
            "vars": unclassified_vars,
            "test_name": None # 确保未分类组没有测试
        })

    return config_data


# --- 路由函数 ---

@env_editor_bp.route('/setting', methods=['GET'])
def config_page():
    """渲染.env编辑器页面"""
    config_data = get_structured_config(env_path)
    all_tests = get_available_tests()
    
    # 找出所有已关联到配置分组的测试
    associated_tests = set()
    for section in config_data:
        if section.get('test_name'):
            associated_tests.add(section['test_name'])
            
    # 计算出未关联的测试，用于页面底部的备用选择框
    unassociated_tests = [t for t in all_tests if t not in associated_tests]
    
    return render_template('setting.html', config_data=config_data, unassociated_tests=unassociated_tests)


@env_editor_bp.route('/setting/save', methods=['POST'])
def save_config():
    """保存提交的表单数据到.env文件。"""
    try:
        # 注意：因为页面上有多个表单，这里只处理属于主配置表单的字段
        # request.form 包含了所有表单的数据，但 set_key 会覆盖，所以没问题
        # 如果有同名字段，需要区分，但这里 test_name 和配置项的 key 不会重名
        form_data = request.form.to_dict()
        form_data.pop('test_name', None) # 移除可能存在的 test_name 字段，避免写入 .env

        for key, value in form_data.items():
            set_key(env_path, key, value, quote_mode="always")
            
        config.reload_config()
        logger.info('配置已成功保存并重新加载！')
        flash('配置已成功保存并重新加载！', 'success')
    except Exception as e:
        flash(f'保存配置时发生错误: {e}', 'danger')
    
    return redirect(url_for('setting.config_page'))


@env_editor_bp.route('/setting/run_test', methods=['POST'])
def run_test_route():
    """运行单个测试并将结果通过 Flash 信息返回"""
    test_name = request.form.get('test_name')
    if not test_name:
        flash('请选择要运行的测试项', 'danger')
        return redirect(url_for('setting.config_page'))

    success, msg = run_single_test(test_name)
    if success:
        flash(f'[{test_name}] 测试通过: {msg}', 'success')
    else:
        flash(f'[{test_name}] 测试失败: {msg}', 'danger')

    return redirect(url_for('setting.config_page'))

