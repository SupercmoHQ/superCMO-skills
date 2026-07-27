"""Shared media-tool schemas — one definition per tool, wrapped per runtime.

The MCP server puts the body under `inputSchema`; the Hermes plugin puts the identical body
under `parameters`.
"""
from . import catalog


def object_schema(properties, required):
    """Wrap shared properties as a JSON-Schema object body — the runtime supplies the outer key
    (`inputSchema` for MCP, `parameters` for Hermes)."""
    return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}


# ---------------------------------------------------------------------------- image_generate
IMAGE_GENERATE_DESCRIPTION = (
    "For a user's image request, load the `generating-images` skill BEFORE calling this — it picks "
    "the right model and builds the prompt (this tool does neither, and calling it raw gives weak, "
    "inconsistent results). "
    "Generate one or many still images from text prompts, optionally guided by reference "
    "images (a product photo, a character, a style or composition to follow). Pass `requests`: "
    "ONE object per image (wrap even a single image — `{ requests: [ { prompt } ] }`). Generate a "
    "batch of DIFFERENT images in a SINGLE call by adding more request objects (up to 10), each "
    "with its own prompt/model/aspect_ratio/resolution/reference_images; a single approval covers "
    "the whole batch. Each result carries a hosted image URL plus a local file `path`, or a "
    "structured error with a hint. Use for graphics, mockups, product/marketing visuals, logos, "
    "concept art, or to render a product or character from a supplied reference. Set dry_run=true "
    "to preview the exact requests and cost without generating (no credits spent)."
)

IMAGE_GENERATE_PROPERTIES = {
    "requests": {
        "type": "array",
        "minItems": 1,
        "maxItems": 10,
        "description": "One object per image (wrap even a single image); add more objects to "
        "batch different images in one call (up to 10).",
        "items": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The image description. Be specific about subject, style, composition, and lighting.",
                },
                "model": {
                    "type": "string",
                    "default": catalog.DEFAULT_MODEL,
                    "description": f"Image model name. Omit to use the default ('{catalog.DEFAULT_MODEL}'). "
                    "If you need to choose and don't already have one in mind, call list_image_models.",
                },
                "aspect_ratio": {
                    "type": "string",
                    "enum": catalog.IMAGE_ASPECTS,
                    "default": catalog.IMAGE_DEFAULT_ASPECT,
                    "description": "Aspect ratio of the output image.",
                },
                "resolution": {
                    "type": "string",
                    "enum": catalog.IMAGE_RESOLUTIONS,
                    "default": catalog.IMAGE_DEFAULT_RESOLUTION,
                    "description": "Output resolution tier. Applied by models that support it; ignored by models that don't.",
                },
                "reference_images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 10,
                    "description": "Optional reference image(s) — each a local file path or an "
                    "image URL. Use for product/character-driven generation or to follow a "
                    "supplied style or composition; if a model rejects the count, the error "
                    "states its limit. Omit for pure text-to-image.",
                },
            },
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
    "dry_run": {
        "type": "boolean",
        "description": "If true, return the requests that would be sent (keys masked), make no API call.",
        "default": False,
    },
}
IMAGE_GENERATE_REQUIRED = ["requests"]


# ---------------------------------------------------------------------------- list_image_models
LIST_IMAGE_MODELS_DESCRIPTION = (
    "List the available image-generation models (with strengths and price), plus the valid "
    "aspect ratios and resolution tiers that image_generate accepts. Use when you need to "
    "choose a model and don't already have one in mind (e.g. an open-ended request), or to "
    "check the valid aspect_ratio / resolution values — most of the time the model is the "
    "default or already specified. Pass an optional 'query' to filter models by use-case "
    "keyword (e.g. 'text', 'photorealistic', 'fast')."
)

LIST_IMAGE_MODELS_PROPERTIES = {
    "query": {
        "type": "string",
        "description": "Optional keyword to filter models by use-case (matches the name, display name, and strengths).",
    },
}
LIST_IMAGE_MODELS_REQUIRED = []
