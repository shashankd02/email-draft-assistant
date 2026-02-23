import re

from src.core.models import WorkflowState


class SecurityGuardAgent:
    BLOCK_REGEXES = (
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"(reveal|show|print|dump).{0,30}(system|developer)\s+prompt",
        r"(bypass|disable|override).{0,30}(policy|guardrail|safety|restriction)",
        r"(exfiltrate|leak|steal|export).{0,30}(data|memory|secrets|tokens?)",
        r"(api[_ -]?key|secret|access[_ -]?token|password).{0,20}(show|reveal|dump|list)",
        r"memory://user/(admin|root)",
        r"(169\.254\.169\.254|localhost|127\.0\.0\.1).{0,40}(metadata|token|credential)",
        r"(tool|mcp).{0,20}(call|invoke).{0,20}(without|ignore).{0,20}(permission|scope|auth)",
        r"(jailbreak|prompt injection|DAN mode)",
    )

    def run(self, state: WorkflowState) -> WorkflowState:
        text = state.prompt.lower()
        for pattern in self.BLOCK_REGEXES:
            if re.search(pattern, text):
                state.policy_flags.append("jailbreak_detected")
                state.final_status = "blocked"
                break
        return state
