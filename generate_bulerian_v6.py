#!/usr/bin/env python3
"""
Булер'ян «Вогонь» — v6.
Виправлення за критикою v5:
 1. SA-002 відсунуто від Шибера (різні пристрої — різні позиції)
 2. Усі резервуари мають явні теги (Ліжко→БТ-001 відмінено, тепер просто підписи)
 3. Ліжко відсунуто від протипожежної шахти + додано розмір відступу
 4. A/S прибрано з легенди (дублюють AA/SA)
"""

from theodolite_mcp.domain.models.schematic import (
    PipelineSchematic, PipeSegment, PipeMedium,
    ValveSymbol, ValveType, EquipmentSymbol, EquipmentType,
    FittingSymbol, FittingType, InstrumentSymbol,
    PipeSupport, PipeSupportType, Point,
)
from theodolite_mcp.domain.schematic_rendering import render_pipeline_schematic


def _aux(x1, y1, x2, y2, color, dn=15):
    return PipeSegment(
        start_pt=Point(x=x1, y=y1), end_pt=Point(x=x2, y=y2),
        medium=PipeMedium.CUSTOM, nominal_diameter=dn,
        flow_direction="none", custom_color=color,
        show_dn_label=False,
    )


def build_v6() -> PipelineSchematic:
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
    D = "#FF6600"   # розмірки відступів

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
    # ================================================================
    cx = bx

    # Ø108 від топки до перехідника
    pipes.append(PipeSegment(
        start_pt=Point(x=cx, y=by + 0.18),
        end_pt=Point(x=cx, y=by + 0.55),
        medium=PipeMedium.CUSTOM, nominal_diameter=100,
        flow_direction="forward", custom_color=C,
        insulated=False, show_dn_label=True,
    ))

    # Перехідник Ø108→Ø150
    fittings.append(FittingSymbol(
        center_pt=Point(x=cx, y=by + 0.7),
        fitting_type=FittingType.REDUCER,
        rotation=90, nominal_diameter=150,
    ))
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=cx + 0.45, y=by + 0.7),
        equipment_type=EquipmentType.Y_STRAINER,
        rotation=0, tag="Перехідник\nØ108→Ø150",
        width=0.01, height=0.01,
    ))

    # Ø150 утеплений до перегородки
    pipes.append(PipeSegment(
        start_pt=Point(x=cx, y=by + 0.85),
        end_pt=Point(x=cx, y=3.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=150,
        flow_direction="forward", custom_color=C,
        insulated=True, show_dn_label=True,
    ))

    # Ø150 через перегородку
    pipes.append(PipeSegment(
        start_pt=Point(x=cx, y=3.5),
        end_pt=Point(x=cx, y=5.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=150,
        flow_direction="forward", custom_color=C,
        insulated=True, show_dn_label=True,
    ))

    # Ø150 на даху
    pipes.append(PipeSegment(
        start_pt=Point(x=cx, y=5.5),
        end_pt=Point(x=cx, y=7.8),
        medium=PipeMedium.CUSTOM, nominal_diameter=150,
        flow_direction="forward", custom_color=C,
        insulated=True, show_dn_label=False,
    ))

    # Шибер — тег без SA-префікса
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
    # 4. БЕЗПЕЧНІ ЗОНИ
    # ================================================================
    hw, hh = 0.28, 0.175
    m = 0.5
    for s in [
        (bx-hw-m, by-hh-m, bx+hw+m, by-hh-m),
        (bx+hw+m, by-hh-m, bx+hw+m, by+hh+m),
        (bx+hw+m, by+hh+m, bx-hw-m, by+hh+m),
        (bx-hw-m, by+hh+m, bx-hw-m, by-hh-m),
    ]:
        pipes.append(_aux(s[0], s[1], s[2], s[3], S))

    # Протипожежна шахта димоходу
    for s in [
        (cx-0.38, 3.0, cx+0.38, 3.0),
        (cx+0.38, 3.0, cx+0.38, 4.0),
        (cx+0.38, 4.0, cx-0.38, 4.0),
        (cx-0.38, 4.0, cx-0.38, 3.0),
    ]:
        pipes.append(_aux(s[0], s[1], s[2], s[3], F))

    # ================================================================
    # 5. КОНВЕКЦІЯ (DN15)
    # ================================================================
    DN = 15
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
    # 6. МЕБЛІ
    #    #2: кожен предмет має явний tag + label
    #    #3: ліжко відсунуто від протипожежної шахти
    # ================================================================
    # Ліжко — у малій кімнаті, відсунуто від шахти димоходу
    bed_x, bed_y = 4.5, 6.0
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=bed_x, y=bed_y),
        equipment_type=EquipmentType.STORAGE_TANK,
        rotation=0, tag="Ліжко", label="1.4×2.0 м\nвідступ 1.0 м",
        width=2.0, height=1.4,
    ))
    # Стіл — у великій кімнаті
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=5.0, y=0.8),
        equipment_type=EquipmentType.STORAGE_TANK,
        rotation=0, tag="Стіл", label="0.8×1.2 м",
        width=1.2, height=0.8,
    ))
    # Шафа — біля правої стіни, з явним tag
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=5.6, y=2.5),
        equipment_type=EquipmentType.STORAGE_TANK,
        rotation=0, tag="Шафа", label="0.6×1.8 м",
        width=0.6, height=1.8,
    ))

    # Розмірки відступів:
    # Піч → ліва стіна
    pipes.append(_aux(0, by, bx-hw-0.5, by, D))
    # Піч → передня стіна
    pipes.append(_aux(bx, 0, bx, by-hh-0.5, D))
    # Безпечна зона → шафа
    pipes.append(_aux(bx+hw+0.5, 2.0, 5.3, 2.0, D))
    # Ліжко → протипожежна шахта (вертикальний відступ)
    pipes.append(_aux(cx+0.38, bed_y - 0.7, cx+0.38, 4.0, D))

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
    #    #1: SA-002 відсунуто від Шибера на стелю малої кімнати
    # ================================================================
    # AA-001: CO-сигналізатор біля печі на стіні
    instruments.append(InstrumentSymbol(
        center_pt=Point(x=bx - 1.0, y=2.8),
        measured_variable="A", suffix="A",
        tag_number="001", in_dcs=False,
    ))
    # SA-002: Датчик диму на стелі малої кімнати (далеко від Шибера!)
    instruments.append(InstrumentSymbol(
        center_pt=Point(x=4.5, y=4.5),
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
        title="Розміщення булер'яна «Вогонь» у хаті 6×7 м (v6)",
        project_number="БЖ-006",
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
    plan = build_v6()
    png = render_pipeline_schematic(plan, "png")
    with open("bulerian_v6.png", "wb") as f:
        f.write(png)
    print(f"PNG: bulerian_v6.png ({len(png)} bytes)")
    svg = render_pipeline_schematic(plan, "svg")
    with open("bulerian_v6.svg", "wb") as f:
        f.write(svg)
    print(f"SVG: bulerian_v6.svg ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
