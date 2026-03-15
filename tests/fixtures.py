"""Shared test fixtures — sample HTML documents."""

SIMPLE_HTML = """\
<!DOCTYPE html>
<html>
<head><title>Simple Article</title></head>
<body>
<article>
<h1>Main Heading</h1>
<p>This is the first paragraph of the article. It contains enough text to pass
the content threshold for the parser to identify it as meaningful content.</p>
<p>Second paragraph with additional details about the topic being discussed in
this test article for the MarkGrab extraction library.</p>
</article>
</body>
</html>"""

NOISY_HTML = """\
<!DOCTYPE html>
<html>
<head>
<title>Page Title</title>
<meta property="og:title" content="OG Title Override">
<meta property="og:description" content="A meta description">
<meta name="author" content="Test Author">
</head>
<body>
<script>var analytics = {};</script>
<style>.ad { display: block; }</style>
<nav><a href="/">Home</a> | <a href="/about">About</a></nav>
<div class="cookie-banner">We use cookies. <button>Accept</button></div>
<article>
<h1>Real Article Title</h1>
<p>This is the actual content that should be extracted. It has meaningful text
about an important topic that readers care about and want to understand.</p>
<p>More content here with details and explanations that add value to the article
and provide additional context for the reader.</p>
<ul>
<li>Point one</li>
<li>Point two</li>
<li>Point three</li>
</ul>
</article>
<aside>Related: <a href="/other">Other article</a></aside>
<footer>Copyright 2024 Test Site</footer>
<script>trackPageView();</script>
</body>
</html>"""

KOREAN_HTML = """\
<!DOCTYPE html>
<html>
<head><title>한국어 기사 제목</title></head>
<body>
<article>
<h1>인공지능의 미래</h1>
<p>인공지능 기술이 빠르게 발전하고 있습니다. 최근 대규모 언어 모델의 등장으로
자연어 처리 분야에서 큰 진전이 이루어졌습니다. 이러한 변화는 산업 전반에 걸쳐
광범위한 영향을 미치고 있습니다.</p>
<p>이러한 기술 발전은 다양한 산업 분야에 혁신을 가져오고 있으며, 앞으로 더 많은
변화가 예상됩니다. 한국에서도 AI 관련 투자가 크게 증가하고 있습니다.</p>
</article>
</body>
</html>"""

MINIMAL_HTML = "<html><body><p>Just a paragraph.</p></body></html>"

NO_ARTICLE_HTML = """\
<!DOCTYPE html>
<html>
<head><title>No Article Tag</title></head>
<body>
<nav><a href="/">Home</a></nav>
<div class="content">
<h1>Page Title</h1>
<p>This page does not use article or main tags. The content is directly in a div
inside body. It has enough text to be meaningful and extracted properly by the
parser even without semantic HTML5 tags.</p>
<p>Additional paragraph with more content that adds context and detail.</p>
</div>
<footer>Site footer</footer>
</body>
</html>"""

HIDDEN_ELEMENTS_HTML = """\
<!DOCTYPE html>
<html>
<head><title>Hidden Test</title></head>
<body>
<article>
<h1>Visible Content</h1>
<p>This paragraph is visible and should be extracted.</p>
<div style="display: none">This is hidden and should be removed.</div>
<div aria-hidden="true">Screen reader hidden content.</div>
<p>Another visible paragraph after hidden content.</p>
</article>
</body>
</html>"""
