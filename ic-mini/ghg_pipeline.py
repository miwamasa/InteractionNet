"""
Factory Production Data → GHG Report Pipeline
==============================================

工場の生産管理システムのデータをGHG（温室効果ガス）レポートに変換する
データパイプラインを、Type Inhabitation + Interaction Calculus で実装。

GHGプロトコルのスコープ:
- Scope 1: 直接排出（自社での燃料燃焼など）
- Scope 2: 間接排出（購入電力など）
- Scope 3: その他間接排出（サプライチェーン）

Interaction Calculus の活用:
- Superposition: 複数の計算方法（排出係数）を同時に保持
- Duplication: 同じ中間計算結果の共有（エネルギー消費量など）
- Labels: Scope1/2/3 の区別
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, date
from enum import Enum
import json

import sys
sys.path.insert(0, 'src')
from ic import evaluate, parse, Sup, Dup, Num, Lam, App


# =============================================================================
# データ型定義（型 = ノード）
# =============================================================================

@dataclass
class Type:
    """型の基底クラス"""
    name: str
    def __str__(self):
        return self.name


# --- 生産管理系データ型 ---

@dataclass
class ProductionRecord:
    """生産記録"""
    product_id: str
    product_name: str
    quantity: float  # 生産量
    unit: str  # 単位（個、kg、Lなど）
    line_id: str  # 生産ライン
    date: date
    duration_hours: float  # 稼働時間


@dataclass
class EnergyConsumption:
    """エネルギー消費データ"""
    electricity_kwh: float  # 電力消費量
    natural_gas_m3: float  # 都市ガス消費量
    heavy_oil_l: float  # 重油消費量
    lpg_kg: float  # LPG消費量
    period: str  # 期間


@dataclass
class MaterialInput:
    """原材料投入データ"""
    material_id: str
    material_name: str
    quantity: float
    unit: str
    supplier: str
    transport_distance_km: float


@dataclass 
class WasteOutput:
    """廃棄物データ"""
    waste_type: str
    quantity_kg: float
    treatment_method: str  # landfill, incineration, recycling


@dataclass
class TransportData:
    """輸送データ"""
    mode: str  # truck, ship, rail, air
    distance_km: float
    weight_ton: float


# --- GHG計算中間データ型 ---

@dataclass
class Scope1Emission:
    """Scope1排出量（直接排出）"""
    natural_gas_co2_kg: float
    heavy_oil_co2_kg: float
    lpg_co2_kg: float
    total_co2_kg: float
    
    @property
    def total_co2_ton(self):
        return self.total_co2_kg / 1000


@dataclass
class Scope2Emission:
    """Scope2排出量（電力由来）"""
    electricity_co2_kg: float
    method: str  # "location-based" or "market-based"
    
    @property
    def total_co2_ton(self):
        return self.electricity_co2_kg / 1000


@dataclass
class Scope3Emission:
    """Scope3排出量（その他間接）"""
    category: str  # 1-15のカテゴリ
    description: str
    co2_kg: float
    
    @property
    def total_co2_ton(self):
        return self.co2_kg / 1000


@dataclass
class GHGReport:
    """GHGレポート（最終出力）"""
    reporting_period: str
    organization: str
    scope1_total_ton: float
    scope2_total_ton: float
    scope3_total_ton: float
    total_ton: float
    intensity: float  # 原単位（ton-CO2/生産量）
    details: Dict[str, Any] = field(default_factory=dict)
    calculation_method: str = ""
    
    def to_json(self) -> str:
        return json.dumps({
            "reporting_period": self.reporting_period,
            "organization": self.organization,
            "emissions": {
                "scope1": {"total_ton_co2": round(self.scope1_total_ton, 2)},
                "scope2": {"total_ton_co2": round(self.scope2_total_ton, 2)},
                "scope3": {"total_ton_co2": round(self.scope3_total_ton, 2)},
                "total": {"total_ton_co2": round(self.total_ton, 2)}
            },
            "intensity": round(self.intensity, 4),
            "calculation_method": self.calculation_method,
            "details": self.details
        }, indent=2, ensure_ascii=False)


# =============================================================================
# 排出係数（Emission Factors）
# =============================================================================

class EmissionFactors:
    """
    排出係数データベース
    
    複数の係数セットを持つ（Superposition的）
    - 日本の環境省係数
    - GHGプロトコルデフォルト係数
    - カスタム係数
    """
    
    # 日本環境省の排出係数（2023年度）
    JAPAN_MOE = {
        "electricity_kg_co2_per_kwh": 0.000441,  # 全国平均
        "natural_gas_kg_co2_per_m3": 2.23,
        "heavy_oil_kg_co2_per_l": 2.71,
        "lpg_kg_co2_per_kg": 3.00,
        "diesel_kg_co2_per_l": 2.58,
        "gasoline_kg_co2_per_l": 2.32,
        "name": "Japan MOE 2023"
    }
    
    # GHGプロトコルデフォルト係数
    GHG_PROTOCOL = {
        "electricity_kg_co2_per_kwh": 0.0005,  # グローバル平均
        "natural_gas_kg_co2_per_m3": 2.0,
        "heavy_oil_kg_co2_per_l": 2.68,
        "lpg_kg_co2_per_kg": 2.98,
        "diesel_kg_co2_per_l": 2.68,
        "gasoline_kg_co2_per_l": 2.31,
        "name": "GHG Protocol Default"
    }
    
    # 輸送の排出係数（ton-km あたり kg-CO2）
    TRANSPORT = {
        "truck": 0.0472,
        "ship": 0.0079,
        "rail": 0.0198,
        "air": 0.8063,
    }
    
    # 廃棄物処理の排出係数
    WASTE = {
        "landfill": 0.5,  # kg-CO2 per kg waste
        "incineration": 2.5,
        "recycling": 0.1,
    }


# =============================================================================
# 変換関数（エッジ）- implを持つ
# =============================================================================

class GHGCalculator:
    """
    GHG計算のための変換関数群
    
    各関数は Type A → Type B の変換（impl付き）
    """
    
    def __init__(self, factors: Dict = None):
        self.factors = factors or EmissionFactors.JAPAN_MOE
    
    # --- Scope 1 計算 ---
    
    def energy_to_scope1(self, energy: EnergyConsumption) -> Scope1Emission:
        """EnergyConsumption → Scope1Emission"""
        gas_co2 = energy.natural_gas_m3 * self.factors["natural_gas_kg_co2_per_m3"]
        oil_co2 = energy.heavy_oil_l * self.factors["heavy_oil_kg_co2_per_l"]
        lpg_co2 = energy.lpg_kg * self.factors["lpg_kg_co2_per_kg"]
        
        return Scope1Emission(
            natural_gas_co2_kg=gas_co2,
            heavy_oil_co2_kg=oil_co2,
            lpg_co2_kg=lpg_co2,
            total_co2_kg=gas_co2 + oil_co2 + lpg_co2
        )
    
    # --- Scope 2 計算 ---
    
    def energy_to_scope2_location(self, energy: EnergyConsumption) -> Scope2Emission:
        """EnergyConsumption → Scope2Emission (Location-based)"""
        elec_co2 = energy.electricity_kwh * self.factors["electricity_kg_co2_per_kwh"]
        
        return Scope2Emission(
            electricity_co2_kg=elec_co2,
            method="location-based"
        )
    
    def energy_to_scope2_market(self, energy: EnergyConsumption, 
                                 renewable_ratio: float = 0.0) -> Scope2Emission:
        """EnergyConsumption → Scope2Emission (Market-based)"""
        # 再エネ比率を考慮
        effective_kwh = energy.electricity_kwh * (1 - renewable_ratio)
        elec_co2 = effective_kwh * self.factors["electricity_kg_co2_per_kwh"]
        
        return Scope2Emission(
            electricity_co2_kg=elec_co2,
            method=f"market-based (renewable: {renewable_ratio*100}%)"
        )
    
    # --- Scope 3 計算 ---
    
    def material_to_scope3_cat1(self, material: MaterialInput) -> Scope3Emission:
        """MaterialInput → Scope3Emission (Category 1: 購入物品)"""
        # 簡略化：材料1kgあたり1.5kg-CO2と仮定
        factor = 1.5
        co2 = material.quantity * factor
        
        return Scope3Emission(
            category="Cat1",
            description=f"Purchased goods: {material.material_name}",
            co2_kg=co2
        )
    
    def transport_to_scope3_cat4(self, transport: TransportData) -> Scope3Emission:
        """TransportData → Scope3Emission (Category 4: 輸送)"""
        ton_km = transport.weight_ton * transport.distance_km
        factor = EmissionFactors.TRANSPORT.get(transport.mode, 0.05)
        co2 = ton_km * factor
        
        return Scope3Emission(
            category="Cat4",
            description=f"Transport ({transport.mode}): {transport.distance_km}km",
            co2_kg=co2
        )
    
    def waste_to_scope3_cat5(self, waste: WasteOutput) -> Scope3Emission:
        """WasteOutput → Scope3Emission (Category 5: 廃棄物)"""
        factor = EmissionFactors.WASTE.get(waste.treatment_method, 1.0)
        co2 = waste.quantity_kg * factor
        
        return Scope3Emission(
            category="Cat5",
            description=f"Waste ({waste.treatment_method}): {waste.quantity_kg}kg",
            co2_kg=co2
        )
    
    # --- レポート生成 ---
    
    def aggregate_to_report(self, 
                           scope1: Scope1Emission,
                           scope2: Scope2Emission,
                           scope3_list: List[Scope3Emission],
                           production_total: float,
                           period: str,
                           org: str) -> GHGReport:
        """全スコープを集約してレポート生成"""
        scope3_total = sum(s.total_co2_ton for s in scope3_list)
        total = scope1.total_co2_ton + scope2.total_co2_ton + scope3_total
        
        return GHGReport(
            reporting_period=period,
            organization=org,
            scope1_total_ton=scope1.total_co2_ton,
            scope2_total_ton=scope2.total_co2_ton,
            scope3_total_ton=scope3_total,
            total_ton=total,
            intensity=total / production_total if production_total > 0 else 0,
            calculation_method=self.factors.get("name", "Custom"),
            details={
                "scope1_breakdown": {
                    "natural_gas_ton": scope1.natural_gas_co2_kg / 1000,
                    "heavy_oil_ton": scope1.heavy_oil_co2_kg / 1000,
                    "lpg_ton": scope1.lpg_co2_kg / 1000,
                },
                "scope2_method": scope2.method,
                "scope3_categories": [
                    {"category": s.category, "description": s.description, "ton": s.total_co2_ton}
                    for s in scope3_list
                ]
            }
        )


# =============================================================================
# Type Inhabitation によるパス探索
# =============================================================================

# 型定義（ノード）
RawProductionData = Type("RawProductionData")
EnergyData = Type("EnergyData")
MaterialData = Type("MaterialData")
WasteData = Type("WasteData")
TransportDataType = Type("TransportData")
Scope1Data = Type("Scope1Data")
Scope2Data = Type("Scope2Data")
Scope3Data = Type("Scope3Data")
GHGReportType = Type("GHGReport")


@dataclass
class TypedTransform:
    """型付き変換関数"""
    name: str
    input_type: Type
    output_type: Type
    impl: Callable
    description: str = ""


class GHGPipelineBuilder:
    """
    GHG計算パイプラインのビルダー
    
    Type Inhabitation を使って、データ型から目標型への
    変換パスを探索・構築する
    """
    
    def __init__(self):
        self.transforms: List[TypedTransform] = []
        self.calculator_moe = GHGCalculator(EmissionFactors.JAPAN_MOE)
        self.calculator_ghg = GHGCalculator(EmissionFactors.GHG_PROTOCOL)
        self._setup_transforms()
    
    def _setup_transforms(self):
        """変換関数を登録"""
        
        # Scope 1 変換（2つの係数セット = Superposition）
        self.transforms.append(TypedTransform(
            name="energy_to_scope1_moe",
            input_type=EnergyData,
            output_type=Scope1Data,
            impl=self.calculator_moe.energy_to_scope1,
            description="Energy → Scope1 (Japan MOE factors)"
        ))
        
        self.transforms.append(TypedTransform(
            name="energy_to_scope1_ghg",
            input_type=EnergyData,
            output_type=Scope1Data,
            impl=self.calculator_ghg.energy_to_scope1,
            description="Energy → Scope1 (GHG Protocol factors)"
        ))
        
        # Scope 2 変換（Location vs Market = Superposition）
        self.transforms.append(TypedTransform(
            name="energy_to_scope2_location",
            input_type=EnergyData,
            output_type=Scope2Data,
            impl=self.calculator_moe.energy_to_scope2_location,
            description="Energy → Scope2 (Location-based)"
        ))
        
        self.transforms.append(TypedTransform(
            name="energy_to_scope2_market",
            input_type=EnergyData,
            output_type=Scope2Data,
            impl=lambda e: self.calculator_moe.energy_to_scope2_market(e, 0.3),
            description="Energy → Scope2 (Market-based, 30% renewable)"
        ))
        
        # Scope 3 変換
        self.transforms.append(TypedTransform(
            name="material_to_scope3",
            input_type=MaterialData,
            output_type=Scope3Data,
            impl=self.calculator_moe.material_to_scope3_cat1,
            description="Material → Scope3 Cat1"
        ))
        
        self.transforms.append(TypedTransform(
            name="transport_to_scope3",
            input_type=TransportDataType,
            output_type=Scope3Data,
            impl=self.calculator_moe.transport_to_scope3_cat4,
            description="Transport → Scope3 Cat4"
        ))
        
        self.transforms.append(TypedTransform(
            name="waste_to_scope3",
            input_type=WasteData,
            output_type=Scope3Data,
            impl=self.calculator_moe.waste_to_scope3_cat5,
            description="Waste → Scope3 Cat5"
        ))
    
    def find_paths(self, from_type: Type, to_type: Type) -> List[TypedTransform]:
        """指定された型間の変換パスを探索"""
        return [t for t in self.transforms 
                if t.input_type == from_type and t.output_type == to_type]
    
    def get_all_scope1_methods(self) -> List[TypedTransform]:
        """Scope1計算の全方法（Superposition的）"""
        return self.find_paths(EnergyData, Scope1Data)
    
    def get_all_scope2_methods(self) -> List[TypedTransform]:
        """Scope2計算の全方法（Superposition的）"""
        return self.find_paths(EnergyData, Scope2Data)


# =============================================================================
# Interaction Calculus 統合
# =============================================================================

class ICGHGCompiler:
    """
    GHG計算パイプラインをInteraction Calculus項に変換
    """
    
    def __init__(self, builder: GHGPipelineBuilder):
        self.builder = builder
    
    def compile_scope1_superposition(self) -> str:
        """
        Scope1計算を Superposition として表現
        
        異なる排出係数での計算を同時に保持
        """
        methods = self.builder.get_all_scope1_methods()
        if len(methods) == 2:
            return f"&Scope1{{{methods[0].name}, {methods[1].name}}}"
        return methods[0].name if methods else "&{}"
    
    def compile_scope2_superposition(self) -> str:
        """
        Scope2計算を Superposition として表現
        
        Location-based vs Market-based
        """
        methods = self.builder.get_all_scope2_methods()
        if len(methods) == 2:
            return f"&Scope2{{{methods[0].name}, {methods[1].name}}}"
        return methods[0].name if methods else "&{}"
    
    def compile_full_pipeline(self) -> str:
        """
        完全なGHG計算パイプラインをIC項として表現
        """
        scope1_sup = self.compile_scope1_superposition()
        scope2_sup = self.compile_scope2_superposition()
        
        return f"""
        # GHG Calculation Pipeline (IC representation)
        
        # エネルギーデータの複製（Scope1とScope2で共有）
        ! energy &E= input_energy;
        
        # Scope1計算（複数の排出係数を同時に）
        ! scope1 &S1= ({scope1_sup} energy_0);
        
        # Scope2計算（Location vs Market）
        ! scope2 &S2= ({scope2_sup} energy_1);
        
        # 結果を組み合わせ
        (scope1_0, scope2_0)  # 特定の組み合わせ
        # または
        # &{{(scope1_0, scope2_0), (scope1_1, scope2_1)}}  # 全組み合わせ
        """


# =============================================================================
# 実行エンジン
# =============================================================================

class GHGReportGenerator:
    """
    GHGレポート生成エンジン
    
    Interaction Calculus の概念を活用:
    - Superposition: 複数計算方法の同時実行
    - Duplication: 中間結果の共有
    """
    
    def __init__(self):
        self.builder = GHGPipelineBuilder()
    
    def generate_with_superposition(self,
                                    energy: EnergyConsumption,
                                    materials: List[MaterialInput],
                                    transports: List[TransportData],
                                    wastes: List[WasteOutput],
                                    production_total: float,
                                    period: str,
                                    org: str) -> Dict[str, GHGReport]:
        """
        複数の計算方法でレポートを生成（Superposition）
        
        返り値: {"方法名": レポート} の辞書
        """
        results = {}
        
        # Scope1: 2つの排出係数で計算
        scope1_methods = self.builder.get_all_scope1_methods()
        
        # Scope2: Location-based と Market-based
        scope2_methods = self.builder.get_all_scope2_methods()
        
        # Scope3: 各カテゴリで計算
        calc = self.builder.calculator_moe
        scope3_list = []
        for mat in materials:
            scope3_list.append(calc.material_to_scope3_cat1(mat))
        for trans in transports:
            scope3_list.append(calc.transport_to_scope3_cat4(trans))
        for waste in wastes:
            scope3_list.append(calc.waste_to_scope3_cat5(waste))
        
        # 全組み合わせを生成（Superposition展開）
        for s1_method in scope1_methods:
            scope1 = s1_method.impl(energy)
            
            for s2_method in scope2_methods:
                scope2 = s2_method.impl(energy)
                
                method_name = f"{s1_method.name} + {s2_method.name}"
                
                # 適切な calculator を選択
                if "moe" in s1_method.name:
                    calc = self.builder.calculator_moe
                else:
                    calc = self.builder.calculator_ghg
                
                report = calc.aggregate_to_report(
                    scope1=scope1,
                    scope2=scope2,
                    scope3_list=scope3_list,
                    production_total=production_total,
                    period=period,
                    org=org
                )
                report.calculation_method = method_name
                results[method_name] = report
        
        return results
    
    def generate_with_duplication(self,
                                  energy: EnergyConsumption,
                                  production_total: float,
                                  period: str,
                                  org: str) -> str:
        """
        Duplicationを使った計算（エネルギーデータの共有）
        
        IC的表現:
        ! e &E= energy;
        ((scope1 e_0), (scope2 e_1))
        
        → 同じエネルギーデータからScope1とScope2を同時計算
        """
        calc = self.builder.calculator_moe
        
        # エネルギーデータを「複製」して両方のスコープで使用
        scope1 = calc.energy_to_scope1(energy)  # e_0
        scope2 = calc.energy_to_scope2_location(energy)  # e_1
        
        return f"""
        Duplication Pattern:
        ! energy &E= {energy};
        
        energy_0 → Scope1: {scope1.total_co2_ton:.2f} ton-CO2
        energy_1 → Scope2: {scope2.total_co2_ton:.2f} ton-CO2
        
        合計: {scope1.total_co2_ton + scope2.total_co2_ton:.2f} ton-CO2
        """


# =============================================================================
# デモ
# =============================================================================

def demo():
    print("=" * 70)
    print(" 工場生産管理 → GHGレポート 変換デモ")
    print("=" * 70)
    
    # --- サンプルデータ作成 ---
    print("\n📊 入力データ（工場の月次データ）")
    print("-" * 50)
    
    energy = EnergyConsumption(
        electricity_kwh=150000,  # 15万kWh
        natural_gas_m3=5000,     # 5000m³
        heavy_oil_l=2000,        # 2000L
        lpg_kg=500,              # 500kg
        period="2024-01"
    )
    print(f"  電力: {energy.electricity_kwh:,} kWh")
    print(f"  都市ガス: {energy.natural_gas_m3:,} m³")
    print(f"  重油: {energy.heavy_oil_l:,} L")
    print(f"  LPG: {energy.lpg_kg:,} kg")
    
    materials = [
        MaterialInput("M001", "鋼材", 10000, "kg", "SupplierA", 200),
        MaterialInput("M002", "プラスチック原料", 5000, "kg", "SupplierB", 500),
    ]
    print(f"\n  原材料: {len(materials)}種類")
    
    transports = [
        TransportData("truck", 300, 5),
        TransportData("ship", 1000, 20),
    ]
    print(f"  輸送: トラック300km, 船舶1000km")
    
    wastes = [
        WasteOutput("industrial", 1000, "recycling"),
        WasteOutput("general", 500, "incineration"),
    ]
    print(f"  廃棄物: リサイクル1000kg, 焼却500kg")
    
    production_total = 50000  # 生産量 50,000個
    print(f"\n  月間生産量: {production_total:,} 個")
    
    # --- Type Inhabitation の説明 ---
    print("\n" + "=" * 70)
    print(" Type Inhabitation によるパス探索")
    print("=" * 70)
    
    builder = GHGPipelineBuilder()
    
    print("\n📍 登録された型変換（エッジ）:")
    for t in builder.transforms:
        print(f"   {t.input_type} → {t.output_type}: {t.name}")
        print(f"      {t.description}")
    
    print("\n📍 EnergyData → Scope1Data のパス（複数の排出係数）:")
    for path in builder.find_paths(EnergyData, Scope1Data):
        print(f"   • {path.name}: {path.description}")
    
    print("\n📍 EnergyData → Scope2Data のパス（計算方法の違い）:")
    for path in builder.find_paths(EnergyData, Scope2Data):
        print(f"   • {path.name}: {path.description}")
    
    # --- Interaction Calculus 表現 ---
    print("\n" + "=" * 70)
    print(" Interaction Calculus による表現")
    print("=" * 70)
    
    compiler = ICGHGCompiler(builder)
    
    print("\n📝 Superposition（複数計算方法の同時保持）:")
    print(f"   Scope1: {compiler.compile_scope1_superposition()}")
    print(f"   Scope2: {compiler.compile_scope2_superposition()}")
    
    print("\n📝 Duplication（エネルギーデータの共有）:")
    print("""   ! energy &E= input_data;
   scope1 = (calc_scope1 energy_0)  # 複製1をScope1計算に
   scope2 = (calc_scope2 energy_1)  # 複製2をScope2計算に""")
    
    print("\n📝 Labels（スコープの区別）:")
    print("""   &Scope1{moe_method, ghg_method}  # Scope1の計算方法
   &Scope2{location, market}         # Scope2の計算方法
   → 同じラベルで展開時に対応付け""")
    
    # --- 実際の計算 ---
    print("\n" + "=" * 70)
    print(" GHGレポート生成（Superposition展開）")
    print("=" * 70)
    
    generator = GHGReportGenerator()
    reports = generator.generate_with_superposition(
        energy=energy,
        materials=materials,
        transports=transports,
        wastes=wastes,
        production_total=production_total,
        period="2024-01",
        org="Sample Factory"
    )
    
    print(f"\n生成されたレポート数: {len(reports)}（全組み合わせ）")
    
    for method_name, report in reports.items():
        print(f"\n{'─' * 60}")
        print(f"📋 計算方法: {method_name}")
        print(f"{'─' * 60}")
        print(f"   Scope1 (直接排出):    {report.scope1_total_ton:>10.2f} ton-CO2")
        print(f"   Scope2 (電力由来):    {report.scope2_total_ton:>10.2f} ton-CO2")
        print(f"   Scope3 (その他):      {report.scope3_total_ton:>10.2f} ton-CO2")
        print(f"   ────────────────────────────────────")
        print(f"   合計:                 {report.total_ton:>10.2f} ton-CO2")
        print(f"   原単位:               {report.intensity:>10.6f} ton-CO2/個")
    
    # --- 最適な方法の選択 ---
    print("\n" + "=" * 70)
    print(" 分析：計算方法による違い")
    print("=" * 70)
    
    # 最小・最大を比較
    min_report = min(reports.values(), key=lambda r: r.total_ton)
    max_report = max(reports.values(), key=lambda r: r.total_ton)
    
    print(f"\n   最小排出量: {min_report.total_ton:.2f} ton-CO2 ({min_report.calculation_method})")
    print(f"   最大排出量: {max_report.total_ton:.2f} ton-CO2 ({max_report.calculation_method})")
    print(f"   差分: {max_report.total_ton - min_report.total_ton:.2f} ton-CO2 "
          f"({(max_report.total_ton - min_report.total_ton) / min_report.total_ton * 100:.1f}%)")
    
    # --- JSON出力例 ---
    print("\n" + "=" * 70)
    print(" JSONレポート出力例")
    print("=" * 70)
    
    # 最も保守的な（排出量が大きい）方法を選択
    print(f"\n{max_report.to_json()}")
    
    # --- Duplicationパターンの説明 ---
    print("\n" + "=" * 70)
    print(" Duplicationパターン（中間計算の共有）")
    print("=" * 70)
    
    dup_result = generator.generate_with_duplication(
        energy=energy,
        production_total=production_total,
        period="2024-01",
        org="Sample Factory"
    )
    print(dup_result)


if __name__ == "__main__":
    demo()
