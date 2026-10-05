"""
Interactive CLI Chat with Real-Time Token & Financial Audit.
Supports:
1. Simple Mode: Clean, fast conversation (no audit clutter).
2. Audit Mode (--audit true): Real-time token counts, rates, and turn-by-turn financial breakdown.
"""

import os
import sys
import argparse
import warnings
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

warnings.filterwarnings("ignore")
load_dotenv(override=True)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.rule import Rule
from rich import box

console = Console(force_terminal=True, legacy_windows=False)

# ---------------------------------------------------------------------------
# Official Dynamic Pricing Catalog (Per 1 Million Tokens in USD)
# ---------------------------------------------------------------------------
MODEL_PRICING_CATALOG = {
    "flash-lite": {
        "name": "Gemini Flash-Lite Tier",
        "standard": {"input": 0.0375, "output": 0.150},
        "over_128k": {"input": 0.0750, "output": 0.300},
    },
    "flash": {
        "name": "Gemini Flash Tier",
        "standard": {"input": 0.0750, "output": 0.300},
        "over_128k": {"input": 0.1500, "output": 0.600},
    },
    "pro": {
        "name": "Gemini Pro Tier",
        "standard": {"input": 1.2500, "output": 5.000},
        "over_128k": {"input": 2.5000, "output": 10.000},
    },
    "default": {
        "name": "Gemini Standard Tier",
        "standard": {"input": 0.0750, "output": 0.300},
        "over_128k": {"input": 0.1500, "output": 0.600},
    },
}

EXCHANGE_RATE_USD_INR = 86.00

def resolve_model_rates(model_id: str, input_token_count: int = 0) -> tuple[float, float, str, str]:
    clean_id = model_id.lower().replace("models/", "")

    if "flash-lite" in clean_id or "lite" in clean_id:
        tier_key = "flash-lite"
    elif "pro" in clean_id:
        tier_key = "pro"
    elif "flash" in clean_id:
        tier_key = "flash"
    else:
        tier_key = "default"

    tier_info = MODEL_PRICING_CATALOG[tier_key]
    is_long_context = input_token_count > 128_000
    bracket_key = "over_128k" if is_long_context else "standard"
    rates = tier_info[bracket_key]

    bracket_label = ">128k tokens" if is_long_context else "<=128k tokens"
    return rates["input"], rates["output"], tier_info["name"], bracket_label


def display_header(model_id: str, show_audit: bool):
    """Renders the top banner depending on whether audit mode is enabled."""
    rate_in, rate_out, tier_name, bracket = resolve_model_rates(model_id, 0)
    in_inr = rate_in * EXCHANGE_RATE_USD_INR
    out_inr = rate_out * EXCHANGE_RATE_USD_INR

    if show_audit:
        # Full Audit Header with rates and settings
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan", expand=True)
        table.add_column("Parameter", style="dim", width=22)
        table.add_column("Configured Value / Rate", style="bold white")

        table.add_row("🤖 Active Model", f"[bold green]{model_id}[/bold green] ({tier_name})")
        table.add_row("📊 Pricing Bracket", f"{bracket} (Context Window)")
        table.add_row(
            "📥 Input Rate",
            f"${rate_in:.4f} / 1M tokens  [dim cyan](₹{in_inr:.2f} INR)[/dim cyan]"
        )
        table.add_row(
            "📤 Output Rate",
            f"${rate_out:.4f} / 1M tokens [dim cyan](₹{out_inr:.2f} INR)[/dim cyan]"
        )
        table.add_row("💱 Exchange Rate", f"1 USD = ₹{EXCHANGE_RATE_USD_INR:.2f} INR")
        table.add_row("🔍 Audit Mode", "[bold green]ENABLED (Real-time Token & Cost Audit)[/bold green]")

        console.print(Panel(
            table,
            title="[bold magenta]⚡ GEMINI CLI CHAT & FINANCIAL AUDITOR ⚡[/bold magenta]",
            border_style="bright_blue"
        ))
        console.print("[dim]Commands: [bold cyan]exit[/bold cyan] to quit | [bold cyan]clear[/bold cyan] to reset memory | [bold cyan]audit[/bold cyan] to toggle off audit[/dim]\n")
    else:
        # Simple, clean, minimalist header
        panel_content = (
            f"[bold green]Model:[/bold green] [white]{model_id}[/white] | "
            f"[dim]Mode: Simple Chat | Type [bold cyan]'audit'[/bold cyan] to enable cost audit | [bold cyan]'exit'[/bold cyan] to quit[/dim]"
        )
        console.print(Panel(panel_content, border_style="cyan", box=box.ROUNDED))
        console.print("")


