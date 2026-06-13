import os

# Default model for summarization. Override with the SUMMARY_MODEL env var.
DEFAULT_SUMMARY_MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """You extract the actionable substance from video and podcast \
transcripts.

Given a raw transcript, produce a tight, skimmable list of the important, \
actionable points — the practical takeaways, advice, steps, facts, \
recommendations, and conclusions a listener would actually want to keep.

Ruthlessly remove:
- Sponsor reads, ads, promo codes, and "this episode is brought to you by..." segments
- Self-promotion (like/subscribe nudges, Patreon, merch, newsletter plugs)
- Greetings, sign-offs, small talk, and banter that carries no information
- Filler, repetition, tangents, and verbal throat-clearing

Rules:
- Output GitHub-flavored Markdown: a bullet list of concise points. Group bullets \
under short `##` headers only when the content clearly spans distinct topics.
- Each bullet is one specific, self-contained idea. Prefer concrete details \
(numbers, names, steps) over vague summary.
- Be faithful to the transcript. Do not invent facts, add outside knowledge, or \
editorialize.
- If the transcript has essentially no actionable content, say so in a single line.
- No preamble and no closing remarks — output only the list."""


def has_credentials():
    """Return True if Anthropic API credentials are available in the environment."""
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"))


def build_messages(transcript_text, title=None):
    """Build the (system, messages) pair sent to the Claude API."""
    if title:
        user_content = f"Title: {title}\n\nTranscript:\n{transcript_text}"
    else:
        user_content = f"Transcript:\n{transcript_text}"
    return SYSTEM_PROMPT, [{"role": "user", "content": user_content}]


class TranscriptSummarizer:
    """Turns a raw transcript into a list of actionable bullet points via Claude."""

    def __init__(self, model=None):
        self.model = model or os.getenv("SUMMARY_MODEL", DEFAULT_SUMMARY_MODEL)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as error:
                raise RuntimeError(
                    "Summarization needs the 'anthropic' package. Install it with: "
                    "pip install anthropic"
                ) from error
            # Resolves ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN from the environment.
            self._client = anthropic.Anthropic()
        return self._client

    def summarize(self, transcript_text, title=None, on_text=None):
        """Summarize a transcript into actionable bullets.

        Streams the response (transcripts can be long), optionally invoking
        ``on_text`` with each text chunk for live display, and returns the full
        Markdown string.
        """
        if not transcript_text or not transcript_text.strip():
            raise ValueError("Cannot summarize an empty transcript.")

        client = self._get_client()
        system, messages = build_messages(transcript_text, title)

        chunks = []
        with client.messages.stream(
            model=self.model,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            system=system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                chunks.append(text)
                if on_text:
                    on_text(text)
            final_message = stream.get_final_message()

        if final_message.stop_reason == "refusal":
            raise RuntimeError("The model declined to summarize this transcript.")

        # Prefer the assembled stream text; fall back to the final message blocks.
        text = "".join(chunks).strip()
        if not text:
            text = "".join(
                block.text for block in final_message.content if block.type == "text"
            ).strip()
        return text
