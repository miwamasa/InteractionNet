# Interaction NET Visualization

**工場生産管理データ → GHGレポート生成を、Interaction NETとして可視化**

## 概要

このプロジェクトは、Interaction Calculus（相互作用計算）の計算プロセスを、グラフ（Interaction NET）として可視化するシステムです。特に、GHG（温室効果ガス）レポート生成という実用的な事例を通じて、Type Inhabitation（型探索）の概念を示します。

## 理論的背景

### Interaction NET とは

Interaction NETは、Lafont (1997) の **Interaction Combinators** に基づく計算モデルのグラフ表現です。

#### 基本要素

| 要素 | 記号 | 説明 | Interaction Calculus |
|------|------|------|---------------------|
| **Constructor** | γ | ラムダ抽象、データ構築 | λx.body |
| **Duplicator** | δ | 複製、重ね合わせ | ! x &L= v; t, &L{a,b} |
| **Eraser** | ε | 消去 | &{} |

#### ノードとエッジ

- **ノード（Node）**: 型やデータを表す
- **エッジ（Edge）**: データフローと計算関数を表す
- **セル（Cell）**: 計算要素（γ, δ, ε）

### Type Inhabitation（型探索）

Type Inhabitationは、「ある型の値を構築する方法を探す」問題です。

```
型（ノード）:        A ────→ B ────→ C
変換関数（エッジ）:    f       g
パス（証明）:       f ∘ g : A → C
```

Interaction Calculusでの表現：
- **Superposition（重ね合わせ）**: 複数の証明を同時に保持
- **Duplication（複製）**: 証明の共有・再利用
- **Labels（ラベル）**: 異なる戦略の区別

## GHG事例の可視化

### 問題設定

工場の生産管理データから、GHGレポートを生成する。

```
入力データ:
- EnergyData (エネルギー消費)
- MaterialData (原材料投入)
- TransportData (輸送)
- WasteData (廃棄物)

出力:
- GHGReport (Scope1 + Scope2 + Scope3)
```

### Interaction NETによる表現

#### 1. Superposition（重ね合わせ）= 複数の計算方法

```python
# Scope1の計算方法の選択肢
&Scope1{
    energy_to_scope1_moe,      # 日本環境省係数
    energy_to_scope1_ghg       # GHGプロトコル係数
}

# Scope2の計算方法の選択肢
&Scope2{
    energy_to_scope2_location,  # Location-based
    energy_to_scope2_market     # Market-based
}
```

結果: **4パターン**のレポートを自動生成
- MOE + Location-based: 42.21 ton-CO2
- MOE + Market-based: 42.20 ton-CO2
- GHG + Location-based: 40.99 ton-CO2
- GHG + Market-based: 40.98 ton-CO2

#### 2. Duplication（複製）= データの共有

```python
# エネルギーデータを複製してScope1とScope2で使用
! energy &E= input_data;

energy₀ → Scope1計算 (直接排出): 18.07 ton
energy₁ → Scope2計算 (電力由来): 0.07 ton
```

#### 3. Labels（ラベル）= スコープの区別

```python
&Scope1{...}  # 直接排出の計算
&Scope2{...}  # 間接排出の計算
&Scope3{...}  # サプライチェーンの計算
```

### ネットワーク構造

```
INPUT               CALCULATION           INTERMEDIATE        OUTPUT
──────────────────────────────────────────────────────────────────────
EnergyData ────┬──→ Scope1 (MOE)    ─┐
               │                     │
               │──→ Scope1 (GHG)    ─┤
               │                     │
               └──→ Scope2 (Loc)    ─┼──→ GHGReport (4パターン)
                  → Scope2 (Mkt)    ─┤
                                     │
MaterialData ─────→ Scope3 (Cat1)  ─┤
TransportData ────→ Scope3 (Cat4)  ─┤
WasteData ────────→ Scope3 (Cat5)  ─┘
```

## 使い方

### 1. インストール

```bash
# Graphvizのインストール（可視化に必要）
apt-get install graphviz

# Pythonライブラリ（不要、標準ライブラリのみ使用）
```

### 2. 基本的な使用

```python
from interaction_net import InteractionNet

# ネットワーク作成
net = InteractionNet("MyNet")

# ノード追加
net.add_node("input", "Int", "42")
net.add_node("output", "String")

# エッジ追加
net.add_edge("input", "output", function="toString")

# 可視化
dot = net.to_dot()
print(dot)
```

### 3. GHGレポート生成の可視化

```python
from ghg_net_visualizer import GHGInteractionNet

# GHGネット生成
ghg_net = GHGInteractionNet()

# スタイル付きDOT形式で出力
dot = ghg_net.to_dot_styled()

# ファイルに保存
with open("ghg_net.dot", "w") as f:
    f.write(dot)

# SVG生成
import subprocess
subprocess.run(["dot", "-Tsvg", "ghg_net.dot", "-o", "ghg_net.svg"])
```

### 4. パス探索（Type Inhabitation）

