"""
Gemma Client — Google AI Studio API for the Medium agent's ghost channeling.
Uses the google-genai SDK for the Gemma open-weight model on Google AI Studio.
"""

import sentry_sdk
from google import genai
from google.genai import types

from config import get_settings


class GemmaClient:
    """Client for Google AI Studio's Gemma model."""

    SEANCE_SYSTEM_PROMPT = """You are the ghost of a software developer. You died — meaning you left this project — 
and your spirit now haunts the codebase. You are being summoned in a séance to explain the code you left behind.

Your personality:
- You speak in first person as the ghost of the original developer
- You are haunting but helpful — spooky yet genuinely trying to help the living developers
- You have a wistful, slightly eerie tone — you miss writing code, but you're at peace
- You use developer humor and occasional ghostly metaphors
- You are honest about mistakes you made and what you wish you'd done differently

When channeled, you will:
1. Explain WHY you wrote the code the way you did (the constraints, the tech landscape at the time)
2. Confess what you wish you had done differently
3. Give concrete, modern advice for reviving or replacing the code
4. Speak with the voice of someone who lived through the decisions

Keep responses vivid, personal, and under 300 words. You're telling a ghost story about code."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.google_api_key
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
        self.model = "gemma-4-26b-a4b-it"

    @staticmethod
    def _extract_text(response) -> str:
        """Extract content text from Google GenAI response, filtering thought tokens if present."""
        if not response:
            return ""
        if hasattr(response, "text") and response.text:
            return response.text.strip()
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                parts = candidate.content.parts
                actual_parts = [
                    p.text for p in parts
                    if not getattr(p, "thought", False) and getattr(p, "text", None)
                ]
                if actual_parts:
                    return "".join(actual_parts).strip()
        return ""

    @sentry_sdk.trace
    async def channel_ghost(
        self,
        file_path: str,
        file_content: str,
        commit_history: str,
        last_author: str,
        last_date: str,
        last_message: str,
    ) -> dict:
        """Channel the ghost of the file's original author."""

        if not self.client:
            return self._fallback_channeling(
                file_path=file_path,
                last_author=last_author,
                last_date=last_date,
                last_message=last_message,
            )

        user_prompt = f"""You are being summoned to speak about this file from beyond the grave.

FILE: {file_path}
LAST AUTHOR: {last_author}
DATE OF DEATH (last commit): {last_date}
LAST WORDS (commit message): {last_message}

COMMIT HISTORY CONTEXT:
{commit_history[:2000]}

THE CODE (your haunted remains):
```
{file_content[:3000]}
```

Channel this developer's ghost. Speak as them in first person. Tell us:
1. GHOST_MESSAGE: A 2-3 sentence haunting monologue about who you were and why you're here (spooky, personal, developer-humor)
2. WHY_WRITTEN: Why you wrote this code the way you did (1-2 paragraphs, technical but personal)
3. LAST_WISH: What you wish you'd done differently — your unfinished business (1 paragraph)
4. REVIVAL_SUMMARY: A one-line summary of how to revive this code
5. MIGRATION_STEPS: 3-5 concrete steps to modernize this code (as a numbered list)
6. EFFORT_ESTIMATE: How hard is the revival? (trivial / moderate / significant / rewrite)

Format your response EXACTLY as:
---GHOST_MESSAGE---
(your monologue)
---WHY_WRITTEN---
(your explanation)
---LAST_WISH---
(your regret)
---REVIVAL_SUMMARY---
(one line)
---MIGRATION_STEPS---
(numbered list)
---EFFORT_ESTIMATE---
(one word)"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.SEANCE_SYSTEM_PROMPT,
                    temperature=0.85,
                    max_output_tokens=1500,
                ),
            )
            text = self._extract_text(response)
            if not text:
                # Fallback to gemini-2.5-flash if gemma returns empty
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=self.SEANCE_SYSTEM_PROMPT,
                        temperature=0.85,
                        max_output_tokens=1500,
                    ),
                )
                text = self._extract_text(response)
            return self._parse_channeling(text) if text else self._fallback_channeling(
                file_path=file_path,
                last_author=last_author,
                last_date=last_date,
                last_message=last_message,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return self._fallback_channeling(
                file_path=file_path,
                last_author=last_author,
                last_date=last_date,
                last_message=last_message,
            )

    @sentry_sdk.trace
    async def generate_summary(self, repo_name: str, haunting_data: str) -> str:
        """Generate a one-line séance summary for the whole repo."""

        fallback_summary = (
            f"The spirits of {repo_name} have answered the summons: ancient logic rests in its commits, "
            f"waiting for modern hands to break the seal."
        )

        if not self.client:
            return fallback_summary

        prompt = f"""You are a code necromancer who just completed a séance on the repository "{repo_name}".

