"""Builds and drives OpenHarness's QueryEngine, forwarding its StreamEvents.

Wired up in Step 4–5. Intended shape:

    from openharness...  import QueryEngine   # exact bootstrap TBD in Step 4

    def build_query_engine(cwd): ...          # Ollama-backed, default tools/prompt
    async def run(job, questions): ...        # yields StreamEvents for SSE
"""
