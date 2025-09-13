# Changelog

## [1.1.0] - 2025-09-13

### 🎯 Major Enhancement: Default System Prompt Changed to Direct Response Mode

**Breaking Change**: The default system prompt has been changed from `2` (Adobe Firefly Image Optimizer) to `0` (No System Prompt) for better user experience with direct, factual answers.

### Added
- **New Configuration Option**: `PEPGENX_DEFAULT_SYSTEM_PROMPT` environment variable
  - Default value: `0` (No System Prompt - direct response mode)
  - Configurable via `.env` file
  - Allows users to override the default behavior

### Changed
- **Default System Prompt**: Changed from `2` to `0`
  - **Before**: Questions like "What is 2+2?" returned image descriptions
  - **After**: Questions like "What is 2+2?" return direct answers like "2 + 2 = 4"
- **PepGenXRequest Model**: Updated to support configurable defaults
  - `system_prompt` field now accepts `None` to trigger default behavior
  - When `system_prompt=0`, the field is excluded from API requests
- **Message Translation**: Enhanced to handle new default behavior
  - No system messages → `system_prompt=None` → uses configurable default
  - Explicit system messages → mapped to appropriate system prompt IDs

### Technical Changes
- **Configuration** (`app/core/config.py`):
  - Added `pepgenx_default_system_prompt: int = Field(default=0)`
- **Models** (`app/models/pepgenx_models.py`):
  - Added `get_default_system_prompt()` function
  - Updated `PepGenXRequest.system_prompt` to `Optional[Union[int, str]]`
  - Modified `get_system_prompt_id()` to use configurable default
  - Enhanced `format_messages_for_pepgenx()` to return `None` for no system messages
- **Translation** (`app/services/translator.py`):
  - Updated `RequestTranslator.translate_chat_completion()` to handle `None` system prompts
  - Added logic to exclude `system_prompt` field when value is `0`
- **Client** (`app/services/pepgenx_client.py`):
  - Updated health check to use new default behavior
- **Environment** (`.env`):
  - Added `PEPGENX_DEFAULT_SYSTEM_PROMPT=0`
- **Documentation**:
  - Updated `README.md` with new configuration option
  - Added `docs/SYSTEM_PROMPT_UPDATE.md` with detailed migration guide
- **Tests** (`tests/test_translator.py`):
  - Added `test_default_system_prompt_behavior()` to verify new functionality
  - All existing tests continue to pass

### Backward Compatibility
✅ **Fully Backward Compatible**:
- OpenAI API format unchanged
- Response format unchanged
- Existing integrations continue to work
- Explicit system messages still mapped correctly

### Migration Guide

#### For New Deployments
- No action required - new default provides better user experience

#### For Existing Deployments
- **Option 1** (Recommended): Keep new default for better responses
- **Option 2**: Restore old behavior by setting `PEPGENX_DEFAULT_SYSTEM_PROMPT=2` in `.env`

#### Configuration Examples
```bash
# New default (direct answers)
PEPGENX_DEFAULT_SYSTEM_PROMPT=0

# Restore old behavior (image optimization)
PEPGENX_DEFAULT_SYSTEM_PROMPT=2

# Use general assistant
PEPGENX_DEFAULT_SYSTEM_PROMPT=6
```

### System Prompt Reference
| ID | Name | Purpose | Best For |
|----|------|---------|----------|
| **0** | No System Prompt | Direct response mode | **Math, facts, general Q&A** |
| 1 | Content Safety Analyzer | Content guidelines analysis | Content moderation |
| 2 | Adobe Firefly Image Optimizer | Image generation optimization | Image prompts |
| 3 | PepsiCo ESG Assistant | ESG-focused responses | Corporate sustainability |
| 4 | System Prompt Generator | Creates system prompts | Meta-prompting |
| 5 | Prompt Enhancer | Improves prompt quality | Prompt optimization |
| 6 | Tool-Aware Assistant | General assistant with tools | General Q&A |
| 7 | Prompt Adaptation Expert | Adapts between models | Cross-model compatibility |

### Testing
- All existing tests pass
- New test added for default system prompt behavior
- Manual testing confirms direct answers for math questions
- Payload generation correctly excludes `system_prompt` when value is `0`

### Impact
- **User Experience**: Significantly improved for factual questions
- **API Compatibility**: No breaking changes to OpenAI API interface
- **Performance**: No performance impact
- **Configurability**: Users can customize default behavior

---

## [1.0.0] - 2025-09-12

### Added
- Initial release of PepGenX OpenAI Wrapper
- OpenAI-compatible Chat Completions API
- Support for multiple AI models (GPT, Claude, etc.)
- OKTA authentication integration
- Comprehensive logging and monitoring
- Docker containerization
- Health check endpoints
- Rate limiting capabilities
- CORS support
- Production-ready configuration management

### Features
- **API Endpoints**:
  - `/v1/chat/completions` - OpenAI-compatible chat completions
  - `/v1/models` - List available models
  - `/health` - Health check endpoints
- **Authentication**: API key validation and OKTA token management
- **Monitoring**: Prometheus metrics and structured logging
- **Security**: Rate limiting, CORS, and input validation
- **Deployment**: Docker and Docker Compose support
