class DemoProvider:
    """Explicit offline test provider. Never use for a real translation run."""
    version = "demo"

    def translate(self, text: str, source: str, target: str) -> str:
        return f"[{target}] {text}"
