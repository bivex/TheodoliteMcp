#!/usr/bin/env python3
"""
Булер'ян «Вогонь» — v5.
Виправлення за критикою v4:
 1. AA-001 і SA-002 у легенді (через prefix_map у renderer)
 2. Червоний прямокутник пояснено в легенді (safety_notes)
 3. Перехідник Ø108→Ø150 явно підписаний
 4. Резервуар (ШАФА) підписаний тегом
 5. Протипожежні відступи від меблів (ліжко, шафа → зона печі)
 6. Димохід з підписами Ø108→Ø150 на кожній ділянці
"""

from theodolite_mcp.domain.models.schematic import (
    PipelineSchematic, PipeSegment, PipeMedium,
    ValveSymbol, ValveType, EquipmentSymbol, EquipmentType,
    FittingSymbol, FittingType, InstrumentSymbol,
    PipeSupport, PipeSupportType, Point,
)
from theodolite_mcp.domain.schematic_rendering import render_pipeline_schematic


def _aux(x1, y1, x2, y2, color, dn=15):
    """Допоміжна лінія (рамка, розмірка) — без DN-мітки."""
    return PipeSegment(
        start_pt=Point(x=x1, y=y1), end_pt=Point(x=x2, y=y2),
        medium=PipeMedium.CUSTOM, nominal_diameter=dn,
        flow_direction="none", custom_color=color,
        show_dn_label=False,
    )


