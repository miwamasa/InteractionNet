"""
Interaction Calculus Mini - シンプルな処理系

このモジュールは Interaction Calculus の核心部分を実装します：
- ラムダ計算 (λx.body, application)
- 複製 (Duplication): ! x &= v; t
- 重ね合わせ (Superposition): &{a, b}
- 数値と基本演算
"""

from dataclasses import dataclass
from typing import Union, Optional, Dict, List
from abc import ABC, abstractmethod
import re


# =============================================================================
# AST (抽象構文木)
# =============================================================================

class Term(ABC):
    """すべての項の基底クラス"""
    @abstractmethod
    def __str__(self) -> str:
        pass


@dataclass
class Var(Term):
    """変数: x"""
    name: str
    
    def __str__(self) -> str:
        return self.name


@dataclass
class Dp0(Term):
    """複製変数の第1要素: x₀"""
    name: str
    
    def __str__(self) -> str:
        return f"{self.name}₀"


@dataclass
class Dp1(Term):
    """複製変数の第2要素: x₁"""
    name: str
    
    def __str__(self) -> str:
        return f"{self.name}₁"


@dataclass
class Num(Term):
    """数値リテラル"""
    value: int
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass
class Lam(Term):
    """ラムダ抽象: λx.body"""
    var: str
    body: Term
    
    def __str__(self) -> str:
        return f"λ{self.var}.{self.body}"


@dataclass
class App(Term):
    """関数適用: (f x)"""
    func: Term
    arg: Term
    
    def __str__(self) -> str:
        return f"({self.func} {self.arg})"


@dataclass
class Sup(Term):
    """重ね合わせ: &L{a, b}"""
    label: str
    fst: Term
    snd: Term
    
    def __str__(self) -> str:
        return f"&{self.label}{{{self.fst}, {self.snd}}}"


@dataclass
class Dup(Term):
    """複製: ! x &L= v; t"""
    name: str
    label: str
    value: Term
    body: Term
    
    def __str__(self) -> str:
        return f"! {self.name} &{self.label}= {self.value}; {self.body}"


@dataclass
class Era(Term):
    """消去: &{}"""
    def __str__(self) -> str:
        return "&{}"


@dataclass
class Op2(Term):
    """二項演算: (a + b)"""
    op: str
    left: Term
    right: Term
    
    def __str__(self) -> str:
        return f"({self.left} {self.op} {self.right})"


@dataclass
class Pair(Term):
    """ペア（構造体）: (a, b)"""
    fst: Term
    snd: Term
    
    def __str__(self) -> str:
        return f"({self.fst}, {self.snd})"


# =============================================================================
# パーサー
# =============================================================================

class ParseError(Exception):
    """パースエラー"""
    pass


