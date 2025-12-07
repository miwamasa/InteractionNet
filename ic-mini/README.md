# Interaction Calculus Mini

Interaction Calculus（相互作用計算）の教育用簡易処理系です。

## 概要

Interaction Calculusは、ラムダ計算を拡張した計算モデルで、**最適な遅延評価**を実現します。通常の遅延評価では、値を複数回使うと計算も複数回行われますが、Interaction Calculusでは「複製」と「重ね合わせ」という2つのプリミティブにより、ラムダの内部でも計算の共有が可能になります。

## インストール

```bash
# リポジトリをクローン（またはファイルをコピー）
cd ic-mini

# 依存関係なし（純粋なPython）
python src/ic.py
```

## 使い方

### REPL（対話モード）

```bash
python src/ic.py
```

```
ic> (λx.x 42)
=> 42

ic> ! x &L= 2; (x₀ + x₁)
=> 4

ic> :h   # ヘルプ表示
ic> :d   # デバッグモード切替
ic> :q   # 終了
```

### コマンドライン

```bash
python src/ic.py "(λx.x 42)"
# => 42
```

### Pythonからの利用

```python
from ic import parse, evaluate

# パースのみ
ast = parse("λx.(x + 1)")
print(ast)  # λx.(x + 1)

# 評価
result = evaluate("(λx.(x + 1) 5)")
print(result)  # 6

# デバッグモード
result = evaluate("! x &L= 2; (x₀ + x₁)", debug=True)
```

## 文法

```
項 ::=
  | 数値        42, 0, 123
  | 変数        x, foo, my_var
  | 複製変数    x₀, x₁, x_0, x_1
  | ラムダ      λx.body  または  \x.body
  | 適用        (f x)
  | 重ね合わせ  &L{a, b}
  | 複製        ! x &L= v; t
  | 消去        &{}
  | 演算        (a + b), (a - b), (a * b), (a / b)
  | ペア        (a, b)
```

## 主要な簡約規則

### APP-LAM（関数適用）

```
(λx.body arg) → body[x ← arg]
```

例:
```
(λx.x 42) → 42
```

### DUP-NUM（数値の複製）

```
! x &L= n; t → t[x₀ ← n, x₁ ← n]
```

例:
```
! x &L= 2; (x₀ + x₁) → (2 + 2) → 4
```

### DUP-SUP（複製と重ね合わせ）

同じラベルの場合（消滅）:
```
! x &L= &L{a, b}; t → t[x₀ ← a, x₁ ← b]
```

例:
```
! x &L= &L{1, 2}; (x₀ + x₁) → (1 + 2) → 3
```

異なるラベルの場合（コミュート）:
```
! x &L= &R{a, b}; t → (複雑な変換)
```

### APP-SUP（重ね合わせへの適用）

```
(&L{f, g} a) → ! x &L= a; &L{(f x₀), (g x₁)}
```

### DUP-LAM（ラムダの複製）

```
! f &L= λx.body; t → (ラムダを複製し、本体を共有)
```

これが最適共有の核心です！

## 最適共有の例

```
! f &L= λx.(2 + 2); (f₀ 10, f₁ 20)
```

この式では:
1. ラムダ `λx.(2 + 2)` が複製される
2. `(2 + 2)` の計算は**一度だけ**行われる
3. 結果 `4` が両方のコピーで共有される

## テスト

```bash
python -m pytest tests/ -v

# または
python tests/test_ic.py
```

## ファイル構成

```
ic-mini/
├── src/
│   └── ic.py          # メインモジュール（パーサー、評価器、REPL）
├── tests/
│   └── test_ic.py     # テストスイート
└── README.md          # このファイル
```

## 理論的背景

Interaction Calculusは、Lafont (1997) の **Interaction Combinators** と密接に関連しています。主な対応:

| Interaction Combinators | Interaction Calculus |
|------------------------|---------------------|
| γ (Constructor)        | λ (Lambda)          |
| δ (Duplicator)         | & (Superposition)   |
| ε (Eraser)             | &{} (Erasure)       |

詳細は [HVM4のドキュメント](https://github.com/HigherOrderCO/HVM) を参照してください。

## 制限事項

この実装は教育目的の簡易版です:

- 一部の高度な機能（動的ラベル、パターンマッチングなど）は未実装
- パフォーマンス最適化なし
- エラーメッセージは最小限

## 参考文献

- [HVM (Higher-order Virtual Machine)](https://github.com/HigherOrderCO/HVM)
- Lafont, Y. (1997). Interaction Combinators
- [Optimal Reduction](https://en.wikipedia.org/wiki/Optimal_reduction)