def build_v5() -> PipelineSchematic:
    pipes = []
    valves = []
    equipment = []
    fittings = []
    instruments = []
    supports = []

    W = "#333333"   # стіни
    P = "#666666"   # перегородка
    C = "#8B4513"   # димохід
    S = "#FF6600"   # безпечна зона 0.5 м
    F = "#CC0000"   # протипожежна шахта
    G = "#00AA00"   # двері
    R = "#999999"   # розмірки загальні
    D = "#FF6600"   # розмірки відступів (безпека)

    # ================================================================
    # 1. СТІНИ 6×7
    # ================================================================
    for seg in [(0,0,6,0),(6,0,6,7),(6,7,0,7),(0,7,0,0)]:
        pipes.append(PipeSegment(
            start_pt=Point(x=seg[0], y=seg[1]),
            end_pt=Point(x=seg[2], y=seg[3]),
            medium=PipeMedium.CUSTOM, nominal_diameter=100,
            flow_direction="none", custom_color=W,
            show_dn_label=False,
        ))

    # Перегородка y=3.5 з отвором для димаря
    pipes.append(PipeSegment(
        start_pt=Point(x=0, y=3.5), end_pt=Point(x=2.0, y=3.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=80,
        flow_direction="none", custom_color=P, show_dn_label=False,
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=3.0, y=3.5), end_pt=Point(x=6, y=3.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=80,
        flow_direction="none", custom_color=P, show_dn_label=False,
    ))

    # ================================================================
    # 2. БУЛЕР'ЯН
    # ================================================================
    bx, by = 2.5, 1.8
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=bx, y=by),
        equipment_type=EquipmentType.BOILER,
        rotation=0, tag="Булер'ян",
        label='"Вогонь"\n4-9 кВт\nØдим.108 мм',
        width=0.56, height=0.35,
    ))

    # ================================================================
    # 3. ДИМОХІД
    #    Ø108 від топки → перехідник → Ø150 до даху
    # ================================================================
    cx = bx

    # Ділянка 1: Ø108 (внутрішній) від топки до перехідника
    pipes.append(PipeSegment(
        start_pt=Point(x=cx, y=by + 0.18),
        end_pt=Point(x=cx, y=by + 0.55),
        medium=PipeMedium.CUSTOM, nominal_diameter=100,
        flow_direction="forward", custom_color=C,
        insulated=False, show_dn_label=True,
    ))

    # Конічний перехідник Ø108→Ø150 (явно підписаний)
    fittings.append(FittingSymbol(
        center_pt=Point(x=cx, y=by + 0.7),
        fitting_type=FittingType.REDUCER,
        rotation=90, nominal_diameter=150,
    ))
    # Підпис перехідника як окреме обладнання з label
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=cx + 0.45, y=by + 0.7),
        equipment_type=EquipmentType.Y_STRAINER,
        rotation=0, tag="Перехідник\nØ108→Ø150",
        width=0.01, height=0.01,
    ))

    # Ділянка 2: Ø150 утеплений до перегородки
    pipes.append(PipeSegment(
        start_pt=Point(x=cx, y=by + 0.85),
        end_pt=Point(x=cx, y=3.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=150,
        flow_direction="forward", custom_color=C,
        insulated=True, show_dn_label=True,
    ))

    # Ділянка 3: Ø150 через перегородку (сендвіч)
    pipes.append(PipeSegment(
        start_pt=Point(x=cx, y=3.5),
        end_pt=Point(x=cx, y=5.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=150,
        flow_direction="forward", custom_color=C,
        insulated=True, show_dn_label=True,
    ))

    # Ділянка 4: Ø150 на даху + 0.5 м вище коника
    pipes.append(PipeSegment(
        start_pt=Point(x=cx, y=5.5),
        end_pt=Point(x=cx, y=7.8),
        medium=PipeMedium.CUSTOM, nominal_diameter=150,
        flow_direction="forward", custom_color=C,
        insulated=True, show_dn_label=False,
    ))

    # Шибер (заслінка тяги)
    valves.append(ValveSymbol(
        center_pt=Point(x=cx, y=by + 1.2),
        valve_type=ValveType.BUTTERFLY,
        rotation=90, nominal_diameter=150,
        tag="Шибер",
    ))

    # Іскрогасник + дефлектор
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=cx, y=7.9),
        equipment_type=EquipmentType.Y_STRAINER,
        rotation=0, tag="Іскрогасник\n+ дефлектор",
        width=0.3, height=0.2,
    ))

    # ================================================================
    # 4. БЕЗПЕЧНІ ЗОНИ (без DN-міток)
    # ================================================================
    hw, hh = 0.28, 0.175

    # Зона 0.5 м від гарячих поверхонь
    m = 0.5
    for s in [
        (bx-hw-m, by-hh-m, bx+hw+m, by-hh-m),
        (bx+hw+m, by-hh-m, bx+hw+m, by+hh+m),
        (bx+hw+m, by+hh+m, bx-hw-m, by+hh+m),
        (bx-hw-m, by+hh+m, bx-hw-m, by-hh-m),
    ]:
        pipes.append(_aux(s[0], s[1], s[2], s[3], S))

    # Протипожежна шахта димоходу (0.38 м від осі = 0.25 від стінки)
    for s in [
        (cx-0.38, 3.0, cx+0.38, 3.0),
        (cx+0.38, 3.0, cx+0.38, 4.0),
        (cx+0.38, 4.0, cx-0.38, 4.0),
        (cx-0.38, 4.0, cx-0.38, 3.0),
    ]:
        pipes.append(_aux(s[0], s[1], s[2], s[3], F))

    # ================================================================
    # 5. КОНВЕКЦІЯ (DN15 скрізь)
    # ================================================================
    DN = 15

    # Подача
    for seg in [
        (bx, by+0.5, bx, by+1.2),
        (bx-0.5, by, bx-1.8, by),
        (bx+0.5, by, bx+1.8, by),
    ]:
        pipes.append(PipeSegment(
            start_pt=Point(x=seg[0], y=seg[1]),
            end_pt=Point(x=seg[2], y=seg[3]),
            medium=PipeMedium.HEATING_SUPPLY, nominal_diameter=DN,
            flow_direction="forward", show_dn_label=True,
        ))

    # Обратка
    for seg in [
        (bx-1.8, 0.2, bx-1.8, by-0.5),
        (bx+1.8, 0.2, bx+1.8, by-0.5),
        (bx-1.8, 0.2, bx+1.8, 0.2),
    ]:
        pipes.append(PipeSegment(
            start_pt=Point(x=seg[0], y=seg[1]),
            end_pt=Point(x=seg[2], y=seg[3]),
            medium=PipeMedium.HEATING_RETURN, nominal_diameter=DN,
            flow_direction="forward", show_dn_label=True,
        ))

    # ================================================================
    # 6. МЕБЛІ (з підписами та розмірками відступів)
    # ================================================================
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=4.8, y=5.8),
        equipment_type=EquipmentType.STORAGE_TANK,
        rotation=0, tag="Ліжко", label="1.4×2.0 м",
        width=2.0, height=1.4,
    ))
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=5.0, y=0.8),
        equipment_type=EquipmentType.STORAGE_TANK,
        rotation=0, tag="Стіл", label="0.8×1.2 м",
        width=1.2, height=0.8,
    ))
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=5.6, y=2.5),
        equipment_type=EquipmentType.STORAGE_TANK,
        rotation=0, tag="Шафа", label="0.6×1.8 м",
        width=0.6, height=1.8,
    ))

    # Розмірки протипожежних відступів:
    # Піч → ліва стіна
    pipes.append(_aux(0, by, bx-hw-0.5, by, D))
    # Піч → передня стіна
    pipes.append(_aux(bx, 0, bx, by-hh-0.5, D))
    # Безпечна зона → шафа (горизонтальний відступ)
    pipes.append(_aux(bx+hw+0.5, 2.0, 5.3, 2.0, D))
    # Ліжко → димохід / перегородка (вертикальний відступ)
    pipes.append(_aux(cx+0.38, 4.3, 3.8, 5.1, D))

    # ================================================================
    # 7. ВІКНА ТА ДВЕРІ
    # ================================================================
    pipes.append(PipeSegment(
        start_pt=Point(x=0, y=1.0), end_pt=Point(x=0, y=2.5),
        medium=PipeMedium.COLD_WATER, nominal_diameter=15,
        flow_direction="none", show_dn_label=False,
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=6, y=4.5), end_pt=Point(x=6, y=6.0),
        medium=PipeMedium.COLD_WATER, nominal_diameter=15,
        flow_direction="none", show_dn_label=False,
    ))
    pipes.append(_aux(2.5, 0, 3.5, 0, G))
    pipes.append(_aux(4.5, 3.5, 5.5, 3.5, G))

    # ================================================================
    # 8. ДАТЧИКИ
    #    AA-001 = CO-сигналізатор (Analysis → Alarm)
    #    SA-002 = Датчик диму (Smoke → Alarm)
    # ================================================================
    instruments.append(InstrumentSymbol(
        center_pt=Point(x=bx - 1.0, y=2.8),
        measured_variable="A", suffix="A",
        tag_number="001", in_dcs=False,
    ))
    instruments.append(InstrumentSymbol(
        center_pt=Point(x=bx + 0.8, y=3.2),
        measured_variable="S", suffix="A",
        tag_number="002", in_dcs=False,
    ))

    # ================================================================
    # 9. ЗАГАЛЬНІ РОЗМІРКИ
    # ================================================================
    pipes.append(_aux(0, -0.5, 6, -0.5, R))
    pipes.append(_aux(6.5, 0, 6.5, 7, R))

    # ================================================================
    # 10. ПІДПИРКИ
    # ================================================================
    supports.append(PipeSupport(
        center_pt=Point(x=cx, y=3.5),
        support_type=PipeSupportType.ANCHOR,
    ))
    supports.append(PipeSupport(
        center_pt=Point(x=cx, y=5.5),
        support_type=PipeSupportType.GUIDE,
    ))

    return PipelineSchematic(
        title="Розміщення булер'яна «Вогонь» у хаті 6×7 м (v5)",
        project_number="БЖ-005",
        organization="Приватне будівництво",
        language="uk",
        paper_format="A3",
        orientation="portrait",
        scale=20,
        dpi=300,
        show_legend=True,
        show_tags=True,
        pipes=pipes, valves=valves, equipment=equipment,
        fittings=fittings, instruments=instruments, supports=supports,
    )


def main():
    plan = build_v5()
    png = render_pipeline_schematic(plan, "png")
    with open("bulerian_v5.png", "wb") as f:
        f.write(png)
    print(f"PNG: bulerian_v5.png ({len(png)} bytes)")
    svg = render_pipeline_schematic(plan, "svg")
    with open("bulerian_v5.svg", "wb") as f:
        f.write(svg)
    print(f"SVG: bulerian_v5.svg ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
