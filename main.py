from fastapi import FastAPI, Header, Response
from pydantic import BaseModel
from loguru import logger
import logfire
from enum import Enum



started_request_counter = logfire.metric_counter("started_request_counter")
finished_request_counter = logfire.metric_counter("finished_request_counter")


logfire.configure(send_to_logfire=False)
logfire.instrument_pydantic()
# logfire.instrument_httpx()
logfire.info("Logging is configured.")
logger.configure(handlers=[logfire.loguru_handler()])


class ResponseModel(BaseModel):
    message: str


app = FastAPI()
logfire.instrument_fastapi(app)


@app.get("/", response_model=ResponseModel)
def read_root(trace_id: str | None = Header(default=None, alias="X-Trace-Id")):
    with logfire.span("This is a span") as span:
        started_request_counter.add(1)
        logger.info(f"Received request with Trace ID: {trace_id}")
        logfire.info("Logfire logs are also actually just spans!")
        logger.debug("Debugging information here.")
        finished_request_counter.add(1)
    return ResponseModel(message="Hello, World!")


@app.get("/health")
def health_check():
    return Response(status_code=200)


def main():
    print("Hello from python-observability!")


if __name__ == "__main__":
    main()
