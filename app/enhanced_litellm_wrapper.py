"""
Enhanced LiteLLM Wrapper for JK-Agents Framework
Provides seamless LiteLLM integration with multimodal support, async operations,
and LangChain compatibility based on test_litellm_multimodal.py insights.
"""

import logging
import os
import asyncio
import base64
import mimetypes
from typing import Dict, Any, List, Optional, Union, AsyncIterator, Iterator
from pathlib import Path
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks.manager import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
from pydantic import Field
from typing import Sequence

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import litellm
    from litellm import completion, acompletion
    # Support both newer and older versions of LiteLLM
    try:
        from litellm.utils import supports_vision, supports_file_inputs
    except ImportError:
        # Fallback for older versions
        supports_vision = lambda model: "gpt-4" in model or "claude" in model or "gemini" in model
        supports_file_inputs = lambda model: "gpt-4" in model or "claude-3" in model
    HAS_LITELLM = True
    print(f"LiteLLM successfully imported from {litellm.__file__}")
except ImportError as e:
    HAS_LITELLM = False
    print(f"Failed to import LiteLLM: {str(e)}")

# Try to import Google Gemini integration
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    HAS_GOOGLE_GENAI = True
    print("Google Generative AI integration available")
except ImportError:
    HAS_GOOGLE_GENAI = False
    print("Google Generative AI integration not available")

log = logging.getLogger("enhanced_litellm_wrapper")

