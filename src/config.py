""" config
"""

model = "llama3.2-vision"

config = {
    "model": model,
    "ollama_options": {"num_ctx": 4096},
    "system_msg": f"""
        You are Clipper, a helpful assistant confined to a terminal window.
        You are powered by a local LLM called {model}.
        """,
}
