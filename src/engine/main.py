from fastapi import FastAPI
from pydantic import BaseModel

# Initialize the API
app = FastAPI(
    title="Trading Strategy Evaluation API",
    description="Backend engine for calculating quantitative strategy performance.",
)


# Define the exact contract Panna will send us (from our earlier JSON mock)
class StrategyRequest(BaseModel):
    strategy: str
    asset: str
    parameters: dict


@app.get("/")
def read_health_check():
    """Simple endpoint to prove the server is alive."""
    return {"status": "online", "message": "Trading Engine API is running."}


@app.post("/run")
def run_strategy(request: StrategyRequest):
    """
    Placeholder endpoint for running the strategy.
    For now, it just echoes back what the UI sent.
    """
    return {
        "message": f"Success! The engine received the request to run {request.strategy} on {request.asset}.",
        "received_parameters": request.parameters,
    }
