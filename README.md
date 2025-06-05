**一个开源的deepresearch方案**

提高搜索资料的质量比获取上百个网页内容更为重要

### 本地运行 Crawl4AI

除了设置 `CRAWL4AI_API_URL` 调用远程接口外, 也可以在本地安装并使用 Crawl4AI。

```bash
pip install -U crawl4ai
crawl4ai-setup    # 下载浏览器依赖
crawl4ai-doctor   # 验证安装
```

安装完成后, 设置环境变量即可让程序走本地模式:

```bash
export CRAWL4AI_LOCAL=true
```

此时 `url2txt` 会自动使用本地 Crawl4AI 抓取网页内容, 不再依赖外部 API。

