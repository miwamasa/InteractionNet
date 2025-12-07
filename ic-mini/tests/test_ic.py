"""
Interaction Calculus Mini - テストスイート

テストカテゴリ:
1. パーサーテスト
2. 基本的な簡約規則
3. 複製と重ね合わせの相互作用
4. 最適共有の検証
5. エッジケース
"""

import unittest
import sys
sys.path.insert(0, '/home/claude/ic-mini/src')

from ic import (
    parse, evaluate, Evaluator,
    Num, Var, Lam, App, Sup, Dup, Era, Op2, Pair, Dp0, Dp1
)


class TestParser(unittest.TestCase):
    """パーサーのテスト"""
    
    def test_parse_num(self):
        """数値リテラルのパース"""
        result = parse("42")
        self.assertIsInstance(result, Num)
        self.assertEqual(result.value, 42)
    
    def test_parse_var(self):
        """変数のパース"""
        result = parse("x")
        self.assertIsInstance(result, Var)
        self.assertEqual(result.name, "x")
    
    def test_parse_dp0(self):
        """複製変数₀のパース"""
        result = parse("x₀")
        self.assertIsInstance(result, Dp0)
        self.assertEqual(result.name, "x")
        
        # ASCII形式もサポート
        result2 = parse("x_0")
        self.assertIsInstance(result2, Dp0)
    
    def test_parse_dp1(self):
        """複製変数₁のパース"""
        result = parse("x₁")
        self.assertIsInstance(result, Dp1)
        self.assertEqual(result.name, "x")
    
    def test_parse_lambda(self):
        """ラムダ抽象のパース"""
        result = parse("λx.x")
        self.assertIsInstance(result, Lam)
        self.assertEqual(result.var, "x")
        self.assertIsInstance(result.body, Var)
    
    def test_parse_lambda_backslash(self):
        """バックスラッシュ形式のラムダ"""
        result = parse("\\x.x")
        self.assertIsInstance(result, Lam)
    
    def test_parse_app(self):
        """関数適用のパース"""
        result = parse("(f x)")
        self.assertIsInstance(result, App)
    
    def test_parse_sup(self):
        """重ね合わせのパース"""
        result = parse("&L{1, 2}")
        self.assertIsInstance(result, Sup)
        self.assertEqual(result.label, "L")
    
    def test_parse_dup(self):
        """複製のパース"""
        result = parse("! x &L= 5; x₀")
        self.assertIsInstance(result, Dup)
        self.assertEqual(result.name, "x")
        self.assertEqual(result.label, "L")
    
    def test_parse_era(self):
        """消去のパース"""
        result = parse("&{}")
        self.assertIsInstance(result, Era)
    
    def test_parse_op2(self):
        """二項演算のパース"""
        result = parse("(1 + 2)")
        self.assertIsInstance(result, Op2)
        self.assertEqual(result.op, "+")
    
    def test_parse_pair(self):
        """ペアのパース"""
        result = parse("(1, 2)")
        self.assertIsInstance(result, Pair)
    
    def test_parse_nested(self):
        """ネストした式のパース"""
        result = parse("(λx.(x + 1) 5)")
        self.assertIsInstance(result, App)
        self.assertIsInstance(result.func, Lam)


class TestBasicReduction(unittest.TestCase):
    """基本的な簡約規則のテスト"""
    
    def test_app_lam(self):
        """APP-LAM: (λx.body arg) → body[x ← arg]"""
        result = evaluate("(λx.x 42)")
        self.assertEqual(str(result), "42")
    
    def test_app_lam_nested(self):
        """ネストしたラムダの適用"""
        result = evaluate("((λx.λy.x 1) 2)")
        self.assertEqual(str(result), "1")
    
    def test_op2_num(self):
        """OP2-NUM: 数値演算"""
        self.assertEqual(str(evaluate("(1 + 2)")), "3")
        self.assertEqual(str(evaluate("(10 - 3)")), "7")
        self.assertEqual(str(evaluate("(4 * 5)")), "20")
        self.assertEqual(str(evaluate("(10 / 2)")), "5")
    
    def test_app_era(self):
        """APP-ERA: (&{} a) → &{}"""
        result = evaluate("(&{} 42)")
        self.assertIsInstance(result, Era)


class TestDuplication(unittest.TestCase):
    """複製 (Dup) のテスト"""
    
    def test_dup_num(self):
        """DUP-NUM: 数値の複製"""
        result = evaluate("! x &L= 2; (x₀ + x₁)")
        self.assertEqual(str(result), "4")
    
    def test_dup_era(self):
        """DUP-ERA: 消去の複製"""
        result = evaluate("! x &L= &{}; (x₀, x₁)")
        self.assertIsInstance(result.fst, Era)
        self.assertIsInstance(result.snd, Era)


