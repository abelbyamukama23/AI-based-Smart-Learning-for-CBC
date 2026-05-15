import logging
import networkx as nx
from typing import List, Dict, Optional
from apps.curriculum.models import CurriculumNode, CurriculumEdge

logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    """
    Singleton service that loads CurriculumNode and CurriculumEdge models 
    into an in-memory networkx Directed Graph for fast KAG traversal.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KnowledgeGraphService, cls).__new__(cls)
            cls._instance._graph = nx.DiGraph()
            cls._instance._is_loaded = False
        return cls._instance

    def load_graph(self, force_reload: bool = False):
        """Loads the nodes and edges from the DB into the NetworkX graph."""
        if self._is_loaded and not force_reload:
            return

        logger.info("Loading Curriculum Knowledge Graph into memory...")
        self._graph.clear()

        # Load Nodes
        nodes = CurriculumNode.objects.all()
        for node in nodes:
            self._graph.add_node(
                str(node.id),
                name=node.name,
                node_type=node.node_type,
                description=node.description,
                chroma_doc_id=node.chroma_doc_id
            )

        # Load Edges
        edges = CurriculumEdge.objects.all()
        for edge in edges:
            self._graph.add_edge(
                str(edge.source.id),
                str(edge.target.id),
                relationship=edge.relationship,
                weight=edge.weight
            )

        self._is_loaded = True
        logger.info(f"Loaded {self._graph.number_of_nodes()} nodes and {self._graph.number_of_edges()} edges into the Knowledge Graph.")

    def get_prerequisites(self, node_id: str) -> List[Dict]:
        """
        Traverse the graph backwards to find all 'REQUIRES' prerequisites 
        for a given concept or lesson.
        """
        if not self._is_loaded:
            self.load_graph()

        if node_id not in self._graph:
            return []

        # Find all ancestors (nodes that have a path TO this node)
        # Specifically filtering for REQUIRES edges.
        prereqs = []
        try:
            # Short-circuit: just immediate predecessors with REQUIRES edge
            for predecessor in self._graph.predecessors(node_id):
                edge_data = self._graph.get_edge_data(predecessor, node_id)
                if edge_data and edge_data.get('relationship') == 'REQUIRES':
                    node_data = self._graph.nodes[predecessor]
                    prereqs.append({
                        "id": predecessor,
                        "name": node_data.get("name"),
                        "node_type": node_data.get("node_type"),
                        "description": node_data.get("description"),
                        "chroma_doc_id": node_data.get("chroma_doc_id")
                    })
        except nx.NetworkXError as e:
            logger.error(f"Error traversing graph: {e}")

        return prereqs

    def get_learning_path(self, source_name: str, target_name: str) -> List[str]:
        """
        Find the shortest path between two concepts.
        """
        if not self._is_loaded:
            self.load_graph()

        # Resolve names to IDs (simplified)
        source_id = next((n for n, d in self._graph.nodes(data=True) if d.get('name', '').lower() == source_name.lower()), None)
        target_id = next((n for n, d in self._graph.nodes(data=True) if d.get('name', '').lower() == target_name.lower()), None)

        if not source_id or not target_id:
            return []

        try:
            path_ids = nx.shortest_path(self._graph, source=source_id, target=target_id)
            return [self._graph.nodes[nid].get("name", nid) for nid in path_ids]
        except nx.NetworkXNoPath:
            return []
