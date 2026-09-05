import logging
import time

from worker.tts import DummyTtsProvider

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("smartlearn.worker")


def run_once() -> None:
    provider = DummyTtsProvider()
    result = provider.synthesize("SmartLearn worker mock narration.", "/tmp")
    logger.info("worker_tick narration_available=%s", result.narration_available)


def main() -> None:
    logger.info("SmartLearn worker started in mock mode")
    while True:
        run_once()
        time.sleep(5)


if __name__ == "__main__":
    main()