def display_turn_audit(
    turn_num: int,
    total_prompt_tokens: int,
    candidate_tokens: int,
    thoughts_tokens: int,
    total_turn_tokens: int,
    rate_in: float,
    rate_out: float,
    session_totals: dict
):
    """Renders a beautiful financial audit table for the current turn."""
    cost_prompt_usd = (total_prompt_tokens / 1_000_000) * rate_in
    billable_output_tokens = candidate_tokens + thoughts_tokens
    cost_output_usd = (billable_output_tokens / 1_000_000) * rate_out
    
    turn_total_usd = cost_prompt_usd + cost_output_usd
    turn_total_inr = turn_total_usd * EXCHANGE_RATE_USD_INR
    turn_paise = turn_total_inr * 100

    session_totals["total_tokens"] += total_turn_tokens
    session_totals["total_cost_usd"] += turn_total_usd
    session_totals["total_cost_inr"] += turn_total_inr
    session_totals["turns"] += 1

    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold yellow", expand=True)
    table.add_column("Token Metric", style="cyan", width=28)
    table.add_column("Tokens Count", justify="right", style="bold white", width=15)
    table.add_column("Cost (USD)", justify="right", style="green", width=16)
    table.add_column("Cost (INR)", justify="right", style="bold green", width=22)

    table.add_row(
        "📥 Input Prompt Tokens",
        f"{total_prompt_tokens:,}",
        f"${cost_prompt_usd:.7f}",
        f"₹{cost_prompt_usd * EXCHANGE_RATE_USD_INR:.4f} ({cost_prompt_usd * EXCHANGE_RATE_USD_INR * 100:.2f}p)"
    )
    table.add_row(
        "📤 Candidate Output Tokens",
        f"{candidate_tokens:,}",
        f"${(candidate_tokens / 1_000_000) * rate_out:.7f}",
        f"₹{(candidate_tokens / 1_000_000) * rate_out * EXCHANGE_RATE_USD_INR:.4f}"
    )

    if thoughts_tokens > 0:
        table.add_row(
            "🧠 Thinking / Reasoning Tokens",
            f"{thoughts_tokens:,}",
            f"${(thoughts_tokens / 1_000_000) * rate_out:.7f}",
            f"₹{(thoughts_tokens / 1_000_000) * rate_out * EXCHANGE_RATE_USD_INR:.4f}"
        )

    table.add_section()
    table.add_row(
        "[bold white]⚡ Turn Total Consumed[/bold white]",
        f"[bold white]{total_turn_tokens:,}[/bold white]",
        f"[bold green]${turn_total_usd:.6f}[/bold green]",
        f"[bold yellow]₹{turn_total_inr:.4f} ({turn_paise:.2f} paise)[/bold yellow]"
    )
    table.add_row(
        "[bold cyan]📈 Cumulative Session Cost[/bold cyan]",
        f"[dim]{session_totals['total_tokens']:,} tokens[/dim]",
        f"[bold cyan]${session_totals['total_cost_usd']:.6f}[/bold cyan]",
        f"[bold cyan]₹{session_totals['total_cost_inr']:.4f} ({session_totals['total_cost_inr'] * 100:.2f} paise)[/bold cyan]"
    )

    console.print(Panel(
        table,
        title=f"[bold yellow]💰 FINANCIAL AUDIT (Turn #{turn_num})[/bold yellow]",
        border_style="yellow",
        box=box.ROUNDED
    ))


def display_session_summary(session_totals: dict):
    """Renders final session totals when user exits."""
    table = Table(box=box.DOUBLE_EDGE, show_header=True, header_style="bold magenta", expand=True)
    table.add_column("Session Summary Metric", style="bold white")
    table.add_column("Session Total", justify="right", style="bold green")

    table.add_row("Total Interaction Turns", str(session_totals["turns"]))
    table.add_row("Total Consumed Tokens", f"{session_totals['total_tokens']:,} tokens")
    table.add_row("Total Session Cost (USD)", f"${session_totals['total_cost_usd']:.6f}")
    table.add_row(
        "Total Session Cost (INR)",
        f"₹{session_totals['total_cost_inr']:.4f} ({session_totals['total_cost_inr'] * 100:.2f} paise)"
    )

    console.print("\n")
    console.print(Panel(table, title="[bold green]🏁 FINAL CHAT FINANCIAL AUDIT REPORT[/bold green]", border_style="green"))
    console.print("[dim italic]Session closed.[/dim italic]\n")


