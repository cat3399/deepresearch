import os
from pathlib import Path
import sys
from flask import Blueprint, render_template, request, redirect, url_for, flash
from dotenv import find_dotenv, set_key, dotenv_values

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
env_path = ROOT_DIR.joinpath(".env")

env_editor_bp = Blueprint('setting', __name__, template_folder='templates')

@env_editor_bp.route('/setting', methods=['GET'])
def config_page():
    """渲染.env编辑器页面"""
    # 使用 dotenv_values 读取所有键值对
    env_vars = dotenv_values(env_path)
    return render_template('setting.html', env_vars=env_vars)
@env_editor_bp.route('/setting/save', methods=['POST'])
def save_config():
    """保存提交的表单数据到.env文件"""
    
    # 遍历表单提交的所有项
    for key, value in request.form.items():
        # 使用 set_key 安全地写入或更新键值对
        set_key(env_path, key, value)
    # 给出用户反馈
    flash('配置已成功保存！', 'success')
    flash('重要提示：你需要重启服务才能让新的配置生效。', 'warning')
    
    return redirect(url_for('setting.config_page'))