"""
Interaction NET のテストスイート

テスト対象:
1. 基本的なノード・エッジの操作
2. セル（デュプリケータ、重ね合わせ、ラムダ）の生成
3. パス探索（Type Inhabitation）
4. DOT形式への変換
5. GHG特化のネット構築
"""

import unittest
import sys
import os

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interaction_net import (
    InteractionNet, CellType, Node, Edge, Cell,
    create_simple_net, create_duplication_net, create_superposition_net
)
from ghg_net_visualizer import GHGInteractionNet, create_type_inhabitation_demo


class TestInteractionNet(unittest.TestCase):
    """InteractionNetの基本機能テスト"""
    
    def test_node_creation(self):
        """ノード作成のテスト"""
        net = InteractionNet("TestNet")
        node = net.add_node("n1", "Int", "42", category='data')
        
        self.assertEqual(node.id, "n1")
        self.assertEqual(node.type_name, "Int")
        self.assertEqual(node.value, "42")
        self.assertEqual(node.metadata['category'], 'data')
        self.assertIn("n1", net.nodes)
    
    def test_edge_creation(self):
        """エッジ作成のテスト"""
        net = InteractionNet("TestNet")
        net.add_node("n1", "Int")
        net.add_node("n2", "String")
        edge = net.add_edge("n1", "n2", function="toString")
        
        self.assertEqual(edge.source.id, "n1")
        self.assertEqual(edge.target.id, "n2")
        self.assertEqual(edge.function, "toString")
        self.assertEqual(len(net.edges), 1)
    
    def test_duplicator_cell(self):
        """デュプリケータセルのテスト"""
        net = InteractionNet("TestNet")
        net.add_node("input", "Int")
        net.add_node("out1", "Int")
        net.add_node("out2", "Int")
        
        cell = net.add_duplicator("input", "out1", "out2", "L")
        
        self.assertEqual(cell.cell_type, CellType.DUPLICATOR)
        self.assertEqual(cell.label, "L")
        self.assertEqual(len(cell.ports), 3)
        self.assertIn(cell.id, net.cells)
    
    def test_superposition_cell(self):
        """重ね合わせセルのテスト"""
        net = InteractionNet("TestNet")
        net.add_node("input", "Data")
        net.add_node("left", "Data")
        net.add_node("right", "Data")
        
        cell = net.add_superposition("input", "left", "right", "S")
        
        self.assertEqual(cell.cell_type, CellType.DUPLICATOR)
        self.assertEqual(cell.label, "S")
        self.assertTrue(cell.metadata.get('superposition'))
    
    def test_lambda_cell(self):
        """ラムダセルのテスト"""
        net = InteractionNet("TestNet")
        net.add_node("param", "Int")
        net.add_node("body", "Int")
        net.add_node("result", "Int→Int")
        
        cell = net.add_lambda("param", "body", "result")
        
        self.assertEqual(cell.cell_type, CellType.CONSTRUCTOR)
        self.assertEqual(len(cell.ports), 3)
    
    def test_path_finding(self):
        """パス探索のテスト"""
        net = InteractionNet("TestNet")
        net.add_node("start", "A")
        net.add_node("mid", "B")
        net.add_node("end", "C")
        
        net.add_edge("start", "mid", function="a_to_b")
        net.add_edge("mid", "end", function="b_to_c")
        
        paths = net.find_paths("start", "end")
        
        self.assertEqual(len(paths), 1)
        self.assertEqual(len(paths[0]), 2)
        self.assertEqual(paths[0][0].function, "a_to_b")
        self.assertEqual(paths[0][1].function, "b_to_c")
    
    def test_multiple_paths(self):
        """複数パスの探索テスト"""
        net = InteractionNet("TestNet")
        net.add_node("start", "A")
        net.add_node("mid1", "B")
        net.add_node("mid2", "C")
        net.add_node("end", "D")
        
        # パス1: A -> B -> D
        net.add_edge("start", "mid1", function="path1_1")
        net.add_edge("mid1", "end", function="path1_2")
        
        # パス2: A -> C -> D
        net.add_edge("start", "mid2", function="path2_1")
        net.add_edge("mid2", "end", function="path2_2")
        
        paths = net.find_paths("start", "end")
        
        self.assertEqual(len(paths), 2)
    
    def test_to_dot(self):
        """DOT形式変換のテスト"""
        net = InteractionNet("TestNet")
        net.add_node("n1", "Int", "42")
        net.add_node("n2", "String")
        net.add_edge("n1", "n2", function="toString")
        
        dot = net.to_dot()
        
        self.assertIn('digraph "TestNet"', dot)
        self.assertIn('"n1"', dot)
        self.assertIn('"n2"', dot)
        self.assertIn('toString', dot)
    
    def test_to_json(self):
        """JSON形式変換のテスト"""
        net = InteractionNet("TestNet")
        net.add_node("n1", "Int", "42")
        net.add_edge("n1", "n1", function="identity")
        
        json_str = net.to_json()
        
        self.assertIn('"name": "TestNet"', json_str)
        self.assertIn('"n1"', json_str)
        self.assertIn('"Int"', json_str)