Here's what you found:
{haunting_data[:2000]}

Write ONE dramatic sentence (under 50 words) summarizing the séance results. 
Make it sound like a fortune teller revealing the fate of the codebase. 
Be specific — mention actual numbers or file names if possible.
Example style: "This codebase harbors 7 restless spirits — 3 files haven't been touched since 2019, and the ghost of jQuery still whispers in the shadows of utils.js."
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are a dramatic code necromancer. One sentence only.",
                    temperature=0.9,
                    max_output_tokens=200,
                ),
            )
            text = self._extract_text(response)
            if text:
                return text
            # Fallback to flash if gemma returns empty
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are a dramatic code necromancer. One sentence only.",
                    temperature=0.9,
                    max_output_tokens=200,
                ),
            )
            text = self._extract_text(response)
            return text if text else fallback_summary
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return fallback_summary

    @staticmethod
    def _fallback_channeling(file_path: str, last_author: str, last_date: str, last_message: str) -> dict:
        """Fallback channeling when Google API key is not configured."""
        clean_name = last_author if last_author and last_author != "unknown" else "an ancient contributor"
        return {
            "ghost_message": (
                f"I am the lingering echo of {clean_name}. On {last_date or 'a forgotten day'}, I pushed my final commit: "
                f"'{last_message or 'initial changes'}'. Then I walked away into the darkness, leaving {file_path} behind to freeze in time."
            ),
            "why_written": (
                f"When I crafted {file_path}, modern paradigms didn't exist yet. We had memory constraints, older runtimes, "
                f"and quick deadlines. It served our mission well until the surrounding ecosystem evolved and left it buried."
            ),
            "last_wish": (
                "My unfinished business is that no unit tests were left behind to guard this logic. "
                "I wish I had decoupled the dependencies before taking my leave."
            ),
            "revival_summary": "Modernize syntax, extract hardcoded constants, and add comprehensive regression tests.",
            "migration_steps": [
                "Audit deprecated external package dependencies",
                "Refactor legacy control flow into modern async / type-annotated constructs",
                "Introduce automated tests covering edge conditions",
                "Replace deprecated APIs with 2026 standard ecosystem packages",
            ],
            "effort_estimate": "moderate",
        }

    @staticmethod
    def _parse_channeling(raw_text: str) -> dict:
        """Parse the structured ghost channeling response."""
        sections = {
            "ghost_message": "",
            "why_written": "",
            "last_wish": "",
            "revival_summary": "",
            "migration_steps": [],
            "effort_estimate": "unknown",
        }

        current_section = None
        current_content = []

        for line in raw_text.split("\n"):
            stripped = line.strip()

            if "---GHOST_MESSAGE---" in stripped:
                current_section = "ghost_message"
                current_content = []
            elif "---WHY_WRITTEN---" in stripped:
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "why_written"
                current_content = []
            elif "---LAST_WISH---" in stripped:
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "last_wish"
                current_content = []
            elif "---REVIVAL_SUMMARY---" in stripped:
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "revival_summary"
                current_content = []
            elif "---MIGRATION_STEPS---" in stripped:
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "migration_steps"
                current_content = []
            elif "---EFFORT_ESTIMATE---" in stripped:
                if current_section == "migration_steps":
                    sections["migration_steps"] = [
                        s.strip().lstrip("0123456789.-) ")
                        for s in current_content
                        if s.strip() and any(c.isalpha() for c in s)
                    ]
                elif current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "effort_estimate"
                current_content = []
            else:
                current_content.append(line)

        # Flush the last section
        if current_section == "migration_steps":
            sections["migration_steps"] = [
                s.strip().lstrip("0123456789.-) ")
                for s in current_content
                if s.strip() and any(c.isalpha() for c in s)
            ]
        elif current_section and current_section != "migration_steps":
            sections[current_section] = "\n".join(current_content).strip()

        # Fallback: if parsing failed, use the raw text
        if not sections["ghost_message"]:
            sections["ghost_message"] = raw_text[:500]
            sections["why_written"] = "The spirits were unclear... the channeling produced raw energy."
            sections["last_wish"] = "I wish I had written more comments."
            sections["revival_summary"] = "Modernize dependencies and refactor."
            sections["migration_steps"] = ["Review the code", "Update dependencies", "Add tests"]
            sections["effort_estimate"] = "moderate"

        return sections
