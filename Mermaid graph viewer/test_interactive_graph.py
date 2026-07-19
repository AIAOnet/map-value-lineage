import unittest

from interactive_graph import FlowchartParser, build_relation_color_map, relation_color


class FlowchartParserTests(unittest.TestCase):
    def test_parses_nodes_relationship_labels_and_shapes(self):
        graph = FlowchartParser().parse("""flowchart LR
            A[Customer] -- places --> B{Valid order?}
            B -->|yes| C((Accepted))
            B -. rejects .-> D(Rejected)
        """)
        self.assertIsNotNone(graph)
        assert graph is not None
        self.assertEqual(graph.nodes["A"].label, "Customer")
        self.assertEqual(graph.nodes["B"].shape, "diamond")
        self.assertEqual([edge.label for edge in graph.edges], ["places", "yes", "rejects"])
        self.assertEqual(graph.edges[2].style, "dashed")

    def test_relation_colors_are_stable_and_label_specific(self):
        self.assertEqual(relation_color("owns"), relation_color("OWNS"))
        labels = ["owns", "calls", "reads", "writes"]
        self.assertGreaterEqual(len({relation_color(label) for label in labels}), 3)
        color_map = build_relation_color_map(labels)
        self.assertEqual(len(set(color_map.values())), len(labels))

    def test_rejects_non_flowchart_diagram(self):
        self.assertIsNone(FlowchartParser().parse("sequenceDiagram\nA->>B: Hello"))

    def test_falls_back_instead_of_partially_parsing_unknown_syntax(self):
        source = "flowchart LR\nA --> B\nA & B --> C"
        self.assertIsNone(FlowchartParser().parse(source))

    def test_parses_entity_and_relation_meanings(self):
        source = """%% entity A: Starts the workflow
%% relation approves: Allows processing to continue
%% relation B->C: Records the final decision
flowchart LR
A[Requester] -- approves --> B[Reviewer]
B -- approves --> C[Archive]
"""
        graph = FlowchartParser().parse(source)
        self.assertIsNotNone(graph)
        assert graph is not None
        self.assertEqual(graph.nodes["A"].meaning, "Starts the workflow")
        self.assertEqual(graph.edges[0].meaning, "Allows processing to continue")
        self.assertEqual(graph.edges[1].meaning, "Records the final decision")

    def test_supplies_meaning_defaults(self):
        graph = FlowchartParser().parse("flowchart LR\nA[Start] --> B[Finish]")
        self.assertIsNotNone(graph)
        assert graph is not None
        self.assertIn("rectangle entity", graph.nodes["A"].meaning)
        self.assertIn("connects Start to Finish", graph.edges[0].meaning)

    def test_supplies_standard_relationship_meanings(self):
        graph = FlowchartParser().parse("""flowchart LR
A -- READS --> B
B -- writes --> C
""")
        self.assertIsNotNone(graph)
        assert graph is not None
        self.assertEqual(graph.edges[0].meaning, "The source reads the value.")
        self.assertEqual(graph.edges[1].meaning, "The source assigns the value.")

    def test_explicit_meaning_overrides_standard_vocabulary(self):
        graph = FlowchartParser().parse("""%% relation READS: Reads a cached copy only
flowchart LR
A -- READS --> B
""")
        self.assertIsNotNone(graph)
        assert graph is not None
        self.assertEqual(graph.edges[0].meaning, "Reads a cached copy only")


if __name__ == "__main__":
    unittest.main()
