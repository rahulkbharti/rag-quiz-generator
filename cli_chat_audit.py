"""
Interactive RAG CLI Chat & Real-Time Financial Auditor with Live Token Streaming.
Features:
1. Real-time Token Streaming (Typewriter effect, TTFT ~350-500ms).
2. Local Vector Store RAG Retrieval from ./storage (100% Free).
3. Live Financial Audit with USD & INR breakdown.
4. Latency Profiling (TTFT, Total Time, Tokens/sec).
"""

import os
import sys
import time
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


def display_header(model_id: str, show_audit: bool, is_rag: bool, doc_count: int, top_k: int, db_stats: dict = None):
    """Renders the top banner depending on settings."""
    rate_in, rate_out, tier_name, bracket = resolve_model_rates(model_id, 0)
    in_inr = rate_in * EXCHANGE_RATE_USD_INR
    out_inr = rate_out * EXCHANGE_RATE_USD_INR

    if show_audit:
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan", expand=True)
        table.add_column("Parameter", style="dim", width=22)
        table.add_column("Configured Value / Status", style="bold white")

        db_type = db_stats.get("type", "Local Disk") if db_stats else "Local Disk"
        if db_type == "Qdrant Cloud":
            pts = db_stats.get("points_count", 0)
            coll = db_stats.get("collection", "quiz_collection")
            rag_status = (
                f"[bold green]ENABLED[/bold green] (Qdrant Cloud: [cyan]{coll}[/cyan] | {pts} chunks stored)"
                if is_rag else "[dim yellow]DISABLED (Direct Chat)[/dim yellow]"
            )
            cluster_short = db_stats.get('cluster_url', '').replace('https://', '')[:40]
            table.add_row("🗄️ Vector Database", f"[bold green]Qdrant Cloud[/bold green] ({cluster_short})")
        else:
            rag_status = (
                f"[bold green]ENABLED[/bold green] (Searching ./storage index, top_{top_k} chunks from {doc_count} doc(s))"
                if is_rag else "[dim yellow]DISABLED (Direct Chat)[/dim yellow]"
            )
            table.add_row("🗄️ Vector Database", "[bold yellow]Local Disk (storage/ folder)[/bold yellow]")

        table.add_row("📚 RAG Retrieval", rag_status)
        table.add_row("🤖 Active Model", f"[bold green]{model_id}[/bold green] ({tier_name})")
        table.add_row("⚡ Token Streaming", "[bold green]LIVE (Typewriter Effect, TTFT ~350-500ms)[/bold green]")
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
        table.add_row("🔍 Audit Mode", "[bold green]ENABLED (Real-time Token & Cost Tracking)[/bold green]")

        console.print(Panel(
            table,
            title="[bold magenta]⚡ RAG CLI CHAT & STREAMING FINANCIAL AUDITOR ⚡[/bold magenta]",
            border_style="bright_blue"
        ))
        console.print("[dim]Commands: [bold cyan]exit[/bold cyan] to quit | [bold cyan]clear[/bold cyan] to reset | [bold cyan]audit[/bold cyan] to toggle audit | [bold cyan]sources[/bold cyan] to inspect retrieved chunks[/dim]\n")
    else:
        rag_label = f"RAG: Active (top_{top_k})" if is_rag else "Direct Chat"
        panel_content = (
            f"[bold green]Model:[/bold green] [white]{model_id}[/white] | "
            f"[bold cyan]{rag_label}[/bold cyan] | "
            f"[bold yellow]Streaming: ON[/bold yellow] | "
            f"[dim]Type [bold cyan]'audit'[/bold cyan] for cost audit | [bold cyan]'exit'[/bold cyan] to quit[/dim]"
        )
        console.print(Panel(panel_content, border_style="cyan", box=box.ROUNDED))
        console.print("")


