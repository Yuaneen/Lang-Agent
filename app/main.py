from __future__ import annotations

from app.agent import run_agent


def main() -> None:
    while True:
        try:
            line = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in ("exit", "quit", "q"):
            break
        try:
            reply = run_agent(line)
        except Exception as e:
            print(f"Error: {e}\n")
            continue
        print(f"AI: {reply}\n")


if __name__ == "__main__":
    main()
