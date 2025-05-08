from mcp import MCPClient

class JarvisMCP:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.client = MCPClient(base_url)
        self.session = self.client.create_session()

    def push_context(self, context: dict):
        self.client.set_context(self.session, context)

    def get_context(self) -> dict:
        return self.client.get_context(self.session)

    def invoke_tool(self, tool: str, args: dict):
        return self.client.invoke(self.session, tool, args)

    def save_state(self, key: str, value: dict):
        self.client.set_state(self.session, key, value)

    def load_state(self, key: str) -> dict:
        return self.client.get_state(self.session, key) 