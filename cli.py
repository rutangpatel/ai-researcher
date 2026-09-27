import asyncio
import os
import shutil

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.lexers import SimpleLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout

from main import run_research

BG = "#2b2b33"
TEXT = "#d4d4d8"
YELLOW = "#e5c07b"
DIM = "#71717a"
ACCENT = "#61afef"
BLUE = "#61afef"

style = Style.from_dict({
    "": f"bg:{BG} fg:{TEXT}",
    "prompt": f"bg:{BG} fg:{ACCENT} bold",
    "question": f"bg:{BG} fg:{YELLOW} bold",
    "dim": f"bg:{BG} fg:{DIM}",
    "banner": f"bg:{BG} fg:{BLUE} bold",
})

BANNER_LINES = [
    "██████╗  ██████╗  ██████╗  ██████╗   █████╗  ████████ ███████╗ ██████╗",
    "██╔══██╗ ██╔══██╗ ██╔══██╗ ██╔══██╗ ██╔══██╗ ╚══██╔══ ██╔════╝ ██╔══██╗",
    "██╔═══╝  ██║  ██║ ██║ ╚═╝  ██████╔╝ ███████║   ██║    █████╗   ██╔═══╝",
    "╚█████╗  ██║  ██║ ██║      ██╔══██╗ ██╔══██║   ██║    ██╔══╝   ╚█████╗",
    " ░╚══██╗ ██║  ██║ ██║      ██║  ██║ ██║  ██║   ██║    ██║       ░╚══██╗",
    "██████╔╝ ╚█████╔╝ ╚█████╗  ██║  ██║ ██║  ██║   ██║    ███████╗ ██████╔╝",
    "╚═════╝  ╚═════╝  ╚═════╝  ╚═╝  ╚═╝ ╚═╝  ╚═╝   ╚═╝    ╚══════╝ ╚═════╝",
]

session = PromptSession(
    style=style,
    # Colors the live input text itself as you type, so the finished
    # line is already yellow when Enter is pressed.
    lexer=SimpleLexer(style="class:question"),
)


def clear_screen() -> None:
    """Clear the terminal from inside the script -- no need to run `clear` first."""
    os.system("cls" if os.name == "nt" else "clear")


def set_block_cursor() -> None:
    print("\x1b[2 q", end="", flush=True)  # steady block cursor


def reset_cursor() -> None:
    print("\x1b[0 q", end="", flush=True)  # restore the terminal's default cursor


def erase_lines(count: int) -> None:
    """Move up `count` rows, clearing each -- used to make the
    blank/'Researching...'/blank block vanish before the answer prints."""
    for _ in range(count):
        print("\x1b[1A\x1b[2K", end="", flush=True)


def term_width() -> int:
    return shutil.get_terminal_size((80, 24)).columns


def emit(text: str = "", cls: str = "") -> None:
    pad = text.ljust(term_width())
    frag_class = f"class:{cls}" if cls else "class:"
    print_formatted_text(FormattedText([(frag_class, pad)]), style=style)


def emit_centered(text: str, cls: str = "") -> None:
    pad = max((term_width() - len(text)) // 2, 0)
    emit(" " * pad + text, cls=cls)


def emit_blank() -> None:
    emit()


def render_header() -> None:
    for line in BANNER_LINES:
        emit(f"  {line}", cls="banner")
    emit_blank()
    emit("─" * term_width(), cls="dim")
    emit_blank()


def render_result(result: str) -> None:
    for line in result.split("\n"):
        emit(f"  {line}")
    emit_blank()


def make_research_key_bindings(research_done: asyncio.Event) -> KeyBindings:
    """Keep the next-question box editable, but block Enter until research finishes."""
    bindings = KeyBindings()

    @bindings.add("enter", eager=True)
    def _(event) -> None:
        # Typing is always allowed. While research is running, Enter simply does
        # nothing, so the text stays in the prompt buffer instead of being queued.
        if research_done.is_set():
            event.current_buffer.validate_and_handle()

    return bindings


async def do_research(question: str, research_done: asyncio.Event) -> str:
    """Run research in the executor and signal when the answer is ready."""
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, run_research, question)
    except Exception as exc:  # keep the app alive even if research blows up
        return f"Error: {exc}"
    finally:
        research_done.set()

async def main_async() -> None:
    clear_screen()
    set_block_cursor()
    try:
        render_header()

        while True:
            try:
                question = (
                    await session.prompt_async(FormattedText([("class:prompt", "› ")]))
                ).strip()
            except (KeyboardInterrupt, EOFError):
                break

            if not question:
                continue
            if question.lower() in ("exit", "quit", "/exit", "/quit"):
                break

            # Keep the next question prompt alive while the current research
            # runs. The user can type normally, but Enter is disabled until the
            # current answer is ready. This is not a queue: the text simply stays
            # in the prompt buffer until the user submits it.
            research_done = asyncio.Event()

            emit_blank()
            emit("Researching...", cls="dim")
            emit_blank()

            research_task = asyncio.create_task(
                do_research(question, research_done)
            )

            # The prompt is active at the same time as research. This means the
            # user can type the next question and actually see it. Enter is still
            # blocked until research_done is set.
            input_task = asyncio.create_task(
                session.prompt_async(
                    FormattedText([("class:prompt", "› ")]),
                    key_bindings=make_research_key_bindings(research_done),
                )
            )

            try:
                # As soon as the answer is ready, print it above the still-active
                # prompt. patch_stdout makes prompt_toolkit redraw the typed text
                # instead of letting the answer overwrite it.
                with patch_stdout():
                    result = await research_task
                    render_result(result)

                next_question = await input_task
            except (KeyboardInterrupt, EOFError):
                research_task.cancel()
                input_task.cancel()
                raise

            question = next_question.strip()
            if not question:
                continue
            if question.lower() in ("exit", "quit", "/exit", "/quit"):
                break

        emit_blank()
        emit("  Bye!", cls="dim")
    finally:
        reset_cursor()


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()