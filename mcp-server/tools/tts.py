"""Text-to-speech tools — thin MCP binding over supercmo_skills.

The tool name (`text_to_speech`) and args match the OSS app's custom tool and Hermes's
native tool name, so one SKILL.md drives both runtimes. All catalog + routing + vendor
logic lives in supercmo_skills.
"""
import os
import sys

# supercmo_skills lives in the plugin's scripts/ dir (repo_root/scripts).
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PLUGIN_ROOT, "scripts"))

import registry  # noqa: E402
import supercmo_skills  # noqa: E402
from supercmo_skills import catalog  # noqa: E402

DEFAULT_MODEL = catalog.default_model("tts")


TEXT_TO_SPEECH = {
    "name": "text_to_speech",
    "description": (
        "Generate spoken audio from text. Returns a hosted audio URL plus metadata (model, voice), "
        "and saves the audio to a local file (absolute path in the 'path' field). Use when the user wants a voiceover, "
        "narration, an ad read, or any text spoken aloud. Pass a 'voice' to pick a specific speaker "
        "(call list_voice_models to see each model's voices) and 'speed' to adjust pacing. Set "
        "dry_run=true to preview the exact request and cost without generating (no credits spent)."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The text to speak. Write it as you want it read aloud, including punctuation for pacing.",
            },
            "model": {
                "type": "string",
                "default": DEFAULT_MODEL,
                "description": f"TTS model name. Omit to use the default ('{DEFAULT_MODEL}'). "
                "Pass a specific model when one is called for; if you need to choose and don't "
                "already have one in mind, call list_voice_models to browse the options.",
            },
            "voice": {
                "type": "string",
                "description": "Optional voice/speaker name. Call list_voice_models to see the voices each model offers.",
            },
            "speed": {
                "type": "number",
                "description": "Optional speaking-rate multiplier (1.0 = normal).",
            },
            "dry_run": {
                "type": "boolean",
                "description": "If true, return the request that would be sent (key masked), make no API call.",
                "default": False,
            },
        },
        "required": ["text"],
        "additionalProperties": False,
    },
}


def text_to_speech(args):
    return supercmo_skills.text_to_speech(
        text=args.get("text"),
        model=args.get("model"),
        voice=args.get("voice"),
        speed=float(args["speed"]) if args.get("speed") is not None else None,
        dry_run=bool(args.get("dry_run", False)),
    )


registry.register(TEXT_TO_SPEECH, text_to_speech)


LIST_VOICE_MODELS = {
    "name": "list_voice_models",
    "description": (
        "List the available text-to-speech models with their strengths, price, and the voices each "
        "offers. Use only when you need to choose a model or voice for text_to_speech and don't "
        "already have one in mind (e.g. an open-ended request). Pass an optional 'query' to filter "
        "by use-case keyword (e.g. 'natural', 'fast', 'expressive')."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Optional keyword to filter models by use-case (matches the name, display name, and strengths).",
            },
        },
        "additionalProperties": False,
    },
}


def list_voice_models(args):
    return {"ok": True, "default": catalog.default_model("tts"),
            "models": catalog.list_models("tts", args.get("query"))}


registry.register(LIST_VOICE_MODELS, list_voice_models)