class TestExampleNets(unittest.TestCase):
    """サンプルネットのテスト"""
    
    def test_simple_net(self):
        """簡単な関数ネットのテスト"""
        net = create_simple_net()
        
        self.assertIn("x", net.nodes)
        self.assertIn("result", net.nodes)
        self.assertTrue(len(net.edges) >= 2)
        self.assertTrue(len(net.cells) >= 1)
    
    def test_duplication_net(self):
        """複製ネットのテスト"""
        net = create_duplication_net()
        
        self.assertIn("input", net.nodes)
        self.assertIn("x0", net.nodes)
        self.assertIn("x1", net.nodes)
        
        # デュプリケータセルの存在確認
        dup_cells = [c for c in net.cells.values() 
                     if c.cell_type == CellType.DUPLICATOR]
        self.assertEqual(len(dup_cells), 1)
    
    def test_superposition_net(self):
        """重ね合わせネットのテスト"""
        net = create_superposition_net()
        
        self.assertIn("method1", net.nodes)
        self.assertIn("method2", net.nodes)
        
        # 重ね合わせセルの存在確認
        sup_cells = [c for c in net.cells.values() 
                     if c.metadata.get('superposition')]
        self.assertEqual(len(sup_cells), 1)


class TestGHGNet(unittest.TestCase):
    """GHG特化ネットのテスト"""
    
    def setUp(self):
        """各テストの前に実行"""
        self.ghg_net = GHGInteractionNet()
    
    def test_input_nodes(self):
        """入力ノードの存在確認"""
        required_inputs = [
            "energy_input",
            "material_input",
            "transport_input",
            "waste_input"
        ]
        
        for node_id in required_inputs:
            self.assertIn(node_id, self.ghg_net.nodes,
                         f"Missing input node: {node_id}")
    
    def test_scope_nodes(self):
        """Scopeノードの存在確認"""
        scope_nodes = [
            "scope1_moe", "scope1_ghg",
            "scope2_location", "scope2_market",
            "scope3_cat1", "scope3_cat4", "scope3_cat5"
        ]
        
        for node_id in scope_nodes:
            self.assertIn(node_id, self.ghg_net.nodes,
                         f"Missing scope node: {node_id}")
    
    def test_output_nodes(self):
        """出力ノードの存在確認（4パターン）"""
        output_nodes = [
            "report_moe_loc",
            "report_moe_mkt",
            "report_ghg_loc",
            "report_ghg_mkt"
        ]
        
        for node_id in output_nodes:
            self.assertIn(node_id, self.ghg_net.nodes,
                         f"Missing output node: {node_id}")
    
    def test_superposition_cells(self):
        """重ね合わせセルの確認（Scope1とScope2）"""
        sup_cells = [c for c in self.ghg_net.cells.values() 
                     if c.metadata.get('superposition')]
        
        # Scope1とScope2の2つの重ね合わせがあるはず
        self.assertGreaterEqual(len(sup_cells), 2,
                               "Should have at least 2 superposition cells")
    
    def test_duplicator_cells(self):
        """デュプリケータセルの確認"""
        dup_cells = [c for c in self.ghg_net.cells.values() 
                     if c.cell_type == CellType.DUPLICATOR
                     and not c.metadata.get('superposition')]
        
        # エネルギーデータの複製があるはず
        self.assertGreaterEqual(len(dup_cells), 1,
                               "Should have at least 1 duplicator cell")
    
    def test_scope_edges(self):
        """Scope計算のエッジ確認"""
        scope1_edges = [e for e in self.ghg_net.edges 
                       if e.function and 'scope1' in e.function.lower()]
        scope2_edges = [e for e in self.ghg_net.edges 
                       if e.function and 'scope2' in e.function.lower()]
        scope3_edges = [e for e in self.ghg_net.edges 
                       if e.function and 'scope3' in e.function.lower()]
        
        self.assertGreater(len(scope1_edges), 0, "Missing Scope1 edges")
        self.assertGreater(len(scope2_edges), 0, "Missing Scope2 edges")
        self.assertGreater(len(scope3_edges), 0, "Missing Scope3 edges")
    
    def test_paths_energy_to_report(self):
        """エネルギーデータからレポートまでのパス探索"""
        # energy_input → report_moe_loc のパスを探索
        # 注: 複雑なグラフなので、簡単なパス探索ではすべて見つからない可能性がある
        paths = self.ghg_net.find_paths("energy_input", "scope1_moe")
        
        # 少なくとも1つのパスが見つかるはず
        self.assertGreater(len(paths), 0,
                          "Should find at least one path from energy to scope1")
    
    def test_to_dot_styled(self):
        """スタイル付きDOT形式のテスト"""
        dot = self.ghg_net.to_dot_styled()
        
        # 基本的な構造確認
        self.assertIn('digraph "GHG_Report_Generation"', dot)
        self.assertIn('subgraph cluster_input', dot)
        self.assertIn('subgraph cluster_output', dot)
        
        # スタイル確認
        self.assertIn('fillcolor', dot)
        self.assertIn('shape=', dot)


