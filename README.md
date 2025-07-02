# DeepRearch 深度研究

本项目是一个基于 Python 实现的 AI 驱动的智能搜索与深度研究解决方案。它旨在通过良好的 Agent 架构设计和精密的搜索策略，帮助用户从海量信息中获取高质量、高相关的资料。

> **核心理念：** 提高搜索资料的质量，远比罗列上百个网页更有价值。

## ✨ 主要特性

*   **可完全本地部署**: 使用到的所有服务,均可本地部署,除大模型API外,不依赖任何在线服务。
*   **可视化的研究过程**: 整个研究过程完全透明，它会实时地向您“直播” AI 从初步规划、动态搜索、评估网页到迭代深化的每一步。
*   **兼容OpenAI格式的 API 服务**: 基于 Flask 构建，提供符合 OpenAI 格式的 API 接口：
    *   `/v1/chat/completions`: 处理用户查询，支持流式和非流式响应，能够根据请求智能选择搜索模式。
    *   `/v1/models`: 列出当前配置支持的 AI 模型。
*   **深度研究模式**:`deep-research`模式，通过多轮搜索、评估、信息提取和规划，实现对复杂问题的深入探索。
*   **灵活的搜索引擎集成**: 支持配置多种搜索引擎，如 SearXNG 和 Tavily，并可在它们之间进行故障切换。
*   **仅浏览高质量的网页**: 使用大模型评估搜索结果的价值，而不是一股脑全部塞入上下文。
*   **高效的网页内容抓取**: 使用 FireCrawl , Crawl4AI 或 Jina 网页爬虫服务。
*   **网页内容压缩**: 使用大模型压缩网页内容，减少上下文长度,提高有效信息密度。
*   **多个大模型协同工作**:
    *   **基础对话**: 处理用户交互和内部功能调度。
    *   **搜索关键词生成**: 智能生成高效的搜索查询。
    *   **网页价值评估**: AI 模型评估搜索结果的相关性和潜在价值。
    *   **内容压缩与提取**: 从抓取的网页中提取核心信息。
    *   **结果总结**: 将多源信息整合成连贯、易懂的答案。
*   **精密的提示工程**: 内置大量精心设计的 Prompt与消息处理，指导 LLM 完成复杂的搜索规划、信息评估和内容生成任务，在全部使用Gemini 2.5 flash模型的情况下，测试数十次未出现差错。

## 🏗️ 系统架构

![系统架构图](img/系统架构图.png)

## 🚀 快速开始

我们提供两种部署方式：使用 Docker（推荐）或直接在本地环境运行。

### **方法一：使用 Docker (推荐)**

这是最简单、最推荐的部署方式，无需手动管理 Python 环境和依赖。项目根目录已提供 `Dockerfile` 和 `docker-compose.yml` 文件。

#### 启动服务

您可以选择使用 Docker Compose 或 Docker CLI 来启动服务。

**A. 使用 Docker Compose (推荐)**

项目根目录已包含 `docker-compose.yml` 文件，内容如下：

```yaml
version: '3'

services:
  deepresearch:
    container_name: deepresearch
    image: cat3399/deepresearch:latest
    ports:
      - "5000:5000"
    # volumes:
    #   - ./.env:/app/.env # 如果您想使用本地的 .env 文件，请取消此行的注释
```

在项目根目录下运行以下命令即可启动服务：

```bash
docker-compose up -d
```
> **注意**：`docker-compose.yml` 文件中的 `volumes` 部分默认被注释。如果您希望将本地的 `.env` 文件直接映射到容器中（推荐做法），请**取消该行的注释**后再运行

**B. 使用 Docker CLI**

如果您不使用 Docker Compose，也可以使用以下命令直接运行 Docker 容器：

```bash
docker run -d --name deepresearch -p 5000:5000 cat3399/deepresearch:latest
```

#### **3. 访问服务**
服务启动后，即可通过 `http://127.0.0.1:5000` 访问 API 服务，或通过 `http://127.0.0.1:5000/setting` 访问可视化配置页面。

---

### **方法二：本地部署**

#### **1. 环境准备**

*   确保您已安装 Python 3.8+
*   建议使用 `uv` 或 `venv` 等虚拟环境。

#### **2. 安装依赖**

克隆本仓库到本地后，在项目根目录下运行：

```bash
pip install -r requirements.txt
```

#### **3. 配置环境变量**

> 可使用浏览器访问`http://127.0.0.1:5000/setting`进入配置文件的webui,进行可视化的配置

**A. 快速上手 (仅使用 Gemini)**

这是最简单的配置方式，如果您只想使用 Gemini API，请采用此方法。

