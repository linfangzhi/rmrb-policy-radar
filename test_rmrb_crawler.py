import json
from argparse import Namespace

from rmrb_crawler import (
    ArticleInfo,
    article_md,
    build_layout_url,
    date_range,
    parse_date_from_url,
    parse_layout_pages,
    sanitize_filename,
    write_article_md,
    write_jsonl,
)


def test_build_layout_url():
    assert build_layout_url("2026-04-28") == "https://paper.people.com.cn/rmrb/pc/layout/202604/28/node_01.html"


def test_parse_date_from_url():
    assert parse_date_from_url("https://paper.people.com.cn/rmrb/pc/layout/202604/28/node_01.html") == "2026-04-28"
    assert parse_date_from_url("https://paper.people.com.cn/rmrb/pc/content/202604/28/content_1.html") == "2026-04-28"


def test_sanitize_filename():
    assert sanitize_filename(' 学会/通过:网络?走"群众"路线 ' ) == "学会_通过_网络_走_群众_路线"
    assert len(sanitize_filename("中" * 100)) == 60


def sample_article():
    return ArticleInfo(
        source="人民日报",
        date="2026-04-28",
        page_no="01",
        page_name="要闻",
        page_title="第01版：要闻",
        article_index=1,
        title="文章标题",
        subtitle="副标题",
        author="本报记者",
        url="https://example.com/a.html",
        content="正文第一段。\n\n正文第二段。",
        images=["https://example.com/a.jpg"],
        word_count=12,
        crawl_time="2026-04-28T09:30:00+08:00",
        file_path="articles/a.md",
    )


def test_markdown_generation(tmp_path):
    article = sample_article()
    path = tmp_path / "a.md"
    write_article_md(article, path)
    text = path.read_text(encoding="utf-8")
    assert "# 文章标题" in text
    assert "## 正文" in text
    assert "- https://example.com/a.jpg" in text
    assert article_md(article).startswith("---")


def test_jsonl_generation(tmp_path):
    path = tmp_path / "articles.jsonl"
    write_jsonl([sample_article()], path)
    rows = path.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    data = json.loads(rows[0])
    assert data["title"] == "文章标题"
    assert data["source"] == "人民日报"


def test_ad_page_skip_parse_basis():
    html = """
    <div class="swiper-slide"><a href="node_01.html">01版：要闻</a></div>
    <div class="swiper-slide"><a href="node_16.html">16版：广告</a></div>
    """
    pages = parse_layout_pages(html, "https://paper.people.com.cn/rmrb/pc/layout/202604/28/node_01.html")
    skipped = [
        {"page_no": p.page_no, "page_name": p.page_name, "reason": "advertisement"}
        for p in pages
        if "广告" in p.page_name
    ]
    assert len(pages) == 2
    assert skipped == [{"page_no": "16", "page_name": "广告", "reason": "advertisement"}]


def test_date_range_inclusive():
    assert date_range("2026-04-01", "2026-04-03") == ["2026-04-01", "2026-04-02", "2026-04-03"]
