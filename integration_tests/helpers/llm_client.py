"""
Live LLM client for integration tests.
Uses real LLM APIs - NO MOCKING.
"""

import os
import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Structure for LLM response."""
    content: str
    model: str
    provider: str
    duration: float
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LiveLLMClient:
    """
    Live LLM client for integration tests.
    Supports multiple providers with real API calls.
    """
    
    def __init__(self, provider: str = "azure_openai", model: Optional[str] = None,
                 temperature: float = 0, top_p: float = 1.0, max_tokens: int = 2000):
        """
        Initialize live LLM client.
        
        Args:
            provider: Provider name (azure_openai, google, anthropic, openai)
            model: Model name (provider-specific format)
            temperature: Temperature for generation (0 for deterministic)
            top_p: Top-p sampling parameter
            max_tokens: Maximum tokens to generate
        """
        self.provider = provider
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        
        # Initialize provider-specific client
        if provider == "azure_openai":
            self.model = model or f"azure_openai:{os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4.1')}"
            self._init_azure_client()
        elif provider == "google":
            self.model = model or "google:gemini-1.5-flash"
            self._init_google_client()
        elif provider == "anthropic":
            self.model = model or "anthropic:claude-3-haiku-20240307"
            self._init_anthropic_client()
        elif provider == "openai":
            self.model = model or "openai:gpt-4o-mini"
            self._init_openai_client()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _init_azure_client(self):
        """Initialize Azure OpenAI client."""
        try:
            from langchain_openai import AzureChatOpenAI
            
            # Extract deployment name from model string
            deployment = self.model.replace("azure_openai:", "")
            
            self.client = AzureChatOpenAI(
                azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", deployment),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Azure OpenAI client: {e}")
    
    def _init_google_client(self):
        """Initialize Google Gemini client."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            self.client = ChatGoogleGenerativeAI(
                model=self.model.replace("google:", ""),
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Google Gemini client: {e}")
    
    def _init_anthropic_client(self):
        """Initialize Anthropic Claude client."""
        try:
            from langchain_anthropic import ChatAnthropic
            
            self.client = ChatAnthropic(
                model=self.model.replace("anthropic:", ""),
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Anthropic client: {e}")
    
    def _init_openai_client(self):
        """Initialize OpenAI client."""
        try:
            from langchain_openai import ChatOpenAI
            
            self.client = ChatOpenAI(
                model=self.model.replace("openai:", ""),
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize OpenAI client: {e}")
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None,
                      retry_count: int = 3) -> LLMResponse:
        """
        Generate response from LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            retry_count: Number of retries on failure
            
        Returns:
            LLMResponse with generated content
        """
        from langchain_core.messages import SystemMessage, HumanMessage
        
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))
        
        last_error = None
        for attempt in range(retry_count):
            try:
                start_time = time.time()
                
                # Invoke client
                response = await self.client.ainvoke(messages)
                
                duration = time.time() - start_time
                
                return LLMResponse(
                    content=response.content,
                    model=self.model,
                    provider=self.provider,
                    duration=duration,
                    tokens_used=getattr(response, 'usage', {}).get('total_tokens') if hasattr(response, 'usage') else None,
                    finish_reason=getattr(response, 'finish_reason', None),
                    metadata={
                        "attempt": attempt + 1,
                        "messages_count": len(messages)
                    }
                )
            
            except Exception as e:
                last_error = e
                if attempt < retry_count - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise RuntimeError(f"LLM generation failed after {retry_count} attempts: {e}") from e
    
    async def generate_json(self, prompt: str, system_prompt: Optional[str] = None,
                           retry_count: int = 3) -> Dict[str, Any]:
        """
        Generate JSON response from LLM.
        
        Args:
            prompt: User prompt (should request JSON output)
            system_prompt: Optional system prompt
            retry_count: Number of retries on failure
            
        Returns:
            Parsed JSON dict
        """
        import json
        import re
        
        if system_prompt is None:
            system_prompt = "You are a helpful assistant that responds in valid JSON format."
        else:
            system_prompt += "\n\nIMPORTANT: Respond only with valid JSON."
        
        response = await self.generate(prompt, system_prompt, retry_count)
        
        # Try to extract JSON from response
        content = response.content.strip()
        
        # Try direct parsing first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to extract any JSON object
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Failed to extract valid JSON from LLM response: {content[:200]}")
    
    async def batch_generate(self, prompts: List[str], system_prompt: Optional[str] = None,
                            max_concurrent: int = 3) -> List[LLMResponse]:
        """
        Generate responses for multiple prompts concurrently.
        
        Args:
            prompts: List of user prompts
            system_prompt: Optional system prompt for all
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of LLMResponse objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(prompt):
            async with semaphore:
                return await self.generate(prompt, system_prompt)
        
        tasks = [generate_with_semaphore(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)
    
    def validate_response(self, response: LLMResponse, 
                         expected_keywords: Optional[List[str]] = None,
                         min_length: Optional[int] = None,
                         max_length: Optional[int] = None) -> bool:
        """
        Validate LLM response meets criteria.
        
        Args:
            response: LLM response to validate
            expected_keywords: Optional list of keywords that should appear
            min_length: Minimum response length
            max_length: Maximum response length
            
        Returns:
            True if valid, False otherwise
        """
        content = response.content.lower()
        
        # Check keywords
        if expected_keywords:
            for keyword in expected_keywords:
                if keyword.lower() not in content:
                    return False
        
        # Check length
        if min_length and len(response.content) < min_length:
            return False
        
        if max_length and len(response.content) > max_length:
            return False
        
        return True