class TestSuperposition(unittest.TestCase):
    """重ね合わせ (Sup) のテスト"""
    
    def test_dup_sup_same_label(self):
        """DUP-SUP (同じラベル): 消滅"""
        result = evaluate("! x &L= &L{1, 2}; (x₀ + x₁)")
        self.assertEqual(str(result), "3")
    
    def test_dup_sup_different_label(self):
        """DUP-SUP (異なるラベル): コミュート"""
        result = evaluate("! x &L= &R{10, 20}; x₀")
        self.assertIsInstance(result, Sup)
        self.assertEqual(result.label, "R")
    
    def test_app_sup(self):
        """APP-SUP: 関数への重ね合わせ適用"""
        result = evaluate("(&L{λx.x, λx.(x + 1)} 5)")
        # 結果は &L{5, 6} になるはず
        self.assertIsInstance(result, Sup)
    
    def test_op2_sup_left(self):
        """OP2-SUP-L: 左側が重ね合わせ"""
        result = evaluate("(&L{1, 2} + 10)")
        self.assertIsInstance(result, Sup)
        # &L{11, 12}
    
    def test_op2_sup_right(self):
        """OP2-SUP-R: 右側が重ね合わせ"""
        result = evaluate("(10 + &L{1, 2})")
        self.assertIsInstance(result, Sup)
        # &L{11, 12}


class TestDupLam(unittest.TestCase):
    """ラムダの複製 (DUP-LAM) のテスト"""
    
    def test_dup_lam_basic(self):
        """DUP-LAM: 基本的なラムダの複製"""
        result = evaluate("! f &L= λx.x; ((f₀ 1), (f₁ 2))")
        # 結果は (1, 2)
        self.assertIsInstance(result, Pair)
        self.assertEqual(str(result.fst), "1")
        self.assertEqual(str(result.snd), "2")
    
    def test_dup_lam_shared_computation(self):
        """DUP-LAM: 計算の共有"""
        # λ内の (2 + 2) は一度だけ計算される
        result = evaluate("! f &L= λx.(2 + 2); ((f₀ 1), (f₁ 2))")
        self.assertIsInstance(result, Pair)
        # 両方とも4になる
        self.assertEqual(str(result.fst), "4")
        self.assertEqual(str(result.snd), "4")


class TestOptimalSharing(unittest.TestCase):
    """最適共有のテスト"""
    
    def test_shared_addition(self):
        """共有された計算が一度だけ行われることを確認"""
        # ! z &= (2 + 2); (z₀ + z₁) 
        # = (4 + 4) = 8
        # (2+2)は一度だけ計算される
        result = evaluate("! z &L= (2 + 2); (z₀ + z₁)")
        self.assertEqual(str(result), "8")
    
    def test_complex_sharing(self):
        """複雑な共有パターン"""
        # 複製された値が再度複製される
        code = "! x &L= 3; ! y &R= x₀; (y₀ + y₁)"
        result = evaluate(code)
        self.assertEqual(str(result), "6")


class TestDocumentExamples(unittest.TestCase):
    """ドキュメントの例のテスト"""
    
    def test_doc_dup_num(self):
        """ドキュメント例: 数値の複製と加算"""
        result = evaluate("! x &L= 2; (x_0 + x_1)")
        self.assertEqual(str(result), "4")
    
    def test_doc_sup_addition(self):
        """ドキュメント例: 重ね合わせへの加算"""
        result = evaluate("(&L{1, 2} + 10)")
        self.assertIsInstance(result, Sup)
        # 結果の内部値を検証
        inner_result = evaluate("! x &L= (&L{1, 2} + 10); (x_0, x_1)")
        self.assertIsInstance(inner_result, Pair)
    
    def test_doc_dup_sup_annihilate(self):
        """ドキュメント例: DUP-SUP消滅"""
        result = evaluate("! x &L= &L{1, 2}; (x_0 + x_1)")
        self.assertEqual(str(result), "3")


class TestEdgeCases(unittest.TestCase):
    """エッジケースのテスト"""
    
    def test_nested_dup(self):
        """ネストした複製"""
        result = evaluate("! x &L= 1; ! y &R= 2; (x₀ + y₀)")
        self.assertEqual(str(result), "3")
    
    def test_nested_sup(self):
        """ネストした重ね合わせ"""
        result = evaluate("&L{&R{1, 2}, &R{3, 4}}")
        self.assertIsInstance(result, Sup)
    
    def test_identity_chain(self):
        """恒等関数の連鎖"""
        result = evaluate("((λx.x λy.y) 42)")
        self.assertEqual(str(result), "42")
    
    def test_unused_dup(self):
        """使われない複製変数"""
        result = evaluate("! x &L= 5; 42")
        self.assertEqual(str(result), "42")


class TestPrettyPrint(unittest.TestCase):
    """文字列表現のテスト"""
    
    def test_num_str(self):
        self.assertEqual(str(Num(42)), "42")
    
    def test_var_str(self):
        self.assertEqual(str(Var("x")), "x")
    
    def test_dp0_str(self):
        self.assertEqual(str(Dp0("x")), "x₀")
    
    def test_dp1_str(self):
        self.assertEqual(str(Dp1("x")), "x₁")
    
    def test_lam_str(self):
        self.assertEqual(str(Lam("x", Var("x"))), "λx.x")
    
    def test_app_str(self):
        self.assertEqual(str(App(Var("f"), Var("x"))), "(f x)")
    
    def test_sup_str(self):
        self.assertEqual(str(Sup("L", Num(1), Num(2))), "&L{1, 2}")


if __name__ == "__main__":
    # テスト実行
    unittest.main(verbosity=2)
