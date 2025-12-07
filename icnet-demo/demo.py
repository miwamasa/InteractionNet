#!/usr/bin/env python3
"""
Interaction NET デモスクリプト

このスクリプトは、Interaction NETの主要機能をデモします。

使用方法:
    python demo.py
"""

import sys
import os

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from interaction_net import (
    InteractionNet,
    create_simple_net,
    create_duplication_net,
    create_superposition_net
)
from ghg_net_visualizer import GHGInteractionNet, create_type_inhabitation_demo


def print_header(title):
    """ヘッダーを表示"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def demo_basic_net():
    """基本的なネットワークのデモ"""
    print_header("1. 基本的なネットワーク: λx.(x + 1)")
    
    net = create_simple_net()
    
    print(f"\nノード数: {len(net.nodes)}")
    print(f"エッジ数: {len(net.edges)}")
    print(f"セル数: {len(net.cells)}")
    
    print("\nノード一覧:")
    for node_id, node in net.nodes.items():
        value_str = f" = {node.value}" if node.value else ""
        print(f"  - {node_id}: {node.type_name}{value_str}")
    
    print("\nDOT形式 (抜粋):")
    dot = net.to_dot()
    print(dot[:300] + "...")


def demo_duplication():
    """複製のデモ"""
    print_header("2. 複製（Duplication）: ! x &L= 7; (x₀ + x₁)")
    
    net = create_duplication_net()
    
    print("\n重要なノード:")
    print(f"  - input (入力): {net.nodes['input'].value}")
    print(f"  - x0 (複製1): {net.nodes['x0'].type_name}")
    print(f"  - x1 (複製2): {net.nodes['x1'].type_name}")
    print(f"  - result (結果): {net.nodes['result'].value}")
    
    print("\nデュプリケータセル:")
    for cell_id, cell in net.cells.items():
        if "dup" in cell_id:
            print(f"  - {cell_id}: ラベル={cell.label}, ポート数={len(cell.ports)}")


def demo_superposition():
    """重ね合わせのデモ"""
    print_header("3. 重ね合わせ（Superposition）: &L{method1, method2}")
    
    net = create_superposition_net()
    
    print("\n重要なノード:")
    print(f"  - input: {net.nodes['input'].type_name}")
    print(f"  - method1: {net.nodes['method1'].type_name}")
    print(f"  - method2: {net.nodes['method2'].type_name}")
    
    print("\n重ね合わせセル:")
    for cell_id, cell in net.cells.items():
        if cell.metadata.get('superposition'):
            print(f"  - {cell_id}: ラベル={cell.label}, ポート数={len(cell.ports)}")


def demo_ghg_net():
    """GHGネットワークのデモ"""
    print_header("4. GHGレポート生成ネットワーク")
    
    ghg_net = GHGInteractionNet()
    
    print(f"\nネットワーク統計:")
    print(f"  - ノード数: {len(ghg_net.nodes)}")
    print(f"  - エッジ数: {len(ghg_net.edges)}")
    print(f"  - セル数: {len(ghg_net.cells)}")
    
    # カテゴリ別にノードを集計
    categories = {}
    for node in ghg_net.nodes.values():
        cat = node.metadata.get('category', 'other')
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nカテゴリ別ノード数:")
    for cat, count in sorted(categories.items()):
        print(f"  - {cat}: {count}")
    
    # 入力ノード
    print("\n入力ノード:")
    for node_id in ["energy_input", "material_input", "transport_input", "waste_input"]:
        if node_id in ghg_net.nodes:
            node = ghg_net.nodes[node_id]
            print(f"  - {node_id}: {node.type_name}")
    
    # 出力ノード
    print("\n出力レポート（4パターン）:")
    for node_id in ["report_moe_loc", "report_moe_mkt", "report_ghg_loc", "report_ghg_mkt"]:
        if node_id in ghg_net.nodes:
            node = ghg_net.nodes[node_id]
            value_lines = node.value.split('\n') if node.value else []
            print(f"  - {node_id}: {value_lines[0] if value_lines else node.type_name}")
    
    # セルの統計
    dup_count = sum(1 for c in ghg_net.cells.values() 
                    if not c.metadata.get('superposition'))
    sup_count = sum(1 for c in ghg_net.cells.values() 
                    if c.metadata.get('superposition'))
    
    print("\nセルの統計:")
    print(f"  - デュプリケータ: {dup_count}")
    print(f"  - 重ね合わせ: {sup_count}")


def demo_type_inhabitation():
    """Type Inhabitationのデモ"""
    print_header("5. Type Inhabitation: Int → String")
    
    net = create_type_inhabitation_demo()
    
    print("\n探索問題:")
    print("  Int (42) を String に変換する方法を探す")
    
    # パスの探索
    print("\n発見された証明（パス）:")
    
    # 証明1: 直接
    paths1 = net.find_paths("int_input", "str_direct")
    print(f"\n  証明1 (直接): {len(paths1)} パス")
    if paths1:
        for edge in paths1[0]:
            print(f"    {edge.source.id} --[{edge.function}]--> {edge.target.id}")
    
    # 証明2: Float経由
    paths2 = net.find_paths("int_input", "str_via_float")
    print(f"\n  証明2 (Float経由): {len(paths2)} パス")
    if paths2:
        for edge in paths2[0]:
            print(f"    {edge.source.id} --[{edge.function}]--> {edge.target.id}")
    
    # 証明3: Bool経由
    paths3 = net.find_paths("int_input", "str_via_bool")
    print(f"\n  証明3 (Bool経由): {len(paths3)} パス")
    if paths3:
        for edge in paths3[0]:
            print(f"    {edge.source.id} --[{edge.function}]--> {edge.target.id}")
    
    print(f"\n合計: {len(paths1) + len(paths2) + len(paths3)} 個の証明を発見")


def demo_json_export():
    """JSON出力のデモ"""
    print_header("6. JSON形式でのエクスポート")
    
    net = create_simple_net()
    json_str = net.to_json()
    
    print("\nJSON出力 (抜粋):")
    print(json_str[:400] + "...")
    
    print(f"\n完全なJSONサイズ: {len(json_str)} バイト")


def main():
    """メイン関数"""
    print("\n" + "🌐" * 35)
    print(" " * 15 + "Interaction NET デモ")
    print("🌐" * 35)
    
    try:
        demo_basic_net()
        demo_duplication()
        demo_superposition()
        demo_ghg_net()
        demo_type_inhabitation()
        demo_json_export()
        
        print_header("デモ完了")
        print("\n次のステップ:")
        print("  1. テストを実行: python test_interaction_net.py")
        print("  2. 可視化を確認: outputs/ghg_net.svg")
        print("  3. HTML版を開く: outputs/interaction_net_visualization.html")
        print("  4. ドキュメント: INTERACTION_NET_GUIDE.md")
        
        print("\n✅ すべてのデモが正常に完了しました！\n")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
