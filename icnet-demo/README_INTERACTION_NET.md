# Interaction NET for GHG Reporting

**Interaction Calculus を用いたGHGレポート生成の可視化システム**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Tests](https://img.shields.io/badge/tests-25%2F25-brightgreen)

## 🎯 プロジェクト概要

このプロジェクトは、**Interaction Calculus**（相互作用計算）の理論を応用し、工場の生産管理データからGHG（温室効果ガス）レポートを生成するプロセスを、**Interaction NET**として可視化します。

### 主な特徴

- ✅ **Type Inhabitation（型探索）**の実装
- ✅ **Superposition（重ね合わせ）**による複数計算方法の同時保持
- ✅ **Duplication（複製）**によるデータ共有
- ✅ **Graphviz**による美しい可視化
- ✅ **25個のテストケース**で品質保証

## 📊 可視化例

### GHGレポート生成ネットワーク

```
INPUT               CALCULATION           OUTPUT
──────────────────────────────────────────────────
EnergyData ────┬──→ Scope1 (MOE)    ─┐
               │    18.07 ton-CO2   │
               │                     │
               ├──→ Scope1 (GHG)    ─┤
               │    16.85 ton-CO2   │  Report
               │                     ├─→ (4パターン)
               ├──→ Scope2 (Loc)    ─┤  42.21 ton
               │    0.07 ton-CO2    │
               │                     │
               └──→ Scope2 (Mkt)    ─┤
                    0.06 ton-CO2    │
                                     │
MaterialData ─────→ Scope3 (Cat1)  ─┤
                    15.0 ton-CO2    │
TransportData ────→ Scope3 (Cat4)  ─┤
                    7.83 ton-CO2    │
WasteData ────────→ Scope3 (Cat5)  ─┘
                    1.25 ton-CO2
```

## 🚀 クイックスタート

### 1. インストール

```bash
# Graphvizのインストール（可視化に必要）
sudo apt-get install graphviz

# リポジトリのクローン
git clone <repository-url>
cd interaction-net-ghg
```

### 2. 基本的な使用

```python
# GHGネットワークの可視化
from ghg_net_visualizer import GHGInteractionNet

ghg_net = GHGInteractionNet()
print(ghg_net.to_dot_styled())
```

### 3. 可視化の生成

```bash
# SVGファイルを生成
python ghg_net_visualizer.py

# 出力先: /mnt/user-data/outputs/ghg_net.svg
```

### 4. テストの実行

```bash
# すべてのテストを実行
python test_interaction_net.py

# 結果:
# Tests run: 25
# Successes: 25
# ✓ All tests passed!
```

## 📚 理論的背景

### Interaction NET

Interaction NETは、Lafont (1997)の**Interaction Combinators**に基づく計算モデルです。

| 要素 | 記号 | 説明 |
|------|------|------|
| Constructor | γ | ラムダ抽象、データ構築 |
| Duplicator | δ | 複製、重ね合わせ |
| Eraser | ε | 消去 |

### Type Inhabitation

「ある型の値を構築する方法を探す」問題：

```
型:     EnergyData → Scope1Data → GHGReport
パス:   energy_to_scope1_moe ∘ aggregate
```

### Interaction Calculusとの対応

| Interaction Calculus | Interaction NET |
|---------------------|-----------------|
| `&L{a, b}` | Superposition Cell (δ) |
| `! x &L= v; t` | Duplicator Cell (δ) |
| `λx.body` | Constructor Cell (γ) |
| `&{}` | Eraser Cell (ε) |

## 🔧 主要な機能

### 1. Superposition（重ね合わせ）

複数の計算方法を同時に保持：

```python
# Scope1の計算方法の選択肢
&Scope1{
    energy_to_scope1_moe,  # 日本環境省係数
    energy_to_scope1_ghg   # GHGプロトコル係数
}
```

**結果**: 4パターンのレポートを自動生成
- MOE + Location-based: 42.21 ton-CO2
- MOE + Market-based: 42.20 ton-CO2
- GHG + Location-based: 40.99 ton-CO2
- GHG + Market-based: 40.98 ton-CO2

### 2. Duplication（複製）

データの効率的な共有：

```python
! energy &E= input_data;

energy₀ → Scope1計算: 18.07 ton
energy₁ → Scope2計算: 0.07 ton
```

### 3. Labels（ラベル）

スコープの区別と対応付け：

```python
&Scope1{...}  # 直接排出
&Scope2{...}  # 間接排出
&Scope3{...}  # サプライチェーン
```

## 📁 プロジェクト構成

```
interaction-net-ghg/
├── src/
│   ├── interaction_net.py         # Interaction NETの基本実装
│   ├── ghg_net_visualizer.py      # GHG特化の可視化
│   └── test_interaction_net.py    # テストスイート（25テスト）
├── docs/
│   └── INTERACTION_NET_GUIDE.md   # 詳細ガイド
├── outputs/
│   ├── ghg_net.svg               # GHGネット可視化（SVG）
│   ├── ghg_net.dot               # DOT形式
│   ├── ghg_net.json              # JSON形式
│   └── type_inhabitation.svg     # Type Inhabitationデモ
└── README.md                      # このファイル
```

## 🧪 テストケース

### テストカバレッジ

| カテゴリ | テスト数 | 説明 |
|---------|----------|------|
| 基本操作 | 10 | ノード・エッジ・セルの操作 |
| パス探索 | 3 | Type Inhabitation |
| GHG特化 | 8 | GHGネットの構造検証 |
| 可視化 | 2 | DOT/JSON形式の出力 |
| サンプル | 2 | 例題ネットの検証 |
| **合計** | **25** | **すべて成功** |

### テスト実行

```bash
# 全テスト実行
python test_interaction_net.py

# 個別テストクラス
python -m unittest test_interaction_net.TestInteractionNet
python -m unittest test_interaction_net.TestGHGNet
python -m unittest test_interaction_net.TestTypeInhabitation
```

## 📖 API ドキュメント

### InteractionNet クラス

```python
# ネットワーク作成
net = InteractionNet("MyNet")

# ノード追加
net.add_node("n1", "Type", "value", category="input")

# エッジ追加
net.add_edge("n1", "n2", function="transform")

# セル追加
net.add_duplicator("input", "out1", "out2", label="L")
net.add_superposition("node", "left", "right", label="S")

# パス探索
paths = net.find_paths("start", "end")

# 可視化
dot = net.to_dot()
json_str = net.to_json()
```

詳細は [INTERACTION_NET_GUIDE.md](docs/INTERACTION_NET_GUIDE.md) を参照。

## 🎨 可視化オプション

### スタイル付きDOT形式

```python
ghg_net = GHGInteractionNet()
dot = ghg_net.to_dot_styled()

# 特徴:
# - カラフルな色分け（Scope1=赤、Scope2=青、Scope3=緑）
# - カテゴリ別のサブグラフ
# - 美しいレイアウト
```

### パスのハイライト

```python
paths = net.find_paths("energy_input", "report_moe_loc")
dot = net.to_dot(highlight_paths=paths)
```

## 💡 実用的な価値

| 課題 | Interaction NET的解決 |
|------|----------------------|
| 複数の排出係数で試算 | Superposition で全パターン同時計算 |
| 計算の監査証跡 | パス（変換関数の列）が証跡になる |
| 中間計算の再利用 | Duplication でデータ共有 |
| スコープ別の管理 | Labels で区別・対応付け |
| 計算方法の比較 | Superposition展開で差分可視化 |

## 🔬 理論的参考文献

- Lafont, Y. (1997). **Interaction Combinators**
- [HVM (Higher-order Virtual Machine)](https://github.com/HigherOrderCO/HVM)
- [Optimal Reduction](https://en.wikipedia.org/wiki/Optimal_reduction)
- [Type Inhabitation](https://en.wikipedia.org/wiki/Type_inhabitation_problem)

## 🌟 今後の拡張

- [ ] より複雑なパターンマッチング
- [ ] 動的なラベル生成
- [ ] インタラクティブな可視化（D3.js、React）
- [ ] パフォーマンス最適化（大規模ネット）
- [ ] 他のドメインへの応用
  - APIパイプライン設計
  - データ変換ワークフロー
  - ビジネスルールエンジン

## 📝 ライセンス

このプロジェクトは教育目的の実装です。自由に使用・改変してください。

## 👥 貢献

Issue、Pull Requestを歓迎します。

---

**作成**: 2024年  
**バージョン**: 1.0.0  
**テスト**: 25/25 passed ✅
