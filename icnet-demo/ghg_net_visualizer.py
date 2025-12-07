"""
GHG Report Generation as Interaction NET

工場生産管理データ → GHGレポートのパイプラインを
Interaction NETとして可視化します。

Type Inhabitation の視点：
- 型（ノード）: EnergyData, Scope1Data, GHGReport など
- 関数（エッジ）: energy_to_scope1_moe, material_to_scope3 など
- パス探索: EnergyData → ... → GHGReport
- 複数の証明: Superposition による複数の計算方法
"""

from interaction_net import InteractionNet, CellType
from typing import List, Dict


class GHGInteractionNet(InteractionNet):
    """GHGレポート生成専用のInteraction NET"""
    
    def __init__(self):
        super().__init__("GHG_Report_Generation")
        self._build_net()
    
    def _build_net(self):
        """GHGレポート生成のネットワークを構築"""
        
        # === 入力データノード ===
        self.add_node("energy_input", "EnergyData", 
                     "Gas: 200 m³\nOil: 20 kL\nElec: 100 kWh",
                     category='input')
        
        self.add_node("material_input", "MaterialData",
                     "Steel: 30 ton",
                     category='input')
        
        self.add_node("transport_input", "TransportData",
                     "Truck: 1000 km",
                     category='input')
        
        self.add_node("waste_input", "WasteData",
                     "Waste: 5 ton",
                     category='input')
        
        # === Scope1 計算方法の選択肢（Superposition） ===
        self.add_node("scope1_moe", "Scope1Data",
                     "MOE係数使用\n18.07 ton-CO2",
                     category='calculation')
        
        self.add_node("scope1_ghg", "Scope1Data",
                     "GHGプロトコル係数\n16.85 ton-CO2",
                     category='calculation')
        
        # 重ね合わせセル
        self.add_superposition("energy_input", "scope1_moe", "scope1_ghg", "Scope1")
        
        # === Scope2 計算方法の選択肢（Superposition） ===
        self.add_node("scope2_location", "Scope2Data",
                     "Location-based\n0.07 ton-CO2",
                     category='calculation')
        
        self.add_node("scope2_market", "Scope2Data",
                     "Market-based\n0.06 ton-CO2",
                     category='calculation')
        
        # エネルギーデータを複製してScope2にも使用（Duplication）
        self.add_node("energy_dup", "EnergyData", category='intermediate')
        self.add_duplicator("energy_input", "energy_dup", "scope2_location", "Energy")
        
        self.add_superposition("energy_dup", "scope2_location", "scope2_market", "Scope2")
        
        # === Scope3 計算（Category別） ===
        self.add_node("scope3_cat1", "Scope3Data",
                     "Cat1: 購入物品\n15.0 ton-CO2",
                     category='calculation')
        
        self.add_node("scope3_cat4", "Scope3Data",
                     "Cat4: 輸送\n7.83 ton-CO2",
                     category='calculation')
        
        self.add_node("scope3_cat5", "Scope3Data",
                     "Cat5: 廃棄物\n1.25 ton-CO2",
                     category='calculation')
        
        # 中間集約ノード
        self.add_node("scope3_total", "Scope3Data",
                     "Total: 24.08 ton-CO2",
                     category='intermediate')
        
        # === 変換エッジ（計算関数） ===
        # Energy → Scope1
        self.add_edge("energy_input", "scope1_moe",
                     function="energy_to_scope1_moe",
                     label="Scope1")
        
        self.add_edge("energy_input", "scope1_ghg",
                     function="energy_to_scope1_ghg",
                     label="Scope1")
        
        # Energy → Scope2
        self.add_edge("energy_dup", "scope2_location",
                     function="energy_to_scope2_location",
                     label="Scope2")
        
        self.add_edge("energy_dup", "scope2_market",
                     function="energy_to_scope2_market",
                     label="Scope2")
        
        # Material → Scope3 Cat1
        self.add_edge("material_input", "scope3_cat1",
                     function="material_to_scope3_cat1")
        
        # Transport → Scope3 Cat4
        self.add_edge("transport_input", "scope3_cat4",
                     function="transport_to_scope3_cat4")
        
        # Waste → Scope3 Cat5
        self.add_edge("waste_input", "scope3_cat5",
                     function="waste_to_scope3_cat5")
        
        # Scope3 集約
        self.add_edge("scope3_cat1", "scope3_total", function="sum")
        self.add_edge("scope3_cat4", "scope3_total", function="sum")
        self.add_edge("scope3_cat5", "scope3_total", function="sum")
        
        # === 最終レポート（4パターン） ===
        self.add_node("report_moe_loc", "GHGReport",
                     "MOE + Location\n42.21 ton-CO2",
                     category='output')
        
        self.add_node("report_moe_mkt", "GHGReport",
                     "MOE + Market\n42.20 ton-CO2",
                     category='output')
        
        self.add_node("report_ghg_loc", "GHGReport",
                     "GHG + Location\n40.99 ton-CO2",
                     category='output')
        
        self.add_node("report_ghg_mkt", "GHGReport",
                     "GHG + Market\n40.98 ton-CO2",
                     category='output')
        
        # Scope1 + Scope2 + Scope3 → Report
        self.add_edge("scope1_moe", "report_moe_loc", function="aggregate")
        self.add_edge("scope2_location", "report_moe_loc", function="aggregate")
        self.add_edge("scope3_total", "report_moe_loc", function="aggregate")
        
        self.add_edge("scope1_moe", "report_moe_mkt", function="aggregate")
        self.add_edge("scope2_market", "report_moe_mkt", function="aggregate")
        self.add_edge("scope3_total", "report_moe_mkt", function="aggregate")
        
        self.add_edge("scope1_ghg", "report_ghg_loc", function="aggregate")
        self.add_edge("scope2_location", "report_ghg_loc", function="aggregate")
        self.add_edge("scope3_total", "report_ghg_loc", function="aggregate")
        
        self.add_edge("scope1_ghg", "report_ghg_mkt", function="aggregate")
        self.add_edge("scope2_market", "report_ghg_mkt", function="aggregate")
        self.add_edge("scope3_total", "report_ghg_mkt", function="aggregate")
    
    def to_dot_styled(self) -> str:
        """スタイル付きDOT形式に変換"""
        lines = [
            f'digraph "{self.name}" {{',
            '  rankdir=LR;',
            '  node [fontname="Helvetica", fontsize=10];',
            '  edge [fontname="Helvetica", fontsize=9];',
            '  bgcolor=white;',
            '  splines=ortho;',  # 直角エッジ
            '',
            '  // ノードスタイル定義',
        ]
        
        # カテゴリ別スタイル
        styles = {
            'input': 'shape=box, style=filled, fillcolor="#E3F2FD", color="#1976D2", penwidth=2',
            'calculation': 'shape=ellipse, style=filled, fillcolor="#FFF3E0", color="#F57C00"',
            'intermediate': 'shape=diamond, style=filled, fillcolor="#F3E5F5", color="#7B1FA2"',
            'output': 'shape=box, style="filled,rounded", fillcolor="#E8F5E9", color="#388E3C", penwidth=2',
        }
        
        # ノードをカテゴリでグループ化
        grouped = {}
        for node in self.nodes.values():
            cat = node.metadata.get('category', 'other')
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(node)
        
        # サブグラフでグループ化
        for cat, nodes in grouped.items():
            style = styles.get(cat, 'shape=circle')
            lines.append(f'  subgraph cluster_{cat} {{')
            lines.append(f'    label="{cat.upper()}";')
            lines.append(f'    style=dashed;')
            lines.append(f'    color=gray;')
            
            for node in nodes:
                label = node.type_name
                if node.value:
                    # 改行を含むラベルを整形
                    label = node.value.replace('\n', '\\n')
                
                lines.append(f'    "{node.id}" [label="{label}", {style}];')
            
            lines.append('  }')
            lines.append('')
        
        # セル（重ね合わせ、複製）
        lines.append('  // セル（計算要素）')
        for cell in self.cells.values():
            if cell.cell_type == CellType.DUPLICATOR:
                if cell.metadata.get('superposition'):
                    # 重ね合わせ
                    shape = 'diamond'
                    color = '#FF6B6B'
                    label = f"&{cell.label}{{...}}"
                else:
                    # 複製
                    shape = 'diamond'
                    color = '#4ECDC4'
                    label = f"! &{cell.label}="
                
                lines.append(f'  "{cell.id}" [label="{label}", shape={shape}, '
                           f'style=filled, fillcolor="{color}", fontcolor=white];')
        
        # エッジ
        lines.append('')
        lines.append('  // データフロー')
        for edge in self.edges:
            label = ""
            if edge.function:
                label = edge.function
            if edge.label:
                label += f"\\n[{edge.label}]" if label else f"[{edge.label}]"
            
            # Scope別に色分け
            color = 'black'
            if 'scope1' in edge.function.lower() if edge.function else False:
                color = '#FF5722'
            elif 'scope2' in edge.function.lower() if edge.function else False:
                color = '#2196F3'
            elif 'scope3' in edge.function.lower() if edge.function else False:
                color = '#4CAF50'
            
            label_attr = f'label="{label}"' if label else ''
            lines.append(f'  "{edge.source.id}" -> "{edge.target.id}" '
                       f'[{label_attr}, color="{color}", penwidth=1.5];')
        
        lines.append('}')
        return '\n'.join(lines)


