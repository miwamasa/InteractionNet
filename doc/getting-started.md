# はじめての Interaction Calculus 統一理論

## このガイドについて

このドキュメントは、**Interaction Calculus、Interaction Net、Type Inhabitation** の統一理論を、これから学び始める方のためのガイドです。

数学的な厳密性よりも、**直感的な理解**と**実用的な使い方**に重点を置いています。

---

## 学習の進め方

### 推奨される学習順序

```
1. このガイド（基本概念の理解）
   ↓
2. Interaction Calculus の実装を試す（ic-mini/）
   ↓
3. 統一理論のドキュメントを読む（unified-theory.md）
   ↓
4. GHG事例で実践を学ぶ（ghg-case-study.md）
   ↓
5. 自分のプロジェクトに応用
```

---

## 基本概念の理解

### 1. なぜ三つの視点が必要なのか？

**例え**: レストランでの料理の作り方を考えてみましょう。

```
┌─────────────────────────────────────────┐
│  料理を作る = 計算する                    │
└─────────────────────────────────────────┘
         │              │              │
         │              │              │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │  レシピ  │    │ キッチン │    │  メニュー │
    │ (手順)   │    │ (構造)   │    │ (選択)   │
    └─────────┘    └─────────┘    └─────────┘
    Interaction     Interaction     Type
    Calculus        Net             Inhabitation
```

- **Interaction Calculus（レシピ）**: **どう作るか**の手順
- **Interaction Net（キッチン）**: **誰がどこで何をするか**の構造
- **Type Inhabitation（メニュー）**: **どんな料理が作れるか**の選択肢

**三つが揃って初めて、効率的に料理（計算）ができます！**

---

### 2. Interaction Calculus の基本

#### 最も重要な3つの概念

**1. Superposition（重ね合わせ）= 複数の選択肢**

```
料理の例:
  「ソースは何にしますか?」
  → &Sauce{トマト, クリーム, デミグラス}

プログラムの例:
  「数値を文字列に変換する方法は?」
  → &Convert{toString, toHex, toBinary}
```

**効果**: 一つの定義で、複数のバリエーションを同時に扱える。

**2. Duplication（複製）= データの共有**

```
料理の例:
  「鶏肉を買ってきた」
  → 一部は焼き鳥に、一部は唐揚げに
  （でも、鶏肉自体は一つ）

プログラムの例:
  「エネルギーデータを読み込んだ」
  → Scope1 の計算にも、Scope2 の計算にも使う
  （でも、データは一度だけ読み込む）
```

**効果**: メモリと計算を節約できる。

**3. Labels（ラベル）= 区別**

```
料理の例:
  &前菜{...}, &メイン{...}, &デザート{...}
  → コースの順番を明示

プログラムの例:
  &Scope1{...}, &Scope2{...}, &Scope3{...}
  → スコープの区別を明示
```

**効果**: 異なる種類の計算を区別できる。

---

### 3. Interaction Net の基本

#### グラフで考える

**ノード（Node）** = データや型を表す箱

```
┌──────────────┐
│   データ     │
│   型: Int    │
│   値: 42     │
└──────────────┘
```

**エッジ（Edge）** = 変換を表す矢印

```
┌────┐    関数: f    ┌────┐
│ 42 │  ───────────→ │ 84 │
└────┘   (x → x*2)   └────┘
```

**セル（Cell）** = 計算の道具

```
δ (デュプリケータ): 複製する道具
  入力: 1つ
  出力: 2つ

γ (コンストラクタ): 組み立てる道具
  入力: 複数
  出力: 1つ

ε (イレーサー): 消す道具
  入力: 1つ
  出力: 0
```

#### 簡単な例

**問題**: 数値を二乗する

```
入力: 5

ステップ1: 複製
  5 → δ → (5, 5)

ステップ2: 掛け算
  (5, 5) → × → 25

出力: 25
```

**グラフ表現**:

```
┌───┐
│ 5 │
└─┬─┘
  │
  δ (複製)
  │
┌─┴─┐
│   │
5   5
│   │
└─┬─┘
  │
  × (掛け算)
  │
┌─▼─┐
│25 │
└───┘
```

---

### 4. Type Inhabitation の基本

#### 型とは何か？

**型** = データの種類や契約

```
Int: 整数
String: 文字列
Bool: 真偽値

EnergyData: エネルギーデータ
GHGReport: GHGレポート
```