class Parser:
    """
    簡易パーサー
    
    文法:
        term ::= num | var | dp0 | dp1 | lam | app | sup | dup | era | op2 | pair
        num  ::= [0-9]+
        var  ::= [a-zA-Z_][a-zA-Z0-9_]*
        dp0  ::= var "₀" | var "_0"
        dp1  ::= var "₁" | var "_1"
        lam  ::= "λ" var "." term | "\\" var "." term
        app  ::= "(" term term ")"
        sup  ::= "&" label "{" term "," term "}"
        dup  ::= "!" var "&" label "=" term ";" term
        era  ::= "&{}"
        op2  ::= "(" term op term ")"
        pair ::= "(" term "," term ")"
        op   ::= "+" | "-" | "*" | "/"
    """
    
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
    
    def parse(self) -> Term:
        self.skip_whitespace()
        term = self.parse_term()
        self.skip_whitespace()
        if self.pos < len(self.text):
            raise ParseError(f"Unexpected character at position {self.pos}: '{self.text[self.pos]}'")
        return term
    
    def skip_whitespace(self):
        while self.pos < len(self.text) and self.text[self.pos] in ' \t\n\r':
            self.pos += 1
    
    def peek(self) -> Optional[str]:
        if self.pos < len(self.text):
            return self.text[self.pos]
        return None
    
    def peek_ahead(self, n: int = 1) -> str:
        return self.text[self.pos:self.pos + n]
    
    def consume(self, expected: str):
        if self.text[self.pos:self.pos + len(expected)] != expected:
            raise ParseError(f"Expected '{expected}' at position {self.pos}")
        self.pos += len(expected)
        self.skip_whitespace()
    
    def parse_term(self) -> Term:
        self.skip_whitespace()
        c = self.peek()
        
        if c is None:
            raise ParseError("Unexpected end of input")
        
        # 消去: &{}
        if self.peek_ahead(3) == "&{}":
            self.consume("&{}")
            return Era()
        
        # 重ね合わせ: &L{a, b}
        if c == '&':
            return self.parse_sup()
        
        # 複製: ! x &L= v; t
        if c == '!':
            return self.parse_dup()
        
        # ラムダ: λx.body or \x.body
        if c == 'λ' or c == '\\':
            return self.parse_lam()
        
        # 括弧で始まる: App, Op2, Pair
        if c == '(':
            return self.parse_paren()
        
        # 数値
        if c.isdigit():
            return self.parse_num()
        
        # 変数（Dp0, Dp1を含む）
        if c.isalpha() or c == '_':
            return self.parse_var()
        
        raise ParseError(f"Unexpected character '{c}' at position {self.pos}")
    
    def parse_num(self) -> Num:
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1
        value = int(self.text[start:self.pos])
        self.skip_whitespace()
        return Num(value)
    
    def parse_var(self) -> Union[Var, Dp0, Dp1]:
        start = self.pos
        # 通常のASCII英数字のみを変数名として扱う（ただし_で終わる場合は特殊処理）
        while self.pos < len(self.text):
            c = self.text[self.pos]
            if c.isascii() and (c.isalnum() or c == '_'):
                # _0 や _1 で終わる場合はDp0/Dp1として処理したいので
                # _の後に0か1が来る場合は変数名に含めない
                if c == '_' and self.pos + 1 < len(self.text):
                    next_c = self.text[self.pos + 1]
                    if next_c == '0' or next_c == '1':
                        break
                self.pos += 1
            else:
                break
        name = self.text[start:self.pos]
        
        # 添字チェック: ₀, ₁, _0, _1
        if self.pos < len(self.text):
            if self.text[self.pos] == '₀':
                self.pos += 1
                self.skip_whitespace()
                return Dp0(name)
            elif self.text[self.pos] == '₁':
                self.pos += 1
                self.skip_whitespace()
                return Dp1(name)
            elif self.peek_ahead(2) == '_0':
                self.pos += 2
                self.skip_whitespace()
                return Dp0(name)
            elif self.peek_ahead(2) == '_1':
                self.pos += 2
                self.skip_whitespace()
                return Dp1(name)
        
        self.skip_whitespace()
        return Var(name)
    
    def parse_lam(self) -> Lam:
        if self.peek() == 'λ':
            self.consume('λ')
        else:
            self.consume('\\')
        
        # 変数名
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        var = self.text[start:self.pos]
        self.skip_whitespace()
        
        self.consume('.')
        body = self.parse_term()
        return Lam(var, body)
    
    def parse_sup(self) -> Sup:
        self.consume('&')
        
        # ラベル（オプション）
        label = ""
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            label += self.text[self.pos]
            self.pos += 1
        if not label:
            label = "L"  # デフォルトラベル
        self.skip_whitespace()
        
        self.consume('{')
        fst = self.parse_term()
        self.consume(',')
        snd = self.parse_term()
        self.consume('}')
        return Sup(label, fst, snd)
    
    def parse_dup(self) -> Dup:
        self.consume('!')
        
        # 変数名
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        name = self.text[start:self.pos]
        self.skip_whitespace()
        
        self.consume('&')
        
        # ラベル
        label = ""
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            label += self.text[self.pos]
            self.pos += 1
        if not label:
            label = "L"
        self.skip_whitespace()
        
        self.consume('=')
        value = self.parse_term()
        self.consume(';')
        body = self.parse_term()
        return Dup(name, label, value, body)
    
    def parse_paren(self) -> Term:
        self.consume('(')
        first = self.parse_term()
        
        # カンマがあればペア
        if self.peek() == ',':
            self.consume(',')
            second = self.parse_term()
            self.consume(')')
            return Pair(first, second)
        
        # 演算子があればOp2
        op = None
        for operator in ['+', '-', '*', '/']:
            if self.peek() == operator:
                op = operator
                self.consume(operator)
                break
        
        if op:
            right = self.parse_term()
            self.consume(')')
            return Op2(op, first, right)
        
        # それ以外はApp
        second = self.parse_term()
        self.consume(')')
        return App(first, second)


