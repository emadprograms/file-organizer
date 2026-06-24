import re

def refactor():
    with open("src/llm.py", "r", encoding="utf-8") as f:
        content = f.read()

    router_code = '''    def _route_llm_call(self, model: str, contents: list, response_schema: type, log_prefix: str = "Retry", max_attempts: int = None) -> any:
        attempts = 0
        if max_attempts is None:
            max_attempts = max(7, len(self.api_keys) * 2)
        invalid_retries = 0
        
        while attempts < max_attempts:
            attempts += 1
            client, key, reserve_time = self._get_client_and_key(estimated_tokens=3000)
            start_time = time.time()
            used_tokens = 0
            
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                        temperature=0
                    )
                )

                latency_ms = int((time.time() - start_time) * 1000)
                used_tokens = 3000
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    used_tokens = response.usage_metadata.total_token_count
                
                self._reconcile_usage(key, reserve_time, used_tokens)
                
                if response.parsed is not None:
                    result = response.parsed
                else:
                    try:
                        text = response.text.strip()
                        json_match = re.search(r"(\\{.*\\}|\\[.*\\])", text, re.DOTALL)
                        if json_match:
                            text = json_match.group(1)
                        data = json.loads(text)
                        result = response_schema(**data)
                    except (json.JSONDecodeError, Exception) as parse_err:
                        raw_preview = ""
                        try:
                            if hasattr(response, "text") and response.text:
                                raw_preview = response.text[:200]
                            elif hasattr(response, "candidates") and response.candidates and response.candidates[0].finish_reason:
                                raw_preview = f"<Finish reason: {response.candidates[0].finish_reason}>"
                        except ValueError:
                            raw_preview = "<ValueError reading response.text>"
                        
                        print(f"JSON PARSE ERROR. Raw text preview: {raw_preview}")
                        raise InvalidResponseError(raw_preview)

                telemetry_logger.info({
                    "timestamp": time.time(),
                    "key_index": self.api_keys.index(key),
                    "latency_ms": latency_ms,
                    "tokens_used": used_tokens,
                    "status_code": 200,
                    "error_type": "none"
                })

                self._report_success(key)
                return result

            except Exception as e:
                error_str = str(e).lower()
                is_429 = "429" in error_str or "too many requests" in error_str or "quota" in error_str or "resource exhausted" in error_str
                is_token_limit = "token" in error_str and is_429
                is_5xx = "500" in error_str or "503" in error_str or "internal error" in error_str
                is_invalid = "invalidresponseerror" in error_str or isinstance(e, InvalidResponseError)
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                error_type = "unknown"
                if is_429:
                    error_type = "token_limit" if is_token_limit else "request_limit"
                elif is_5xx:
                    error_type = "server_error"
                elif is_invalid:
                    error_type = "model_refusal"
                
                raw_preview = str(e) if is_invalid else ""
                
                log_payload = {
                    "timestamp": time.time(),
                    "key_index": self.api_keys.index(key),
                    "latency_ms": latency_ms,
                    "tokens_used": used_tokens if is_invalid else 0,
                    "status_code": 429 if is_429 else (500 if is_5xx else 400),
                    "error_type": error_type
                }
                if is_invalid:
                    log_payload["raw_preview"] = raw_preview
                    
                telemetry_logger.error(log_payload)
                
                print(f"[{log_prefix} {attempts}/{max_attempts}] LLM call failed: {e}")
                
                if is_invalid:
                    invalid_retries += 1
                    if invalid_retries >= 2:
                        raise InvalidResponseError(raw_preview)
                
                if is_429 or is_5xx or is_invalid:
                    self._report_failure(key, is_429=is_429, is_token_limit=is_token_limit)
                    if attempts == max_attempts:
                        raise LLMFailureError(f"Max retries reached. Last error: {error_str}")
                    time.sleep(7.5)
                    continue
                else:
                    if attempts == max_attempts:
                        raise e
                    self._report_failure(key, is_429=False)
                    continue
'''

    content = content.replace("    def _build_system_prompt(self) -> str:", router_code + "\n    def _build_system_prompt(self) -> str:")
    
    with open("src/llm.py", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    refactor()
