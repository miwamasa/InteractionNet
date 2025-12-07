"""
Type Inhabitation Solver using Interaction Calculus
====================================================

型理論における type inhabitation 問題を、グラフ上のパス探索として解く。
各関数（エッジ）には impl が付随し、パスに沿って計算を実行できる。

概念:
- 型 = ノード (例: Int, String, List[Int], ...)
- 関数 = エッジ (例: toString: Int → String)
- impl = エッジに付随する実際の計算
- 探索 = Start型からGoal型へのパスを見つける
- 計算 = 見つかったパスに沿ってimplを合成・実行

Interaction Calculus の活用:
- Superposition: 複数のパスを同時に探索
- Duplication: 同じ部分パスの共有
- Labels: 異なる探索ブランチの区別
"""

from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any, Optional, Set, Tuple
from abc import ABC, abstractmethod
import sys
sys.path.insert(0, 'src')
from ic import Term, Lam, App, Sup, Dup, Num, Var, Dp0, Dp1, Era, Pair, evaluate, parse


# =============================================================================
# 型システム
# =============================================================================

@dataclass(frozen=True)
class Type:
    """型を表す基底クラス"""
    name: str
    
    def __str__(self):
        return self.name


@dataclass(frozen=True)
class FuncType(Type):
    """関数型 A → B"""
    arg: Type
    ret: Type
    
    def __str__(self):
        return f"({self.arg} → {self.ret})"


@dataclass(frozen=True)
class ListType(Type):
    """リスト型 List[A]"""
    elem: Type
    
    def __str__(self):
        return f"List[{self.elem}]"


@dataclass(frozen=True) 
class OptionType(Type):
    """オプション型 Option[A]"""
    elem: Type
    
    def __str__(self):
        return f"Option[{self.elem}]"


# 基本型
Int = Type("Int")
String = Type("String")
Bool = Type("Bool")
Float = Type("Float")
Unit = Type("Unit")


# =============================================================================
# 関数（エッジ）定義
# =============================================================================

@dataclass
class TypedFunc:
    """
    型付き関数 = グラフのエッジ
    
    - name: 関数名
    - arg_type: 引数の型（始点ノード）
    - ret_type: 戻り値の型（終点ノード）
    - impl: 実際の計算（Python関数）
    - cost: パス探索時のコスト（オプション）
    """
    name: str
    arg_type: Type
    ret_type: Type
    impl: Callable[[Any], Any]
    cost: float = 1.0
    
    def __str__(self):
        return f"{self.name}: {self.arg_type} → {self.ret_type}"
    
    def __call__(self, x):
        return self.impl(x)


# =============================================================================
# 型環境（グラフ）
# =============================================================================

class TypeEnvironment:
    """
    型環境 = 関数のグラフ
    
    ノード: 型
    エッジ: 関数（impl付き）
    """
    
    def __init__(self):
        self.functions: List[TypedFunc] = []
        self.by_arg: Dict[Type, List[TypedFunc]] = {}
        self.by_ret: Dict[Type, List[TypedFunc]] = {}
    
    def add(self, func: TypedFunc):
        """関数を環境に追加"""
        self.functions.append(func)
        
        if func.arg_type not in self.by_arg:
            self.by_arg[func.arg_type] = []
        self.by_arg[func.arg_type].append(func)
        
        if func.ret_type not in self.by_ret:
            self.by_ret[func.ret_type] = []
        self.by_ret[func.ret_type].append(func)
    
    def get_outgoing(self, typ: Type) -> List[TypedFunc]:
        """指定した型から出ていくエッジ（関数）を取得"""
        return self.by_arg.get(typ, [])
    
    def get_incoming(self, typ: Type) -> List[TypedFunc]:
        """指定した型に入ってくるエッジ（関数）を取得"""
        return self.by_ret.get(typ, [])
    
    def get_types(self) -> Set[Type]:
        """環境内のすべての型を取得"""
        types = set()
        for f in self.functions:
            types.add(f.arg_type)
            types.add(f.ret_type)
        return types


# =============================================================================
# パス（証明/項）
# =============================================================================

