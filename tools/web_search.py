from __future__ import annotations

import os
import re
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

from langchain.tools import tool


def _baidu_endpoint() -> str:
    return os.getenv("BAIDU_SEARCH_ENDPOINT", "https://www.baidu.com/s")


def _http_timeout_seconds() -> int:
    raw = os.getenv("BAIDU_SEARCH_TIMEOUT_SECONDS", "10").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 10


def _clean_text(raw: str) -> str:
    text = re.sub(r"<[^>]+>", "", raw)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_baidu_items(html: str, max_results: int) -> list[dict[str, str]]:
    # 百度结构会变化，这里使用宽松正则做 MVP 解析。
    title_pattern = re.compile(
        r'<h3[^>]*>.*?<a[^>]*href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?</h3>',
        re.S,
    )
    snippet_pattern = re.compile(
        r'<div[^>]*class="[^"]*(?:c-abstract|content-right_8Zs40|c-span-last)[^"]*"[^>]*>'
        r"(?P<snippet>.*?)</div>",
        re.S,
    )
    source_pattern = re.compile(
        r'<span[^>]*class="[^"]*(?:source|cosc-source-text)[^"]*"[^>]*>(?P<source>.*?)</span>',
        re.S,
    )

    items: list[dict[str, str]] = []
    snippets = snippet_pattern.findall(html)
    sources = source_pattern.findall(html)
    for idx, match in enumerate(title_pattern.finditer(html)):
        if len(items) >= max_results:
            break
        url = match.group("url").strip()
        if not url:
            continue
        title = _clean_text(match.group("title"))
        snippet = _clean_text(snippets[idx]) if idx < len(snippets) else ""
        source = _clean_text(sources[idx]) if idx < len(sources) else "unknown"
        if not title:
            continue
        items.append(
            {
                "name": title,
                "url": url,
                "snippet": snippet or "（无摘要）",
                "source": source,
            }
        )
    return items


def _to_http_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme == "https":
        return urlunsplit(("http", parts.netloc, parts.path, parts.query, parts.fragment))
    return url


def _format_results(items: list[dict[str, str]], query: str, days: int) -> str:
    if not items:
        return f"未检索到结果。query={query}, days={days}"

    lines = [f"最新网络检索结果（query={query}, days={days}）:"]
    for idx, item in enumerate(items, start=1):
        name = item.get("name", "")
        url = item.get("url", "")
        snippet = item.get("snippet", "")
        source = item.get("source", "unknown")
        lines.append(
            f"{idx}. {name}\n"
            f"   来源: {source}\n"
            f"   链接: {url}\n"
            f"   摘要: {snippet}"
        )
    return "\n".join(lines)


@tool
def web_search(query: str, days: int = 7, max_results: int = 5) -> str:
    """使用百度搜索网络最新信息。适用于“最新消息/近期新闻/刚刚发生”类问题。"""
    clean_query = query.strip()
    if not clean_query:
        return "百度搜索不可用：query 不能为空。"

    safe_days = max(1, min(days, 30))
    safe_max_results = max(1, min(max_results, 10))
    # 百度网页检索没有稳定的公开 freshness 参数，MVP 通过追加时效语义增强近期召回。
    query_with_time = f"{clean_query} 最近{safe_days}天"

    params = {
        "wd": query_with_time,
        "rn": safe_max_results,
        "ie": "utf-8",
    }
    url = f"{_baidu_endpoint()}?{urlencode(params)}"
    request = Request(
        url=url,
        headers={
            "User-Agent": "Lang-Agent/1.0",
            "Accept-Language": "zh-CN,zh;q=0.9",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=_http_timeout_seconds()) as response:
            body = response.read().decode("utf-8")
    except HTTPError as e:
        return f"百度搜索失败：HTTP {e.code}"
    except URLError as e:
        reason_text = str(e.reason)
        if "CERTIFICATE_VERIFY_FAILED" in reason_text or "key too weak" in reason_text:
            fallback_url = _to_http_url(url)
            fallback_request = Request(
                url=fallback_url,
                headers={
                    "User-Agent": "Lang-Agent/1.0",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                },
                method="GET",
            )
            try:
                with urlopen(
                    fallback_request, timeout=_http_timeout_seconds()
                ) as response:
                    body = response.read().decode("utf-8")
            except HTTPError as http_err:
                return f"百度搜索失败：HTTP {http_err.code}"
            except URLError as url_err:
                return f"百度搜索失败：网络错误 {url_err.reason}"
            except Exception as ex:
                return f"百度搜索失败：{ex}"
        else:
            return f"百度搜索失败：网络错误 {e.reason}"
    except Exception as e:
        return f"百度搜索失败：{e}"

    items = _extract_baidu_items(body, safe_max_results)
    return _format_results(items, clean_query, safe_days)
