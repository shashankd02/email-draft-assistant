from src.core.models import WorkflowState
from src.services.memory_vector import get_vector_memory_service


class PersonalizationAgent:
    def run(self, state: WorkflowState) -> WorkflowState:
        state.context_sources.append("profile_memories")
        memory = get_vector_memory_service()
        hits = memory.get_profile_context(user_id=state.user_id, query=state.prompt, limit=2)
        if hits:
            context_lines = [f"- {h.text}" for h in hits]
            state.metadata["memory_context"] = "\\n".join(context_lines)
            state.context_sources.extend([f"chroma:{h.source}" for h in hits])
        return state
