import asyncio, os, sys

# make `import app` work no matter where you launch from
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows consoles default to cp1252 and choke on non-ASCII — force UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from app.agent import build_agent, reply

USER = "local-test-user"  # fixed id so history persists across turns


async def main():
    build_agent()
    args = sys.argv[1:]
    if args:
        print("Bot:", await reply(USER, " ".join(args)))
    else:
        print("Type a message (or 'quit'):")
        while True:
            msg = input("You: ").strip()
            if msg.lower() in {"quit", "exit", "q"}:
                break
            if msg:
                print("Bot:", await reply(USER, msg), "\n")


if __name__ == "__main__":
    asyncio.run(main())