def parse(text: str) -> Term:
    """文字列をパースしてASTを返す"""
    return Parser(text).parse()


# =============================================================================
# 評価器 (Reducer)
# =============================================================================

class Evaluator:
    """
    Interaction Calculus の評価器
    
    主要な簡約規則:
    - APP-LAM: (λx.body arg) → body[x ← arg]
    - DUP-SUP (同じラベル): ! x &L= &L{a,b}; t → t[x₀←a, x₁←b]
    - DUP-SUP (異なるラベル): コミュート
    - APP-SUP: (&L{a,b} c) → ! x &L= c; &L{(a x₀), (b x₁)}
    - DUP-LAM: ! f &L= λx.body; t → ...
    - OP2-NUM: (a + b) → a + b
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.fresh_counter = 0
        self.steps = 0
        self.max_steps = 10000
    
    def fresh_name(self, prefix: str = "v") -> str:
        """新しい一意な変数名を生成"""
        self.fresh_counter += 1
        return f"${prefix}{self.fresh_counter}"
    
    def log(self, msg: str):
        if self.debug:
            print(f"[Step {self.steps}] {msg}")
    
    def evaluate(self, term: Term) -> Term:
        """項を正規形まで簡約"""
        self.steps = 0
        prev = None
        while str(term) != str(prev) and self.steps < self.max_steps:
            prev = term
            term = self.reduce(term)
            self.steps += 1
        return term
    
    def reduce(self, term: Term) -> Term:
        """1ステップ簡約を試みる"""
        
        # Num, Var, Era は既に正規形
        if isinstance(term, (Num, Var, Dp0, Dp1, Era)):
            return term
        
        # App
        if isinstance(term, App):
            return self.reduce_app(term)
        
        # Dup
        if isinstance(term, Dup):
            return self.reduce_dup(term)
        
        # Lam
        if isinstance(term, Lam):
            return Lam(term.var, self.reduce(term.body))
        
        # Sup
        if isinstance(term, Sup):
            return Sup(term.label, self.reduce(term.fst), self.reduce(term.snd))
        
        # Op2
        if isinstance(term, Op2):
            return self.reduce_op2(term)
        
        # Pair
        if isinstance(term, Pair):
            return Pair(self.reduce(term.fst), self.reduce(term.snd))
        
        return term
    
    def reduce_app(self, app: App) -> Term:
        func = self.reduce(app.func)
        arg = app.arg
        
        # APP-LAM: (λx.body arg) → body[x ← arg]
        if isinstance(func, Lam):
            self.log(f"APP-LAM: ({func} {arg})")
            return self.substitute(func.body, func.var, arg)
        
        # APP-SUP: (&L{a,b} c) → ! x &L= c; &L{(a x₀), (b x₁)}
        if isinstance(func, Sup):
            self.log(f"APP-SUP: ({func} {arg})")
            x = self.fresh_name("x")
            return Dup(
                x, func.label, arg,
                Sup(func.label, App(func.fst, Dp0(x)), App(func.snd, Dp1(x)))
            )
        
        # APP-ERA: (&{} a) → &{}
        if isinstance(func, Era):
            self.log(f"APP-ERA: ({func} {arg})")
            return Era()
        
        return App(func, self.reduce(arg))
    
    def reduce_dup(self, dup: Dup) -> Term:
        value = self.reduce(dup.value)
        
        # まずbodyにDp0/Dp1が含まれているか確認
        has_dp0 = self.contains_dp(dup.body, dup.name, 0)
        has_dp1 = self.contains_dp(dup.body, dup.name, 1)
        
        # どちらも使われていなければbodyを返す
        if not has_dp0 and not has_dp1:
            self.log(f"DUP-UNUSED: {dup}")
            return self.reduce(dup.body)
        
        # DUP-NUM: ! x &L= n; t → t[x₀←n, x₁←n]
        if isinstance(value, Num):
            self.log(f"DUP-NUM: {dup}")
            result = self.substitute_dp(dup.body, dup.name, value, value)
            return self.reduce(result)
        
        # DUP-ERA: ! x &L= &{}; t → t[x₀←&{}, x₁←&{}]
        if isinstance(value, Era):
            self.log(f"DUP-ERA: {dup}")
            result = self.substitute_dp(dup.body, dup.name, Era(), Era())
            return self.reduce(result)
        
        # DUP-SUP (同じラベル): ! x &L= &L{a,b}; t → t[x₀←a, x₁←b]
        if isinstance(value, Sup) and value.label == dup.label:
            self.log(f"DUP-SUP (annihilate): {dup}")
            result = self.substitute_dp(dup.body, dup.name, value.fst, value.snd)
            return self.reduce(result)
        
        # DUP-SUP (異なるラベル): コミュート
        if isinstance(value, Sup) and value.label != dup.label:
            self.log(f"DUP-SUP (commute): {dup}")
            a_name = self.fresh_name("a")
            b_name = self.fresh_name("b")
            result = Dup(
                a_name, dup.label, value.fst,
                Dup(
                    b_name, dup.label, value.snd,
                    self.substitute_dp(
                        dup.body, dup.name,
                        Sup(value.label, Dp0(a_name), Dp0(b_name)),
                        Sup(value.label, Dp1(a_name), Dp1(b_name))
                    )
                )
            )
            return self.reduce(result)
        
        # DUP-LAM: ! f &L= λx.body; t → ...
        if isinstance(value, Lam):
            self.log(f"DUP-LAM: {dup}")
            x0 = self.fresh_name("x")
            x1 = self.fresh_name("x")
            b_name = self.fresh_name("b")
            
            # body内のxを &L{x0, x1} で置換
            new_body = self.substitute(value.body, value.var, Sup(dup.label, Var(x0), Var(x1)))
            
            # f₀ ← λx0.B₀, f₁ ← λx1.B₁
            result = Dup(
                b_name, dup.label, new_body,
                self.substitute_dp(
                    dup.body, dup.name,
                    Lam(x0, Dp0(b_name)),
                    Lam(x1, Dp1(b_name))
                )
            )
            return self.reduce(result)
        
        # DUP-PAIR: ! x &L= (a,b); t → ...
        if isinstance(value, Pair):
            self.log(f"DUP-PAIR: {dup}")
            a_name = self.fresh_name("a")
            b_name = self.fresh_name("b")
            result = Dup(
                a_name, dup.label, value.fst,
                Dup(
                    b_name, dup.label, value.snd,
                    self.substitute_dp(
                        dup.body, dup.name,
                        Pair(Dp0(a_name), Dp0(b_name)),
                        Pair(Dp1(a_name), Dp1(b_name))
                    )
                )
            )
            return self.reduce(result)
        
        # valueがまだ簡約可能な場合
        if str(value) != str(dup.value):
            return Dup(dup.name, dup.label, value, dup.body)
        
        # bodyを簡約してみる
        new_body = self.reduce(dup.body)
        if str(new_body) != str(dup.body):
            return Dup(dup.name, dup.label, value, new_body)
        
        return Dup(dup.name, dup.label, value, new_body)
    
    def contains_dp(self, term: Term, name: str, idx: int) -> bool:
        """項にname₀またはname₁が含まれているか確認"""
        if isinstance(term, Dp0):
            return term.name == name and idx == 0
        if isinstance(term, Dp1):
            return term.name == name and idx == 1
        if isinstance(term, (Var, Num, Era)):
            return False
        if isinstance(term, Lam):
            return self.contains_dp(term.body, name, idx)
        if isinstance(term, App):
            return self.contains_dp(term.func, name, idx) or self.contains_dp(term.arg, name, idx)
        if isinstance(term, Sup):
            return self.contains_dp(term.fst, name, idx) or self.contains_dp(term.snd, name, idx)
        if isinstance(term, Dup):
            return self.contains_dp(term.value, name, idx) or self.contains_dp(term.body, name, idx)
        if isinstance(term, Op2):
            return self.contains_dp(term.left, name, idx) or self.contains_dp(term.right, name, idx)
        if isinstance(term, Pair):
            return self.contains_dp(term.fst, name, idx) or self.contains_dp(term.snd, name, idx)
        return False
    
    def reduce_op2(self, op2: Op2) -> Term:
        left = self.reduce(op2.left)
        right = self.reduce(op2.right)
        
        # OP2-NUM: (#a + #b) → #(a + b)
        if isinstance(left, Num) and isinstance(right, Num):
            self.log(f"OP2-NUM: ({left} {op2.op} {right})")
            result = self.compute_op(op2.op, left.value, right.value)
            return Num(result)
        
        # OP2-SUP-L: (&L{a,b} + y) → ! Y &L= y; &L{(a + Y₀), (b + Y₁)}
        if isinstance(left, Sup):
            self.log(f"OP2-SUP-L: {op2}")
            y = self.fresh_name("y")
            return Dup(
                y, left.label, right,
                Sup(left.label, Op2(op2.op, left.fst, Dp0(y)), Op2(op2.op, left.snd, Dp1(y)))
            )
        
        # OP2-SUP-R: (#n + &L{a,b}) → &L{(#n + a), (#n + b)}
        if isinstance(right, Sup):
            self.log(f"OP2-SUP-R: {op2}")
            return Sup(right.label, Op2(op2.op, left, right.fst), Op2(op2.op, left, right.snd))
        
        # OP2-ERA-L: (&{} + y) → &{}
        if isinstance(left, Era):
            self.log(f"OP2-ERA-L: {op2}")
            return Era()
        
        # OP2-ERA-R: (x + &{}) → &{}
        if isinstance(right, Era):
            self.log(f"OP2-ERA-R: {op2}")
            return Era()
        
        return Op2(op2.op, left, right)
    
    def compute_op(self, op: str, a: int, b: int) -> int:
        """演算を実行"""
        if op == '+':
            return a + b
        elif op == '-':
            return a - b
        elif op == '*':
            return a * b
        elif op == '/':
            return a // b if b != 0 else 0
        else:
            raise ValueError(f"Unknown operator: {op}")
    
    def substitute(self, term: Term, var: str, value: Term) -> Term:
        """term内のvarをvalueで置換"""
        if isinstance(term, Var):
            return value if term.name == var else term
        
        if isinstance(term, Dp0):
            return term
        
        if isinstance(term, Dp1):
            return term
        
        if isinstance(term, Num):
            return term
        
        if isinstance(term, Era):
            return term
        
        if isinstance(term, Lam):
            if term.var == var:
                return term  # シャドウイング
            return Lam(term.var, self.substitute(term.body, var, value))
        
        if isinstance(term, App):
            return App(
                self.substitute(term.func, var, value),
                self.substitute(term.arg, var, value)
            )
        
        if isinstance(term, Sup):
            return Sup(
                term.label,
                self.substitute(term.fst, var, value),
                self.substitute(term.snd, var, value)
            )
        
        if isinstance(term, Dup):
            return Dup(
                term.name,
                term.label,
                self.substitute(term.value, var, value),
                self.substitute(term.body, var, value)
            )
        
        if isinstance(term, Op2):
            return Op2(
                term.op,
                self.substitute(term.left, var, value),
                self.substitute(term.right, var, value)
            )
        
        if isinstance(term, Pair):
            return Pair(
                self.substitute(term.fst, var, value),
                self.substitute(term.snd, var, value)
            )
        
        return term
    
    def substitute_dp(self, term: Term, name: str, val0: Term, val1: Term) -> Term:
        """term内のname₀をval0、name₁をval1で置換"""
        if isinstance(term, Dp0):
            return val0 if term.name == name else term
        
        if isinstance(term, Dp1):
            return val1 if term.name == name else term
        
        if isinstance(term, (Var, Num, Era)):
            return term
        
        if isinstance(term, Lam):
            return Lam(term.var, self.substitute_dp(term.body, name, val0, val1))
        
        if isinstance(term, App):
            return App(
                self.substitute_dp(term.func, name, val0, val1),
                self.substitute_dp(term.arg, name, val0, val1)
            )
        
        if isinstance(term, Sup):
            return Sup(
                term.label,
                self.substitute_dp(term.fst, name, val0, val1),
                self.substitute_dp(term.snd, name, val0, val1)
            )
        
        if isinstance(term, Dup):
            return Dup(
                term.name,
                term.label,
                self.substitute_dp(term.value, name, val0, val1),
                self.substitute_dp(term.body, name, val0, val1)
            )
        
        if isinstance(term, Op2):
            return Op2(
                term.op,
                self.substitute_dp(term.left, name, val0, val1),
                self.substitute_dp(term.right, name, val0, val1)
            )
        
        if isinstance(term, Pair):
            return Pair(
                self.substitute_dp(term.fst, name, val0, val1),
                self.substitute_dp(term.snd, name, val0, val1)
            )
        
        return term


def evaluate(text: str, debug: bool = False) -> Term:
    """文字列をパースして評価"""
    term = parse(text)
    evaluator = Evaluator(debug=debug)
    return evaluator.evaluate(term)


# =============================================================================
# REPL
# =============================================================================

def repl():
    """対話型REPL"""
    print("Interaction Calculus Mini REPL")
    print("Commands: :q (quit), :d (toggle debug), :h (help)")
    print()
    
    debug = False
    
    while True:
        try:
            line = input("ic> ").strip()
        except EOFError:
            break
        
        if not line:
            continue
        
        if line == ':q':
            break
        elif line == ':d':
            debug = not debug
            print(f"Debug mode: {'ON' if debug else 'OFF'}")
            continue
        elif line == ':h':
            print_help()
            continue
        
        try:
            result = evaluate(line, debug=debug)
            print(f"=> {result}")
        except Exception as e:
            print(f"Error: {e}")


def print_help():
    """ヘルプを表示"""
    print("""
Syntax:
  λx.body  or  \\x.body    Lambda abstraction
  (f x)                    Application
  &L{a, b}                 Superposition with label L
  ! x &L= v; t             Duplication
  &{}                      Erasure
  (a + b)                  Binary operation (+, -, *, /)
  (a, b)                   Pair
  x₀ or x_0                First dup variable
  x₁ or x_1                Second dup variable

Examples:
  (λx.x 42)                => 42 (identity)
  ! x &L= 2; (x₀ + x₁)     => 4 (duplication)
  (&L{1, 2} + 10)          => &L{11, 12} (superposition)
  ! x &L= &L{1, 2}; x₀     => 1 (annihilation)
""")


# =============================================================================
# メイン
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # コマンドライン引数があればそれを評価
        code = ' '.join(sys.argv[1:])
        result = evaluate(code)
        print(result)
    else:
        # REPLを起動
        repl()
