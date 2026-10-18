import logging

def configure_logging(level="INFO"):
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(name)s job=%(job_id)s %(message)s" if False else "%(asctime)s %(levelname)s %(name)s %(message)s")