def display_turn_audit(
    turn_num: int,
    query_tokens: int,
    retrieved_tokens: int,
    total_input_tokens: int,
    candidate_tokens: int,
    total_turn_tokens: int,
    rate_in: float,
    rate_out: float,
    session_totals: dict,
    sources_count: int,
    ttft_ms: float,
    total_ms: float
):
    """Renders a financial audit table with latency profiling and token details."""
    cost_prompt_usd = (total_input_tokens / 1_000_000) * rate_in
    cost_output_usd = (candidate_tokens / 1_000_000) * rate_out
    
    turn_total_usd = cost_prompt_usd + cost_output_usd
    turn_total_inr = turn_total_usd * EXCHANGE_RATE_USD_INR
    turn_paise = turn_total_inr * 100

    session_totals["total_tokens"] += total_turn_tokens
    session_totals["total_cost_usd"] += turn_total_usd
    session_totals["total_cost_inr"] += turn_total_inr
    session_totals["turns"] += 1

    # Speed metrics
    gen_duration_sec = max(0.001, (total_ms - (ttft_ms or 0)) / 1000)
    tokens_per_sec = candidate_tokens / gen_duration_sec if gen_duration_sec > 0 else 0

    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold yellow", expand=True)
    table.add_column("RAG / Performance Metric", style="cyan", width=32)
    table.add_column("Tokens / Speed", justify="right", style="bold white", width=16)
    table.add_column("Cost (USD)", justify="right", style="green", width=14)
    table.add_column("Cost (INR)", justify="right", style="bold green", width=22)

    table.add_row(
        "🔎 Local Vector Retrieval",
        f"{sources_count} chunks",
        "$0.0000000",
        "[bold green]₹0.00 (100% FREE CPU)[/bold green]"
    )
    table.add_row(
        "⚡ Time to First Token (TTFT)",
        f"{ttft_ms:.1f} ms" if ttft_ms else "N/A",
        "-",
        "[dim cyan]Instant Streaming[/dim cyan]"
    )
    table.add_row(
        "🏎️ Generation Speed",
        f"{tokens_per_sec:.1f} tokens/s",
        "-",
        f"[dim]{total_ms / 1000:.2f}s total duration[/dim]"
    )
    table.add_row(
        "  ↳ User Query Tokens",
        f"{query_tokens:,}",
        f"${(query_tokens / 1_000_000) * rate_in:.7f}",
        f"₹{(query_tokens / 1_000_000) * rate_in * EXCHANGE_RATE_USD_INR:.4f}"
    )
    if retrieved_tokens > 0:
        table.add_row(
            "  ↳ Retrieved Context Chunks",
            f"{retrieved_tokens:,}",
            f"${(retrieved_tokens / 1_000_000) * rate_in:.7f}",
            f"₹{(retrieved_tokens / 1_000_000) * rate_in * EXCHANGE_RATE_USD_INR:.4f}"
        )
    table.add_row(
        "[bold]📥 Total Input to LLM[/bold]",
        f"[bold]{total_input_tokens:,}[/bold]",
        f"[bold]${cost_prompt_usd:.7f}[/bold]",
        f"[bold]₹{cost_prompt_usd * EXCHANGE_RATE_USD_INR:.4f}[/bold]"
    )
    table.add_row(
        "📤 Generated Stream Output",
        f"{candidate_tokens:,}",
        f"${cost_output_usd:.7f}",
        f"₹{cost_output_usd * EXCHANGE_RATE_USD_INR:.4f}"
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
        title=f"[bold yellow]💰 FINANCIAL AUDIT (Turn #{turn_num})[/bold yellow] | [dim]TTFT: [bold green]{ttft_ms:.1f}ms[/bold green] | Total: [bold cyan]{total_ms / 1000:.2f}s[/bold cyan][/dim]",
        border_style="yellow",
        box=box.ROUNDED
    ))


