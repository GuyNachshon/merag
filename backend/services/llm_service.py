import logging
from typing import Optional, Dict, Any, AsyncGenerator
import httpx
import json

from config import settings

logger = logging.getLogger(__name__)

class OllamaLLMService:
    """Service for interacting with Ollama-hosted LLMs"""
    
    def __init__(self):
        self.base_url = settings.ollama_host
        self.model_name = settings.llm_model
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout
        
    async def initialize(self):
        """Initialize the LLM service and pull the model if needed"""
        try:
            logger.info(f"Initializing LLM service with model: {self.model_name}")
            
            # Check if Ollama is running
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code != 200:
                raise RuntimeError(f"Ollama not accessible at {self.base_url}")
            
            # Check if our model is available
            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]
            
            if self.model_name not in model_names:
                logger.info(f"Model {self.model_name} not found locally, pulling...")
                await self._pull_model()
            else:
                logger.info(f"Model {self.model_name} is already available")
                
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise
    
    async def _pull_model(self):
        """Pull the model from Ollama registry"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model_name}
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully pulled model {self.model_name}")
            else:
                raise RuntimeError(f"Failed to pull model: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to pull model {self.model_name}: {e}")
            raise
    
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response from the LLM"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
                
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                raise RuntimeError(f"LLM generation failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise
    
    async def generate_response_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": temperature,
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
                
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens
            
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status_code != 200:
                    raise RuntimeError(f"LLM streaming failed: {await response.aread()}")
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"Failed to generate streaming response: {e}")
            raise
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

class HebrewLLMService:
    """Enhanced LLM service with Hebrew-specific optimizations"""
    
    def __init__(self):
        self.ollama_service = OllamaLLMService()
        self.hebrew_system_prompt = """
אתה עוזר AI מתקדם המתמחה בעיבוד טקסטים בעברית.
אתה עונה בעברית בצורה ברורה ומדויקת.
כאשר אתה מקבל מידע מבסיס הנתונים, אתה משתמש בו כדי לענות על השאלות בצורה מקיפה ומדויקת.
אם אין לך מספיק מידע לענות על השאלה, אמור זאת בבירור.
"""
    
    async def initialize(self):
        """Initialize the Hebrew LLM service"""
        await self.ollama_service.initialize()
        logger.info("Hebrew LLM service initialized")
    
    async def generate_hebrew_response(
        self,
        query: str,
        context: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """Generate a Hebrew response with optional context"""
        
        # Construct the prompt with context
        if context:
            prompt = f"""
בהתבסס על המידע הבא:
{context}

שאלה: {query}

תשובה:"""
        else:
            prompt = f"שאלה: {query}\n\nתשובה:"
        
        return await self.ollama_service.generate_response(
            prompt=prompt,
            system_prompt=self.hebrew_system_prompt,
            temperature=temperature
        )
    
    async def generate_hebrew_response_stream(
        self,
        query: str,
        context: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming Hebrew response with optional context"""
        
        # Construct the prompt with context
        if context:
            prompt = f"""
בהתבסס על המידע הבא:
{context}

שאלה: {query}

תשובה:"""
        else:
            prompt = f"שאלה: {query}\n\nתשובה:"
        
        async for token in self.ollama_service.generate_response_stream(
            prompt=prompt,
            system_prompt=self.hebrew_system_prompt,
            temperature=temperature
        ):
            yield token
    
    async def close(self):
        """Close the LLM service"""
        await self.ollama_service.close()

# Global LLM service instance
hebrew_llm_service = HebrewLLMService()