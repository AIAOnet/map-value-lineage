"""Small native model/parser for interactive Mermaid flowcharts."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


RELATION_COLORS = (
    "#2563eb", "#dc2626", "#059669", "#d97706",
    "#7c3aed", "#0891b2", "#db2777", "#65a30d",
)

RELATION_MEANINGS = {
    "ORIGINATES_FROM": "The value comes from the source.",
    "READS": "The source reads the value.",
    "WRITES": "The source assigns the value.",
    "MUTATES": "The source changes the value.",
    "VALIDATES": "The source checks whether the value is valid.",
    "BRANCHES_ON": "The source uses the value to choose a control-flow path.",
    "TRANSFORMS_TO": "The source converts or derives the target value.",
    "STORES_IN": "The source persists the value in the target.",
    "LOADS_FROM": "The source loads the value from the target.",
    "ACCEPTS": "The source accepts the value as input.",
    "EXPOSES": "The source presents or returns the value.",
    "EMITS": "The source publishes the target event or message.",
    "CONSUMES": "The source receives and uses the target value or message.",
    "CALLS": "The source invokes the target.",
    "INVALIDATES": "The source makes the target stale so it must be refreshed.",
    "CONSTRAINS": "The source limits the valid form or values of the target.",
    "AFFECTS": "The source changes the target's behavior or outcome.",
}


@dataclass(frozen=True)
class GraphNode:
    id: str
    label: str
    shape: str = "rectangle"
    meaning: str = ""


@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    label: str
    style: str = "solid"
    meaning: str = ""


@dataclass
class InteractiveGraph:
    nodes: dict[str, GraphNode]
    edges: list[GraphEdge]
    positions: dict[str, tuple[float, float]]


def relation_color(label: str) -> str:
    """Return the same accessible palette color for the same relation label."""
    digest = hashlib.sha256(label.strip().casefold().encode("utf-8")).digest()
    return RELATION_COLORS[int.from_bytes(digest[:2], "big") % len(RELATION_COLORS)]


def build_relation_color_map(labels: list[str]) -> dict[str, str]:
    """Assign distinct colors in first-seen order, wrapping only past the palette."""
    unique_labels = list(dict.fromkeys(labels))
    return {label: RELATION_COLORS[index % len(RELATION_COLORS)] for index, label in enumerate(unique_labels)}


class FlowchartParser:
    """Parse the common Mermaid flowchart node/edge syntax used by the viewer."""

    _shapes = (
        (r"\(\((?P<label>.*?)\)\)", "circle"),
        (r"\{(?P<label>.*?)\}", "diamond"),
        (r"\((?P<label>.*?)\)", "rounded"),
        (r"\[(?P<label>.*?)\]", "rectangle"),
    )
    _labelled_edge = re.compile(r"^(?P<left>.+?)\s*--\s*(?P<label>.+?)\s*-->\s*(?P<right>.+?)\s*$")
    _plain_edge = re.compile(
        r"^(?P<left>.+?)\s*(?P<arrow>-->|==>|-.->)\s*(?:\|(?P<label>.*?)\|\s*)?(?P<right>.+?)\s*$"
    )
    _labelled_dotted = re.compile(r"^(?P<left>.+?)\s*-\.\s*(?P<label>.+?)\s*\.->\s*(?P<right>.+?)\s*$")
    _entity_meaning = re.compile(r"^%%\s*entity\s+(?P<id>[A-Za-z_][\w.-]*)\s*:\s*(?P<meaning>.+)$", re.IGNORECASE)
    _relation_meaning = re.compile(r"^%%\s*relation\s+(?P<key>.+?)\s*:\s*(?P<meaning>.+)$", re.IGNORECASE)

    def parse(self, source: str) -> InteractiveGraph | None:
        lines = [line.strip() for line in source.splitlines()]
        first = next((line for line in lines if line and not line.startswith("%%")), "")
        if not re.match(r"^(flowchart|graph)\s+(TB|TD|BT|LR|RL)\b", first, re.IGNORECASE):
            return None

        direction = first.split()[1].upper()
        entity_meanings: dict[str, str] = {}
        relation_meanings: dict[str, str] = {}
        for line in lines:
            entity_annotation = self._entity_meaning.match(line)
            relation_annotation = self._relation_meaning.match(line)
            if entity_annotation:
                entity_meanings[entity_annotation["id"]] = entity_annotation["meaning"].strip()
            elif relation_annotation:
                relation_meanings[relation_annotation["key"].strip().casefold()] = relation_annotation["meaning"].strip()
        nodes: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []
        for line in lines[lines.index(first) + 1:]:
            if not line or line.startswith("%%") or re.match(
                r"^(subgraph|end\b|style\b|classDef\b|class\b|linkStyle\b|click\b)", line, re.IGNORECASE
            ):
                continue
            parsed = self._parse_edge(line)
            if parsed:
                left_text, right_text, label, style = parsed
                left = self._parse_node(left_text)
                right = self._parse_node(right_text)
                if left and right:
                    nodes[left.id] = self._merge_node(nodes.get(left.id), left)
                    nodes[right.id] = self._merge_node(nodes.get(right.id), right)
                    edges.append(GraphEdge(left.id, right.id, label or "flow", style))
                continue
            node = self._parse_node(line)
            if node:
                nodes[node.id] = self._merge_node(nodes.get(node.id), node)
            else:
                # A partially parsed graph is misleading; let the viewer use
                # its complete static Mermaid fallback for unsupported syntax.
                return None

        if not nodes or not edges:
            return None
        nodes = {
            node_id: GraphNode(
                node.id, node.label, node.shape,
                entity_meanings.get(node_id, f'{node.label} is a {node.shape} entity in this diagram.'),
            )
            for node_id, node in nodes.items()
        }
        edges = [
            GraphEdge(
                edge.source, edge.target, edge.label, edge.style,
                relation_meanings.get(
                    f"{edge.source}->{edge.target}".casefold(),
                    relation_meanings.get(
                        edge.label.casefold(),
                        RELATION_MEANINGS.get(
                            edge.label.upper(),
                            f'{edge.label} connects {nodes[edge.source].label} to {nodes[edge.target].label}.',
                        ),
                    ),
                ),
            )
            for edge in edges
        ]
        return InteractiveGraph(nodes, edges, self._layout(nodes, edges, direction))

    def _parse_edge(self, line: str) -> tuple[str, str, str, str] | None:
        dotted = self._labelled_dotted.match(line)
        if dotted:
            return dotted["left"], dotted["right"], dotted["label"].strip(), "dashed"
        labelled = self._labelled_edge.match(line)
        if labelled:
            return labelled["left"], labelled["right"], labelled["label"].strip(), "solid"
        plain = self._plain_edge.match(line)
        if plain:
            style = "dashed" if plain["arrow"] == "-.->" else "solid"
            return plain["left"], plain["right"], (plain["label"] or "").strip(), style
        return None

    def _parse_node(self, text: str) -> GraphNode | None:
        text = text.strip().rstrip(";")
        match = re.match(r"^(?P<id>[A-Za-z_][\w.-]*)(?P<shape>.*)$", text)
        if not match:
            return None
        node_id, shape_text = match["id"], match["shape"].strip()
        if not shape_text:
            return GraphNode(node_id, node_id)
        for pattern, shape in self._shapes:
            shape_match = re.fullmatch(pattern, shape_text)
            if shape_match:
                return GraphNode(node_id, self._clean_label(shape_match["label"]), shape)
        return None

    @staticmethod
    def _clean_label(label: str) -> str:
        return re.sub(r"<br\s*/?>", "\n", label.strip().strip('"'), flags=re.IGNORECASE)

    @staticmethod
    def _merge_node(old: GraphNode | None, new: GraphNode) -> GraphNode:
        return new if old is None or new.label != new.id else old

    @staticmethod
    def _layout(nodes: dict[str, GraphNode], edges: list[GraphEdge], direction: str) -> dict[str, tuple[float, float]]:
        incoming = {node_id: 0 for node_id in nodes}
        outgoing: dict[str, list[str]] = {node_id: [] for node_id in nodes}
        for edge in edges:
            incoming[edge.target] += 1
            outgoing[edge.source].append(edge.target)
        levels = {node_id: 0 for node_id in nodes}
        queue = [node_id for node_id, count in incoming.items() if count == 0] or [next(iter(nodes))]
        seen: set[str] = set()
        while queue:
            current = queue.pop(0)
            if current in seen:
                continue
            seen.add(current)
            for target in outgoing[current]:
                levels[target] = max(levels[target], levels[current] + 1)
                incoming[target] -= 1
                if incoming[target] <= 0:
                    queue.append(target)
        for node_id in nodes:
            if node_id not in seen:
                levels[node_id] = max(levels.values(), default=0) + 1

        grouped: dict[int, list[str]] = {}
        for node_id, level in levels.items():
            grouped.setdefault(level, []).append(node_id)
        positions: dict[str, tuple[float, float]] = {}
        horizontal = direction in {"LR", "RL"}
        reverse = direction in {"RL", "BT"}
        max_level = max(grouped, default=0)
        for level, ids in grouped.items():
            axis_level = max_level - level if reverse else level
            for index, node_id in enumerate(ids):
                x, y = (140 + axis_level * 250, 110 + index * 150) if horizontal else (140 + index * 250, 110 + axis_level * 150)
                positions[node_id] = (float(x), float(y))
        return positions
