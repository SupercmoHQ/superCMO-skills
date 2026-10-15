"""url_extraction's one Firecrawl read returns what a brand profile needs beyond the page's text: the
colours, fonts and logo the page renders (branding) and a screenshot, at no extra
Firecrawl credit. Image fields pass only as URLs: an inline logo would bloat every reply. The response
below is trimmed from a real read of a brand's homepage (2026-10-15)."""

import supercmo_env
from supercmo_skills.providers import firecrawl

_SHOT = "https://storage.googleapis.com/firecrawl-scrape-media/screenshot-74c5.png?sig=x"
_REAL = {"success": True, "data": {
    "json": {"brand_name": "Northwind"},
    "screenshot": _SHOT,
    "metadata": {"title": "Northwind", "creditsUsed": 5},
    "branding": {
        "brandName": "AI Ad Maker for Indian Brands",
        "colorScheme": "light",
        "colors": {"primary": "#8E51FF", "secondary": "#090E34", "accent": "#314158",
                   "background": "#FFFFFF", "textPrimary": "#637381", "link": "#314158"},
        "fonts": [{"family": "Inter", "role": "body"}],
        "typography": {"fontFamilies": {"primary": "Inter", "heading": "Inter"}},
        "personality": {"tone": "modern", "energy": "medium", "targetAudience": "businesses"},
        "confidence": {"colors": 0.97, "overall": 0.82},
        "logo": "https://imagedelivery.net/x/mascot-image/w=36",
        "images": {"logo": "https://imagedelivery.net/x/mascot-image/w=36",
                   "favicon": "data:image/png;base64," + "A" * 30000,
                   "ogImage": None, "logoHref": "/", "logoAlt": "Northwind"},
        "components": {"buttonPrimary": {"background": "#FFFFFF"}},
        "spacing": {"baseUnit": 4},
        "designSystem": {"framework": "tailwind"},
    }}}


def _read(monkeypatch, response):
    sent = {}

    def fake(method, url, body=None, headers=None):
        sent["body"] = body
        return response, 200, None
    monkeypatch.setattr(supercmo_env, "_request", fake)
    return firecrawl.extract_generate(None, {"url": "https://example.com", "prompt": "p"}, "k"), sent


def test_one_read_asks_for_branding_and_a_viewport_screenshot(monkeypatch):
    _, sent = _read(monkeypatch, _REAL)
    formats = sent["body"]["formats"]
    assert formats[0]["type"] == "json" and "branding" in formats
    assert {"type": "screenshot", "fullPage": False} in formats


def test_branding_keeps_what_a_profile_uses_and_image_fields_only_as_urls(monkeypatch):
    out, _ = _read(monkeypatch, _REAL)
    b = out["branding"]
    assert b["colors"]["primary"] == "#8E51FF" and b["fonts"] == [{"family": "Inter", "role": "body"}]
    assert b["logo"].startswith("https://")
    assert b["images"] == {"logo": "https://imagedelivery.net/x/mascot-image/w=36", "logoAlt": "Northwind"}
    assert not {"components", "spacing", "designSystem", "brandName", "personality", "confidence"} & set(b)
    assert out["screenshot"] == _SHOT and out["data"] == {"brand_name": "Northwind"}


def test_a_page_without_branding_or_screenshot_still_returns_its_data(monkeypatch):
    out, _ = _read(monkeypatch, {"success": True, "data": {"json": {"brand_name": "X"}}})
    assert out["ok"] and out["branding"] is None and out["screenshot"] is None


def test_without_a_prompt_the_page_text_comes_back_for_one_credit(monkeypatch):
    page = {"success": True, "data": {"markdown": "# Northwind\n" + "x" * 70_000, "branding": _REAL["data"]["branding"],
                                      "screenshot": _SHOT}}
    sent = {}

    def fake(method, url, body=None, headers=None):
        sent["body"] = body
        return page, 200, None
    monkeypatch.setattr(supercmo_env, "_request", fake)
    out = firecrawl.extract_generate(None, {"url": "https://example.com"}, "k")
    assert sent["body"]["formats"][0] == "markdown"
    assert not any(isinstance(f, dict) and f.get("type") == "json" for f in sent["body"]["formats"])
    assert out["ok"] and out["data"]["markdown"].startswith("# Northwind")
    assert len(out["data"]["markdown"]) == firecrawl.PAGE_CHARS and out["data"]["truncated"] is True
    assert out["branding"]["colors"]["primary"] == "#8E51FF" and out["screenshot"] == _SHOT


def test_a_page_with_no_text_still_returns_what_it_renders(monkeypatch):
    out, _ = _read_page(monkeypatch, {"success": True, "data": {"markdown": "", "screenshot": _SHOT,
                                                                 "branding": _REAL["data"]["branding"]}})
    assert out["ok"] and out["data"] == {"markdown": "", "truncated": False} and out["screenshot"] == _SHOT
    out, _ = _read_page(monkeypatch, {"success": True, "data": {"markdown": ""}})
    assert out["ok"] is False


def _read_page(monkeypatch, response):
    monkeypatch.setattr(supercmo_env, "_request", lambda method, url, body=None, headers=None: (response, 200, None))
    return firecrawl.extract_generate(None, {"url": "https://example.com"}, "k"), None
