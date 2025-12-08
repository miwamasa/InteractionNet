# Interaction Calculus、Interaction Net、Type Inhabitation の統一理論

## 目次

1. [はじめに](#はじめに)
2. [三つの柱](#三つの柱)
3. [統一的な視点](#統一的な視点)
4. [理論的基礎](#理論的基礎)
5. [実装への写像](#実装への写像)
6. [まとめ](#まとめ)

---

## はじめに

本ドキュメントは、**Interaction Calculus（相互作用計算）**、**Interaction Net（相互作用ネット）**、**Type Inhabitation（型探索）** という三つの概念が、どのように統一的な理論体系を形成しているかを解説します。

これらは互いに独立した理論ではなく、同一の数学的構造を異なる視点から見たものです：

```
┌─────────────────────────────────────────────────┐
│         統一理論：Optimal Computation           │
│  (最適計算 - 無駄のない、共有された計算)          │
└─────────────────────────────────────────────────┘
         │              │              │
         │              │              │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │ Calculus │    │   Net   │    │  Type   │
    │  (計算)   │    │ (構造)   │    │ (証明)   │
    └─────────┘    └─────────┘    └─────────┘
```

### 統一理論の核心

**Lafont (1997) の Interaction Combinators** が理論的基盤を提供し、以下の三つの視点が統合されます：

1. **Interaction Calculus** = **計算の実行方法**（How to compute）
2. **Interaction Net** = **計算の構造**（How it's structured）
3. **Type Inhabitation** = **計算の意味**（What it proves）

---

## 三つの柱

### 1. Interaction Calculus（相互作用計算）

**定義**: ラムダ計算を拡張した計算モデル。最適な共有評価を実現。

#### 基本要素

```
項 ::=
  | λx.body           -- ラムダ抽象（関数定義）
  | (f x)             -- 関数適用
  | ! x &L= v; t      -- 複製（Duplication）
  | &L{a, b}          -- 重ね合わせ（Superposition）
  | &{}               -- 消去（Erasure）
```

#### 核心的な簡約規則

**APP-LAM（関数適用）**:
```
(λx.body arg) → body[x ← arg]
```

**DUP-NUM（数値の複製）**:
```
! x &L= n; t → t[x₀ ← n, x₁ ← n]
```

**DUP-SUP（複製と重ね合わせの相互作用）**:

同じラベル（消滅）:
```
! x &L= &L{a, b}; t → t[x₀ ← a, x₁ ← b]
```

異なるラベル（コミュート）:
```
! x &L= &R{a, b}; t → (新しい複製の生成)
```

**DUP-LAM（ラムダの複製 - 最適共有の核心）**:
```
! f &L= λx.body; t
→ t[f₀ ← λx.body', f₁ ← λx.body']
  where body' は共有された計算
```

#### 特徴

- **最適共有**: 計算結果を複数箇所で再利用
- **遅延評価**: 必要になるまで計算を遅延
- **並列性**: 独立した計算の同時実行
- **決定性**: 計算順序に依存しない結果

---

### 2. Interaction Net（相互作用ネット）

**定義**: Interaction Calculus の計算過程をグラフとして表現したもの。

#### グラフの構成要素

**ノード（Node）**: 型やデータを表す
```
┌─────────┐
│  Type   │  例: Int, String, EnergyData
│  Value  │
└─────────┘
```

**エッジ（Edge）**: データフローと変換関数を表す
```
┌────┐      f: A → B       ┌────┐
│ A  │ ──────────────────→ │ B  │
└────┘                      └────┘
```

**セル（Cell）**: Interaction Combinators の三つの基本要素

| セル | 記号 | 意味 | Interaction Calculus |
|------|------|------|---------------------|
| **Constructor** | γ | ラムダ、データ構築 | λx.body |
| **Duplicator** | δ | 複製 | ! x &L= v; t |
| **Superposition** | δ | 重ね合わせ | &L{a, b} |
| **Eraser** | ε | 消去 | &{} |

#### グラフとしての計算

```
入力ノード → [セル群での変換] → 出力ノード
```

**例**: 数値の二乗を計算
```
┌─────┐   duplicate   ┌─────┐   multiply   ┌─────┐
│  5  │ ─────δ──────→ │ 5,5 │ ─────×─────→ │ 25  │
└─────┘               └─────┘              └─────┘
```

#### Interaction Net の利点

1. **視覚的理解**: 計算過程が一目瞭然
2. **構造の明示**: データフローが明確
3. **並列化**: 独立した部分グラフの同時計算
4. **デバッグ**: ノードごとの状態確認が容易

---

### 3. Type Inhabitation（型探索）

**定義**: ある型を持つ値（またはプログラム）を構築する問題。

#### 型理論との対応

**Curry-Howard同型対応**:
```
論理        型理論          プログラム
─────────────────────────────────────
命題 P      型 T           値 v : T
証明 π      項 e           プログラム
P ⊃ Q       T → U          関数
P ∧ Q       T × U          ペア
∃x.P(x)     Σx:T.U(x)      依存ペア
```

#### Type Inhabitation 問題

**問題**: 型 `T` が与えられたとき、`v : T` となる値 `v` を見つけよ。

**例1**: `Int → Int` の inhabitant（住人）
```haskell
id : Int → Int
id x = x

double : Int → Int
double x = x + x

square : Int → Int
square x = x * x
```

**例2**: `A → B → C` へのパス探索

Interaction Net での表現:
```
┌───┐   f   ┌───┐   g   ┌───┐
│ A │ ────→ │ B │ ────→ │ C │
└───┘       └───┘       └───┘

パス: [f, g]
合成: g ∘ f : A → C
```

#### Interaction Calculus での Type Inhabitation

**重ね合わせ（Superposition）** は複数の証明を同時に保持：

```
&L{証明1, 証明2} : T
```

**例**: `Int → String` への複数の変換
```
&Convert{
  toString : Int → String,
  toHex : Int → String,
  toBinary : Int → String
}
```

結果: **3つの証明**を同時に保持し、後で選択可能。

---

## 統一的な視点

### 三つの視点の対応関係

| Interaction Calculus | Interaction Net | Type Inhabitation |
|---------------------|-----------------|-------------------|
| 項（Term） | ノード（Node） | 型（Type） |
| 簡約（Reduction） | エッジ辿り（Edge Traversal） | 変換（Transformation） |
| λx.body | Constructor セル | 関数型 A → B |
| ! x &L= v; t | Duplicator セル | データの共有 |
| &L{a, b} | Superposition セル | 複数の証明 |
| 評価 | パス探索 | 型の構築 |

### 統一的な計算モデル

```
┌──────────────────────────────────────────────────┐
│           Input（入力データ）                      │
│              型: DataIn                           │
└──────────────────┬───────────────────────────────┘
                   │
        ┌──────────▼──────────┐
        │  Interaction Net    │
        │  ────────────────   │
        │  ノード: 型・値      │ ◄── Type Inhabitation
        │  エッジ: 変換関数    │     証明パスの探索
        │  セル: 計算要素      │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │ Interaction Calculus │ ◄── 計算の実行
        │  簡約規則の適用       │     最適共有の実現
        └──────────┬──────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│           Output（出力結果）                      │
│              型: DataOut                         │
└──────────────────────────────────────────────────┘
```

### 相互作用の美しさ

1. **Interaction Calculus** が**どう計算するか**を定義
2. **Interaction Net** が**構造と依存関係**を可視化
3. **Type Inhabitation** が**何を証明するか**を明確化

この三つが一体となることで、**最適で、視覚的で、証明可能な計算システム**が実現されます。

---

## 理論的基礎

### Lafont's Interaction Combinators (1997)

**三つの基本的なシンボル**:

```
γ (gamma)    - Constructor（構築子）
δ (delta)    - Duplicator（複製子）
ε (epsilon)  - Eraser（消去子）
```

**相互作用規則**（一部）:

```
γ と γ:  コミュート（引数の交換）
γ と δ:  複製の伝播
δ と δ:  消滅（同じラベル）またはコミュート（異なるラベル）
γ と ε:  消去の伝播
δ と ε:  複製先も消去
ε と ε:  消滅
```

これらの規則は、**合流性（Confluence）** と**強正規化性（Strong Normalization）** を持ちます。

### Optimal Reduction（最適簡約）

**Lévy (1978)** による最適簡約理論:

- **共有グラフ簡約**: 同じ部分式を複数回計算しない
- **最小のβ-簡約ステップ**: 無駄な計算を排除
- **並列性の最大化**: 独立した簡約の同時実行

Interaction Calculus は、この理論を**構文レベル**で実現します。

### Linear Logic との関係

**Girard (1987)** の線形論理との対応:

| Linear Logic | Interaction Calculus |
|--------------|---------------------|
| ⊗ (Tensor) | ペア |
| ⊕ (Plus) | 和型 |
| ! (Exponential) | Duplication |
| ? (Why Not) | Weakening/Contraction |

線形論理の証明が、Interaction Net のグラフに対応します。

---

## 実装への写像

### Pythonでの実装例

#### 1. Interaction Calculus の評価器

```python
# ic-mini/src/ic.py から抜粋
def evaluate(term, env={}, debug=False):
    """Interaction Calculus の項を評価"""
    if isinstance(term, Num):
        return term

    elif isinstance(term, Var):
        return env.get(term.name, term)

    elif isinstance(term, Lam):
        return Lam(term.param, evaluate(term.body, env))

    elif isinstance(term, App):
        func = evaluate(term.func, env)
        if isinstance(func, Lam):
            # APP-LAM 規則
            arg = term.arg
            new_env = {**env, func.param: arg}
            return evaluate(func.body, new_env)

    elif isinstance(term, Dup):
        # DUP 規則
        val = evaluate(term.value, env)
        if isinstance(val, Num):
            # DUP-NUM: 数値を複製
            new_env = {
                **env,
                f"{term.var}₀": val,
                f"{term.var}₁": val
            }
            return evaluate(term.body, new_env)
        # ... 他の DUP 規則
```

#### 2. Interaction Net の構築

```python
# icnet-demo/interaction_net.py から抜粋
class InteractionNet:
    def __init__(self, name):
        self.name = name
        self.nodes = {}
        self.edges = []
        self.cells = []

    def add_node(self, node_id, type_name, value=None):
        """ノード（型）を追加"""
        node = Node(node_id, type_name, value)
        self.nodes[node_id] = node
        return node

    def add_edge(self, source_id, target_id, function=None):
        """エッジ（変換関数）を追加"""
        edge = Edge(
            self.nodes[source_id],
            self.nodes[target_id],
            function
        )
        self.edges.append(edge)
        return edge

    def add_duplicator(self, input_id, output1_id, output2_id, label="L"):
        """Duplicator セルを追加"""
        cell = Cell(
            type="duplicator",
            label=label,
            inputs=[self.nodes[input_id]],
            outputs=[self.nodes[output1_id], self.nodes[output2_id]]
        )
        self.cells.append(cell)
        return cell
```

#### 3. Type Inhabitation のパス探索

```python
def find_paths(self, start_id, end_id):
    """Type Inhabitation: 型 start → end のパスを探索"""
    paths = []
    visited = set()

    def dfs(current, path):
        if current == end_id:
            paths.append(path.copy())
            return

        if current in visited:
            return
        visited.add(current)

        # 出力エッジを辿る
        for edge in self.edges:
            if edge.source.id == current:
                path.append(edge)
                dfs(edge.target.id, path)
                path.pop()

        visited.remove(current)

    dfs(start_id, [])
    return paths
```

### 統一的な実行フロー

```python
# 統一フロー: Calculus → Net → Type Inhabitation
def unified_computation(source_code):
    # 1. Interaction Calculus でパース
    ast = parse(source_code)

    # 2. Interaction Net を構築
    net = build_interaction_net(ast)

    # 3. Type Inhabitation でパス探索
    paths = net.find_paths("input", "output")

    # 4. 各パスで評価（並列実行可能）
    results = []
    for path in paths:
        result = evaluate_path(ast, path)
        results.append(result)

    return results
```

---

## まとめ

### 統一理論の本質

**Interaction Calculus、Interaction Net、Type Inhabitation** は、同一の数学的構造を異なる側面から捉えたものです：

```
┌────────────────────────────────────────────┐
│  Optimal Computation（最適計算）            │
│                                            │
│  ∙ 無駄のない計算（共有）                   │
│  ∙ 視覚的な構造（グラフ）                   │
│  ∙ 証明可能性（型）                        │
└────────────────────────────────────────────┘
```

### 三位一体の美しさ

| 視点 | 問い | 答え |
|------|------|------|
| **Interaction Calculus** | どう計算するか？ | 簡約規則による最適実行 |
| **Interaction Net** | 構造はどうなっているか？ | グラフとしての可視化 |
| **Type Inhabitation** | 何を証明するか？ | 型によるパスの探索 |

### 実用的な意義

1. **効率性**: 最適共有による計算の高速化
2. **明瞭性**: グラフによる直感的理解
3. **正確性**: 型による証明の保証
4. **並列性**: 独立した計算の同時実行

これらが統合された体系は、**理論的に美しく、実用的に強力**です。

---

## 次のステップ

1. **GHG事例の学習**: [ghg-case-study.md](./ghg-case-study.md) で実際の応用例を学ぶ
2. **実装の確認**: `ic-mini/` と `icnet-demo/` のコードを読む
3. **理論の深掘り**: 参考文献を読む

### 参考文献

- **Lafont, Y. (1997)**. "Interaction Combinators". *Information and Computation*.
- **Lévy, J.-J. (1978)**. "Réductions correctes et optimales dans le lambda-calcul". *Thèse d'État*.
- **Girard, J.-Y. (1987)**. "Linear Logic". *Theoretical Computer Science*.
- **[HVM (Higher-order Virtual Machine)](https://github.com/HigherOrderCO/HVM)** - 実装の参考
- **[Optimal Reduction](https://en.wikipedia.org/wiki/Optimal_reduction)** - Wikipedia

---

**作成日**: 2025年
**バージョン**: 1.0.0
**ライセンス**: 教育目的の自由使用