#### Type Inhabitation 問題

**問題**: 「ある型の値を作る方法はあるか？」

**例1**: `Int → String` の値（変換関数）は？

```
方法1: toString
  42 → "42"

方法2: toHex
  42 → "0x2A"

方法3: toBinary
  42 → "101010"
```

**答え**: 3つの方法がある！（3つの inhabitant）

**例2**: `EnergyData → GHGReport` の値（変換パス）は？

```
方法1: MOE係数 + Location-based
  EnergyData → Scope1(MOE) → Scope2(Loc) → GHGReport

方法2: MOE係数 + Market-based
  EnergyData → Scope1(MOE) → Scope2(Mkt) → GHGReport

方法3: GHG係数 + Location-based
  EnergyData → Scope1(GHG) → Scope2(Loc) → GHGReport

方法4: GHG係数 + Market-based
  EnergyData → Scope1(GHG) → Scope2(Mkt) → GHGReport
```

**答え**: 4つの方法がある！

---

## 実践: 簡単な例から始める

### 例1: 数値の二乗（最も簡単）

#### Interaction Calculus で書く

```haskell
-- 方法1: 直接計算
square1 = λx.(x * x)

-- 方法2: 複製を使う
square2 = λx.(! y &L= x; (y₀ * y₁))
```

#### Interaction Net で可視化

```
┌─────┐
│  x  │ (入力)
└──┬──┘
   │
   δ (複製、ラベル L)
   │
┌──┴──┐
│     │
x₀    x₁
│     │
└──┬──┘
   │
   × (掛け算)
   │
┌──▼──┐
│ x²  │ (出力)
└─────┘
```

#### Type Inhabitation で確認

```
型: Int → Int

Inhabitant（住人）:
  - square1 : Int → Int
  - square2 : Int → Int
  （両方とも同じ型を持つ）
```

---

### 例2: 複数の変換方法（Superposition）

#### 問題設定

数値を文字列に変換する。**3つの方法**がある。

#### Interaction Calculus で書く

```haskell
convert = &Format{
  toString,   -- "42"
  toHex,      -- "0x2A"
  toBinary    -- "101010"
}

-- 使い方
result = convert 42
-- 結果: 3つの文字列が生成される
```

#### Interaction Net で可視化

```
        ┌─────────┐
        │   42    │ (入力: Int)
        └────┬────┘
             │
      ┌──────┼──────┐
      │      │      │
      │      │      │
  toString toHex toBinary
      │      │      │
      ▼      ▼      ▼
    "42"  "0x2A" "101010"
    (3つの出力: String)
```

#### Type Inhabitation で確認

```
型: Int → String

Inhabitant（住人）= 3つの変換パス:
  1. toString
  2. toHex
  3. toBinary
```

---

### 例3: データの共有（Duplication）

#### 問題設定

エネルギーデータを読み込み、Scope1 と Scope2 の両方で使う。

#### Interaction Calculus で書く

```haskell
-- エネルギーデータを複製
! energy &E= read_energy_data();

-- energy₀ を Scope1 で使う
scope1 = calculate_scope1(energy₀)

-- energy₁ を Scope2 で使う
scope2 = calculate_scope2(energy₁)

-- レポートを生成
report = make_report(scope1, scope2)
```

#### Interaction Net で可視化

```
┌──────────────┐
│ EnergyData   │ (一度だけ読み込み)
└──────┬───────┘
       │
    ┌──δ──┐ (Duplicator、ラベル E)
    │     │
    ▼     ▼
energy₀ energy₁
    │     │
    │     │
    ▼     ▼
 Scope1 Scope2
    │     │
    └──┬──┘
       ▼
  GHGReport
```

#### Type Inhabitation で確認

```
型: EnergyData → GHGReport

パス:
  EnergyData
    → [duplicate] → (EnergyData, EnergyData)
    → [scope1, scope2] → (Scope1Data, Scope2Data)
    → [aggregate] → GHGReport
```

---

## 実装を試してみる

### ステップ1: Interaction Calculus を試す

```bash
# ic-mini ディレクトリに移動
cd ic-mini

# REPL を起動
python src/ic.py

# 簡単な式を試す
ic> (λx.x 42)
=> 42

ic> ! x &L= 5; (x₀ + x₁)
=> 10

ic> &L{1, 2}
=> &L{1, 2}
```

### ステップ2: Interaction Net を可視化