class EnhancedLiteLLMChat(BaseChatModel):
    """Enhanced LiteLLM chat model with tool binding support."""
    """
    Enhanced LiteLLM chat model with multimodal support for the JK-Agents Framework.
    
    Supports:
    - All LiteLLM providers (OpenAI, Anthropic, Google Gemini, Azure OpenAI, etc.)
    - Multimodal content (images, files)
    - Async and sync operations
    - LangChain compatibility
    - Framework integration patterns
    """
    
    model: str = Field(default="openai/gpt-4o")
    temperature: float = Field(default=0.2)
    max_tokens: Optional[int] = Field(default=None)
    timeout: int = Field(default=60)
    
    def __init__(self, **data):
        super().__init__(**data)
        
        # Check if LiteLLM is available
        try:
            import litellm
            from litellm import completion
            self._has_litellm = True
            log.info(f"LiteLLM found in {litellm.__file__}")
        except ImportError as e:
            self._has_litellm = False
            error_msg = f"LiteLLM is required for EnhancedLiteLLMChat. Install with: pip install litellm. Error: {e}"
            log.error(error_msg)
            raise ImportError(error_msg)
        
        # Set up environment variables for the model
        self._setup_environment()
        
        # Check model capabilities
        self._capabilities = self._check_model_capabilities()
        log.info(f"Initialized {self.model} with capabilities: {self._capabilities}")
    
    def _setup_environment(self):
        """Set up environment variables based on model provider."""
        provider = self.model.split('/')[0] if '/' in self.model else 'openai'
        
        if provider == 'google' or provider == 'gemini':
            # Set GOOGLE_API_KEY if not already set
            if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
                os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
            # Store provider for later use in bind_tools
            self._provider = 'google'
        
        elif provider == 'azure':
            # Ensure Azure OpenAI environment variables are set
            required_vars = ["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"]
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                # Try alternative names
                if not os.getenv("AZURE_API_KEY") and os.getenv("AZURE_OPENAI_API_KEY"):
                    os.environ["AZURE_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
                if not os.getenv("AZURE_API_BASE") and os.getenv("AZURE_OPENAI_ENDPOINT"):
                    os.environ["AZURE_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT")
            self._provider = 'azure'
        
        else:
            self._provider = provider
    
    def _check_model_capabilities(self) -> Dict[str, bool]:
        """Check model capabilities for multimodal support."""
        capabilities = {
            "supports_vision": False,
            "supports_files": False
        }
        
        try:
            capabilities["supports_vision"] = supports_vision(self.model)
            capabilities["supports_files"] = supports_file_inputs(self.model)
        except Exception as e:
            log.warning(f"Could not check capabilities for {self.model}: {e}")
        
        return capabilities
    
    @property
    def _llm_type(self) -> str:
        return "enhanced_litellm_chat"
    
    def _convert_message_to_dict(self, message: BaseMessage) -> Dict[str, Any]:
        """Convert LangChain message to LiteLLM format with multimodal support."""
        if isinstance(message, HumanMessage):
            # Check if content contains multimodal elements
            if isinstance(message.content, list):
                return {"role": "user", "content": message.content}
            else:
                return {"role": "user", "content": str(message.content)}
        elif isinstance(message, AIMessage):
            return {"role": "assistant", "content": str(message.content)}
        elif isinstance(message, SystemMessage):
            return {"role": "system", "content": str(message.content)}
        else:
            return {"role": "user", "content": str(message.content)}
    
    def create_image_content_item(self, image_path_or_url: str) -> Dict[str, Any]:
        """Create an image content item for LiteLLM (from test insights)."""
        if image_path_or_url.lower().startswith(("http://", "https://")):
            return {"type": "image_url", "image_url": {"url": image_path_or_url}}
        
        # Local file - convert to base64
        p = Path(image_path_or_url).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"Image not found: {image_path_or_url}")
        
        # Create base64 data URI
        with open(p, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        return {
            "type": "image_url", 
            "image_url": {"url": f"data:image/png;base64,{image_data}"}
        }
    
    def create_multimodal_content(
        self,
        text: str,
        images: Optional[List[str]] = None,
        files: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Create multimodal content array for LiteLLM."""
        content = []
        
        # Add text content
        if text:
            content.append({"type": "text", "text": text})
        
        # Add images if supported
        if images and self._capabilities.get("supports_vision", False):
            for image_path in images:
                try:
                    content.append(self.create_image_content_item(image_path))
                except Exception as e:
                    log.warning(f"Failed to add image {image_path}: {e}")
        elif images and not self._capabilities.get("supports_vision", False):
            log.warning(f"Model {self.model} does not support vision. Images will be ignored.")
        
        # Add files if supported (basic implementation)
        if files and self._capabilities.get("supports_files", False):
            for file_path in files:
                try:
                    # For now, treat files as text content
                    p = Path(file_path).expanduser().resolve()
                    if p.exists() and p.suffix.lower() in ['.txt', '.md', '.py', '.json', '.yaml', '.yml']:
                        file_content = p.read_text(encoding='utf-8')
                        content.append({
                            "type": "text", 
                            "text": f"File: {p.name}\n```\n{file_content}\n```"
                        })
                except Exception as e:
                    log.warning(f"Failed to add file {file_path}: {e}")
        elif files and not self._capabilities.get("supports_files", False):
            log.warning(f"Model {self.model} does not support file inputs. Files will be ignored.")
        
        return content if content else [{"type": "text", "text": text or ""}]
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat response using LiteLLM (sync version)."""
        
        # Convert messages to LiteLLM format
        litellm_messages = [self._convert_message_to_dict(msg) for msg in messages]
        
        # Prepare parameters
        params = {
            "model": self.model,
            "messages": litellm_messages,
            "temperature": self.temperature,
            "timeout": self.timeout
        }
        
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        
        if stop:
            params["stop"] = stop
            
        # Add any additional kwargs
        params.update(kwargs)
        
        try:
            log.info(f"Calling LiteLLM sync with model: {self.model}")
            response = completion(**params)
            
            # Extract response content
            response_content = response.choices[0].message.content
            
            # Create ChatGeneration
            message = AIMessage(content=response_content)
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            log.error(f"Error in LiteLLM sync completion: {str(e)}")
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
            "timeout": self.timeout
        }
        
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        
        if stop:
            params["stop"] = stop
            
        # Add any additional kwargs
        params.update(kwargs)
        
        try:
            log.info(f"Calling LiteLLM async with model: {self.model}")
            response = await acompletion(**params)
            
            # Extract response content
            response_content = response.choices[0].message.content
            
            # Create ChatGeneration
            message = AIMessage(content=response_content)
            generation = ChatGeneration(message=message)
            
            return ChatResult(generations=[generation])
            
        except Exception as e:
            log.error(f"Error in LiteLLM async completion: {str(e)}")
            raise e
    
    # Framework integration methods
    
    def create_multimodal_message(
        self,
        text: str,
        images: Optional[List[str]] = None,
        files: Optional[List[str]] = None
    ) -> HumanMessage:
        """Create a multimodal HumanMessage for the framework."""
        content = self.create_multimodal_content(text, images, files)
        return HumanMessage(content=content)
    
    def check_capabilities(self) -> Dict[str, bool]:
        """Get model capabilities."""
        return self._capabilities.copy()
        
    def bind_tools(self, tools: Sequence) -> BaseChatModel:
        """Bind tools to the model, with special handling for Google Gemini models."""
        try:
            # For Google/Gemini models, use the custom adapter
            if self._provider == 'google' and HAS_GOOGLE_GENAI:
                log.info(f"Using Google Gemini-specific tool binding for {self.model}")
                return get_tool_compatible_model(self, tools)
            else:
                # Default implementation for other providers
                log.info(f"Using standard tool binding for {self.model}")
                return super().bind_tools(tools)
        except Exception as e:
            log.warning(f"Tool binding failed for {self.model}: {e}. Falling back to wrapper.")
            # Fallback to a simple wrapper that will handle tool calls manually
            return get_fallback_tool_binding(self, tools)
    
    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Get list of supported LiteLLM providers."""
        return [
            "openai",      # OpenAI GPT models
            "azure",       # Azure OpenAI
            "anthropic",   # Anthropic Claude
            "google",      # Google Gemini
            "gemini",      # Alternative Gemini format
            "cohere",      # Cohere models
            "replicate",   # Replicate models
            "huggingface", # Hugging Face models
        ]
    
    @classmethod
    def create_from_test_format(cls, model_string: str, **kwargs) -> "EnhancedLiteLLMChat":
        """
        Create instance from test format model strings.
        Examples: "gemini/gemini-2.5-flash-lite", "azure/gpt-4.1", "openai/gpt-4o"
        """
        return cls(model=model_string, **kwargs)


# Utility functions for framework integration

def create_litellm_model(
    model_id: str,
    temperature: float = 0.2,
    **kwargs
) -> EnhancedLiteLLMChat:
    """
    Factory function to create LiteLLM models for the framework.
    
    Args:
        model_id: Model identifier in LiteLLM format (e.g., "openai/gpt-4o", "gemini/gemini-2.5-flash-lite")
        temperature: Model temperature
        **kwargs: Additional parameters
    
    Returns:
        Configured EnhancedLiteLLMChat instance
    """
    return EnhancedLiteLLMChat(
        model=model_id,
        temperature=temperature,
        **kwargs
    )

def is_litellm_model(model_id: str) -> bool:
    """Check if a model ID is in LiteLLM format."""
    if not isinstance(model_id, str):
        return False
    
    # LiteLLM format: provider/model
    if "/" in model_id and not model_id.startswith(("http://", "https://")):
        provider = model_id.split("/")[0]
        return provider in EnhancedLiteLLMChat.get_supported_providers()
    
    return False

async def test_litellm_model(model_id: str, test_message: str = "Hello, test message.") -> Dict[str, Any]:
    """
    Test a LiteLLM model with a simple message.
    
    Args:
        model_id: Model identifier
        test_message: Test message to send
    
    Returns:
        Test result dictionary
    """
    try:
        model = create_litellm_model(model_id)
        message = HumanMessage(content=test_message)
        
        start_time = asyncio.get_event_loop().time()
        result = await model._agenerate([message])
        end_time = asyncio.get_event_loop().time()
        
        return {
            "success": True,
            "model": model_id,
            "response": result.generations[0].message.content,
            "processing_time": round(end_time - start_time, 2),
            "capabilities": model.check_capabilities()
        }
    
    except Exception as e:
        return {
            "success": False,
            "model": model_id,
            "error": str(e)
        }


def get_tool_compatible_model(model_instance: EnhancedLiteLLMChat, tools: Sequence) -> BaseChatModel:
    """
    Convert LiteLLM models to tool-compatible versions based on provider.
    
    Args:
        model_instance: The LiteLLM model instance to convert
        tools: The tools to bind to the model
    
    Returns:
        Tool-compatible model instance
    """
    # Extract provider and model name from model format (e.g., gemini/model-name)
    provider = model_instance._provider
    model_name = model_instance.model.split('/')[1] if '/' in model_instance.model else model_instance.model
    
    if provider == 'google' and HAS_GOOGLE_GENAI:
        # Use LangChain's native Gemini integration for tool binding
        from langchain_google_genai import ChatGoogleGenerativeAI
        log.info(f"Creating native Google Gemini model {model_name} for tool binding")
        
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
            temperature=model_instance.temperature,
            convert_system_message_to_human=True
        ).bind_tools(tools)
    
    # Return original model for providers that already support tool binding
    return model_instance


def get_fallback_tool_binding(model_instance: EnhancedLiteLLMChat, tools: Sequence) -> BaseChatModel:
    """
    Create a fallback tool binding implementation when native binding fails.
    
    This creates a model that can handle tool calls even if the bind_tools method
    is not available in the model implementation.
    
    Args:
        model_instance: The original model instance
        tools: The tools to bind to the model
        
    Returns:
        Tool-compatible model wrapper
    """
    # Attempt to use LangChain's ChatPromptTemplate system for tools
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.runnables import RunnablePassthrough
        from langchain.agents import AgentExecutor, create_openai_tools_agent
        
        # Get tool descriptions
        tool_descriptions = [{
            "name": tool.name,
            "description": tool.description
        } for tool in tools]
        
        # Create a prompt template that includes tool information
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant with access to the following tools:\n\n" + 
                     "\n".join([f"{t['name']}: {t['description']}" for t in tool_descriptions])),
            ("user", "{input}")
        ])
        
        # Create chain with tool handling
        chain = prompt | model_instance
        
        log.info(f"Created fallback tool binding for {model_instance.model} with {len(tools)} tools")
        return chain
        
    except Exception as e:
        log.warning(f"Failed to create fallback tool binding: {e}. Returning original model.")
        return model_instance
