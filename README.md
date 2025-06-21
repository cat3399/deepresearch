# AI 驱动的深度研究和智能搜索项目

本项目是一个基于 Python 实现的 AI 驱动的智能搜索与深度研究解决方案。它旨在通过良好的 Agent 架构设计和精密的搜索策略，帮助用户从海量信息中获取高质量、高相关的资料，而不仅仅是罗列大量网页

核心理念：**提高搜索资料的质量比获取上百个网页内容更为重要。**

## ✨ 主要特性

*   **强大的 API 服务**: 基于 Flask 构建，提供符合 OpenAI 格式的 API 接口：
    *   `/v1/chat/completions`: 处理用户查询，支持流式和非流式响应，能够根据请求智能选择搜索模式。
    *   `/v1/models`: 列出当前配置支持的 AI 模型。
*   **深度研究模式**: 独有的“deep-research”模式，通过多轮搜索、评估、信息提取和规划，实现对复杂问题的深入探索。
*   **灵活的搜索引擎集成**: 支持配置多种搜索引擎，如 SearXNG 和 Tavily，并可在它们之间进行故障切换。
*   **高效的网页内容抓取**: 集成 FireCrawl 和 Crawl4AI 等专业网页爬虫服务，确保高质量的网页内容获取。
*   **多个大模型协同工作**:
    *   **基础对话**: 处理用户交互和内部功能调度。
    *   **搜索关键词生成**: 智能生成高效的搜索查询。
    *   **网页价值评估**: AI 模型评估搜索结果的相关性和潜在价值。
    *   **内容压缩与提取**: 从抓取的网页中提取核心信息。
    *   **结果总结**: 将多源信息整合成连贯、易懂的答案。
*   **精密的提示工程**: 内置大量精心设计的 Prompt，指导 LLM 完成复杂的搜索规划、信息评估和内容生成任务。
*   **高度可配置**: 通过 `.env` 文件轻松配置所有外部服务（搜索引擎、爬虫、LLM API）的密钥和 URL。
*   **依赖清晰**: 使用 `requirements.txt` 管理所有 Python 依赖。

## 🚀 快速开始

### 1. 环境准备

*   确保您已安装 Python3
*   建议使用uv

### 2. 安装依赖

克隆本仓库到本地后，在项目根目录下运行：

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

*   复制 `.env.template` 文件并重命名为 `.env`。
*   根据您的实际情况，在 `.env` 文件中填写必要的 API 密钥和 URL。关键配置项包括：
    *   `SEARXNG_URL` 或 `TAVILY_KEY` (至少配置一个搜索引擎)
    *   `FIRECRAWL_API_URL` / `FIRECRAWL_API_KEY` 或 `CRAWL4AI_API_URL` (至少配置一个网页爬虫)
    *   `BASE_CHAT_API_KEY`, `BASE_CHAT_API_URL`, `BASE_CHAT_MODEL` (基础对话模型)
    *   `COMPRESS_API_KEY`, `COMPRESS_API_URL`, `COMPRESS_MODEL` (内容压缩模型)
    *   其他可选的模型配置 (如搜索关键词生成、评估、总结模型，若不单独配置则默认使用基础对话模型配置)

    详细配置说明请参考 `config/base_config.py` 中的注释和校验逻辑。

### 4. 运行服务

在项目根目录下运行：

```bash
python main.py
```

服务默认启动在 `http://0.0.0.0:5000`。

## 🛠️ 使用示例

您可以使用任何兼容 OpenAI API 格式的客户端（如 Cherry Studio或者OpenWebui）与服务进行交互。

**请求 `/v1/chat/completions`:**

*   **URL**: `http://localhost:5000/v1/chat/completions`
*   **Method**: `POST`
*   **Headers**:
    *   `Authorization`: `Bearer sk-1` (或您在代码中设置的其他 API Key)
    *   `Content-Type`: `application/json`
*   **Body** (示例):

    ```json
    {
        "model": "your-summary-model-deep-research", // 使用 "deep-research" 后缀触发深度研究模式
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "请详细介绍一下最近发布的AI视频生成模型Sora和Kling，并对比它们的区别。"}
        ],
        "stream": false // 设置为 true 以获取流式响应
    }
    ```

    支持的模型 ID 可以在 `/v1/models` 接口获取，通常包含 `-search`, `-re-search`, `-deep-research` 等后缀以指示不同的处理流程。


```

## 📦 主要依赖

*   Flask: Web 框架。
*   OpenAI Python SDK: 与 OpenAI 兼容的 API 进行交互。
*   Requests: HTTP 请求库。
*   BeautifulSoup4: HTML/XML 解析。
*   PyMuPDF, python-docx, openpyxl: 用于解析 PDF, DOCX, XLSX 等文件。
*   python-dotenv: 加载环境变量。

完整的依赖列表请查看 `requirements.txt`。

## 🤝 贡献

欢迎提交 Pull Requests 或 Issues 来改进本项目。

## 📄 开源许可

本项目采用 [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) 许可证](http://creativecommons.org/licenses/by-nc-sa/4.0/)。

简单来说，这意味着：
*   **您可以自由地**：
    *   **共享** — 在任何媒介以任何形式复制、发行本作品
    *   **演绎** — 修改、转换或以本作品为基础进行创作
    只要你遵守许可协议条款。
*   **惟须遵守下列条件**：
    *   **署名** — 您必须给出适当的署名，提供指向本许可的链接，同时标明是否（对原始作品）作了修改。您可以用任何合理的方式来署名，但是不得以任何方式暗示许可人为您或您的使用背书。
    *   **非商业性使用** — 您不得将本作品用于商业目的。
    *   **相同方式共享** — 如果您再混合、转换或者基于本作品进行创作，您必须基于与原先许可协议相同的许可协议分发您贡献的作品。

如果您希望将本项目用于商业目的，请联系作者获取商业授权。