*   复制 `.env.template` 文件并重命名为 `.env`
```bash
cp .env.template .env
```
*   **唯一步骤**: 只需在配置文件中填入 `ALL_IN_GEMINI_KEY` 即可。
*   **多 Key 支持**: 您可以填入多个 Gemini API Key，并用英文逗号 `,` 分隔。
>此配置基础与总结模型使用2.5pro,评估使用2.5flash 压缩使用 2.5flash lite 具体模型配置优先级高于此默认值
---

**B. 完整配置 (适用于所有模型)**
*   复制 `.env.template` 文件并重命名为 `.env`
```bash
cp .env.template .env
```
*   根据您的实际情况，在 `.env` 文件中填写必要的 API 密钥和 URL。

> **通用说明**:
> *   所有模型的 `API_KEY` 字段均支持填写多个密钥，用逗号 `,` 分隔，程序会从中随机选择一个使用。
> *   对于除内容压缩模型外的其他模型，如果将特定模型的配置项（如 `SEARCH_KEYWORD_API_KEY`, `SEARCH_KEYWORD_API_URL` 等）留空，系统将默认使用 `BASE_CHAT_*` 的配置。
> *   `API_TYPE` 字段用于指定 API 格式，留空默认为 `OPENAI` 格式,除内容压缩模型,其余暂不支持Gemini格式(Gemini有OpenAI兼容模式[OpenAI 兼容性  | Gemini API  | Google AI for Developers](https://ai.google.dev/gemini-api/docs/openai?hl=zh-cn))。

以下是关键配置项的详细说明：

#### **基础配置**
*   `API_KEY`: 访问本项目 API 服务时所需的授权密钥。

#### **搜索引擎配置**
> 优先使用 `SearXNG`，当 `SearXNG` 请求失败时，会自动切换到 `Tavily`。

* `SEARXNG_URL`: 自建 或 公共 SearXNG 实例，**必须支持 JSON 格式输出**。 

  

* `TAVILY_KEY`: Tavily 服务的 API 密钥。

* `TAVILY_MAX_NUM`: 使用 Tavily 搜索时，返回结果的最大数量 建议`20`。

  

  > `SEARCH_API_LIMIT`: 限制搜索引擎 API 的并发请求数，请根据您使用的服务商限制进行设置。

#### **网页爬虫配置 (至少配置一个)**
> 如果全部配置,优先级FireCrawl>Crawl4ai>Jina

* `FIRECRAWL_API_URL`: FireCrawl 服务的 URL。如果使用官方 API，此项可留空。

* `FIRECRAWL_API_KEY`: FireCrawl 服务的 API 密钥。本地部署时若未设置可留空，使用官方 API 则必须填写。

  

* `CRAWL4AI_API_URL`: Crawl4AI 服务的 URL。

  

* `JINA_API_URL`: Jina 服务的URL (官方提供免费版,详见 https://jina.ai/reader/ )

*   `JINA_API_KEY`: Jina 服务的API 密钥

#### **搜索与研究参数**
*   `CRAWL_THREAD_NUM`: 抓取网页时的并发任务数。建议根据网络和服务器性能适当调低以提高成功率（例如，FireCrawl 官方免费版限制为 10次/分钟）。
*   `MAX_SEARCH_RESULTS`: 普通搜索模式下，单次搜索最多处理的网页数量。
*   `MAX_DEEPRESEARCH_RESULTS`: 深度研究模式下，每次迭代最多处理的网页数量，不建议设置过大 建议`3`。
*   `MAX_STEPS_NUM`: 深度研究模式下的最大迭代次数 建议 `12`。

#### **大模型 (LLM) 配置**

*   **基础对话模型 (必须配置)**
    > 用于处理用户交互和工具调用，**模型需要支持 Function Calling**。
    *   `BASE_CHAT_API_KEY`: API 密钥。
    *   `BASE_CHAT_API_URL`: API 地址。
    *   `BASE_CHAT_MODEL`: 模型名称。

*   **搜索关键词生成模型 (必须配置)**
    
    *   `SEARCH_KEYWORD_API_KEY`, `SEARCH_KEYWORD_API_URL`, `SEARCH_KEYWORD_MODEL`
    
*   **搜索结果评估模型 (必须配置)**
    
    *   `EVALUATE_THREAD_NUM`: 评估网页价值时的并发任务数。
    *   `EVALUATE_API_KEY`, `EVALUATE_API_URL`, `EVALUATE_MODEL`
    
*   **网页内容压缩模型 (必须配置)**
    
    > 建议选择支持长上下文、响应速度快的模型。
    *   `COMPRESS_API_TYPE`: 指定 API 格式，如 `GEMINI` 或 `OPENAI`。
    *   `COMPRESS_API_KEY`: API 密钥。若使用 Gemini，建议至少提供两个密钥以避免速率限制问题。
    *   `COMPRESS_API_URL`: API 地址。
    *   `COMPRESS_MODEL`: 模型名称。
    
*   **最终总结生成模型 (必须配置)**
    
    *   `SUMMARY_API_TYPE`, `SUMMARY_API_KEY`, `SUMMARY_API_URL`, `SUMMARY_MODEL`

#### **4. 运行服务**

一键测试所有API是否正常
```
python main.py --test
```

在项目根目录下运行：

```bash
python main.py
```

服务默认启动在 `http://0.0.0.0:5000`。

## 🧩 外部服务依赖

**搜索引擎 API (二选一)**:

*   **Searxng**: [自建](https://docs.searxng.org/admin/installation-docker.html) 或使用 [公共服务器](https://searx.space/)。需开启 JSON 格式支持。
*   **Tavily**: [Tavily 官网](https://www.tavily.com/)

**网页爬虫 (三选一)**:

*   **FireCrawl**: [自建](https://docs.firecrawl.dev/contributing/self-host#docker-containers-fail-to-start) 或使用 [官方 API](https://firecrawl.dev)
*   **Crawl4AI**: [自建](https://docs.crawl4ai.com/core/docker-deployment/)
*   **Jina**: [官方免费API](https://jina.ai/reader/) 或者 [自建](https://github.com/intergalacticalvariable/reader)

**LLM**: 大模型 API 供应商

## 🛠️ API 使用示例

您可以使用任何兼容 OpenAI API 格式的客户端（如 LobeChat, One-API, OpenWebui, Cherry Studio）与服务进行交互。

以Cherry Studio为例

![使用示例_CherryStudio](img/使用示例_CherryStudio.png)

> **提示**: 使用带 `deep-research` 的模型 ID 即可触发深度研究模式。支持的模型 ID 列表可通过 `/v1/models` 接口获取。

## 📦 Python 库依赖

*   **Flask**: Web 框架。
*   **OpenAI Python SDK**: 与 OpenAI 兼容的 API 进行交互。
*   **Requests**: HTTP 请求库。
*   **BeautifulSoup4**: HTML/XML 解析。
*   **PyMuPDF, python-docx, openpyxl**: 用于解析 PDF, DOCX, XLSX 等文件。
*   **python-dotenv**: 加载环境变量。

完整的依赖列表请查看 `requirements.txt`。

## 💡 效果展示

### 总结类
> prompt:获取gemini claude deepseek glm qwen全部对话模型的参数,和官方api的价格,用表格清晰的展示,我要非常完整的数据,最后总结的时候不要有遗漏

> 本项目效果 (除最后总结使用 Gemini 2.5 Pro, 其余均使用 2.5 Flash 模型)

![模型总结1](img/模型总结1.png)
![模型总结2](img/模型总结2.png)

> OpenAI 免费版本 Deepresearch 效果 (欢迎提供付费版效果示例)
>
> [查看完整对话](https://chatgpt.com/share/6856adee-76ec-8004-a601-132d43ed1dab)

![模型总结-openai](img/模型总结-openai.png)

### 冷门问题
> prompt:rk3399 怎么在linux下,使用qemu 的kvm加速

> 关于 "RK3399 QEMU 启用 KVM"，重点在于大小核，**需要使用 `taskset` 绑核**。

![RK3399-kvm1](img/RK3399-kvm1.png)
![RK3399-kvm2](img/RK3399-kvm2.png)

> OpenAI 免费版本 Deepresearch 效果

![RK3399-kvm-openai](img/RK3399-kvm-openai.png)

## 🤔已知问题
*   过早结束研究 - 发起请求时带上"详细研究"之类的关键词

## ✍️ TODO

*   更加完善的项目管理
*   使用asyncio重构,避免超时,增强并发能力
*   更加优秀的架构设计(目前为顺序迭代,部分任务并不适合这个模式)
*   智能读取网页结果中的URL
*   追问


## 🤝 贡献

欢迎通过提交 Pull Requests 或 Issues 来改进本项目。您的每一个贡献都非常有价值！

## 📄 开源许可

本项目采用 [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) 许可证](http://creativecommons.org/licenses/by-nc-sa/4.0/)。

简单来说，这意味着：

*   **您可以自由地**：
    *   **共享** — 在任何媒介以任何形式复制、发行本作品
    *   **演绎** — 修改、转换或以本作品为基础进行创作
*   **惟须遵守下列条件**：
    *   **署名** — 您必须给出适当的署名，提供指向本许可的链接，并标明是否对原作品作了修改。
    *   **非商业性使用** — 您不得将本作品用于商业目的。
    *   **相同方式共享** — 如果您再混合、转换，或者基于本作品进行创作，您必须基于与原先许可协议相同的许可协议来分发您的贡献。

> 如果您希望将本项目用于商业目的，请联系作者获取商业授权。

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=cat3399/deepresearch&Date)](https://star-history.com/#cat3399/deepresearch&Date)
