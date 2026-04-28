#!/usr/bin/env python3
"""人民日报电子版文章采集 CLI。"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import logging
import random
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Comment
from dateutil import parser as date_parser


SOURCE = "人民日报"
DEFAULT_OUTPUT = "./data/rmrb"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 rmrb-crawler/1.0"


@dataclass
class PageInfo:
    page_no: str
    page_name: str
    page_title: str
    url: str


@dataclass
class ArticleInfo:
    source: str
    date: str
    page_no: str
    page_name: str
    page_title: str
    article_index: int
    title: str
    subtitle: str
    author: str
    url: str
    content: str
    images: list[str]
    word_count: int
    crawl_time: str
    file_path: str = ""


@dataclass
class CrawlResult:
    source: str
    date: str
    layout_url: str
    output_dir: str
    total_pages_found: int = 0
    pages_crawled: int = 0
    pages_skipped: list[dict[str, Any]] = field(default_factory=list)
    article_count: int = 0
    failed_count: int = 0
    articles: list[ArticleInfo] = field(default_factory=list)
    failed: list[dict[str, Any]] = field(default_factory=list)
    files: dict[str, str] = field(default_factory=dict)
    started_at: str = ""
    finished_at: str = ""
    success: bool = True


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="采集人民日报电子版文章")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--date")
    g.add_argument("--url")
    g.add_argument("--start-date")
    p.add_argument("--end-date")
    p.add_argument("--output", default=DEFAULT_OUTPUT)
    p.add_argument("--force", action="store_true")
    p.add_argument("--min-sleep", type=float, default=1)
    p.add_argument("--max-sleep", type=float, default=5)
    p.add_argument("--retries", type=int, default=3)
    p.add_argument("--timeout", type=float, default=15)
    args = p.parse_args()
    if args.start_date and not args.end_date:
        p.error("--start-date requires --end-date")
    if args.end_date and not args.start_date:
        p.error("--end-date requires --start-date")
    if args.min_sleep < 0 or args.max_sleep < args.min_sleep:
        p.error("--max-sleep must be >= --min-sleep >= 0")
    return args


def build_layout_url(day: str | date) -> str:
    d = date_parser.parse(str(day)).date()
    return f"https://paper.people.com.cn/rmrb/pc/layout/{d:%Y%m}/{d:%d}/node_01.html"


def parse_date_from_url(url: str) -> str:
    m = re.search(r"/layout/(\d{6})/(\d{2})/node_\d+\.html", url)
    if not m:
        m = re.search(r"/content/(\d{6})/(\d{2})/", url)
    if not m:
        raise ValueError(f"cannot parse date from URL: {url}")
    return date(int(m.group(1)[:4]), int(m.group(1)[4:6]), int(m.group(2))).isoformat()


def date_range(start: str, end: str) -> list[str]:
    s = date_parser.parse(start).date()
    e = date_parser.parse(end).date()
    if e < s:
        raise ValueError("end-date must be >= start-date")
    days = []
    while s <= e:
        days.append(s.isoformat())
        s += timedelta(days=1)
    return days


def fetch_html(session: requests.Session, url: str, retries: int, timeout: float, min_sleep: float, max_sleep: float) -> str:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        if attempt or min_sleep or max_sleep:
            time.sleep(random.uniform(min_sleep, max_sleep))
        try:
            r = session.get(url, timeout=timeout)
            r.raise_for_status()
            r.encoding = r.apparent_encoding or "utf-8"
            return r.text
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            logging.warning("fetch failed attempt=%s url=%s error=%s", attempt + 1, url, exc)
    raise RuntimeError(f"fetch failed after {retries + 1} attempts: {last_error}")


def clean_text(text: str) -> str:
    text = html.unescape(text or "")
    text = text.replace("\xa0", " ").replace("\u3000", " ")
    lines = [re.sub(r"[ \t]+", " ", x).strip() for x in text.splitlines()]
    return "\n".join(x for x in lines if x)


def parse_page_label(label: str, fallback_url: str = "") -> tuple[str, str, str]:
    label = clean_text(label).replace("版：", "版:")
    m = re.search(r"第?(\d{1,2})版[:：]?\s*(.*)", label)
    if m:
        no = m.group(1).zfill(2)
        name = m.group(2).strip() or ""
        return no, name, f"第{no}版：{name}" if name else f"第{no}版"
    m = re.search(r"node_(\d{1,2})\.html", fallback_url)
    no = m.group(1).zfill(2) if m else ""
    return no, label, f"第{no}版：{label}" if no and label else label


def parse_layout_pages(html_text: str, base_url: str) -> list[PageInfo]:
    soup = BeautifulSoup(html_text, "lxml")
    base_date = re.search(r"/pc/layout/(\d{6}/\d{2})/", base_url)
    base_marker = f"/rmrb/pc/layout/{base_date.group(1)}/" if base_date else "/rmrb/pc/layout/"
    pages: list[PageInfo] = []
    seen: set[str] = set()
    for a in soup.select(".swiper-slide a[href*='node_'], a[href*='node_']"):
        href = a.get("href")
        if not href:
            continue
        url = urljoin(base_url, href)
        if base_marker not in url:
            continue
        if url in seen:
            continue
        no, name, title = parse_page_label(a.get_text(" ", strip=True), url)
        if no:
            pages.append(PageInfo(no, name, title, url))
            seen.add(url)
    return sorted(pages, key=lambda x: x.page_no)


def parse_page_articles(html_text: str, base_url: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html_text, "lxml")
    nodes = soup.select(".news-list a[href*='content_']")
    if not nodes:
        nodes = soup.select("a[href*='content_']")
    articles, seen = [], set()
    for a in nodes:
        href = a.get("href")
        if not href:
            continue
        url = urljoin(base_url, href)
        if url in seen:
            continue
        title = clean_text(a.get_text(" ", strip=True))
        if title:
            articles.append({"title": title, "url": url})
            seen.add(url)
    return articles


def _prop_from_comments(soup: BeautifulSoup, key: str) -> str:
    pat = re.compile(rf"<{key}>(.*?)</{key}>", re.S)
    for c in soup.find_all(string=lambda x: isinstance(x, Comment)):
        m = pat.search(str(c))
        if m:
            return clean_text(BeautifulSoup(m.group(1), "lxml").get_text(" ", strip=True))
    return ""


def parse_article(html_text: str, url: str, metadata: dict[str, Any]) -> ArticleInfo:
    soup = BeautifulSoup(html_text, "lxml")
    box = soup.select_one("#ozoom") or soup.select_one("#articleContent") or soup.select_one(".article")
    title = _prop_from_comments(soup, "title")
    if not title:
        h1 = soup.select_one(".article h1, h1")
        title = clean_text(h1.get_text(" ", strip=True) if h1 else metadata.get("title", ""))
    subtitle = _prop_from_comments(soup, "subtitle")
    if not subtitle:
        h2 = soup.select_one(".article h2, h2")
        subtitle = clean_text(h2.get_text(" ", strip=True) if h2 else "")
    author = _prop_from_comments(soup, "author")
    images = []
    if box:
        for tag in box.select("script, style, .art-btn"):
            tag.decompose()
        for img in box.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src:
                images.append(urljoin(url, src))
        paras = [clean_text(p.get_text(" ", strip=True)) for p in box.find_all("p")]
        content = "\n\n".join(p for p in paras if p and p not in {title, subtitle, author})
        if not content:
            content = clean_text(box.get_text("\n", strip=True))
    else:
        content = ""
    for noise in ("上一篇", "下一篇", "返回目录", "字号", "复制"):
        content = re.sub(rf"(^|\n).*{noise}.*(?=\n|$)", "", content)
    content = clean_text(content).replace("\n", "\n\n")
    crawl_time = now_iso()
    return ArticleInfo(
        source=SOURCE,
        date=metadata["date"],
        page_no=metadata["page_no"],
        page_name=metadata["page_name"],
        page_title=metadata["page_title"],
        article_index=metadata["article_index"],
        title=title or metadata.get("title", ""),
        subtitle=subtitle,
        author=author,
        url=url,
        content=content,
        images=sorted(dict.fromkeys(images)),
        word_count=len(re.sub(r"\s+", "", content)),
        crawl_time=crawl_time,
    )


def sanitize_filename(name: str) -> str:
    name = clean_text(name)
    name = re.sub(r'[\\/:*?"<>|\s]+', "_", name)
    name = re.sub(r"_+", "_", name).strip("._ ")
    return (name[:60] or "untitled")


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem_hash = hashlib.md5(path.stem.encode("utf-8")).hexdigest()[:8]
    candidate = path.with_name(f"{path.stem}_{stem_hash}{path.suffix}")
    i = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}_{stem_hash}_{i}{path.suffix}")
        i += 1
    return candidate


def yaml_quote(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def article_md(article: ArticleInfo) -> str:
    images_yaml = "\n".join(f"  - {yaml_quote(x)}" for x in article.images) or "  []"
    meta = [
        "---",
        f"source: {article.source}",
        f"date: {article.date}",
        f'page_no: "{article.page_no}"',
        f"page_name: {article.page_name}",
        f"page_title: {article.page_title}",
        f"article_index: {article.article_index}",
        f"title: {yaml_quote(article.title)}",
        f"subtitle: {yaml_quote(article.subtitle)}",
        f"author: {yaml_quote(article.author)}",
        f"url: {yaml_quote(article.url)}",
        "images:",
        images_yaml,
        f"word_count: {article.word_count}",
        f"crawl_time: {yaml_quote(article.crawl_time)}",
        "---",
        "",
        f"# {article.title}",
        "",
    ]
    if article.subtitle:
        meta += [f"> {article.subtitle}", ""]
    meta += [
        f"- 来源：{article.source}",
        f"- 日期：{article.date}",
        f"- 版面：{article.page_title}",
    ]
    if article.author:
        meta.append(f"- 作者：{article.author}")
    meta += [f"- 原文链接：{article.url}", "", "## 正文", "", article.content or "", "", "## 图片链接", ""]
    meta += [*(f"- {x}" for x in article.images)] if article.images else ["无"]
    return "\n".join(meta).rstrip() + "\n"


def write_article_md(article: ArticleInfo, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(article_md(article), encoding="utf-8")


def article_to_dict(article: ArticleInfo) -> dict[str, Any]:
    return asdict(article)


def write_jsonl(items: Iterable[Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            if hasattr(item, "__dataclass_fields__"):
                item = asdict(item)
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def write_full_md(result: CrawlResult, path: Path) -> None:
    lines = [f"# 人民日报 {result.date}", ""]
    current_page = None
    for a in sorted(result.articles, key=lambda x: (x.page_no, x.article_index)):
        if a.page_title != current_page:
            current_page = a.page_title
            lines += [f"## {a.page_title}", ""]
        lines += [f"### {a.title}", ""]
        if a.subtitle:
            lines += [f"> {a.subtitle}", ""]
        lines += [f"- 来源：{a.source}", f"- 日期：{a.date}", f"- 版面：{a.page_title}"]
        if a.author:
            lines.append(f"- 作者：{a.author}")
        lines += [f"- 原文链接：{a.url}", "", "#### 正文", "", a.content or "", "", "#### 图片链接", ""]
        lines += [*(f"- {x}" for x in a.images)] if a.images else ["无"]
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_index(result: CrawlResult, path: Path) -> None:
    data = asdict(result)
    data["articles"] = [
        {"page_no": a.page_no, "page_name": a.page_name, "article_index": a.article_index, "title": a.title, "url": a.url, "file_path": a.file_path}
        for a in result.articles
    ]
    data.pop("failed", None)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def setup_logging(path: Path) -> None:
    logging.getLogger().handlers.clear()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(path, encoding="utf-8"), logging.StreamHandler(sys.stderr)],
    )


def make_article_path(article: ArticleInfo, articles_dir: Path, force: bool) -> Path:
    prefix = f"{article.date.replace('-', '')}_{article.page_no}_{article.article_index:03d}_"
    path = articles_dir / f"{prefix}{sanitize_filename(article.title)}.md"
    return path if force else unique_path(path)


def load_existing_article(path: Path) -> ArticleInfo | None:
    text = path.read_text(encoding="utf-8")
    fm = re.search(r"^---\n(.*?)\n---\n", text, re.S)
    if not fm:
        return None
    def get(k: str) -> str:
        m = re.search(rf"^{k}:\s*(.*)$", fm.group(1), re.M)
        if not m:
            return ""
        v = m.group(1).strip()
        try:
            return json.loads(v)
        except Exception:
            return v.strip('"')
    body = text.split("## 正文", 1)[-1].split("## 图片链接", 1)[0].strip()
    images = re.findall(r"^\s*-\s+(https?://\S+)", text.split("## 图片链接", 1)[-1], re.M)
    return ArticleInfo(SOURCE, get("date"), get("page_no"), get("page_name"), get("page_title"), int(get("article_index") or 0), get("title"), get("subtitle"), get("author"), get("url"), body, images, int(get("word_count") or len(body)), get("crawl_time"), str(path))


def crawl_date(day: str, output_root: str | Path, options: argparse.Namespace, layout_url: str | None = None) -> CrawlResult:
    layout_url = layout_url or build_layout_url(day)
    day = parse_date_from_url(layout_url) if layout_url else day
    out_dir = Path(output_root) / day
    out_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(out_dir / "crawler.log")
    result = CrawlResult(SOURCE, day, layout_url, str(out_dir), started_at=now_iso())
    result.files = {"full_md": "full.md", "articles_jsonl": "articles.jsonl", "failed_jsonl": "failed.jsonl", "log": "crawler.log"}
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    articles_dir = out_dir / "articles"
    try:
        layout_html = fetch_html(session, layout_url, options.retries, options.timeout, options.min_sleep, options.max_sleep)
        pages = parse_layout_pages(layout_html, layout_url) or [PageInfo("01", "", "第01版", layout_url)]
        result.total_pages_found = len(pages)
        for page in pages:
            if "广告" in page.page_name or "广告" in page.page_title:
                result.pages_skipped.append({"page_no": page.page_no, "page_name": page.page_name, "reason": "advertisement"})
                continue
            result.pages_crawled += 1
            logging.info("crawl page %s %s", page.page_no, page.page_name)
            try:
                page_html = layout_html if page.url == layout_url else fetch_html(session, page.url, options.retries, options.timeout, options.min_sleep, options.max_sleep)
                links = parse_page_articles(page_html, page.url)
            except Exception as exc:  # noqa: BLE001
                result.failed.append({"date": day, "page_no": page.page_no, "page_name": page.page_name, "title": "", "url": page.url, "error": str(exc), "failed_at": now_iso()})
                continue
            for idx, link in enumerate(links, 1):
                meta = {"date": day, "page_no": page.page_no, "page_name": page.page_name, "page_title": page.page_title, "article_index": idx, "title": link["title"]}
                try:
                    temp_title = sanitize_filename(link["title"])
                    expected = articles_dir / f"{day.replace('-', '')}_{page.page_no}_{idx:03d}_{temp_title}.md"
                    if expected.exists() and not options.force:
                        old = load_existing_article(expected)
                        if old:
                            old.file_path = str(Path("articles") / expected.name)
                            result.articles.append(old)
                            continue
                    article_html = fetch_html(session, link["url"], options.retries, options.timeout, options.min_sleep, options.max_sleep)
                    article = parse_article(article_html, link["url"], meta)
                    path = make_article_path(article, articles_dir, options.force)
                    article.file_path = str(Path("articles") / path.name)
                    write_article_md(article, path)
                    result.articles.append(article)
                except Exception as exc:  # noqa: BLE001
                    logging.exception("article failed url=%s", link["url"])
                    result.failed.append({"date": day, "page_no": page.page_no, "page_name": page.page_name, "title": link.get("title", ""), "url": link["url"], "error": str(exc), "failed_at": now_iso()})
    except Exception as exc:  # noqa: BLE001
        result.success = False
        result.failed.append({"date": day, "page_no": "", "page_name": "", "title": "", "url": layout_url, "error": str(exc), "failed_at": now_iso()})
    result.article_count = len(result.articles)
    result.failed_count = len(result.failed)
    result.finished_at = now_iso()
    result.success = result.success and result.article_count > 0 and result.failed_count == 0
    write_full_md(result, out_dir / "full.md")
    write_jsonl(result.articles, out_dir / "articles.jsonl")
    write_jsonl(result.failed, out_dir / "failed.jsonl")
    result.files["index_json"] = "index.json"
    write_index(result, out_dir / "index.json")
    return result


def main() -> int:
    args = parse_args()
    try:
        if args.url:
            days = [parse_date_from_url(args.url)]
            urls = {days[0]: args.url}
        elif args.date:
            days, urls = [date_parser.parse(args.date).date().isoformat()], {}
        else:
            days, urls = date_range(args.start_date, args.end_date), {}
        results = [crawl_date(d, args.output, args, urls.get(d)) for d in days]
        summary = {
            "success": all(r.success for r in results),
            "dates": days,
            "output_root": args.output,
            "total_articles": sum(r.article_count for r in results),
            "total_failed": sum(r.failed_count for r in results),
            "date_results": [
                {
                    "date": r.date,
                    "success": r.success,
                    "article_count": r.article_count,
                    "failed_count": r.failed_count,
                    "output_dir": r.output_dir,
                    "full_md": str(Path(r.output_dir) / "full.md"),
                    "articles_jsonl": str(Path(r.output_dir) / "articles.jsonl"),
                    "index_json": str(Path(r.output_dir) / "index.json"),
                }
                for r in results
            ],
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if summary["success"] else 1
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False), file=sys.stdout)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