@dataclass
class Path:
    """
    型から型へのパス = 関数の合成列
    
    これは型理論的には「証明」または「項」に対応する
    """
    steps: List[TypedFunc]
    
    @property
    def start(self) -> Optional[Type]:
        return self.steps[0].arg_type if self.steps else None
    
    @property
    def end(self) -> Optional[Type]:
        return self.steps[-1].ret_type if self.steps else None
    
    @property
    def cost(self) -> float:
        return sum(s.cost for s in self.steps)
    
    def __str__(self):
        if not self.steps:
            return "(empty path)"
        path_str = str(self.start)
        for step in self.steps:
            path_str += f" --[{step.name}]--> {step.ret_type}"
        return path_str
    
    def compose_impl(self) -> Callable[[Any], Any]:
        """パスに沿ったimplを合成"""
        def composed(x):
            result = x
            for step in self.steps:
                result = step.impl(result)
            return result
        return composed
    
    def execute(self, input_value: Any) -> Any:
        """パスに沿って計算を実行"""
        return self.compose_impl()(input_value)
    
    def to_lambda(self) -> str:
        """パスをラムダ式として表現"""
        if not self.steps:
            return "λx.x"
        
        # 内側から構築: f3(f2(f1(x)))
        expr = "x"
        for step in self.steps:
            expr = f"({step.name} {expr})"
        return f"λx.{expr}"


# =============================================================================
# パス探索エンジン（Interaction Calculus風）
# =============================================================================

@dataclass
class SearchState:
    """探索状態"""
    current_type: Type
    path: Path
    visited: Set[Type] = field(default_factory=set)


class PathFinder:
    """
    Type Inhabitation を解くパス探索エンジン
    
    Interaction Calculus の概念を活用:
    - 複数パスの同時探索 (Superposition的)
    - パスの共有 (Duplication的)
    """
    
    def __init__(self, env: TypeEnvironment, max_depth: int = 10):
        self.env = env
        self.max_depth = max_depth
    
    def find_paths(self, start: Type, goal: Type) -> List[Path]:
        """
        startからgoalへのすべてのパスを探索
        
        これは type inhabitation: 型 (start → goal) の住人を見つける
        """
        all_paths = []
        
        # BFS探索
        initial_state = SearchState(
            current_type=start,
            path=Path([]),
            visited={start}
        )
        queue = [initial_state]
        
        while queue:
            state = queue.pop(0)
            
            # ゴールに到達
            if state.current_type == goal:
                all_paths.append(state.path)
                continue
            
            # 深さ制限
            if len(state.path.steps) >= self.max_depth:
                continue
            
            # 次の候補を探索（Superposition的に全候補を考慮）
            for func in self.env.get_outgoing(state.current_type):
                next_type = func.ret_type
                
                # サイクル回避（単純なケース）
                if next_type in state.visited and next_type != goal:
                    continue
                
                new_path = Path(state.path.steps + [func])
                new_visited = state.visited | {next_type}
                
                queue.append(SearchState(
                    current_type=next_type,
                    path=new_path,
                    visited=new_visited
                ))
        
        return all_paths
    
    def find_shortest_path(self, start: Type, goal: Type) -> Optional[Path]:
        """最短パスを見つける"""
        paths = self.find_paths(start, goal)
        if not paths:
            return None
        return min(paths, key=lambda p: len(p.steps))
    
    def find_cheapest_path(self, start: Type, goal: Type) -> Optional[Path]:
        """最小コストパスを見つける"""
        paths = self.find_paths(start, goal)
        if not paths:
            return None
        return min(paths, key=lambda p: p.cost)
    
    def paths_to_superposition(self, paths: List[Path]) -> str:
        """
        複数のパスを Interaction Calculus の Superposition として表現
        """
        if not paths:
            return "&{}"  # Era (空)
        if len(paths) == 1:
            return paths[0].to_lambda()
        
        # 複数パスを重ね合わせ
        lambdas = [p.to_lambda() for p in paths]
        return f"&{{{', '.join(lambdas)}}}"


# =============================================================================
# Interaction Calculus への変換
# =============================================================================

class ICCompiler:
    """
    パス探索結果を Interaction Calculus の項に変換
    """
    
    def __init__(self, env: TypeEnvironment):
        self.env = env
        self.func_impls: Dict[str, Callable] = {}
        
        # 関数名とimplの対応を記録
        for f in env.functions:
            self.func_impls[f.name] = f.impl
    
    def path_to_ic(self, path: Path) -> str:
        """パスをIC項に変換"""
        return path.to_lambda()
    
    def paths_to_ic_superposition(self, paths: List[Path], label: str = "P") -> str:
        """複数パスをSuperpositionに変換"""
        if not paths:
            return "&{}"
        if len(paths) == 1:
            return self.path_to_ic(paths[0])
        
        # 2つずつSuperpositionにまとめる
        lambdas = [self.path_to_ic(p) for p in paths]
        
        # 簡単のため最初の2つだけ
        if len(lambdas) == 2:
            return f"&{label}{{{lambdas[0]}, {lambdas[1]}}}"
        else:
            # 再帰的にネスト
            rest = self.paths_to_ic_superposition(
                paths[1:], 
                label=chr(ord(label) + 1)
            )
            return f"&{label}{{{lambdas[0]}, {rest}}}"
    
    def compile_search(self, start: Type, goal: Type, input_var: str = "x") -> str:
        """
        型探索をIC項としてコンパイル
        
        返り値: 入力を受け取り、全パスの結果を返すIC項
        """
        finder = PathFinder(self.env)
        paths = finder.find_paths(start, goal)
        
        if not paths:
            return "&{}"  # 住人なし
        
        sup = self.paths_to_ic_superposition(paths)
        return f"({sup} {input_var})"


