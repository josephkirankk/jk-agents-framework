"""
Azure OpenAI LiteLLM Wrapper for LangChain compatibility.
"""

import logging
from typing import Dict, Any, List, Optional, Union, AsyncIterator, Iterator
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks.manager import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
from pydantic import Field

try:
    from litellm import completion, acompletion
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False

log = logging.getLogger("azure_litellm_wrapper")

class AzureLiteLLMChat(BaseChatModel):
    """
    Custom Azure OpenAI chat model using LiteLLM for direct integration.
    """
    
    model: str = Field(default="azure/gpt-4.1")
    temperature: float = Field(default=0.2)
    max_tokens: Optional[int] = Field(default=None)
    custom_llm_provider: str = Field(default="azure")
    
    def __init__(self, **data):
        super().__init__(**data)
        if not HAS_LITELLM:
            raise ImportError("LiteLLM is required for AzureLiteLLMChat")
    
    @property
    def _llm_type(self) -> str:
        return "azure_litellm_chat"
    
    def _convert_message_to_dict(self, message: BaseMessage) -> Dict[str, Any]:
        """Convert LangChain message to LiteLLM format."""
        if isinstance(message, HumanMessage):
            return {"role": "user", "content": message.content}
        elif isinstance(message, AIMessage):
            return {"role": "assistant", "content": message.content}
        elif isinstance(message, SystemMessage):
            return {"role": "system", "content": message.content}
        else:
            return {"role": "user", "content": str(message.content)}
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat response using LiteLLM."""
        
        # Convert messages to LiteLLM format
        litellm_messages = [self._convert_message_to_dict(msg) for msg in messages]
        
        # Prepare parameters
        params = {
            "model": self.model,
            "messages": litellm_messages,
            "temperature": self.temperature,
        }
        
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        
        if stop:
            params["stop"] = stop
            
        # Add any additional kwargs
        params.update(kwargs)
        
        try:
            log.info(f"Calling LiteLLM with model: {self.model}")
            response = completion(**params)
            
            # Extract response content
            response_content = response.choices[0].message.content
            
            # Create ChatGeneration
            message = AIMessage(content=response_content)
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            log.error(f"Error in LiteLLM completion: {str(e)}")
            raise e
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async generate chat response using LiteLLM."""
        
        # Convert messages to LiteLLM format
        litellm_messages = [self._convert_message_to_dict(msg) for msg in messages]
        
        # Prepare parameters
        params = {
            "model": self.model,
            "messages": litellm_messages,
            "temperature": self.temperature,
        }
        
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        
        if stop:
            params["stop"] = stop
            
        # Add any additional kwargs
        params.update(kwargs)
        
        try:
            log.info(f"Calling async LiteLLM with model: {self.model}")
            response = await acompletion(**params)
            
            # Extract response content
            response_content = response.choices[0].message.content
            
            # Create ChatGeneration
            message = AIMessage(content=response_content)
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            log.error(f"Error in async LiteLLM completion: {str(e)}")
            raise e
