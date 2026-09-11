"""FastAPI web backend for Algorithm Discovery Lab."""

from __future__ import annotations

import json
import os
import platform
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from algorithm_discovery_lab.config.experiment import ExperimentConfig
from algorithm_discovery_lab.core.candidate import Candidate, CandidateState
from algorithm_discovery_lab.experiments.runner import ExperimentRunner
from algorithm_discovery_lab.problems.sorting_network import SortingNetworkProblem
from algorithm_discovery_lab.storage.db import Storage
from algorithm_discovery_lab.verification.verifier import get_verifier
from algorithm_discovery_lab.benchmarking.engine import benchmark_sorting_network

app = FastAPI(title="Algorithm Discovery Lab", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.environ.get("ADL_DB", "adl.db")
storage = Storage(DB_PATH)

# Active WebSocket connections
ws_connections: list[WebSocket] = []


class DiscoverRequest(BaseModel):
    n: int = 8
    search: str = "evolutionary"
    population: int = 200
    generations: int = 500
    mutation_rate: float = 0.15
    crossover_rate: float = 0.7
    elitism_rate: float = 0.05
    seed: int = 42
    benchmark_reps: int = 1000


class VerifyRequest(BaseModel):
    n: int = 8
    comparators: list[dict[str, int]]


class BenchmarkRequest(BaseModel):
    n: int = 8
    comparators: list[dict[str, int]]
    repetitions: int = 1000


@app.get("/api/problems")
async def list_problems() -> dict[str, Any]:
    return {
        "problems": [
            {
                "type": "sorting_network",
                "name": "Sorting Network",
                "description": "Discover optimal comparator networks that sort small inputs",
                "min_n": 2,
                "max_n": 16,
            }
        ]
    }


@app.post("/api/experiments")
async def create_experiment(req: DiscoverRequest) -> dict[str, Any]:
    config = ExperimentConfig(
        problem_type="sorting_network",
        n=req.n,
        search=ExperimentConfig.search.__class__(
            algorithm=req.search,
            population_size=req.population,
            generations=req.generations,
            mutation_rate=req.mutation_rate,
            crossover_rate=req.crossover_rate,
            elitism_rate=req.elitism_rate,
        ),
        seed=req.seed,
        benchmark_repetitions=req.benchmark_reps,
    )
    runner = ExperimentRunner(config, storage)
    result = runner.run()
    return result


@app.get("/api/experiments")
async def list_experiments() -> dict[str, Any]:
    return {"experiments": storage.list_experiments()}


@app.get("/api/experiments/{exp_id}")
async def get_experiment(exp_id: str) -> dict[str, Any]:
    exp = storage.get_experiment(exp_id)
    if not exp:
        raise HTTPException(404, "Experiment not found")
    return exp


@app.get("/api/discoveries")
async def list_discoveries() -> dict[str, Any]:
    return {"discoveries": storage.list_discoveries()}


@app.get("/api/discoveries/{disc_id}")
async def get_discovery(disc_id: str) -> dict[str, Any]:
    disc = storage.get_discovery(disc_id)
    if not disc:
        raise HTTPException(404, "Discovery not found")
    return disc


@app.post("/api/verify")
async def verify_candidate(req: VerifyRequest) -> dict[str, Any]:
    problem = SortingNetworkProblem(req.n)
    network = problem.deserialize({"n": req.n, "comparators": req.comparators})
    verifier = get_verifier("exhaustive", req.n)
    result = verifier.verify(network)
    return result.to_dict()


@app.post("/api/benchmark")
async def benchmark_candidate(req: BenchmarkRequest) -> dict[str, Any]:
    problem = SortingNetworkProblem(req.n)
    network = problem.deserialize({"n": req.n, "comparators": req.comparators})
    br = benchmark_sorting_network(network, "api-candidate", repetitions=req.repetitions)
    return br.to_dict()


@app.get("/api/stats")
async def get_stats() -> dict[str, Any]:
    experiments = storage.list_experiments(limit=1000)
    discoveries = storage.list_discoveries(limit=1000)
    return {
        "total_experiments": len(experiments),
        "total_discoveries": len(discoveries),
        "hardware": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python": platform.python_version(),
        },
    }


@app.websocket("/ws/experiments")
async def websocket_experiments(websocket: WebSocket) -> None:
    await websocket.accept()
    ws_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Client can send commands; for now just keep alive
    except WebSocketDisconnect:
        ws_connections.remove(websocket)


async def broadcast_event(event: dict[str, Any]) -> None:
    """Broadcast event to all connected WebSocket clients."""
    dead = []
    for ws in ws_connections:
        try:
            await ws.send_json(event)
        except Exception:
            dead.append(ws)
    for ws in dead:
        ws_connections.remove(ws)