def create_type_inhabitation_demo() -> InteractionNet:
    """Type Inhabitation デモ: Int → String"""
    net = InteractionNet("TypeInhabitation_Demo")
    
    # ノード（型）
    net.add_node("int_input", "Int", "42", category='input')
    
    # 証明1: 直接変換
    net.add_node("str_direct", "String", '"42"', category='output')
    net.add_edge("int_input", "str_direct", 
                function="intToString",
                proof=1, path_length=1)
    
    # 証明2: Float経由
    net.add_node("float_via", "Float", "42.0", category='intermediate')
    net.add_node("str_via_float", "String", '"42.00"', category='output')
    net.add_edge("int_input", "float_via", function="intToFloat", proof=2)
    net.add_edge("float_via", "str_via_float", function="floatToString", proof=2, path_length=2)
    
    # 証明3: Bool経由
    net.add_node("bool_via", "Bool", "true", category='intermediate')
    net.add_node("str_via_bool", "String", '"true"', category='output')
    net.add_edge("int_input", "bool_via", function="isPositive", proof=3)
    net.add_edge("bool_via", "str_via_bool", function="boolToString", proof=3, path_length=2)
    
    # 重ね合わせ: 3つの証明を同時に保持
    net.add_node("str_superposition", "String", 
                "&P{direct, viaFloat, viaBool}",
                category='output')
    net.add_superposition("int_input", "str_direct", "str_via_float", "Proof")
    
    return net