```bash
# icnet-demo ディレクトリに移動
cd ../icnet-demo

# デモを実行
python demo.py

# GHGネットを可視化
python -c "
from ghg_net_visualizer import GHGInteractionNet
net = GHGInteractionNet()
print(net.to_dot_styled())
" > ghg.dot

# SVG に変換（Graphviz 必要）
dot -Tsvg ghg.dot -o ghg.svg
```

### ステップ3: Type Inhabitation を試す

```python
# Python スクリプトで試す
from interaction_net import InteractionNet

# ネットを作成
net = InteractionNet("MyNet")

# ノードを追加
net.add_node("int_val", "Int", "42")
net.add_node("str_val", "String")

# エッジ（変換関数）を追加
net.add_edge("int_val", "str_val", function="toString")

# パスを探索
paths = net.find_paths("int_val", "str_val")
print(f"見つかったパス: {len(paths)}個")
for path in paths:
    print(f"  {path[0].source.id} --[{path[0].function}]--> {path[0].target.id}")
```

---

## よくある質問

### Q1: なぜ Superposition が便利なのですか？

**A**: 複数の選択肢を**一つの定義**で扱えるからです。

**従来の方法**:
```python
# 4パターンを手動で書く
report1 = calc(moe, location)
report2 = calc(moe, market)
report3 = calc(ghg, location)
report4 = calc(ghg, market)
```

**Superposition を使う**:
```haskell
report = &Report{
  &Coef{moe, ghg},
  &Method{location, market}
}
-- 自動的に4パターン生成
```

### Q2: Duplication は普通のコピーと何が違うのですか？

**A**: **共有**です。データはコピーされず、参照されます。

```
通常のコピー:
  data1 = [1, 2, 3]
  data2 = data1.copy()  # メモリを2倍使う

Duplication:
  ! x &L= [1, 2, 3];
  -- x₀ と x₁ は同じデータを指す（メモリは1つ）
```

### Q3: Type Inhabitation は何の役に立つのですか？

**A**: **証明の探索**と**証跡の記録**です。

```
問題: A → B への変換方法は？

Type Inhabitation:
  → すべての変換パスを自動探索
  → 各パスの正当性を型で保証
  → 証跡（どのパスを通ったか）を記録
```

### Q4: いつ使うべきですか？

**A**: 以下のような場合に有効です：

1. **複数の方法で計算したい**
   - Superposition を使う

2. **データを効率的に共有したい**
   - Duplication を使う

3. **計算の証跡が必要**
   - Type Inhabitation を使う

4. **計算フローを可視化したい**
   - Interaction Net を使う

---

## 次のステップ

### 初級

1. `ic-mini/README.md` を読む
2. REPL で基本的な式を試す
3. `tests/test_ic.py` のテストを読む

### 中級

1. `doc/unified-theory.md` を読む
2. Interaction Net の構造を理解する
3. Type Inhabitation のアルゴリズムを学ぶ

### 上級

1. `doc/ghg-case-study.md` を読む
2. GHG事例の実装を理解する
3. 自分のドメインに応用する

---

## 参考資料

### 本プロジェクトのドキュメント

- `doc/unified-theory.md` - 統一理論の詳細
- `doc/ghg-case-study.md` - GHG事例の解説
- `ic-mini/README.md` - Interaction Calculus の実装
- `icnet-demo/INTERACTION_NET_GUIDE.md` - Interaction Net の詳細

### 外部リソース

- [HVM (Higher-order Virtual Machine)](https://github.com/HigherOrderCO/HVM)
- [Interaction Combinators (Lafont 1997)](https://en.wikipedia.org/wiki/Interaction_nets)
- [Optimal Reduction](https://en.wikipedia.org/wiki/Optimal_reduction)
- [Type Inhabitation](https://en.wikipedia.org/wiki/Type_inhabitation_problem)

---

## まとめ

**Interaction Calculus、Interaction Net、Type Inhabitation** の統一理論は、以下を提供します：

1. **表現力**: 複雑な計算を簡潔に記述
2. **効率性**: 最適共有による高速化
3. **視覚性**: グラフによる直感的理解
4. **証明性**: 型による正当性の保証

これらが統合された体系は、**理論的に美しく、実用的に強力**です。

**さあ、始めましょう！**

---

**作成日**: 2025年
**バージョン**: 1.0.0
**対象**: 初学者〜中級者
