# Phase 01: Cleanup Patterns

## `src/llm.py`
**Role:** Coordinates all language model interactions, managing requests to cloud LLMs (Gemini) and currently handling local LLMs (Qwen).
**Data Flow:** Receives images and text from the pipeline, routes them to the appropriate model, and returns structured classifications or groupings.
**Analog:** No analog is needed as we are purely removing existing functionality.

### Pattern: Remove Local Client & Parameters
```python
-    def __init__(self, api_keys: Optional[list[str]] = None, delay_between_pages: float = 5.0, telemetry_queue: Any = None, use_local_llm: bool = True) -> None:
-        self.use_local_llm = use_local_llm
...
-        local_base_url = os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1")
-        self.local_client = openai.OpenAI(base_url=local_base_url, api_key="ollama")
```

### Pattern: Remove Local Fallback Checks & Extraction Methods
```python
-    def should_use_local_fallback(self) -> bool:
...
-    def extract_page(self, image_bytes: bytes) -> str:
...
-    def classify_extracted_page(self, text: str, extracted_footer: Optional[str] = None) -> PageClassification:
...
```

### Pattern: Simplify Direct Classification
```python
-        attempts = 1 if self.use_local_llm else 100
+        attempts = 100
```

### Pattern: Simplify Bulk Grouping
```python
-        use_local = self.should_use_local_fallback()
-        
-        if not use_local:
-            try:
-                print(" Running bulk semantic grouping using Cloud Model...")
-                ...
-            except Exception as e:
-                ...
-                use_local = True
-
-        if use_local:
-            ...
```
*(Replace entirely with just the cloud logic, removing `use_local` checks and the local inference block).*

## `src/pipeline.py`
**Role:** Orchestrates the multi-pass document processing workflow.
**Data Flow:** Takes a PDF, extracts pages, queries `GemmaClient` for classification, and groups them by tenant/category.
**Analog:** Purely pruning unused logic.

### Pattern: Remove Local Variables and Deferred Caching
```python
-        text_cache = SimpleCache(f"{pdf_path}.extracted.cache.json")
...
-            deferred_local_pages: list[tuple[int, str, Optional[str]]] = []
...
-                if str(p_idx) in text_cache:
-                    print(f" Loaded Arabic text for Page {p_idx} from cache. Deferring local classification.")
-                    text = text_cache[str(p_idx)]
-                    deferred_local_pages.append((p_idx, text, extracted_footer))
-                    continue
```

### Pattern: Remove Fallback Logic in Extraction Loop
```python
-                use_local = self.client.should_use_local_fallback()
-                
-                if not use_local:
...
-                if use_local:
-                    try:
-                        print(f" Extracting Arabic text from Page {p_idx} using Local Vision Model (Qwen-VL)...")
...
```

### Pattern: Remove Deferred Processing Block (Pass 1b)
```python
-            # Phase 2: Run deferred local classification (Pass 1b) at the very end
-            if deferred_local_pages:
-                ...
```

## `src/main.py`
**Role:** CLI Entry point.
**Data Flow:** Parses arguments and instantiates the `Pipeline`.

### Pattern: Remove CLI Flags and Pipeline Args
```python
-    parser.add_argument("--no-local", action="store_true", help="Disable local LLM fallback and wait for cloud rate limits instead")
...
-    env_use_local = str(os.getenv("USE_LOCAL_LLM", "true")).lower() == "true"
-    final_use_local = False if args.no_local else env_use_local
-    
-    pipeline = Pipeline(api_keys=api_keys, use_local_llm=final_use_local)
+    pipeline = Pipeline(api_keys=api_keys)
```

## `.env` and `.env.example`
**Role:** Environment configuration.
**Data Flow:** Injected into `os.environ` during `main.py`.

### Pattern: Delete Unused Keys
```env
-LOCAL_BASE_URL
-LOCAL_MODEL_NAME
-LOCAL_TEXT_MODEL_NAME
-USE_LOCAL_LLM
```

## Scripts to Delete
- `scripts/evaluate_local.py`
- `scripts/test_local_qwen.py`