# =============================================================================
# 実用例：データ変換パイプライン
# =============================================================================

def create_data_pipeline_env() -> TypeEnvironment:
    """データ変換パイプラインの型環境を作成"""
    env = TypeEnvironment()
    
    # Int → String
    env.add(TypedFunc(
        name="intToString",
        arg_type=Int,
        ret_type=String,
        impl=lambda x: str(x)
    ))
    
    # String → Int (parse)
    env.add(TypedFunc(
        name="parseInt",
        arg_type=String,
        ret_type=Int,
        impl=lambda x: int(x) if x.isdigit() else 0
    ))
    
    # Int → Float
    env.add(TypedFunc(
        name="intToFloat",
        arg_type=Int,
        ret_type=Float,
        impl=lambda x: float(x)
    ))
    
    # Float → Int (truncate)
    env.add(TypedFunc(
        name="truncate",
        arg_type=Float,
        ret_type=Int,
        impl=lambda x: int(x)
    ))
    
    # Float → String
    env.add(TypedFunc(
        name="floatToString",
        arg_type=Float,
        ret_type=String,
        impl=lambda x: f"{x:.2f}"
    ))
    
    # Int → Bool (isPositive)
    env.add(TypedFunc(
        name="isPositive",
        arg_type=Int,
        ret_type=Bool,
        impl=lambda x: x > 0
    ))
    
    # Bool → String
    env.add(TypedFunc(
        name="boolToString",
        arg_type=Bool,
        ret_type=String,
        impl=lambda x: "true" if x else "false"
    ))
    
    # Bool → Int
    env.add(TypedFunc(
        name="boolToInt",
        arg_type=Bool,
        ret_type=Int,
        impl=lambda x: 1 if x else 0
    ))
    
    # Int → Int (いくつかの変換)
    env.add(TypedFunc(
        name="double",
        arg_type=Int,
        ret_type=Int,
        impl=lambda x: x * 2,
        cost=0.5
    ))
    
    env.add(TypedFunc(
        name="square",
        arg_type=Int,
        ret_type=Int,
        impl=lambda x: x * x,
        cost=0.5
    ))
    
    env.add(TypedFunc(
        name="negate",
        arg_type=Int,
        ret_type=Int,
        impl=lambda x: -x,
        cost=0.3
    ))
    
    return env


# =============================================================================
# 実用例：API変換
# =============================================================================

# カスタム型
UserId = Type("UserId")
UserName = Type("UserName")  
Email = Type("Email")
JsonString = Type("JsonString")
HttpResponse = Type("HttpResponse")


def create_api_env() -> TypeEnvironment:
    """API変換の型環境"""
    env = TypeEnvironment()
    
    env.add(TypedFunc(
        name="lookupUser",
        arg_type=UserId,
        ret_type=UserName,
        impl=lambda uid: f"User_{uid}"
    ))
    
    env.add(TypedFunc(
        name="getEmail",
        arg_type=UserName,
        ret_type=Email,
        impl=lambda name: f"{name.lower()}@example.com"
    ))
    
    env.add(TypedFunc(
        name="toJson",
        arg_type=Email,
        ret_type=JsonString,
        impl=lambda email: f'{{"email": "{email}"}}'
    ))
    
    env.add(TypedFunc(
        name="wrapResponse",
        arg_type=JsonString,
        ret_type=HttpResponse,
        impl=lambda json: f"HTTP 200 OK\n\n{json}"
    ))
    
    # 直接パスも追加
    env.add(TypedFunc(
        name="userIdToJson",
        arg_type=UserId,
        ret_type=JsonString,
        impl=lambda uid: f'{{"userId": {uid}}}',
        cost=0.5  # より低コスト
    ))
    
    return env


# =============================================================================
# デモ
# =============================================================================

