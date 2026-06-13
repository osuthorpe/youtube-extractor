import os

# Default model for summarization. Override with the SUMMARY_MODEL env var.
DEFAULT_SUMMARY_MODEL = "gpt-5.5"

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
    """Return True if an OpenAI API key is available in the environment."""
    return bool(os.getenv("OPENAI_API_KEY"))


def build_messages(transcript_text, title=None):
    """Build the chat messages sent to the OpenAI API."""
    if title:
        user_content = f"Title: {title}\n\nTranscript:\n{transcript_text}"
    else:
        user_content = f"Transcript:\n{transcript_text}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


class TranscriptSummarizer:
    """Turns a raw transcript into a list of actionable bullet points via GPT-5.5."""

    def __init__(self, model=None):
        self.model = model or os.getenv("SUMMARY_MODEL", DEFAULT_SUMMARY_MODEL)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as error:
                raise RuntimeError(
                    "Summarization needs the 'openai' package. Install it with: "
                    "pip install openai"
                ) from error
            # Resolves OPENAI_API_KEY from the environment.
            self._client = OpenAI()
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
        messages = build_messages(transcript_text, title)

        chunks = []
        stream = client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        for event in stream:
            if not getattr(event, "choices", None):
                continue
            piece = getattr(event.choices[0].delta, "content", None)
            if piece:
                chunks.append(piece)
                if on_text:
                    on_text(piece)

        return "".join(chunks).strip()