def main():
    parser = argparse.ArgumentParser(description="Gemini Interactive CLI Chat & Financial Auditor")
    parser.add_argument("--model", default="gemini-3.5-flash", help="Gemini Model ID (default: gemini-3.5-flash)")
    parser.add_argument(
        "--audit",
        type=str,
        default="true",
        help="Enable audit mode (true/false, default: true)"
    )
    args = parser.parse_args()

    show_audit = args.audit.strip().lower() in ("true", "1", "yes", "y")
    model_id = args.model

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if not api_key or api_key == "your_key_here":
        console.print("[bold red]❌ Error:[/bold red] Valid [cyan]GOOGLE_API_KEY[/cyan] not found in .env or environment.")
        console.print("Please set your API key in [.env](file:///.env):")
        console.print("  GOOGLE_API_KEY=your_gemini_api_key\n")
        sys.exit(1)

    from google import genai
    from google.genai import errors

    client = genai.Client(api_key=api_key)

    display_header(model_id, show_audit)

    # Initialize stateful multi-turn chat
    chat = client.chats.create(model=model_id)

    session_totals = {
        "turns": 0,
        "total_tokens": 0,
        "total_cost_usd": 0.0,
        "total_cost_inr": 0.0,
    }

    turn_counter = 0

    while True:
        try:
            console.print("[bold cyan]You[/bold cyan] [dim]>[/dim] ", end="")
            user_input = input().strip()

            if not user_input:
                continue

            # Command Handlers
            if user_input.lower() in ("exit", "quit", "q"):
                if show_audit and session_totals["turns"] > 0:
                    display_session_summary(session_totals)
                else:
                    console.print("[dim]Goodbye![/dim]\n")
                break

            if user_input.lower() == "clear":
                chat = client.chats.create(model=model_id)
                console.clear()
                display_header(model_id, show_audit)
                console.print("[bold green]🧹 Chat history cleared.[/bold green]\n")
                continue

            if user_input.lower() == "audit":
                show_audit = not show_audit
                status_str = "ENABLED" if show_audit else "DISABLED"
                console.print(f"[bold yellow]🔄 Audit mode is now {status_str}.[/bold yellow]\n")
                continue

            turn_counter += 1

            # 1. Pre-flight Question Token & Cost Estimation
            try:
                user_tokens_est = client.models.count_tokens(model=model_id, contents=user_input).total_tokens
            except Exception:
                user_tokens_est = len(user_input) // 4

            rate_in, rate_out, _, _ = resolve_model_rates(model_id, user_tokens_est)
            quick_in_cost_inr = (user_tokens_est / 1_000_000) * rate_in * EXCHANGE_RATE_USD_INR

            if show_audit:
                console.print(
                    f"  [dim cyan]↳ Prompt Tokens: [bold]{user_tokens_est}[/bold] | "
                    f"Est. Question Cost: [bold yellow]₹{quick_in_cost_inr:.5f}[/bold yellow] ({quick_in_cost_inr * 100:.3f} paise)[/dim cyan]"
                )

            # 2. Execute Model Inference
            console.print("\n[bold green]Gemini[/bold green] [dim]>[/dim] ", end="")
            
            with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
                response = chat.send_message(user_input)

            # Display response with Markdown syntax highlighting
            console.print(Markdown(response.text))
            console.print("")

            # 3. Post-execution Metadata Audit
            meta = response.usage_metadata
            actual_prompt_tokens = meta.prompt_token_count
            candidate_tokens = meta.candidates_token_count
            thoughts_tokens = getattr(meta, "thoughts_token_count", 0) or 0
            total_turn_tokens = meta.total_token_count

            if show_audit:
                display_turn_audit(
                    turn_num=turn_counter,
                    total_prompt_tokens=actual_prompt_tokens,
                    candidate_tokens=candidate_tokens,
                    thoughts_tokens=thoughts_tokens,
                    total_turn_tokens=total_turn_tokens,
                    rate_in=rate_in,
                    rate_out=rate_out,
                    session_totals=session_totals,
                )

            console.print(Rule(style="dim"))

        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]Chat interrupted by user.[/bold yellow]")
            if show_audit and session_totals["turns"] > 0:
                display_session_summary(session_totals)
            break
        except errors.ServerError as e:
            console.print(f"\n[bold red]⚠️ Google Server Error ({e.code}):[/bold red] {e.message}")
            console.print("[dim]Google server busy. Please try again.[/dim]\n")
        except errors.ClientError as e:
            console.print(f"\n[bold red]❌ API Error ({e.code}):[/bold red] {e.message}\n")
        except Exception as e:
            console.print(f"\n[bold red]❌ Error:[/bold red] {e}\n")


if __name__ == "__main__":
    main()