def visualize_all_examples():
    """すべての例を可視化"""
    import subprocess
    import os
    
    examples = [
        ("ghg_net", GHGInteractionNet()),
        ("type_inhabitation", create_type_inhabitation_demo()),
    ]
    
    output_dir = "/mnt/user-data/outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    
    for name, net in examples:
        # DOT形式で保存
        dot_file = f"{output_dir}/{name}.dot"
        if hasattr(net, 'to_dot_styled'):
            dot_content = net.to_dot_styled()
        else:
            dot_content = net.to_dot()
        
        with open(dot_file, 'w') as f:
            f.write(dot_content)
        
        # SVG生成
        svg_file = f"{output_dir}/{name}.svg"
        try:
            subprocess.run(['dot', '-Tsvg', dot_file, '-o', svg_file],
                         check=True, capture_output=True)
            results.append(f"✓ {name}: {svg_file}")
        except subprocess.CalledProcessError as e:
            results.append(f"✗ {name}: Graphviz not available")
        except FileNotFoundError:
            results.append(f"✗ {name}: Graphviz not installed")
        
        # JSON形式でも保存
        json_file = f"{output_dir}/{name}.json"
        with open(json_file, 'w') as f:
            f.write(net.to_json())
        results.append(f"  JSON: {json_file}")
    
    return results


if __name__ == "__main__":
    print("=== GHG Report Generation as Interaction NET ===\n")
    
    # GHGネット生成
    ghg_net = GHGInteractionNet()
    
    print("DOT形式:")
    print(ghg_net.to_dot_styled())
    print()
    
    print("JSON形式:")
    print(ghg_net.to_json())
    print()
    
    # 可視化
    print("=== Visualization ===")
    results = visualize_all_examples()
    for r in results:
        print(r)
