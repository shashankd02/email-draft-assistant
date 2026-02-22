import re

from src.core.models import WorkflowState


class InputParsingAgent:
    EMAIL_ACTION_PATTERNS = (
        r"\bdraft\b",
        r"\bcompose\b",
        r"\bwrite\b",
        r"\bsend\b",
        r"\bemail\b",
        r"\bmail\b",
        r"\bfollow[- ]?up\b",
        r"\breply\b",
        r"\brespond\b",
        r"\b(let|inform|notify|tell)\b.{0,40}\b(team|client|manager|everyone|them|him|her)\b",
        r"\bi need to\b.{0,40}\b(update|inform|notify|tell|follow[- ]?up|apologize|respond)\b",
        r"\b(correo|mail|email)\b",
        r"\b(redacta|escribe|envia|enviar|responde|respuesta|seguimiento)\b",
        r"\b(necesito|quiero)\b.{0,40}\b(enviar|redactar|escribir)\b",
        r"(ईमेल|मेल|email)\b",
        r"(ड्राफ्ट|लिखो|लिखें|लिखना|भेजो|भेजें|भेजना|उत्तर|फॉलोअप)",
    )
    NON_EMAIL_QUERY_PATTERNS = (
        r"\bweather\b",
        r"\btemperature\b",
        r"\bforecast\b",
        r"\bnews\b",
        r"\bstock\b",
        r"\bprice\b",
        r"\bscore\b",
        r"\btime\b",
        r"\bdate\b",
    )
    SMALL_TALK_PATTERNS = (
        r"^\s*how are you\??\s*$",
        r"^\s*what'?s up\??\s*$",
        r"^\s*hello\??\s*$",
        r"^\s*hi\??\s*$",
        r"^\s*hey\??\s*$",
    )
    RECIPIENT_PATTERNS = (
        r"\b(to|for)\s+(my\s+)?(manager|team|client|customer|hr|recruiter|professor|lead|everyone)\b",
        r"\b(my\s+)?(manager|team|client|customer|hr|recruiter|professor|lead)\b",
        r"\b(a|para|mi)\s+(gerente|equipo|cliente|todos|profesor|lider)\b",
        r"\b(mi)\s+(gerente|equipo|cliente|profesor|lider)\b",
        r"(मेरे|मेरी)\s+(मैनेजर|टीम|क्लाइंट|ग्राहक|लीड)",
        r"(को|के लिए)\s+(मैनेजर|टीम|क्लाइंट|ग्राहक|लीड)",
        r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b",
    )
    CONTEXT_PATTERNS = (
        r"\babout\b",
        r"\bregarding\b",
        r"\bthat\b",
        r"\bbecause\b",
        r"\bon\b",
        r"\brequest\b",
        r"\bupdate\b",
        r"\bfollow[- ]?up\b",
        r"\bapolog\w*\b",
        r"\bsobre\b",
        r"\bporque\b",
        r"\bsolicita\w*\b",
        r"\bactualiza\w*\b",
        r"\bseguimiento\b",
        r"(बारे|क्योंकि|अनुरोध|अपडेट|माफी|क्षमा)",
    )

    def _extract_email_target(self, prompt: str) -> str | None:
        text = prompt.lower()
        patterns = (
            r"(?:email|mail|correo|write|draft|send|redacta|escribe|envia|ईमेल|मेल|लिखो|भेजो)\s+(?:to|for|a|para|को|के लिए)\s+([^\n,.!?]+)",
            r"(?:tell|inform|notify|update|informa|notificar|avisar|सूचित|बताओ)\s+([^\n,.!?]+)",
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                target = match.group(1).strip(" .,-")
                if target:
                    return target
        return None

    def _looks_like_email_task(self, prompt: str) -> bool:
        text = prompt.lower()
        has_email_signal = any(re.search(pattern, text) for pattern in self.EMAIL_ACTION_PATTERNS)
        has_non_email_signal = any(re.search(pattern, text) for pattern in self.NON_EMAIL_QUERY_PATTERNS)
        small_talk = any(re.search(pattern, text) for pattern in self.SMALL_TALK_PATTERNS)

        if small_talk:
            return False
        if has_non_email_signal and not has_email_signal:
            return False
        if not has_email_signal and text.endswith("?"):
            return False
        return True

    def _has_enough_context(self, prompt: str, has_email_signal: bool) -> bool:
        text = prompt.lower().strip()
        words = re.findall(r"[^\W\d_]+", text, flags=re.UNICODE)
        if len(words) < 5:
            return False
        if not has_email_signal:
            return False
        has_recipient = any(re.search(pattern, text) for pattern in self.RECIPIENT_PATTERNS)
        has_context = any(re.search(pattern, text) for pattern in self.CONTEXT_PATTERNS)
        # Require at least recipient or context detail to avoid vague/empty prompts.
        return has_recipient or has_context

    def run(self, state: WorkflowState) -> WorkflowState:
        state.prompt = state.prompt.strip()
        if not state.intent:
            state.intent = "informational"
        if not state.tone:
            state.tone = "professional"
        is_email_task = self._looks_like_email_task(state.prompt)
        has_email_signal = any(re.search(pattern, state.prompt.lower()) for pattern in self.EMAIL_ACTION_PATTERNS)
        has_enough_context = self._has_enough_context(state.prompt, has_email_signal)
        state.metadata["is_email_task"] = is_email_task
        state.metadata["has_enough_context"] = has_enough_context
        email_target = self._extract_email_target(state.prompt)
        if email_target:
            state.metadata["email_target"] = email_target
        if not is_email_task:
            state.policy_flags.append("not_email_task")
            state.final_status = "blocked"
            return state
        if not has_enough_context:
            state.policy_flags.append("insufficient_prompt_context")
            state.final_status = "blocked"
        return state
