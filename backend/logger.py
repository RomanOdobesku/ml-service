import logging
import sys

LOGGER = logging.getLogger("logger")
LOGGER.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter("%(levelname)s %(asctime)s - %(message)s"))
LOGGER.addHandler(handler)