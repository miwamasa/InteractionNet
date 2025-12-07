"""
Interaction NET - グラフベースの計算モデル

Interaction Calculusの計算を、グラフ（ネット）として表現・可視化します。

基本要素：
- Node（ノード）: 型やデータを表す
- Edge（エッジ）: データフロー
- Cell（セル）: 計算要素
  - Constructor (γ, Lambda λ)
  - Duplicator (δ, Superposition &)
  - Eraser (ε, Erasure &{})

理論的背景：
- Lafont's Interaction Combinators (1997)
- Optimal Reduction
- Type Inhabitation / Proof Search
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from enum import Enum
import json


class CellType(Enum):
    """セルの種類"""
    CONSTRUCTOR = "γ"  # Lambda, Constructor
    DUPLICATOR = "δ"   # Superposition, Duplication
    ERASER = "ε"       # Erasure
    DATA = "data"      # データノード
    FUNCTION = "fn"    # 関数ノード


@dataclass
class Node:
    """ノード（型・データを表す）"""
    id: str
    type_name: str
    value: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Edge:
    """エッジ（データフロー）"""
    source: Node
    target: Node
    label: Optional[str] = None  # ラベル（&L, &R など）
    function: Optional[str] = None  # 変換関数
    metadata: Dict = field(default_factory=dict)


@dataclass
class Cell:
    """セル（計算要素）"""
    id: str
    cell_type: CellType
    ports: List[Node]  # ポート（接続点）
    label: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


class InteractionNet:
    """Interaction NET - 計算グラフ"""
    
    def __init__(self, name: str = "InteractionNet"):
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.cells: Dict[str, Cell] = {}
        
    def add_node(self, node_id: str, type_name: str, value: Optional[str] = None, **metadata) -> Node:
        """ノードを追加"""
        node = Node(node_id, type_name, value, metadata)
        self.nodes[node_id] = node
        return node
    
    def add_edge(self, source_id: str, target_id: str, label: Optional[str] = None, 
                 function: Optional[str] = None, **metadata) -> Edge:
        """エッジを追加"""
        source = self.nodes[source_id]
        target = self.nodes[target_id]
        edge = Edge(source, target, label, function, metadata)
        self.edges.append(edge)
        return edge
    
    def add_cell(self, cell_id: str, cell_type: CellType, port_ids: List[str], 
                 label: Optional[str] = None, **metadata) -> Cell:
        """セルを追加"""
        ports = [self.nodes[pid] for pid in port_ids]
        cell = Cell(cell_id, cell_type, ports, label, metadata)
        self.cells[cell_id] = cell
        return cell
    
    def add_duplicator(self, input_id: str, output1_id: str, output2_id: str, 
                      label: str = "L") -> Cell:
        """デュプリケータを追加（複製）"""
        cell_id = f"dup_{label}_{input_id}"
        return self.add_cell(cell_id, CellType.DUPLICATOR, 
                           [input_id, output1_id, output2_id], label)
    
    def add_superposition(self, node_id: str, left_id: str, right_id: str, 
                         label: str = "L") -> Cell:
        """重ね合わせを追加"""
        cell_id = f"sup_{label}_{node_id}"
        return self.add_cell(cell_id, CellType.DUPLICATOR, 
                           [node_id, left_id, right_id], label,
                           superposition=True)
    
    def add_lambda(self, param_id: str, body_id: str, result_id: str) -> Cell:
        """ラムダ抽象を追加"""
        cell_id = f"lam_{param_id}_{body_id}"
        return self.add_cell(cell_id, CellType.CONSTRUCTOR,
                           [param_id, body_id, result_id])
    
    def find_paths(self, start_id: str, end_id: str) -> List[List[Edge]]:
        """2つのノード間のパスを探索（Type Inhabitation）"""
        paths = []
        visited = set()
        
        def dfs(current_id: str, path: List[Edge]):
            if current_id == end_id:
                paths.append(path.copy())
                return
            
            if current_id in visited:
                return
            
            visited.add(current_id)
            
            for edge in self.edges:
                if edge.source.id == current_id:
                    path.append(edge)
                    dfs(edge.target.id, path)
                    path.pop()
            
            visited.remove(current_id)
        
        dfs(start_id, [])
        return paths
    
    def to_dot(self, show_cells: bool = True, highlight_paths: Optional[List[List[Edge]]] = None) -> str:
        """Graphviz DOT形式に変換"""
        lines = [
            f'digraph "{self.name}" {{',
            '  rankdir=LR;',
            '  node [shape=circle, style=filled, fontname="Helvetica"];',
            '  edge [fontname="Helvetica"];',
            ''
        ]
        
        # ノードのスタイル定義
        node_styles = {
            'data': 'fillcolor=lightblue',
            'function': 'fillcolor=lightgreen',
            'result': 'fillcolor=lightyellow',
        }
        
        # ノード定義
        for node in self.nodes.values():
            style = node_styles.get(node.metadata.get('category', 'data'), 'fillcolor=lightgray')
            label = f"{node.type_name}"
            if node.value:
                # ダブルクォートをエスケープ
                value_escaped = node.value.replace('"', '\\"')
                label += f"\\n{value_escaped}"
            
            lines.append(f'  "{node.id}" [label="{label}", {style}];')
        
        # セルを表示
        if show_cells:
            for cell in self.cells.values():
                shape = {
                    CellType.CONSTRUCTOR: 'triangle',
                    CellType.DUPLICATOR: 'diamond',
                    CellType.ERASER: 'square',
                }.get(cell.cell_type, 'circle')
                
                label = f"{cell.cell_type.value}"
                if cell.label:
                    label += f"_{cell.label}"
                
                lines.append(f'  "{cell.id}" [label="{label}", shape={shape}, fillcolor=lightcoral];')
                
                # セルとポートの接続
                for i, port in enumerate(cell.ports):
                    lines.append(f'  "{cell.id}" -> "{port.id}" [style=dashed, label="p{i}"];')
        
        # エッジ定義
        highlighted = set()
        if highlight_paths:
            for path in highlight_paths:
                for edge in path:
                    highlighted.add((edge.source.id, edge.target.id))
        
        for edge in self.edges:
            edge_label = ""
            if edge.function:
                edge_label = edge.function
            if edge.label:
                edge_label += f" [{edge.label}]" if edge_label else f"[{edge.label}]"
            
            is_highlighted = (edge.source.id, edge.target.id) in highlighted
            style = 'color=red, penwidth=2' if is_highlighted else ''
            
            label_attr = f'label="{edge_label}"' if edge_label else ''
            lines.append(f'  "{edge.source.id}" -> "{edge.target.id}" [{label_attr}, {style}];')
        
        lines.append('}')
        return '\n'.join(lines)
    
    def to_json(self) -> str:
        """JSON形式に変換（デバッグ用）"""
        return json.dumps({
            'name': self.name,
            'nodes': [
                {
                    'id': n.id,
                    'type': n.type_name,
                    'value': n.value,
                    'metadata': n.metadata
                }
                for n in self.nodes.values()
            ],
            'edges': [
                {
                    'source': e.source.id,
                    'target': e.target.id,
                    'label': e.label,
                    'function': e.function,
                    'metadata': e.metadata
                }
                for e in self.edges
            ],
            'cells': [
                {
                    'id': c.id,
                    'type': c.cell_type.value,
                    'ports': [p.id for p in c.ports],
                    'label': c.label,
                    'metadata': c.metadata
                }
                for c in self.cells.values()
            ]
        }, indent=2)


def create_simple_net() -> InteractionNet:
    """簡単な例：λx.(x + 1)"""
    net = InteractionNet("SimpleFunction")
    
    # ノード
    net.add_node("x", "Int", metadata={'category': 'data'})
    net.add_node("one", "Int", "1", metadata={'category': 'data'})
    net.add_node("plus", "Int→Int→Int", metadata={'category': 'function'})
    net.add_node("result", "Int", metadata={'category': 'result'})
    
    # エッジ
    net.add_edge("x", "plus", function="arg1")
    net.add_edge("one", "plus", function="arg2")
    net.add_edge("plus", "result", function="apply")
    
    # ラムダセル
    net.add_lambda("x", "plus", "result")
    
    return net


def create_duplication_net() -> InteractionNet:
    """複製の例：! x &L= 7; (x₀ + x₁)"""
    net = InteractionNet("Duplication")
    
    # ノード
    net.add_node("input", "Int", "7", metadata={'category': 'data'})
    net.add_node("x0", "Int", metadata={'category': 'data'})
    net.add_node("x1", "Int", metadata={'category': 'data'})
    net.add_node("plus", "Int→Int→Int", metadata={'category': 'function'})
    net.add_node("result", "Int", "14", metadata={'category': 'result'})
    
    # デュプリケータセル
    net.add_duplicator("input", "x0", "x1", "L")
    
    # エッジ
    net.add_edge("x0", "plus", function="arg1")
    net.add_edge("x1", "plus", function="arg2")
    net.add_edge("plus", "result", function="apply")
    
    return net


def create_superposition_net() -> InteractionNet:
    """重ね合わせの例：&L{method1, method2}"""
    net = InteractionNet("Superposition")
    
    # ノード
    net.add_node("input", "Data", metadata={'category': 'data'})
    net.add_node("method1", "Method1", metadata={'category': 'function'})
    net.add_node("method2", "Method2", metadata={'category': 'function'})
    net.add_node("result1", "Result", metadata={'category': 'result'})
    net.add_node("result2", "Result", metadata={'category': 'result'})
    
    # 重ね合わせセル
    net.add_superposition("input", "method1", "method2", "L")
    
    # エッジ
    net.add_edge("method1", "result1", function="compute")
    net.add_edge("method2", "result2", function="compute")
    
    return net


if __name__ == "__main__":
    # 例1: 簡単な関数
    print("=== Simple Function: λx.(x + 1) ===")
    net1 = create_simple_net()
    print(net1.to_dot())
    print()
    
    # 例2: 複製
    print("=== Duplication: ! x &L= 7; (x₀ + x₁) ===")
    net2 = create_duplication_net()
    print(net2.to_dot())
    print()
    
    # 例3: 重ね合わせ
    print("=== Superposition: &L{method1, method2} ===")
    net3 = create_superposition_net()
    print(net3.to_dot())
