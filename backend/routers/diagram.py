"""다이어그램 생성 API"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.diagram_service import (
    generate_nodered_diagram,
    generate_circuit_diagram
)

router = APIRouter()


class NodeREDRequest(BaseModel):
    title: str = "Node-RED Flow"
    nodes: list
    connections: list


class CircuitRequest(BaseModel):
    title: str = "회로도"
    components: list
    connections: list


@router.post("/nodered")
async def create_nodered(req: NodeREDRequest):
    url = generate_nodered_diagram(req.nodes, req.connections, req.title)
    return {"url": url, "type": "nodered"}


@router.post("/circuit")
async def create_circuit(req: CircuitRequest):
    url = generate_circuit_diagram(req.components, req.connections, req.title)
    return {"url": url, "type": "circuit"}