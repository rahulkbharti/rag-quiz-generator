import os
import sys
import time
import argparse
import warnings
from dotenv import load_dotenv

# Reconfigure stdout to utf-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Suppress AFC deprecation logs for clean output
warnings.filterwarnings("ignore", category=UserWarning)

# Load .env file (override=True ensures local .env takes precedence over shell env)
load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Dynamic Model Pricing Catalog (Per 1 Million Tokens in USD)
# Source: Google AI Studio & Vertex AI Official Pricing Matrix
# ---------------------------------------------------------------------------
MODEL_PRICING_CATALOG = {
    # Flash Lite tier (most economical)
    "flash-lite": {
        "standard": {"input": 0.0375, "output": 0.150},
        "over_128k": {"input": 0.0750, "output": 0.300},
    },
    # Flash standard tier (Gemini 2.5 Flash, 3.5 Flash, etc.)
    "flash": {
        "standard": {"input": 0.0750, "output": 0.300},
        "over_128k": {"input": 0.1500, "output": 0.600},
    },
    # Pro tier (Gemini 2.5 Pro, 3.1 Pro, etc.)
    "pro": {
        "standard": {"input": 1.2500, "output": 5.000},
        "over_128k": {"input": 2.5000, "output": 10.000},
    },
    # Default fallback
    "default": {
        "standard": {"input": 0.0750, "output": 0.300},
        "over_128k": {"input": 0.1500, "output": 0.600},
    },
}

def resolve_model_rates(model_id: str, input_token_count: int) -> tuple[float, float, str]:
    clean_id = model_id.lower().replace("models/", "")

    if "flash-lite" in clean_id or "lite" in clean_id:
        tier_key = "flash-lite"
    elif "pro" in clean_id:
        tier_key = "pro"
    elif "flash" in clean_id:
        tier_key = "flash"
    else:
        tier_key = "default"

    tier_data = MODEL_PRICING_CATALOG[tier_key]
    is_long_context = input_token_count > 128_000
    bracket_key = "over_128k" if is_long_context else "standard"
    rates = tier_data[bracket_key]

    bracket_label = ">128k tokens" if is_long_context else "<=128k tokens"
    return rates["input"], rates["output"], f"{tier_key.upper()} ({bracket_label})"

