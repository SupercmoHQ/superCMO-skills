# Voices — picking one per model

`list_voice_models` returns the live catalog — each model's row lists its available voices. Always
prefer it over guessing a name. This guide is for choosing among them.

## How to choose

1. **Match the brief** — a calm explainer, an energetic ad, a character read each suit a different
   voice. Pick on tone first.
2. **Match the language** — for a non-English script, choose a voice the model lists for that
   language; `elevenlabs-v3` is the strongest multilingual option.
3. **Omit to default** — if no voice fits or the user has no preference, leave `voice` unset and the
   model uses its default.

## Per model

- `elevenlabs-v3` — the widest, most expressive voice set; best for multilingual and character work.
- `openai-tts` — a small set of clean, natural narration voices; low latency.
- `gemini-tts` — expressive voices plus style control; direct the tone in the request when you want a
  specific delivery.
