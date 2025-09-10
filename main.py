from fastapi import FastAPI, Header, Response, Request
from pydantic import BaseModel
from loguru import logger
import logfire
from asyncio import sleep
import openai



started_request_counter = logfire.metric_counter("started_request_counter")
finished_request_counter = logfire.metric_counter("finished_request_counter")


logfire.configure(send_to_logfire=False)
logfire.instrument_pydantic()
logfire.instrument_openai()
# logfire.instrument_httpx()
logfire.info("Logging is configured.")
logger.configure(handlers=[logfire.loguru_handler()])


class ResponseModel(BaseModel):
    message: str


app = FastAPI()
# OTEL_PYTHON_FASTAPI_EXCLUDED_URLS
logfire.instrument_fastapi(app, excluded_urls=["/health"], capture_headers=True)



@app.middleware("http")
async def set_baggage(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID")
    user_id = request.headers.get("X-UserID")
    with logfire.set_baggage(correlation_id=correlation_id, user_id=user_id):
        response = await call_next(request)
    return response




@app.get("/", response_model=ResponseModel)
async def read_root(
    cor_id: str | None = Header(default=None, alias="X-Correlation-ID"),
    user_id: str | None = Header(default=None, alias="X-UserID"),
    ) -> ResponseModel:
    with logfire.span("This is the root span"), logger.contextualize(correlation_id=cor_id, user_id=user_id):
        with logfire.span("This is a span number 1") as span:
            span.set_attribute("custom_attribute", "my_value")
            logger.info(f"Baggage: {logfire.get_baggage()}")
            started_request_counter.add(1)
            await sleep(1)
            logger.info("Loguru log")
            logfire.info("Logfire log!")
            finished_request_counter.add(1)
        with logfire.span("This is a span number 2"):
            started_request_counter.add(1)
            # raise Exception("This is a test exception")
            await sleep(1)
            logger.info("Loguru log")
            logfire.info("Logfire log!")
            finished_request_counter.add(1)
    return ResponseModel(message="Hello, World!")

@app.get("/error", response_model=ResponseModel)
async def read_root_with_error(
    cor_id: str | None = Header(default=None, alias="X-Correlation-ID"),
    user_id: str | None = Header(default=None, alias="X-UserID"),
    ) -> ResponseModel:
    with logfire.span("This is the root span"), logger.contextualize(correlation_id=cor_id, user_id=user_id):
        with logfire.span("This is a span number 1") as span:
            span.set_attribute("custom_attribute", "my_value")
            await sleep(1)
            logger.info("Loguru log")
            logfire.info("Logfire log!")
        with logfire.span("This is a span number 2"):
            started_request_counter.add(1)
            raise Exception("This is a test exception")
    return ResponseModel(message="Hello, World!")


@app.get("/openai_hello", response_model=ResponseModel)
async def openai_hello(
    cor_id: str | None = Header(default=None, alias="X-Correlation-ID"),
    user_id: str | None = Header(default=None, alias="X-UserID"),
):
    client = openai.AsyncClient()
    with logfire.span("OpenAI request"):
        response = await client.responses.create(
            model="gpt-5",
            input="Say hello!"
        )
    return ResponseModel(message=response.output_text)

@app.get("/health")
def health_check():
    return Response(status_code=200)