def demo_basic():
    """基本的なデモ"""
    print("=" * 60)
    print(" Type Inhabitation / Path Finding Demo")
    print("=" * 60)
    
    env = create_data_pipeline_env()
    finder = PathFinder(env)
    
    print("\n📊 登録された関数（エッジ）:")
    for f in env.functions:
        print(f"   {f}")
    
    # Int → String のパスを探索
    print("\n" + "-" * 60)
    print("🔍 探索: Int → String")
    print("-" * 60)
    
    paths = finder.find_paths(Int, String)
    print(f"   見つかったパス数: {len(paths)}")
    
    for i, path in enumerate(paths[:5]):  # 最初の5つ
        print(f"\n   パス {i+1}: {path}")
        print(f"   ラムダ式: {path.to_lambda()}")
        print(f"   コスト: {path.cost}")
        
        # 実行
        result = path.execute(42)
        print(f"   実行: 42 → {result}")
    
    # 最短パス
    shortest = finder.find_shortest_path(Int, String)
    print(f"\n   📌 最短パス: {shortest}")
    
    # Superpositionとして表現
    compiler = ICCompiler(env)
    if len(paths) >= 2:
        sup = compiler.paths_to_ic_superposition(paths[:2])
        print(f"\n   IC Superposition: {sup}")


def demo_api():
    """API変換のデモ"""
    print("\n" + "=" * 60)
    print(" API Pipeline Demo")
    print("=" * 60)
    
    env = create_api_env()
    finder = PathFinder(env)
    
    print("\n📊 API関数:")
    for f in env.functions:
        print(f"   {f}")
    
    # UserId → HttpResponse
    print("\n" + "-" * 60)
    print("🔍 探索: UserId → HttpResponse")
    print("-" * 60)
    
    paths = finder.find_paths(UserId, HttpResponse)
    
    for i, path in enumerate(paths):
        print(f"\n   パス {i+1}: {path}")
        result = path.execute(123)
        print(f"   実行結果:\n   {result}")


def demo_ic_integration():
    """Interaction Calculusとの統合デモ"""
    print("\n" + "=" * 60)
    print(" Interaction Calculus Integration Demo")
    print("=" * 60)
    
    env = create_data_pipeline_env()
    finder = PathFinder(env)
    compiler = ICCompiler(env)
    
    # 複数パスをSuperpositionとして表現
    paths = finder.find_paths(Int, String)[:3]
    
    print("\n📝 複数パスの Superposition 表現:")
    for i, p in enumerate(paths):
        print(f"   Path {i+1}: {p.to_lambda()}")
    
    sup_expr = compiler.paths_to_ic_superposition(paths)
    print(f"\n   Superposition: {sup_expr}")
    
    # IC項として評価（シミュレーション）
    print("\n📝 Duplicationによるパス共有の例:")
    print("   ! path &L= <shortest_path>; ((path_0 42), (path_1 100))")
    print("   → 同じパスを異なる入力に適用")
    
    shortest = finder.find_shortest_path(Int, String)
    if shortest:
        r1 = shortest.execute(42)
        r2 = shortest.execute(100)
        print(f"   結果: ({r1}, {r2})")


def demo_proof_search():
    """証明探索としての解釈"""
    print("\n" + "=" * 60)
    print(" Proof Search Interpretation")
    print("=" * 60)
    
    print("""
    型理論的解釈:
    ─────────────────────────────────────────────
    型 A          = 命題 A
    型 A → B      = 「AならばB」という命題
    型の住人      = 証明
    パス探索      = 証明探索
    パスの実行    = 証明から計算を抽出
    
    Interaction Calculus での表現:
    ─────────────────────────────────────────────
    Superposition = 複数の証明を同時に保持
                    &{proof1, proof2}
    
    Duplication   = 証明の再利用
                    ! p &= <proof>; (use p₀, use p₁)
    
    Labels        = 異なる証明戦略の区別
                    &A{...} vs &B{...}
    """)
    
    # 具体例
    env = create_data_pipeline_env()
    finder = PathFinder(env)
    
    print("具体例: Int → String の「証明」を探す")
    print("-" * 40)
    
    paths = finder.find_paths(Int, String)
    
    print(f"見つかった証明（パス）: {len(paths)}個\n")
    
    for i, path in enumerate(paths[:3]):
        print(f"証明 {i+1}:")
        print(f"  構造: {' → '.join([str(path.start)] + [str(s.ret_type) for s in path.steps])}")
        print(f"  項: {path.to_lambda()}")
        print(f"  計算抽出: {path.execute(42)}")
        print()


if __name__ == "__main__":
    demo_basic()
    demo_api()
    demo_ic_integration()
    demo_proof_search()
