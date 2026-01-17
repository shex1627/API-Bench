# Daily Updates - 2026-01-17

## Summary

Multiple features added to API Workbench MCP today:

1. **Dynamic Variables** - Postman-compatible runtime variables
2. **Streaming Support** - SSE/streaming response handling for LLM APIs
3. **File Export** - Save requests/responses to JSON, YAML, Markdown, HAR
4. **Hints Configuration** - Configurable context hints via YAML
5. **Collection Reorganization** - New "LLM APIs" collection structure
6. **Variable Overrides Enhancement** - Per-request variable overrides

---

## 1. Dynamic Variables (Committed: 98e5424)

### Files
- `src/api_workbench_mcp/services/dynamic_variables.py` (new)
- `src/api_workbench_mcp/services/variable_store.py` (modified)
- `tests/unit/test_dynamic_variables.py` (new)

### Features
45 Postman-compatible dynamic variables that generate values at runtime:

| Category | Variables |
|----------|-----------|
| Core | `$guid`, `$randomUUID`, `$timestamp`, `$isoTimestamp`, `$randomInt`, `$randomBoolean` |
| Names | `$randomFirstName`, `$randomLastName`, `$randomFullName` |
| Internet | `$randomEmail`, `$randomUserName`, `$randomPassword`, `$randomUrl`, `$randomIP`, `$randomIPV6`, `$randomPhoneNumber`, `$randomMACAddress` |
| Location | `$randomCity`, `$randomCountry`, `$randomCountryCode`, `$randomStreetAddress`, `$randomLatitude`, `$randomLongitude` |
| Business | `$randomCompanyName`, `$randomJobTitle`, `$randomDepartment` |
| Financial | `$randomPrice`, `$randomCurrencyCode`, `$randomCurrencyName`, `$randomCurrencySymbol`, `$randomBankAccount` |
| Dates | `$randomDatePast`, `$randomDateFuture`, `$randomDateRecent`, `$randomWeekday`, `$randomMonth` |
| Content | `$randomFileName`, `$randomFileExt`, `$randomMimeType`, `$randomWord`, `$randomWords`, `$randomLoremSentence`, `$randomLoremParagraph` |

### Usage
```yaml
body:
  id: "{{$guid}}"
  email: "{{$randomEmail}}"
  created_at: "{{$isoTimestamp}}"
```

---

## 2. Streaming Support (Uncommitted)

### Files
- `src/api_workbench_mcp/services/http_client.py` (modified)
- `src/api_workbench_mcp/server.py` (modified)

### Features
- New `stream` parameter in `request_send`
- Captures all SSE events during streaming
- Accumulates full response text
- Tracks timing metadata (first/last chunk times)
- Returns streaming metadata alongside response

### Usage
```python
request_send(
    method="POST",
    url="https://api.anthropic.com/v1/messages",
    body={"model": "claude-3-5-sonnet", "stream": true, ...},
    stream=True  # Enable streaming capture
)
```

### Response includes
```json
{
  "streaming": {
    "events": ["data: {...}", "data: {...}", ...],
    "event_count": 15,
    "first_chunk_time_ms": 245,
    "last_chunk_time_ms": 1823
  }
}
```

---

## 3. File Export (Uncommitted)

### Files
- `src/api_workbench_mcp/server.py` (modified)

### Features
- New `save_to_file` parameter - path or `True` for auto-generated filename
- New `save_format` parameter - json, yaml, markdown, har
- Sanitized auto-generated filenames with timestamp
- Exports directory at `exports/`

### Formats
| Format | Extension | Description |
|--------|-----------|-------------|
| `json` | `.json` | Structured JSON with metadata, request, response |
| `yaml` | `.yaml` | YAML format, easier to read |
| `markdown` | `.md` | Human-readable documentation, masks sensitive headers |
| `har` | `.har` | HTTP Archive format for browser dev tools |

### Usage
```python
# Auto-generate filename
request_send(..., save_to_file=True, save_format="json")

# Custom filename
request_send(..., save_to_file="debug/claude-response.json")

# Markdown for documentation
request_send(..., save_to_file="docs/api-example.md", save_format="markdown")
```

---

## 4. Hints Configuration (Uncommitted)

### Files
- `config/hints.yaml` (new)
- `src/api_workbench_mcp/server.py` (modified)

### Features
- Externalized hints configuration
- Loaded from `config/hints.yaml`
- Provides context hints for `get_api_context()` tool
- Includes LLM-specific examples for Anthropic and OpenAI

### Configuration
```yaml
calling_apis: "Use request_send with method, url, headers, and body."
streaming: "For LLM APIs, use stream=True to capture all SSE events."
saving_files: "Use save_to_file=True or save_to_file='filename.json' to export."
examples:
  anthropic: |
    request_send(
      method="POST",
      url="{{anthropic_base_url}}/messages",
      ...
    )
```

---

## 5. Collection Reorganization (Uncommitted)

### Files
- `collections/Anthropic API/` (deleted)
- `collections/OpenAI API/` (deleted)
- `collections/random/` (deleted)
- `collections/LLM APIs/` (new)

### New Structure
```
collections/
└── LLM APIs/
    ├── collection.yaml
    └── requests/
        ├── Claude Chat.yaml
        ├── GPT Chat (Fixed).yaml
        └── GPT Chat (GPT-5.2).yaml
```

### Changes
- Consolidated Anthropic and OpenAI into single "LLM APIs" collection
- Organized by folders within collection
- Removed old random/test collections

---

## 6. Variable Overrides Enhancement (Previously Committed)

### Files
- `src/api_workbench_mcp/server.py`
- `src/api_workbench_mcp/services/http_client.py`

### Features
- `variable_overrides` parameter in `request_send`
- Override any variable at request time without modifying environment
- Useful for testing different models, prompts, etc.

### Usage
```python
request_send(
    method="POST",
    url="{{base_url}}/messages",
    body={"model": "{{model}}", "messages": [...]},
    variable_overrides={
        "model": "claude-opus-4.5",
        "prompt": "Custom prompt for this request"
    }
)
```

---

## Supporting Files (Uncommitted)

### Environment Files
- `environments/development.json` - Development environment with API keys
- `environments/.state.json` - Active environment state

### Scripts
- `setup_clean.sh` - Setup script
- `setup_llm_collection.py` - Collection setup script

### Directories
- `exports/` - Directory for exported request/response files
- `config/` - Configuration files directory
- `docs/` - Documentation directory

---

## Backlog Updates

Added to `BACKLOG.md`:

### Priority 12: Collection-Based Prompts & Learning
- **API Hints & Skills System** - CRUD for collection prompts
- **Learning from Request History** - Auto-generate learnings from patterns
- **Prompt Inheritance** - Global > Collection > Folder > Request precedence

### Updated Quick Wins
- Added "Dynamic variables" as implemented ✓
- Added "Collection-based prompts/hints CRUD"

---

## Variable Precedence (Updated)

1. **Overrides** (runtime `variable_overrides`)
2. **Dynamic variables** (`$timestamp`, `$guid`, etc.)
3. **Environment variables**
4. **Collection variables**
5. **Global variables**
