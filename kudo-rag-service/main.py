import sys
import logging
from pathlib import Path

# Ensure project root directory is added to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from interfaces.discord_bot.bot import bot
from interfaces.discord_bot.handlers import setup_bot_handlers

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("kudo-rag-service")


def main() -> None:
    """
    Main entrypoint for the kudo-rag-service application.
    """
    logger.info("Initializing kudo-rag-service Discord Bot...")

    if not settings.DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN is missing in environment variables or .env configuration.")
        print("❌ Error: DISCORD_TOKEN is not configured in .env file.")
        sys.exit(1)

    # Register bot handlers (on_ready, on_message)
    setup_bot_handlers(bot)

    # Run the Discord Bot
    try:
        logger.info("Connecting to Discord Gateway...")
        bot.run(settings.DISCORD_TOKEN)
    except Exception as e:
        logger.critical(f"Fatal error starting Discord bot: {e}", exc_info=True)


if __name__ == "__main__":
    main()
