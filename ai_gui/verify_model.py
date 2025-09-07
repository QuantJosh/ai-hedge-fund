#!/usr/bin/env python3
"""
Simple verifier for the LLM model configuration in ai_gui/configs.

Usage:
  - python -m ai_gui.verify_model
  - python -m ai_gui.verify_model --provider OpenRouter --model openai/gpt-4o-mini

It loads ai_gui/configs/default.json by default and tries a minimal LLM call.
Exits with code 0 on success, 1 on failure.
"""
import sys
import os
import time
import argparse
from pathlib import Path

# Ensure project src/ is importable
ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

# GUI config loader
from ai_gui.config_manager import load_config

# Load environment variables from project .env so API keys are available
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(dotenv_path=ROOT / ".env")
except Exception:
    pass

# LLM model helpers
from src.llm.models import get_model, get_model_info, ModelProvider


def _normalize_provider(provider: str) -> ModelProvider:
    # Try value first (e.g., "OpenRouter"), then enum-name (e.g., "OPENROUTER")
    try:
        return ModelProvider(provider)
    except Exception:
        try:
            return ModelProvider[provider.upper()]
        except Exception:
            # Default to OpenAI
            return ModelProvider.OPENAI


def main():
    parser = argparse.ArgumentParser(description="Verify configured LLM model endpoint by making a minimal call.")
    parser.add_argument("--provider", help="Model provider name (overrides config)")
    parser.add_argument("--model", help="Model name (overrides config)")
    parser.add_argument("--timeout", type=float, default=float(os.getenv("LLM_REQUEST_TIMEOUT", "60")), help="Request timeout seconds")
    args = parser.parse_args()

    cfg = load_config()
    provider = args.provider or cfg.get("model_provider") or "OpenRouter"
    model_name = args.model or cfg.get("model_name") or "openai/gpt-4o-mini"

    provider_enum = _normalize_provider(provider)

    # Quick environment checks for common providers
    missing_keys = []
    if provider_enum == ModelProvider.OPENROUTER:
        if not (os.getenv("OPENROUTER_API_KEY")):
            missing_keys.append("OPENROUTER_API_KEY")
    elif provider_enum == ModelProvider.OPENAI:
        if not (os.getenv("OPENAI_API_KEY")):
            missing_keys.append("OPENAI_API_KEY")
    elif provider_enum == ModelProvider.GROQ:
        if not (os.getenv("GROQ_API_KEY")):
            missing_keys.append("GROQ_API_KEY")
    elif provider_enum == ModelProvider.ANTHROPIC:
        if not (os.getenv("ANTHROPIC_API_KEY")):
            missing_keys.append("ANTHROPIC_API_KEY")
    elif provider_enum == ModelProvider.GOOGLE:
        if not (os.getenv("GOOGLE_API_KEY")):
            missing_keys.append("GOOGLE_API_KEY")

    print(f"Provider: {provider_enum.value} | Model: {model_name}")
    if missing_keys:
        print(f"Missing API keys: {', '.join(missing_keys)}")
        print("Please set the required environment variables and retry.")
        sys.exit(1)

    try:
        # Build client (get_model already respects LLM_REQUEST_TIMEOUT via src/llm/models.py)
        llm = get_model(model_name, provider_enum)
        prompt = "You are a connectivity probe. Reply with a single word: pong."
        print("Sending test request...")
        t0 = time.time()
        resp = llm.invoke(prompt)
        dt = time.time() - t0
        content = getattr(resp, "content", str(resp))
        print("Received response in %.2fs" % dt)
        print("--- Response (truncated to 500 chars) ---")
        print(content[:500])
        print("--- End ---")
        print("OK: Model endpoint is reachable and responded.")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Model call failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
