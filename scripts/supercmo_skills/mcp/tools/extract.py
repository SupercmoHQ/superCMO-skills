"""URL extraction tool — thin MCP binding over supercmo_skills.

Structured extraction from a web/product page (Firecrawl under the hood). All routing/vendor
logic lives in supercmo_skills; this only declares the schema and forwards the call.
"""

from .. import registry
import supercmo_skills


URL_EXTRACTION = {
    "name": "url_extraction",
    "description": (
        "Extract structured data from a web page — a product listing (Amazon, Shopify, AliExpress, "
        "any store) or any URL — guided by a prompt and/or a JSON schema. Returns the requested "
        "fields (e.g. name, brand, price, description, specs) and any gallery image URLs as a compact "
        "JSON object — not the page's full text — plus the colours, fonts and logo the page renders "
        "(branding), a screenshot URL of the page as a visitor first sees it, and page metadata. Omit "
        "both prompt and schema to get the page's own text (markdown) instead, which costs less. "
        "Use when you need specific data, image URLs or the text of a page. Set dry_run=true to "
        "preview the exact request without spending."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The page URL to extract from (an http(s) URL).",
            },
            "prompt": {
                "type": "string",
                "description": "What to extract, in plain language — e.g. 'product name, brand, price, "
                "currency, variant, full description, feature bullets, specs, and all product-gallery "
                "image URLs (front/side/back/close-up/packaging); exclude review photos, related "
                "products, banners, logos'.",
            },
            "schema": {
                "type": "object",
                "description": "Optional JSON Schema describing the exact shape to return. Use for a "
                "strict, typed result; omit to let the prompt guide the extraction.",
            },
            "dry_run": {
                "type": "boolean",
                "description": "If true, return the request that would be sent (key masked), make no API call.",
                "default": False,
            },
        },
        "required": ["url"],
        "additionalProperties": False,
    },
}


def url_extraction(args):
    return supercmo_skills.url_extraction(
        url=args.get("url"),
        prompt=args.get("prompt"),
        schema=args.get("schema"),
        dry_run=bool(args.get("dry_run", False)),
    )


registry.register(URL_EXTRACTION, url_extraction)