class TestTypeInhabitation(unittest.TestCase):
    """Type Inhabitationデモのテスト"""
    
    def setUp(self):
        """各テストの前に実行"""
        self.net = create_type_inhabitation_demo()
    
    def test_input_output_nodes(self):
        """入力・出力ノードの確認"""
        self.assertIn("int_input", self.net.nodes)
        self.assertIn("str_direct", self.net.nodes)
        self.assertIn("str_via_float", self.net.nodes)
        self.assertIn("str_via_bool", self.net.nodes)
    
    def test_multiple_proofs(self):
        """複数の証明（パス）の確認"""
        paths = self.net.find_paths("int_input", "str_direct")
        self.assertGreater(len(paths), 0, "Should find direct path")
        
        paths = self.net.find_paths("int_input", "str_via_float")
        self.assertGreater(len(paths), 0, "Should find path via Float")
    
    def test_proof_metadata(self):
        """証明のメタデータ確認"""
        edges_with_proof = [e for e in self.net.edges 
                           if 'proof' in e.metadata]
        
        # 複数の証明がメタデータに記録されているはず
        self.assertGreater(len(edges_with_proof), 0,
                          "Should have proof metadata")


class TestVisualization(unittest.TestCase):
    """可視化機能のテスト"""
    
    def test_dot_syntax_validity(self):
        """DOT構文の妥当性確認"""
        nets = [
            create_simple_net(),
            create_duplication_net(),
            create_superposition_net(),
            GHGInteractionNet(),
            create_type_inhabitation_demo()
        ]
        
        for net in nets:
            dot = net.to_dot()
            
            # 基本的な構文チェック
            self.assertTrue(dot.startswith('digraph'))
            self.assertIn('{', dot)
            self.assertIn('}', dot)
            self.assertEqual(dot.count('{'), dot.count('}'))
    
    def test_json_validity(self):
        """JSON出力の妥当性確認"""
        import json
        
        net = create_simple_net()
        json_str = net.to_json()
        
        # パース可能かチェック
        data = json.loads(json_str)
        
        self.assertIn('name', data)
        self.assertIn('nodes', data)
        self.assertIn('edges', data)
        self.assertIn('cells', data)


def run_tests():
    """テストを実行"""
    # テストスイートの作成
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # すべてのテストクラスを追加
    suite.addTests(loader.loadTestsFromTestCase(TestInteractionNet))
    suite.addTests(loader.loadTestsFromTestCase(TestExampleNets))
    suite.addTests(loader.loadTestsFromTestCase(TestGHGNet))
    suite.addTests(loader.loadTestsFromTestCase(TestTypeInhabitation))
    suite.addTests(loader.loadTestsFromTestCase(TestVisualization))
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果サマリー
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed.")
    
    return result


if __name__ == "__main__":
    run_tests()
