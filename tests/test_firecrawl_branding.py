"""url_extraction's Firecrawl reads. With a prompt or schema it asks for the JSON reader alone, exactly as
0.1.24 did: branding bypasses Firecrawl's cache and some third-party pages refuse it. Without either it
returns the page's own text with the colours, fonts and logo the page renders (branding) and a
screenshot. A page that answers HTTP 400 or above is a failed read. The branding below is trimmed from a real read of a brand's homepage."""

import pytest
import supercmo_env
from supercmo_skills.providers import firecrawl

_SHOT = "https://storage.googleapis.com/firecrawl-scrape-media/screenshot-74c5.png?sig=x"
_BRANDING = {
    "brandName": "AI Ad Maker",
    "colorScheme": "light",
    "colors": {"primary": "#8E51FF", "secondary": "#090E34", "accent": "#314158",
               "background": "#FFFFFF", "textPrimary": "#637381", "link": "#314158"},
    "fonts": [{"family": "Inter", "role": "body"}],
    "typography": {"fontFamilies": {"primary": "Inter", "heading": "Inter"}},
    "personality": {"tone": "modern"},
    "confidence": {"colors": 0.97},
    "logo": "https://imagedelivery.net/x/mascot-image/w=36",
    "images": {"logo": "https://imagedelivery.net/x/mascot-image/w=36",
               "favicon": "data:image/png;base64," + "A" * 30000,
               "ogImage": None, "logoHref": "/", "logoAlt": "Northwind"},
    "components": {"buttonPrimary": {"background": "#FFFFFF"}},
}


def _run(monkeypatch, payload, *responses):
    """Feed the provider one (parsed, status, err) per request it makes; return its result and the bodies sent."""
    sent, queue = [], list(responses)

    def fake(method, url, body=None, headers=None):
        sent.append(body)
        return queue.pop(0)
    monkeypatch.setattr(supercmo_env, "_request", fake)
    return firecrawl.extract_generate(None, {"url": "https://example.com", **payload}, "k"), sent


def _v0124_body(payload):
    """0.1.24's request, verbatim: the structured read must not drift from it."""
    fmt = {"type": "json"}
    if payload.get("prompt"):
        fmt["prompt"] = payload["prompt"]
    if payload.get("schema"):
        fmt["schema"] = payload["schema"]
    return {"url": payload["url"], "formats": [fmt]}


@pytest.mark.parametrize("payload", [{"prompt": "name"}, {"schema": {"type": "object"}},
                                     {"prompt": "name", "schema": {"type": "object"}}])
def test_a_structured_read_sends_exactly_what_0_1_24_sent(payload):
    p = {"url": "https://example.com", **payload}
    assert firecrawl._build_extract_input(None, p) == _v0124_body(p)


def test_a_structured_read_returns_json_without_branding_or_screenshot(monkeypatch):
    ok = ({"data": {"json": {"name": "Northwind"}, "metadata": {"statusCode": 200, "creditsUsed": 5}}}, 200, None)
    out, sent = _run(monkeypatch, {"prompt": "name"}, ok)
    assert out == {"ok": True, "model": None, "data": {"name": "Northwind"},
                   "metadata": {"statusCode": 200, "creditsUsed": 5}}
    assert len(sent) == 1


def test_a_page_read_returns_its_text_branding_and_screenshot(monkeypatch):
    page = ({"data": {"markdown": "# Northwind\n" + "x" * 70_000, "branding": _BRANDING, "screenshot": _SHOT,
                      "metadata": {"statusCode": 200}}}, 200, None)
    out, sent = _run(monkeypatch, {}, page)
    assert sent[0]["formats"] == ["markdown", "branding", {"type": "screenshot", "fullPage": False}]
    assert out["ok"] and out["data"]["markdown"].startswith("# Northwind")
    assert len(out["data"]["markdown"]) == firecrawl.PAGE_CHARS and out["data"]["truncated"] is True
    b = out["branding"]
    assert b["colors"]["primary"] == "#8E51FF" and b["logo"].startswith("https://")
    assert b["images"] == {"logo": "https://imagedelivery.net/x/mascot-image/w=36", "logoAlt": "Northwind"}
    assert not {"components", "brandName", "personality", "confidence"} & set(b)
    assert out["screenshot"] == _SHOT


def test_a_refused_read_is_not_retried(monkeypatch):
    out, sent = _run(monkeypatch, {}, (None, 400, '{"error": "bad url"}'))
    assert out["ok"] is False and len(sent) == 1


@pytest.mark.parametrize("payload", [{}, {"prompt": "name"}])
def test_a_page_that_answers_404_is_a_failed_read(monkeypatch, payload):
    wall = ({"data": {"markdown": "Store unavailable", "json": {"name": "Shop"}, "branding": _BRANDING,
                      "screenshot": _SHOT, "metadata": {"statusCode": 404, "title": "Store unavailable"}}}, 200, None)
    out, _ = _run(monkeypatch, payload, wall)
    assert out == {"ok": False, "error": "the page answered HTTP 404",
                   "metadata": {"statusCode": 404, "title": "Store unavailable"}}


def test_a_page_with_no_text_still_returns_what_it_renders(monkeypatch):
    out, _ = _run(monkeypatch, {}, ({"data": {"markdown": "", "screenshot": _SHOT, "branding": _BRANDING}}, 200, None))
    assert out["ok"] and out["data"] == {"markdown": "", "truncated": False} and out["screenshot"] == _SHOT
    out, _ = _run(monkeypatch, {}, ({"data": {"markdown": ""}}, 200, None))
    assert out["ok"] is False