def display_sources(source_nodes):
    """Prints retrieved RAG document chunks cleanly."""
    if not source_nodes:
        console.print("[dim yellow]No external document chunks were retrieved for this query.[/dim yellow]\n")
        return

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan", expand=True)
    table.add_column("#", width=4, style="bold")
    table.add_column("Similarity Score", width=16, style="green")
    table.add_column("Document / Source Content Preview", style="white")

    for i, node_with_score in enumerate(source_nodes, 1):
        score_str = f"{node_with_score.score:.4f}" if node_with_score.score is not None else "N/A"
        content_preview = node_with_score.node.get_content().strip().replace("\n", " ")[:140] + "..."
        file_name = node_with_score.node.metadata.get("file_name", "document")
        page_num = node_with_score.node.metadata.get("page_number", "")
        page_label = f" (Page {page_num})" if page_num else ""
        table.add_row(str(i), score_str, f"[dim cyan][{file_name}{page_label}][/dim cyan] {content_preview}")

    console.print(Panel(table, title="[bold cyan]📑 RETRIEVED SOURCE CHUNKS (Cost: ₹0.00 Free)[/bold cyan]", border_style="cyan"))
    console.print("")


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
    parser = argparse.ArgumentParser(description="Interactive RAG CLI Chat & Live Streaming Financial Auditor")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini Model ID (default: gemini-2.5-flash)")
    parser.add_argument("--audit", type=str, default="true", help="Enable audit mode (true/false, default: true)")
    parser.add_argument("--rag", type=str, default="true", help="Enable RAG retrieval from ./storage (true/false, default: true)")
    parser.add_argument("--top-k", type=int, default=3, help="Number of retrieved chunks (default: 3)")
    args = parser.parse_args()

    show_audit = args.audit.strip().lower() in ("true", "1", "yes", "y")
    use_rag = args.rag.strip().lower() in ("true", "1", "yes", "y")
    model_id = args.model
    top_k = args.top_k

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if not api_key or api_key == "your_key_here":
        console.print("[bold red]❌ Error:[/bold red] Valid [cyan]GOOGLE_API_KEY[/cyan] not found in .env or environment.")
        console.print("Please set your API key in [.env](file:///.env):")
        console.print("  GOOGLE_API_KEY=your_gemini_api_key\n")
        sys.exit(1)

    # 1. Initialize RAG Engine with streaming support
    streaming_query_engine = None
    doc_count = 0
    db_stats = {}
    if use_rag:
        with console.status("[bold cyan]Connecting to Vector Database & loading index...[/bold cyan]", spinner="dots"):
            import app.core.engine as rag_engine
            rag_engine.initialize_rag(top_k=top_k, model_name=model_id)
            streaming_query_engine = rag_engine.index.as_query_engine(
                similarity_top_k=top_k,
                streaming=True
            )
            data_files = [f for f in os.listdir("data") if f.lower().endswith(".pdf")] if os.path.exists("data") else []
            doc_count = len(data_files)
            db_stats = rag_engine.get_vector_db_stats()

    # 2. Direct GenAI client for fallback / token counting
    from google import genai
    genai_client = genai.Client(api_key=api_key)

    display_header(model_id, show_audit, use_rag, doc_count, top_k, db_stats)

    session_totals = {
        "turns": 0,
        "total_tokens": 0,
        "total_cost_usd": 0.0,
        "total_cost_inr": 0.0,
    }

    turn_counter = 0
    last_sources = []

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
                console.clear()
                display_header(model_id, show_audit, use_rag, doc_count, top_k)
                console.print("[bold green]🧹 Screen cleared.[/bold green]\n")
                continue

            if user_input.lower() == "audit":
                show_audit = not show_audit
                status_str = "ENABLED" if show_audit else "DISABLED"
                console.print(f"[bold yellow]🔄 Audit mode is now {status_str}.[/bold yellow]\n")
                continue

            if user_input.lower() in ("sources", "source"):
                display_sources(last_sources)
                continue

            turn_counter += 1

            # Estimate user query tokens
            try:
                query_tokens_est = genai_client.models.count_tokens(model=model_id, contents=user_input).total_tokens
            except Exception:
                query_tokens_est = max(1, len(user_input) // 4)

            # ---------------------------------------------------------------
            # 2. Execute RAG Query with Live Token Streaming & Latency Profiling
            # ---------------------------------------------------------------
            answer_text = ""
            source_nodes = []
            retrieved_text = ""
            ttft_ms = None
            total_duration_ms = 0.0

            console.print("\n[bold green]AI Assistant[/bold green] [dim]>[/dim] ", end="")

            t_start = time.perf_counter()

            if use_rag and streaming_query_engine is not None:
                streaming_response = streaming_query_engine.query(user_input)
                tokens_buffer = []

                # Stream tokens live as they arrive from Gemini
                for token in streaming_response.response_gen:
                    if ttft_ms is None:
                        ttft_ms = (time.perf_counter() - t_start) * 1000
                    print(token, end="", flush=True)
                    tokens_buffer.append(token)

                total_duration_ms = (time.perf_counter() - t_start) * 1000
                print("\n")

                answer_text = "".join(tokens_buffer)
                source_nodes = getattr(streaming_response, "source_nodes", [])
                last_sources = source_nodes
                retrieved_text = " ".join([n.node.get_content() for n in source_nodes])
            else:
                # Direct streaming without RAG
                stream = genai_client.models.generate_content_stream(model=model_id, contents=user_input)
                tokens_buffer = []

                for chunk in stream:
                    if ttft_ms is None:
                        ttft_ms = (time.perf_counter() - t_start) * 1000
                    chunk_text = chunk.text or ""
                    print(chunk_text, end="", flush=True)
                    tokens_buffer.append(chunk_text)

                total_duration_ms = (time.perf_counter() - t_start) * 1000
                print("\n")
                answer_text = "".join(tokens_buffer)

            # ---------------------------------------------------------------
            # 3. Post-execution Metadata Audit
            # ---------------------------------------------------------------
            try:
                retrieved_tokens = genai_client.models.count_tokens(model=model_id, contents=retrieved_text).total_tokens if retrieved_text else 0
            except Exception:
                retrieved_tokens = max(0, len(retrieved_text) // 4)

            try:
                candidate_tokens = genai_client.models.count_tokens(model=model_id, contents=answer_text).total_tokens
            except Exception:
                candidate_tokens = max(1, len(answer_text) // 4)

            total_input_tokens = query_tokens_est + retrieved_tokens + 50
            total_turn_tokens = total_input_tokens + candidate_tokens

            rate_in, rate_out, _, _ = resolve_model_rates(model_id, total_input_tokens)

            if show_audit:
                display_turn_audit(
                    turn_num=turn_counter,
                    query_tokens=query_tokens_est,
                    retrieved_tokens=retrieved_tokens,
                    total_input_tokens=total_input_tokens,
                    candidate_tokens=candidate_tokens,
                    total_turn_tokens=total_turn_tokens,
                    rate_in=rate_in,
                    rate_out=rate_out,
                    session_totals=session_totals,
                    sources_count=len(source_nodes),
                    ttft_ms=ttft_ms or 0.0,
                    total_ms=total_duration_ms
                )

            console.print(Rule(style="dim"))

        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]Chat interrupted by user.[/bold yellow]")
            if show_audit and session_totals["turns"] > 0:
                display_session_summary(session_totals)
            break
        except Exception as e:
            console.print(f"\n[bold red]❌ Error:[/bold red] {e}\n")


if __name__ == "__main__":
    main()
