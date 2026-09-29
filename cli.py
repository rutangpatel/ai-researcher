import asyncio
import os
import shutil

from dotenv import load_dotenv

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from prompt_toolkit.lexers import SimpleLexer

from rich.console import Console
from rich.markdown import Markdown
import warnings
from langchain_core._api import LangChainBetaWarning

warnings.filterwarnings("ignore", category=LangChainBetaWarning)

from main import run_research as graph_run_research


load_dotenv()

FOREGROUND = "#DCD7BA"
MAIN = "#DCA561"
SECONDARY = "#7E9CD8"
GREEN = "#98BB6C"
RED = "#E82424"
DIM = "#727169"

style = Style.from_dict({
    "": f"fg:{FOREGROUND}",
    "prompt": f"fg:{SECONDARY} bold",
    "box": f"fg:{MAIN}",
    "question": f"fg:{FOREGROUND} bold",
    "dim": f"fg:{DIM}",
    "banner": f"fg:{SECONDARY} bold",
    "success": f"fg:{GREEN}",
    "error": f"fg:{RED}",
    "footer": f"fg:{DIM}",
    "footer.model": f"fg:{SECONDARY}",
})

BANNER_LINES = [
    "██████╗  ██████╗  ██████╗  ██████╗   █████╗  ████████  ███████╗ ██████╗",
    "██╔══██╗ ██╔══██╗ ██╔══██╗ ██╔══██╗ ██╔══██╗ ╚══██╔══  ██╔════╝ ██╔══██╗",
    "██╔═══╝  ██║  ██║ ██║ ╚═╝  ██████╔╝ ███████║    ██║    █████╗   ██╔═══╝",
    "╚█████╗  ██║  ██║ ██║      ██╔══██╗ ██╔══██║    ██║    ██╔══╝   ╚█████╗",
    " ░╚══██╗ ██║  ██║ ██║      ██║  ██║ ██║  ██║    ██║    ██║       ░╚══██╗",
    "██████╔╝ ╚█████╔╝ ╚█████╗  ██║  ██║ ██║  ██║    ██║    ███████╗ ██████╔╝",
    "╚═════╝  ╚═════╝  ╚═════╝  ╚═╝  ╚═╝ ╚═╝  ╚═╝    ╚═╝    ╚══════╝ ╚═════╝",
]

console = Console()

session = PromptSession(
    style=style,
    lexer=SimpleLexer(style="class:question"),
)


PROVIDER_MODEL_VAR = {
    "openai": ("OPENAI_MODEL", "OPENAI_SMALLER_MODEL"),
    "gemini": ("GEMINI_MODEL", "GEMINI_SMALLER_MODEL"),
    "groq": ("GROQ_MODEL", "GROQ_SMALLER_MODEL"),
}


def get_active_model() -> str:
    provider = os.environ.get("MODEL_PROVIDER", "").strip().lower()

    if provider in PROVIDER_MODEL_VAR:
        model_var, smaller_var = PROVIDER_MODEL_VAR[provider]
        model = os.environ.get(model_var)
        smaller = os.environ.get(smaller_var)
        if not model:
            return f"{provider}: model not set"
        if smaller and smaller != model:
            return f"{model} | {smaller}"
        return model

    for model_var, smaller_var in PROVIDER_MODEL_VAR.values():
        model = os.environ.get(model_var)
        if model:
            smaller = os.environ.get(smaller_var)
            if smaller and smaller != model:
                return f"{model} | {smaller}"
            return model

    return "no model configured"


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def term_width() -> int:
    width = console.width or shutil.get_terminal_size((80, 24)).columns
    return max(20, width - 2)


def render_header() -> None:
    width = term_width()
    banner_width = max(len(line) for line in BANNER_LINES)

    if width < banner_width + 2:
        console.print(f"[bold {MAIN}]{'SOCRATES':^{width}}[/]")
    else:
        for line in BANNER_LINES:
            console.print(f"[bold {MAIN}]  {line}[/]")
    console.print()


def render_top_border() -> None:
    width = term_width()
    console.print(f"[{MAIN}]╭{'─' * width}╮[/]")


def render_bottom_border() -> None:
    width = term_width()
    model = get_active_model()
    available_label_width = max(1, width - 3)
    if len(model) > available_label_width:
        model = f"{model[:max(1, available_label_width - 3)]}..."

    label = f" {model} "
    dashes_after = max(1, width - len(label) - 1)
    console.print(f"[{MAIN}]╰─[/][{SECONDARY}]{label}[/][{MAIN}]{'─' * dashes_after}╯[/]")


async def run_research(question: str) -> str:
    updates = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def stream_graph() -> None:
        try:
            for chunk in graph_run_research(question):
                loop.call_soon_threadsafe(
                    updates.put_nowait,
                    ("update", chunk),
                )
        except Exception as exc:
            loop.call_soon_threadsafe(
                updates.put_nowait,
                ("error", exc),
            )
        finally:
            loop.call_soon_threadsafe(
                updates.put_nowait,
                ("done", None),
            )

    graph_task = asyncio.create_task(
        asyncio.to_thread(stream_graph)
    )

    stage_messages = {
        "read_memory": "Checking memory...",
        "classifier": "Choosing how to answer...",
        "memory": "Answering from memory...",
        "chat": "Thinking...",
        "planner": "Planning research...",
        "researcher": "Researching...",
        "tools": "Searching the web...",
        "summarizer": "Summarizing...",
        "save_memory": "Saving memory...",
    }
    summary = None

    try:
        with console.status(
            f"[{DIM}]Checking memory...[/]",
            spinner="dots",
            speed=1.2,
        ) as status:
            while True:
                event, payload = await updates.get()

                if event == "error":
                    raise payload

                if event == "done":
                    break

                for node, values in payload.items():
                    if node in stage_messages:
                        status.update(
                            f"[{DIM}]{stage_messages[node]}[/]"
                        )

                    # memory, chat and summarizer nodes all produce the final answer
                    if node in {"memory", "chat", "summarizer"}:
                        summary = values.get("summary")
    finally:
        await graph_task

    if summary is None:
        raise RuntimeError("The graph returned no answer.")

    return summary


def is_exit_command(text: str) -> bool:
    return text.lower().strip() in {"exit", "quit", "/exit", "/quit"}


def is_help_command(text: str) -> bool:
    return text.lower().strip() in {"help", "/help"}


def show_help() -> None:
    console.print()
    console.print(f"[{GREEN}]Commands[/]")
    console.print(f"[{DIM}]  /help     Show this help[/]")
    console.print(f"[{DIM}]  /exit     Exit Socrates[/]")
    console.print()


async def main_async() -> None:

    clear_screen()
    render_header()

    while True:

        render_top_border()

        try:
            question = await session.prompt_async(
                FormattedText([("class:box", "│ "), ("class:prompt", "› ")]),
            )
        except (KeyboardInterrupt, EOFError):
            render_bottom_border()
            break

        render_bottom_border()

        question = question.strip()
        if not question:
            continue

        if is_exit_command(question):
            break

        if is_help_command(question):
            show_help()
            continue

        try:
            result = await run_research(question)

            console.print()
            console.print(Markdown(result))
            console.print()

        except Exception as exc:
            console.print()
            console.print(f"[{RED}]That question failed: {exc}[/]")
            console.print()

    console.print()
    console.print(f"[{DIM}]  Bye![/]")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()