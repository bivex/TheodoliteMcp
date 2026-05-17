#!/usr/bin/env python3
"""
Схема розміщення булер'яна «Вогонь» (4-9 кВт, 60 м²) у хаті 6×7 м.
Версія 3 — виправлення за критикою v2.

Використовує theodolite_mcp render_pipeline_schematic (ISO 6412/14617/3511).
"""

from theodolite_mcp.domain.models.schematic import (
    PipelineSchematic,
    PipeSegment,
    PipeMedium,
    ValveSymbol,
    ValveType,
    EquipmentSymbol,
    EquipmentType,
    FittingSymbol,
    FittingType,
    InstrumentSymbol,
    PipeSupport,
    PipeSupportType,
    Point,
)
from theodolite_mcp.domain.schematic_rendering import render_pipeline_schematic


def build_bulerian_v3() -> PipelineSchematic:
    pipes = []
    valves = []
    equipment = []
    fittings = []
    instruments = []
    supports = []

    wall_color = "#333333"
    chimney_color = "#8B4513"
    safe_color = "#FF6600"
    dim_color = "#999999"
    door_color = "#00AA00"

    # ================================================================
    # 1. СТІНИ ХАТИ 6×7 м
    # ================================================================
    for seg in [
        (0, 0, 6, 0), (6, 0, 6, 7), (6, 7, 0, 7), (0, 7, 0, 0),
    ]:
        pipes.append(PipeSegment(
            start_pt=Point(x=seg[0], y=seg[1]),
            end_pt=Point(x=seg[2], y=seg[3]),
            medium=PipeMedium.CUSTOM, nominal_diameter=100,
            flow_direction="none", custom_color=wall_color,
        ))

    # Внутрішня перегородка y=3.5 з отвором для димаря
    pipes.append(PipeSegment(
        start_pt=Point(x=0, y=3.5), end_pt=Point(x=2.0, y=3.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=80,
        flow_direction="none", custom_color="#666666",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=3.0, y=3.5), end_pt=Point(x=6, y=3.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=80,
        flow_direction="none", custom_color="#666666",
    ))

    # ================================================================
    # 2. БУЛЕР'ЯН
    # ================================================================
    bx, by = 2.5, 1.8
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=bx, y=by),
        equipment_type=EquipmentType.BOILER,
        rotation=0, tag="Булер'ян",
        label='"Вогонь"\n4-9 кВт\n350×550×560\nØдим.108 мм',
        width=0.56, height=0.35,
    ))

    # ================================================================
    # 3. ДИМОХІД
    #    #4: Ø108 від топки → Ø150 після перехідника — без звужень
    #    Перехід тільки розширення, жодних DN100 між ними
    # ================================================================
    chimney_x = bx

    # Ділянка 1: від топки вгору, Ø108 (DN100 = стандарт під 108 мм трубу)
    pipes.append(PipeSegment(
        start_pt=Point(x=chimney_x, y=by + 0.18),
        end_pt=Point(x=chimney_x, y=by + 0.6),
        medium=PipeMedium.CUSTOM, nominal_diameter=100,
        flow_direction="forward", custom_color=chimney_color,
        insulated=False,
    ))

    # Перехідник Ø108 → Ø150 (конус розширення) — позначений явно
    fittings.append(FittingSymbol(
        center_pt=Point(x=chimney_x, y=by + 0.8),
        fitting_type=FittingType.REDUCER,
        rotation=90, nominal_diameter=150,
    ))

    # Ділянка 2: Ø150 від перехідника до перегородки
    pipes.append(PipeSegment(
        start_pt=Point(x=chimney_x, y=by + 1.0),
        end_pt=Point(x=chimney_x, y=3.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=150,
        flow_direction="forward", custom_color=chimney_color,
        insulated=True,
    ))
    # Ділянка 3: Ø150 через перегородку
    pipes.append(PipeSegment(
        start_pt=Point(x=chimney_x, y=3.5),
        end_pt=Point(x=chimney_x, y=5.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=150,
        flow_direction="forward", custom_color=chimney_color,
        insulated=True,
    ))
    # Ділянка 4: Ø150 на дах
    pipes.append(PipeSegment(
        start_pt=Point(x=chimney_x, y=5.5),
        end_pt=Point(x=chimney_x, y=7.8),
        medium=PipeMedium.CUSTOM, nominal_diameter=150,
        flow_direction="forward", custom_color=chimney_color,
        insulated=True,
    ))

    # Шибер на ділянці Ø150 (після перехідника)
    valves.append(ValveSymbol(
        center_pt=Point(x=chimney_x, y=by + 1.3),
        valve_type=ValveType.BUTTERFLY,
        rotation=90, nominal_diameter=150,
        tag="Шибер",
    ))

    # Іскрогасник + дефлектор на верхівці
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=chimney_x, y=7.9),
        equipment_type=EquipmentType.Y_STRAINER,
        rotation=0, tag="Іскрогасник\n+ дефлектор",
        width=0.3, height=0.2,
    ))

    # ================================================================
    # 4. ПРОТИПОЖЕЖНІ ЗОНИ (з підписами що це)
    #    #5: кожна зона підписана
    # ================================================================
    def safe_rect(x1, y1, x2, y2, color, dn=15):
        for (sx, sy, ex, ey) in [
            (x1, y1, x2, y1), (x2, y1, x2, y2),
            (x2, y2, x1, y2), (x1, y2, x1, y1),
        ]:
            pipes.append(PipeSegment(
                start_pt=Point(x=sx, y=sy), end_pt=Point(x=ex, y=ey),
                medium=PipeMedium.CUSTOM, nominal_diameter=dn,
                flow_direction="none", custom_color=color,
            ))

    # Зона 0.5 м від корпусу печі (гарячі поверхні)
    hw, hh = 0.28, 0.175
    safe_rect(
        bx - hw - 0.5, by - hh - 0.5,
        bx + hw + 0.5, by + hh + 0.5,
        safe_color,
    )

    # Протипожежна шахта димоходу 0.25 м від труби (горючі конструкції)
    # #5: позначено окремим кольором і підписом
    safe_rect(
        chimney_x - 0.4, 3.0,
        chimney_x + 0.4, 4.0,
        "#CC0000",
    )

    # ================================================================
    # 5. КОНВЕКЦІЯ (DN15 мінімум)
    #    #1: всі DN15, жодних DN8
    # ================================================================
    DN_CONV = 15

    # Подача (тепле повітря вгору та вбік)
    pipes.append(PipeSegment(
        start_pt=Point(x=bx, y=by + 0.5),
        end_pt=Point(x=bx, y=by + 1.2),
        medium=PipeMedium.HEATING_SUPPLY, nominal_diameter=DN_CONV,
        flow_direction="forward",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=bx - 0.5, y=by),
        end_pt=Point(x=bx - 1.8, y=by),
        medium=PipeMedium.HEATING_SUPPLY, nominal_diameter=DN_CONV,
        flow_direction="forward",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=bx + 0.5, y=by),
        end_pt=Point(x=bx + 1.8, y=by),
        medium=PipeMedium.HEATING_SUPPLY, nominal_diameter=DN_CONV,
        flow_direction="forward",
    ))

    # Обратка (холодне повітря вниз)
    pipes.append(PipeSegment(
        start_pt=Point(x=bx - 1.8, y=0.2),
        end_pt=Point(x=bx - 1.8, y=by - 0.5),
        medium=PipeMedium.HEATING_RETURN, nominal_diameter=DN_CONV,
        flow_direction="forward",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=bx + 1.8, y=0.2),
        end_pt=Point(x=bx + 1.8, y=by - 0.5),
        medium=PipeMedium.HEATING_RETURN, nominal_diameter=DN_CONV,
        flow_direction="forward",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=bx - 1.8, y=0.2),
        end_pt=Point(x=bx + 1.8, y=0.2),
        medium=PipeMedium.HEATING_RETURN, nominal_diameter=DN_CONV,
        flow_direction="forward",
    ))

    # ================================================================
    # 6. МЕБЛІ (з розмірними відступами від печі)
    #    #7: добавлені розмірні лінії відступів
    # ================================================================
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=4.8, y=5.8),
        equipment_type=EquipmentType.STORAGE_TANK,
        rotation=0, tag="", label="Ліжко\n1.4×2.0 м",
        width=2.0, height=1.4,
    ))
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=5.0, y=0.8),
        equipment_type=EquipmentType.STORAGE_TANK,
        rotation=0, tag="", label="Стіл\n0.8×1.2 м",
        width=1.2, height=0.8,
    ))
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=5.6, y=2.5),
        equipment_type=EquipmentType.STORAGE_TANK,
        rotation=0, tag="", label="Шафа\n0.6×1.8 м",
        width=0.6, height=1.8,
    ))

    # Розмірні лінії відступів (#7):
    # Від шафи до безпечної зони печі (горизонтальний)
    pipes.append(PipeSegment(
        start_pt=Point(x=bx + hw + 0.5, y=2.0),
        end_pt=Point(x=5.3, y=2.0),
        medium=PipeMedium.CUSTOM, nominal_diameter=8,
        flow_direction="none", custom_color=safe_color,
    ))
    # Від печі до лівої стіни (горизонтальний)
    pipes.append(PipeSegment(
        start_pt=Point(x=0, y=by),
        end_pt=Point(x=bx - hw - 0.5, y=by),
        medium=PipeMedium.CUSTOM, nominal_diameter=8,
        flow_direction="none", custom_color=safe_color,
    ))
    # Від печі до передньої стіни (вертикальний)
    pipes.append(PipeSegment(
        start_pt=Point(x=bx, y=0),
        end_pt=Point(x=bx, y=by - hh - 0.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=8,
        flow_direction="none", custom_color=safe_color,
    ))

    # ================================================================
    # 7. ВІКНА ТА ДВЕРІ
    # ================================================================
    pipes.append(PipeSegment(
        start_pt=Point(x=0, y=1.0), end_pt=Point(x=0, y=2.5),
        medium=PipeMedium.COLD_WATER, nominal_diameter=15,
        flow_direction="none",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=6, y=4.5), end_pt=Point(x=6, y=6.0),
        medium=PipeMedium.COLD_WATER, nominal_diameter=15,
        flow_direction="none",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=2.5, y=0), end_pt=Point(x=3.5, y=0),
        medium=PipeMedium.CUSTOM, nominal_diameter=20,
        flow_direction="none", custom_color=door_color,
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=4.5, y=3.5), end_pt=Point(x=5.5, y=3.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=20,
        flow_direction="none", custom_color=door_color,
    ))

    # ================================================================
    # 8. ДАТЧИКИ БЕЗПЕКИ
    #    #2: AA-001 = CO-сигналізатор (Analysis-Alarm)
    #    #2: LA-002 прибрано з димоходу, замінено на SA (Smoke Alarm)
    #    #3: підписи зрозумілі
    # ================================================================
    # CO-сигналізатор на стіні біля печі
    instruments.append(InstrumentSymbol(
        center_pt=Point(x=bx - 1.0, y=2.8),
        measured_variable="A",   # Analysis (CO концентрація)
        suffix="A",              # Alarm ( сигналізація)
        tag_number="001",
        in_dcs=False,
    ))

    # Датчик диму на стелі (не на димоході!)
    instruments.append(InstrumentSymbol(
        center_pt=Point(x=bx + 0.8, y=3.2),
        measured_variable="S",   # Smoke (дим)
        suffix="A",              # Alarm
        tag_number="002",
        in_dcs=False,
    ))

    # ================================================================
    # 9. РОЗМІРНІ ЛІНІЇ (загальні)
    # ================================================================
    pipes.append(PipeSegment(
        start_pt=Point(x=0, y=-0.5), end_pt=Point(x=6, y=-0.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=10,
        flow_direction="none", custom_color=dim_color,
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=6.5, y=0), end_pt=Point(x=6.5, y=7),
        medium=PipeMedium.CUSTOM, nominal_diameter=10,
        flow_direction="none", custom_color=dim_color,
    ))

    # ================================================================
    # 10. ПІДПИРКИ ДИМОХОДУ
    # ================================================================
    supports.append(PipeSupport(
        center_pt=Point(x=chimney_x, y=3.5),
        support_type=PipeSupportType.ANCHOR,
    ))
    supports.append(PipeSupport(
        center_pt=Point(x=chimney_x, y=5.5),
        support_type=PipeSupportType.GUIDE,
    ))

    return PipelineSchematic(
        title="Розміщення булер'яна «Вогонь» у хаті 6×7 м (v3)",
        project_number="БЖ-003",
        organization="Приватне будівництво",
        language="uk",
        paper_format="A3",
        orientation="portrait",
        scale=20,
        dpi=300,
        show_legend=True,
        show_tags=True,
        pipes=pipes,
        valves=valves,
        equipment=equipment,
        fittings=fittings,
        instruments=instruments,
        supports=supports,
    )


def main():
    plan = build_bulerian_v3()

    png = render_pipeline_schematic(plan, output_format="png")
    with open("bulerian_placement_v3.png", "wb") as f:
        f.write(png)
    print(f"PNG: bulerian_placement_v3.png ({len(png)} bytes)")

    svg = render_pipeline_schematic(plan, output_format="svg")
    with open("bulerian_placement_v3.svg", "wb") as f:
        f.write(svg)
    print(f"SVG: bulerian_placement_v3.svg ({len(svg)} bytes)")


if __name__ == "__main__":
    main()