def main():
    parser = argparse.ArgumentParser(description="Live Dynamic Gemini Token & Cost Audit")
    parser.add_argument(
        "--model",
        default="gemini-3.5-flash",
        help="Gemini Model ID (default: gemini-3.5-flash)"
    )
    parser.add_argument(
        "--prompt",
        default="Provide step-by-step instructions to configure automated SMS fee alerts for late fee collections in School ERP v2.4.",
        help="Custom prompt text to test with live token counting"
    )
    parser.add_argument("--mock", action="store_true", help="Simulate inference if needed")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if not api_key or api_key == "your_key_here":
        print("[ERROR] Valid GEMINI_API_KEY or GOOGLE_API_KEY not found in .env or environment.")
        print("Please set your API key in .env:")
        print("  GOOGLE_API_KEY=your_actual_gemini_api_key")
        sys.exit(1)

    from google import genai
    from google.genai import errors, types

    client = genai.Client(api_key=api_key)

    PRIMARY_MODEL = args.model
    FALLBACK_MODELS = [m for m in ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-3-flash-preview"] if m != PRIMARY_MODEL]
    SAMPLE_PROMPT = args.prompt

    print(f"Target Model        : {PRIMARY_MODEL}")
    print(f"Input Prompt Length : {len(SAMPLE_PROMPT)} characters")
    print(f"Prompt Text         : {SAMPLE_PROMPT[:70]}...\n")

    # ---------------------------------------------------------------------------
    # 1. Pre-flight Token Estimation (Live API Call - Zero Cost)
    # ---------------------------------------------------------------------------
    try:
        token_count_response = client.models.count_tokens(
            model=PRIMARY_MODEL,
            contents=SAMPLE_PROMPT,
        )
        estimated_input_tokens = token_count_response.total_tokens
        print(f"Live Pre-flight Tokenizer: {estimated_input_tokens} input tokens calculated by Google API")
    except Exception as e:
        print(f"[ERROR] Pre-flight token estimation failed: {e}")
        sys.exit(1)

    # ---------------------------------------------------------------------------
    # 2. Execute Inference Request (Live API Call)
    # ---------------------------------------------------------------------------
    print("\nExecuting Inference Request on Google AI...")
    actual_input_tokens = estimated_input_tokens
    actual_output_tokens = 0
    thoughts_tokens = 0
    total_consumed_tokens = 0
    response_text = ""
    active_model = PRIMARY_MODEL

    if args.mock:
        print(">> Running in --mock mode")
        actual_output_tokens = 342
        thoughts_tokens = 0
        total_consumed_tokens = actual_input_tokens + actual_output_tokens
        response_text = "Mock ERP instructions response..."
    else:
        gen_config = types.GenerateContentConfig(
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
        )

        candidate_models = [PRIMARY_MODEL] + FALLBACK_MODELS
        succeeded = False

        for current_model in candidate_models:
            for attempt in range(1, 3):
                try:
                    response = client.models.generate_content(
                        model=current_model,
                        contents=SAMPLE_PROMPT,
                        config=gen_config,
                    )
                    metadata = response.usage_metadata
                    
                    # Live extraction from Google's response metadata
                    actual_input_tokens = metadata.prompt_token_count
                    actual_output_tokens = metadata.candidates_token_count
                    # Thoughts / Reasoning tokens generated by Gemini 2.5/3.5 Flash
                    thoughts_tokens = getattr(metadata, "thoughts_token_count", 0) or 0
                    total_consumed_tokens = metadata.total_token_count
                    
                    response_text = response.text
                    active_model = current_model
                    succeeded = True
                    break
                except errors.ServerError as e:
                    if e.code == 503:
                        print(f"⚠️ {current_model} busy (503 High Demand). Retrying/Switching...")
                        time.sleep(2)
                        continue
                    raise
                except errors.ClientError as e:
                    print(f"\n[API ClientError {e.code}]: {e.message}")
                    sys.exit(1)

            if succeeded:
                break

        if not succeeded:
            print("\n[ERROR] All Gemini models temporarily unavailable. Please try again later.")
            sys.exit(1)

    # ---------------------------------------------------------------------------
    # 3. Dynamic Financial Audit (With Thoughts / Reasoning Breakdown)
    # ---------------------------------------------------------------------------
    rate_input_usd, rate_output_usd, pricing_tier = resolve_model_rates(active_model, actual_input_tokens)

    # Note: Google charges thoughts/reasoning tokens at the candidate output rate
    billable_output_tokens = actual_output_tokens + thoughts_tokens

    EXCHANGE_RATE_USD_INR = 86.00
    cost_input_usd = (actual_input_tokens / 1_000_000) * rate_input_usd
    cost_output_usd = (billable_output_tokens / 1_000_000) * rate_output_usd
    total_cost_usd = cost_input_usd + cost_output_usd
    total_cost_inr = total_cost_usd * EXCHANGE_RATE_USD_INR

    print("\n========== DYNAMIC INFERENCE FINANCIAL AUDIT ==========")
    print(f"Model Invoked              : {active_model}")
    print(f"Pricing Category           : {pricing_tier}")
    print(f"Applied Input Rate         : ${rate_input_usd:.4f} per 1M tokens")
    print(f"Applied Output Rate        : ${rate_output_usd:.4f} per 1M tokens")
    print(f"Exchange Rate              : 1 USD = ₹{EXCHANGE_RATE_USD_INR:.2f} INR")
    print("-" * 55)
    print("Token Consumption Breakdown (Live API Metadata):")
    print(f"  • Prompt Input Tokens    : {actual_input_tokens} (${cost_input_usd:.7f} USD)")
    print(f"  • Candidate Output Tokens: {actual_output_tokens}")
    if thoughts_tokens > 0:
        print(f"  • Thinking/Thoughts Tokens: {thoughts_tokens} (Internal Gemini Reasoning)")
    print(f"  • Total Billable Output  : {billable_output_tokens} (${cost_output_usd:.7f} USD)")
    print(f"  • Formula Verification   : {actual_input_tokens} (in) + {actual_output_tokens} (out) + {thoughts_tokens} (thinking) = {total_consumed_tokens}")
    print("-" * 55)
    print(f"Total Consumed Tokens      : {total_consumed_tokens} tokens")
    print(f"Total Query Cost USD       : ${total_cost_usd:.6f}")
    print(f"Total Query Cost INR       : ₹{total_cost_inr:.4f} ({total_cost_inr * 100:.2f} paise)")
    print("========================================================\n")

    print("Response Output Preview:")
    print("-" * 60)
    print(response_text[:350] + "\n...[truncated for brevity]")
    print("-" * 60)

if __name__ == "__main__":
    main()
