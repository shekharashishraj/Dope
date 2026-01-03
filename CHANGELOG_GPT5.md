# Changelog: GPT-5.1 Implementation

## [2026-01-02] - GPT-5.1 Model Support

### Added

#### Configuration
- Added `reasoning_effort` field to `OpenAIConfig` (values: none, low, medium, high)
- Added `verbosity` field to `OpenAIConfig` (values: low, medium, high)
- Added `is_gpt5_model()` helper method to `OpenAIConfig`
- Updated `config.yaml` to use `gpt-5.1-2025-11-13` as default model
- Added GPT-5.1 specific parameters to config with comments

#### API Client
- Added `_is_gpt5_model()` method to `OpenAIClient`
- Added conditional parameter handling for GPT-5.1 models
- Added `_repair_json_word_numbers()` method for JSON repair
- Enhanced JSON parsing with multi-layer repair strategy
- Added individual object extraction fallback
- Updated logging to show GPT-5.1 parameters when applicable

#### Response Collector
- Added `_is_gpt5_model()` method to `ResponseCollector`
- Added conditional parameter handling for GPT-5.1 models
- Added reasoning_effort and verbosity initialization

#### Prompt Templates
- Restructured `prompts/grouped_batch_v3/tf_grouped_prompt.py` for grouped batches
- Removed single-question placeholders from main template
- Maintained original content structure while supporting batch processing

#### Documentation
- Created `GPT5_IMPLEMENTATION.md` - Comprehensive implementation guide
- Created `JSON_REPAIR_DOCUMENTATION.md` - JSON repair functionality details
- Created `PROMPT_TEMPLATE_STRUCTURE.md` - Prompt template architecture
- Created `CHANGELOG_GPT5.md` - This changelog

### Changed

#### Configuration Model (`src/models/config.py`)
- Added new optional fields for GPT-5.1 parameters
- Added helper method for model detection

#### OpenAI Client (`src/openai_client.py`)
- Modified `_call_api_with_retry()` to conditionally exclude deprecated parameters for GPT-5.1
- Modified `create_batch_file()` to conditionally exclude deprecated parameters for GPT-5.1
- Enhanced JSON parsing with word number repair
- Added fallback strategies for malformed JSON

#### Response Collector (`src/detection/response_collector.py`)
- Modified `_call_api_with_retry_file_id()` to conditionally exclude deprecated parameters
- Added GPT-5.1 parameter initialization

#### Config YAML (`config/config.yaml`)
- Changed default model from `gpt-4o` to `gpt-5.1-2025-11-13`
- Added reasoning_effort and verbosity parameters
- Added comments noting deprecated parameters

#### Prompt Template (`prompts/grouped_batch_v3/tf_grouped_prompt.py`)
- Restructured to work with grouped batch queries
- Removed single-question placeholders
- Maintained original content structure

### Fixed

- Fixed `KeyError: 'latex_stem_text'` in grouped batch prompts
- Fixed JSON parsing failures due to word numbers (e.g., "fifty" → 50)
- Fixed API parameter errors for GPT-5.1 models

### Known Issues

1. **SDK Limitation**: OpenAI Python SDK does not yet support `reasoning` and `verbosity` parameters. These are configured but not passed to the API. The model uses default values. TODO comments mark where to enable them when SDK is updated.

2. **Word Number Support**: Currently supports basic word numbers (zero through ninety, hundred, thousand). Compound numbers (e.g., "twenty-five") are not supported but can be added if needed.

### Migration Notes

#### Upgrading to GPT-5.1

1. Update `config/config.yaml`:
   ```yaml
   openai:
     model: "gpt-5.1-2025-11-13"
     reasoning_effort: "medium"
     verbosity: "medium"
   ```

2. No code changes needed - automatic detection handles everything

#### Downgrading to GPT-4

Simply change model in config:
```yaml
openai:
  model: "gpt-4o"
```

### Testing

- Created verification script `verify_gpt5_changes.py`
- All verification checks pass
- Tested with actual API calls
- JSON repair tested with word number cases

### Performance Impact

- **Minimal**: Conditional checks are O(1)
- **JSON Repair**: O(n) where n is response length
- **No significant overhead** for non-GPT-5 models

### Backward Compatibility

- ✅ Fully backward compatible
- ✅ Non-GPT-5 models continue using traditional parameters
- ✅ Existing configs work without modification
- ✅ Can mix GPT-4 and GPT-5.1 in same codebase

### Future Work

1. Enable `reasoning` and `verbosity` parameters when SDK supports them
2. Add support for compound word numbers
3. Enhance error messages for JSON parsing failures
4. Add metrics for repair success rate

---

## Technical Details

### Parameter Exclusion Logic

For GPT-5.1 models, the following parameters are excluded:
- `temperature`
- `top_p`
- `frequency_penalty`
- `presence_penalty`
- `max_tokens`
- `logprobs`
- `top_logprobs`

### Word Number Repair

Supported conversions:
- Basic: zero → 0, one → 1, ..., nineteen → 19
- Tens: twenty → 20, thirty → 30, ..., ninety → 90
- Hundreds/Thousands: hundred → 100, thousand → 1000

### JSON Parsing Flow

1. Standard parse attempt
2. Word number repair + escape repair + parse
3. Individual object extraction
4. Array pattern extraction
5. Return valid objects or empty list

---

## Contributors

- Implementation: AI Assistant
- Testing: User verification
- Documentation: AI Assistant

---

## References

- OpenAI GPT-5.1 Docs: https://platform.openai.com/docs/models/gpt-5.1
- OpenAI Python SDK: https://github.com/openai/openai-python
- JSON Specification: https://www.json.org/

