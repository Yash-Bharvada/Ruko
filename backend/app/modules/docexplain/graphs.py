"""Diagram validation, repair, and cycle detection for JSON-only graph models."""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.logging import logger
from app.core.schemas import Diagrams, FlowGraph, GraphEdge, GraphNode, TimelineItem


def _has_cycle(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> bool:
    """Detect cycles in directed graph using DFS, ignoring explicit 'loop' nodes."""
    loop_node_ids = {n["id"] for n in nodes if n.get("kind") == "loop"}

    adj = defaultdict(list)
    for e in edges:
        src = e.get("source")
        tgt = e.get("target")
        if src in loop_node_ids or tgt in loop_node_ids:
            continue
        if src and tgt:
            adj[src].append(tgt)

    visited: Dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited

    def dfs(u: str) -> bool:
        visited[u] = 1
        for v in adj.get(u, []):
            if visited.get(v, 0) == 1:
                return True  # Back-edge (cycle detected)
            if visited.get(v, 0) == 0:
                if dfs(v):
                    return True
        visited[u] = 2
        return False

    all_node_ids = [n["id"] for n in nodes if n["id"] not in loop_node_ids]
    for nid in all_node_ids:
        if visited.get(nid, 0) == 0:
            if dfs(nid):
                return True
    return False


def _validate_and_repair_graph(raw_graph: Optional[Dict[str, Any]]) -> Optional[FlowGraph]:
    """Validate and auto-repair a single flow graph. Returns FlowGraph or None."""
    if not raw_graph or not isinstance(raw_graph, dict):
        return None

    title = str(raw_graph.get("title", "")).strip() or "Process Diagram"
    raw_nodes = raw_graph.get("nodes", [])
    raw_edges = raw_graph.get("edges", [])

    if not isinstance(raw_nodes, list) or not isinstance(raw_edges, list):
        return None
    if not raw_nodes:
        return None

    # 1. Enforce max 12 nodes
    if len(raw_nodes) > 12:
        raw_nodes = raw_nodes[:12]

    # 2. Validate unique IDs and repair labels
    nodes: List[GraphNode] = []
    seen_ids: Set[str] = set()
    valid_kinds = {"start", "step", "decision", "end", "money", "party", "loop"}

    for n in raw_nodes:
        if not isinstance(n, dict):
            continue
        nid = str(n.get("id", "")).strip()
        if not nid or nid in seen_ids:
            continue

        raw_label = str(n.get("label", "")).strip() or nid
        # Trim label to max 60 chars
        label = raw_label[:60]
        kind = str(n.get("kind", "step")).lower().strip()
        if kind not in valid_kinds:
            kind = "step"

        nodes.append(GraphNode(id=nid, label=label, kind=kind))
        seen_ids.add(nid)

    if not nodes:
        return None

    # 3. Validate & repair edges: must reference existing node IDs
    edges: List[GraphEdge] = []
    connected_node_ids: Set[str] = set()

    for e in raw_edges:
        if not isinstance(e, dict):
            continue
        src = str(e.get("source", "")).strip()
        tgt = str(e.get("target", "")).strip()
        if src in seen_ids and tgt in seen_ids and src != tgt:
            raw_edge_label = e.get("label")
            edge_label = str(raw_edge_label).strip()[:40] if raw_edge_label else None
            edges.append(GraphEdge(source=src, target=tgt, label=edge_label))
            connected_node_ids.add(src)
            connected_node_ids.add(tgt)

    # 4. Remove orphan nodes if there are edges
    if edges and len(nodes) > 1:
        nodes = [n for n in nodes if n.id in connected_node_ids]

    if not nodes:
        return None

    # 5. Check for unwanted cycles
    raw_node_dicts = [{"id": n.id, "kind": n.kind} for n in nodes]
    raw_edge_dicts = [{"source": e.source, "target": e.target} for e in edges]
    if _has_cycle(raw_node_dicts, raw_edge_dicts):
        logger.warning("Diagram contains unwanted cycles; dropping diagram.")
        return None

    return FlowGraph(title=title, nodes=nodes, edges=edges)


def validate_diagrams(raw_diagrams: Optional[Dict[str, Any]]) -> Tuple[Diagrams, List[str]]:
    """Validate and sanitize full Diagrams object."""
    degraded: List[str] = []
    if not raw_diagrams or not isinstance(raw_diagrams, dict):
        return Diagrams(flowchart=None, money_flow=None, timeline=[]), degraded

    # 1. Flowchart
    raw_fc = raw_diagrams.get("flowchart")
    flowchart = None
    if raw_fc:
        flowchart = _validate_and_repair_graph(raw_fc)
        if not flowchart:
            degraded.append("graph_dropped")

    # 2. Money Flow
    raw_mf = raw_diagrams.get("money_flow")
    money_flow = None
    if raw_mf:
        money_flow = _validate_and_repair_graph(raw_mf)
        if not money_flow:
            degraded.append("graph_dropped")

    # 3. Timeline
    timeline_items: List[TimelineItem] = []
    for item in raw_diagrams.get("timeline", []):
        try:
            if isinstance(item, dict) and item.get("label") and item.get("evidence"):
                timeline_items.append(
                    TimelineItem(
                        label=str(item["label"]).strip()[:100],
                        date_text=str(item.get("date_text", "")).strip()[:50],
                        evidence=str(item["evidence"]).strip()[:150],
                    )
                )
        except Exception:
            continue

    return (
        Diagrams(
            flowchart=flowchart,
            money_flow=money_flow,
            timeline=timeline_items,
        ),
        list(dict.fromkeys(degraded)),
    )
