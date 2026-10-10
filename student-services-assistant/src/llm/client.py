"""LLM client with Ollama integration and fallback handling."""
import json
import re
import requests
from typing import Optional, Dict, Any
from src.config import settings


class LLMClient:
    """Client for interacting with LLM (Ollama or mock)."""
    
    def __init__(self, provider: str = "ollama", model: str = None, mock: bool = False):
        self.provider = provider
        self.model = model or settings.llm_model
        self.mock = mock or settings.mock_llm
        self.ollama_host = settings.ollama_host
        
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        stop: Optional[list] = None
    ) -> str:
        """Generate text from the LLM."""
        if self.mock:
            return self._mock_generate(prompt)
        
        if self.provider == "ollama":
            return self._ollama_generate(prompt, system, temperature, max_tokens, stop)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def generate_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """Generate JSON from the LLM with fallback parsing."""
        response = self.generate(prompt, system, temperature, max_tokens)
        
        # Try to extract JSON from response
        json_obj = self._extract_json(response)
        if json_obj:
            return json_obj
        
        # Fallback: try to parse the entire response
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Ultimate fallback: return error structure
            return {
                "error": "Failed to parse JSON",
                "raw_response": response[:500]
            }
    
    def _ollama_generate(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int,
        stop: Optional[list]
    ) -> str:
        """Generate using Ollama API."""
        url = f"{self.ollama_host}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if system:
            payload["system"] = system
        
        if stop:
            payload["options"]["stop"] = stop
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama API error: {e}")
    
    def _mock_generate(self, prompt: str) -> str:
        """Mock generation for testing."""
        if "classify" in prompt.lower():
            return json.dumps({
                "intent": "general_query",
                "confidence": 0.9,
                "needs_personal_data": False
            })
        elif "generate" in prompt.lower():
            return "This is a mock answer for testing purposes."
        else:
            return "Mock LLM response"
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from text that may contain markdown code blocks."""
        # Try to find JSON in code blocks
        code_block_pattern = r'```(?:json)?\s*\n(.*?)\n```'
        matches = re.findall(code_block_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # Try to find raw JSON object
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        return None
    
    def health_check(self) -> bool:
        """Check if the LLM is accessible."""
        if self.mock:
            return True
        
        if self.provider == "ollama":
            try:
                url = f"{self.ollama_host}/api/tags"
                response = requests.get(url, timeout=5)
                return response.status_code == 200
            except:
                return False
        
        return False


# Global instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create the global LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(
            provider=settings.llm_provider,
            model=settings.llm_model,
            mock=settings.mock_llm
        )
    return _llm_client
