from typing import Protocol, Any, Dict, List


class TextScreeningProvider(Protocol):
    def screen(self, text: str, language: str = "en") -> Dict[str, Any]:
        ...


class WellbeingProvider(Protocol):
    def recommend(self, usage_summary: Dict[str, Any]) -> Dict[str, Any]:
        ...


class MissionProvider(Protocol):
    def recommend(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        ...
