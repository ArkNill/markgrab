"""Tests for content density filter."""

from bs4 import BeautifulSoup

from markgrab.filter.density import filter_low_density


def _make_soup(html):
    return BeautifulSoup(html, "html.parser")


def test_aside_removed():
    soup = _make_soup("""
    <div>
        <p>Main content paragraph with enough text.</p>
        <aside><ul><li><a href="#">Link 1</a></li><li><a href="#">Link 2</a></li></ul></aside>
    </div>
    """)
    content = soup.find("div")
    filter_low_density(content)

    assert content.find("aside") is None
    assert "Main content" in content.get_text()


def test_nav_removed():
    soup = _make_soup("""
    <div>
        <p>Article body text here.</p>
        <nav><a href="/">Home</a> | <a href="/about">About</a></nav>
    </div>
    """)
    content = soup.find("div")
    filter_low_density(content)

    assert content.find("nav") is None
    assert "Article body" in content.get_text()


def test_sidebar_class_removed():
    soup = _make_soup("""
    <div>
        <p>This is the main article content.</p>
        <div class="sidebar-widget">Related articles here</div>
    </div>
    """)
    content = soup.find("div", recursive=False)
    filter_low_density(content)

    assert "sidebar" not in content.get_text().lower() or "Related" not in content.get_text()


def test_sidebar_id_removed():
    soup = _make_soup("""
    <div>
        <p>Main text.</p>
        <div id="sidebar">Side content</div>
    </div>
    """)
    content = soup.find("div", recursive=False)
    filter_low_density(content)

    assert soup.find(id="sidebar") is None


def test_related_pattern_removed():
    soup = _make_soup("""
    <div>
        <p>Article content here.</p>
        <div class="related-posts"><a href="/1">Post 1</a><a href="/2">Post 2</a></div>
    </div>
    """)
    content = soup.find("div", recursive=False)
    filter_low_density(content)

    assert soup.find(class_="related-posts") is None


def test_newsletter_pattern_removed():
    soup = _make_soup("""
    <div>
        <p>Article content here.</p>
        <div class="newsletter-signup">Subscribe to our newsletter!</div>
    </div>
    """)
    content = soup.find("div", recursive=False)
    filter_low_density(content)

    assert soup.find(class_="newsletter-signup") is None


def test_high_link_density_block_removed():
    links = " ".join(f'<a href="/{i}">Link number {i} text</a>' for i in range(20))
    soup = _make_soup(f"""
    <div>
        <p>This is real article content that should be preserved.</p>
        <ul>{links}</ul>
    </div>
    """)
    content = soup.find("div", recursive=False)
    filter_low_density(content)

    assert "real article content" in content.get_text()
    assert content.find("ul") is None


def test_low_link_density_preserved():
    soup = _make_soup("""
    <div>
        <div>This is a paragraph with a <a href="/link">single link</a> in a long block of text
        that has plenty of non-link content to keep the link density low enough to be preserved
        as actual content rather than being filtered out as navigation.</div>
    </div>
    """)
    content = soup.find("div", recursive=False)
    filter_low_density(content)

    assert "single link" in content.get_text()


def test_content_without_noise_unchanged():
    soup = _make_soup("""
    <article>
        <h1>Title</h1>
        <p>First paragraph of the article.</p>
        <p>Second paragraph with more details.</p>
    </article>
    """)
    content = soup.find("article")
    original_text = content.get_text(strip=True)
    filter_low_density(content)

    assert content.get_text(strip=True) == original_text


def test_toc_removed():
    soup = _make_soup("""
    <div>
        <p>Introduction text.</p>
        <div class="toc">
            <a href="#s1">Section 1</a>
            <a href="#s2">Section 2</a>
        </div>
        <p>More content.</p>
    </div>
    """)
    content = soup.find("div", recursive=False)
    filter_low_density(content)

    assert soup.find(class_="toc") is None
    assert "Introduction" in content.get_text()
    assert "More content" in content.get_text()


def test_social_share_removed():
    soup = _make_soup("""
    <div>
        <p>Article text.</p>
        <div class="social-share">
            <a href="#">Twitter</a><a href="#">Facebook</a>
        </div>
    </div>
    """)
    content = soup.find("div", recursive=False)
    filter_low_density(content)

    assert soup.find(class_="social-share") is None


def test_comment_section_removed():
    soup = _make_soup("""
    <div>
        <p>Article text.</p>
        <div id="comments">
            <p>User comment here</p>
        </div>
    </div>
    """)
    content = soup.find("div", recursive=False)
    filter_low_density(content)

    assert soup.find(id="comments") is None
