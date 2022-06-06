import logging

import debugpy

# Initialize logger
logging.basicConfig(
    format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO
)
LOGGER = logging.getLogger(__name__)


LOGGER.info("Waiting for debugger to attach...")
debugpy.listen(("0.0.0.0", 8999))
debugpy.wait_for_client()

# Disable lint as we need to attach the debugger before running the script
from service.app import app, run  # noqa # isort:skip

# If use_reloader is set to True, the debugger will try to connect twice to the ports and will crash
run(app, use_reloader=False)