```python
# パスの探索
paths = net.find_paths("energy_input", "scope1_moe")

for i, path in enumerate(paths, 1):
    print(f"パス {i}:")
    for edge in path:
        print(f"  {edge.source.id} --[{edge.function}]--> {edge.target.id}")
```

## API リファレンス

### InteractionNet クラス

```python
class InteractionNet:
    def __init__(self, name: str)
    
    # ノード操作
    def add_node(self, node_id: str, type_name: str, 
                 value: str = None, **metadata) -> Node
    
    # エッジ操作
    def add_edge(self, source_id: str, target_id: str,
                 label: str = None, function: str = None, 
                 **metadata) -> Edge
    
    # セル操作
    def add_duplicator(self, input_id: str, output1_id: str, 
                      output2_id: str, label: str = "L") -> Cell
    
    def add_superposition(self, node_id: str, left_id: str, 
                         right_id: str, label: str = "L") -> Cell
    
    def add_lambda(self, param_id: str, body_id: str, 
                  result_id: str) -> Cell
    
    # パス探索
    def find_paths(self, start_id: str, end_id: str) -> List[List[Edge]]
    
    # 変換
    def to_dot(self, show_cells: bool = True, 
              highlight_paths: List[List[Edge]] = None) -> str
    
    def to_json(self) -> str
```

### GHGInteractionNet クラス

```python
class GHGInteractionNet(InteractionNet):
    def __init__(self)
    
    def to_dot_styled(self) -> str
    # カラフルなスタイル付きDOT形式
```

## テストケース

```bash
# すべてのテストを実行
python test_interaction_net.py

# 個別テストクラスの実行
python -m unittest test_interaction_net.TestInteractionNet
python -m unittest test_interaction_net.TestGHGNet
```

### テストカバレッジ

- ✓ ノード・エッジの基本操作（10テスト）
- ✓ セル（デュプリケータ、重ね合わせ、ラムダ）の生成（5テスト）
- ✓ パス探索（Type Inhabitation）（3テスト）
- ✓ GHG特化ネットの構造（8テスト）
- ✓ 可視化（DOT/JSON形式）（2テスト）

**合計: 25テスト、すべて成功**

## 出力例

### DOT形式

```dot
digraph "GHG_Report_Generation" {
  rankdir=LR;
  
  subgraph cluster_input {
    label="INPUT";
    "energy_input" [label="EnergyData", shape=box, ...];
    ...
  }
  
  subgraph cluster_calculation {
    label="CALCULATION";
    "scope1_moe" [label="Scope1 (MOE)\n18.07 ton-CO2", ...];
    ...
  }
  
  "energy_input" -> "scope1_moe" [label="energy_to_scope1_moe", ...];
  ...
}
```

### JSON形式

```json
{
  "name": "GHG_Report_Generation",
  "nodes": [
    {
      "id": "energy_input",
      "type": "EnergyData",
      "value": "Gas: 200 m³\nOil: 20 kL\nElec: 100 kWh",
      "metadata": {"category": "input"}
    },
    ...
  ],
  "edges": [
    {
      "source": "energy_input",
      "target": "scope1_moe",
      "function": "energy_to_scope1_moe",
      "label": "Scope1"
    },
    ...
  ],
  "cells": [...]
}
```

## 実用的な価値

| 課題 | Interaction NET的解決 |
|------|----------------------|
| 複数の排出係数で試算したい | Superposition で全パターン同時計算 |
| 計算の監査証跡が必要 | パス（変換関数の列）が証跡になる |
| 中間計算を再利用したい | Duplication でデータ共有 |
| スコープ別に分けて管理 | Labels で区別・対応付け |
| 計算方法の違いを比較 | Superposition展開で差分可視化 |

## ファイル構成

```
.
├── interaction_net.py          # Interaction NETの基本実装
├── ghg_net_visualizer.py       # GHG特化の可視化
├── test_interaction_net.py     # テストスイート（25テスト）
├── INTERACTION_NET_GUIDE.md    # このドキュメント
└── outputs/
    ├── ghg_net.svg            # GHGネットの可視化（SVG）
    ├── ghg_net.dot            # DOT形式
    ├── ghg_net.json           # JSON形式
    ├── type_inhabitation.svg  # Type Inhabitationデモ
    └── ...
```

## 理論的参考文献

- Lafont, Y. (1997). **Interaction Combinators**
- [HVM (Higher-order Virtual Machine)](https://github.com/HigherOrderCO/HVM)
- [Optimal Reduction](https://en.wikipedia.org/wiki/Optimal_reduction)
- [Type Inhabitation](https://en.wikipedia.org/wiki/Type_inhabitation_problem)

## 今後の拡張

- [ ] より複雑なパターンマッチング
- [ ] 動的なラベル生成
- [ ] インタラクティブな可視化（D3.js）
- [ ] パフォーマンス最適化（大規模ネット）
- [ ] 他のドメインへの応用（API設計、データパイプライン等）

## ライセンス

このプロジェクトは教育目的の実装です。自由に使用・改変してください。

---

**作成日**: 2024年
**バージョン**: 1.0.0
