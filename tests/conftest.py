import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class RespostaFalsa:
    """Imita requests.Response nos testes."""

    def __init__(self, status=200, json_data=None, content=b"", headers=None):
        self.status_code = status
        self._json = json_data
        self.content = content
        self.headers = headers or {}
        self.text = str(json_data)

    @property
    def ok(self):
        return 200 <= self.status_code < 400

    def json(self):
        if self._json is None:
            raise ValueError("sem JSON")
        return self._json

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError(f"HTTP {self.status_code}")
