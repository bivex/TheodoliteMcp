#!/usr/bin/env python3
"""
Схема розміщення булер'яна «Вогонь» (4-9 кВт, 60 м²) у хаті 6×7 м.
Версія 2 — з виправленнями за критикою.

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


def build_bulerian_plan_v2() -> PipelineSchematic:
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
    vent_color = "#00AA00"

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
    # 2. БУЛЕР'ЯН (центр великої кімнати)
    # ================================================================
    bx, by = 2.5, 1.8  # центр печі — подалі від стін
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=bx, y=by),
        equipment_type=EquipmentType.BOILER,
        rotation=0, tag="Булер'ян",
        label='"Вогонь"\n4-9 кВт\n350×550×560\n45 кг\nØдим.108мм',
        width=0.56, height=0.35,
    ))

    # ================================================================
    # 3. ДИМОХІД Ø150 мм (НІМЕЧЧИНА → DN150 по всій довжині)
    #    Виправлення #1, #2: постійний DN150, без звужень
    # ================================================================
    DN_CHIMNEY = 150
    chimney_x = bx  # по центру печі (заднє підключення)

    # Від топки вгору до перегородки
    pipes.append(PipeSegment(
        start_pt=Point(x=chimney_x, y=by + 0.18),
        end_pt=Point(x=chimney_x, y=3.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=DN_CHIMNEY,
        flow_direction="forward", custom_color=chimney_color,
        insulated=True,
    ))
    # Через отвір у перегородці
    pipes.append(PipeSegment(
        start_pt=Point(x=chimney_x, y=3.5),
        end_pt=Point(x=chimney_x, y=5.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=DN_CHIMNEY,
        flow_direction="forward", custom_color=chimney_color,
        insulated=True,
    ))
    # Виходить на дах (вище коника)
    pipes.append(PipeSegment(
        start_pt=Point(x=chimney_x, y=5.5),
        end_pt=Point(x=chimney_x, y=7.8),
        medium=PipeMedium.CUSTOM, nominal_diameter=DN_CHIMNEY,
        flow_direction="forward", custom_color=chimney_color,
        insulated=True,
    ))

    # Перехідник конічний Ø108→Ø150 одразу після топки
    fittings.append(FittingSymbol(
        center_pt=Point(x=chimney_x, y=by + 0.4),
        fitting_type=FittingType.REDUCER,
        rotation=90, nominal_diameter=DN_CHIMNEY,
    ))

    # Шибер (заслінка) — узгоджено з легендою
    valves.append(ValveSymbol(
        center_pt=Point(x=chimney_x, y=by + 0.8),
        valve_type=ValveType.BUTTERFLY,
        rotation=90, nominal_diameter=DN_CHIMNEY,
        tag="Шибер",
    ))

    # Зонтик/іскрогасник на верхівці димоходу
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=chimney_x, y=7.8),
        equipment_type=EquipmentType.Y_STRAINER,
        rotation=0, tag="Іскрогасник",
        width=0.25, height=0.15,
    ))

    # ================================================================
    # 4. ПРОТИПОЖЕЖНІ ВІДСТУПИ (0.5 м від печі + 1.0 м від стін)
    #    Виправлення #6
    # ================================================================
    def safe_box(cx, cy, hw, hh, margin, color):
        """Малює пунктирний прямокутник безпечної зони."""
        pts = [
            (cx - hw - margin, cy - hh - margin),
            (cx + hw + margin, cy - hh - margin),
            (cx + hw + margin, cy + hh + margin),
            (cx - hw - margin, cy + hh + margin),
        ]
        for i in range(4):
            j = (i + 1) % 4
            pipes.append(PipeSegment(
                start_pt=Point(x=pts[i][0], y=pts[i][1]),
                end_pt=Point(x=pts[j][0], y=pts[j][1]),
                medium=PipeMedium.CUSTOM, nominal_diameter=15,
                flow_direction="none", custom_color=color,
            ))

    # Зона 0.5 м навколо корпусу печі (гарячі поверхні)
    safe_box(bx, by, 0.28, 0.175, 0.5, safe_color)
    # Зона 1.0 м навколо димаря (горючі конструкції)
    safe_box(chimney_x, 3.5, 0.15, 1.5, 0.25, "#CC0000")

    # ================================================================
    # 5. КОНВЕКЦІЙНІ ПОТОКИ (подача + обратка)
    #    Виправлення #3: DN15 мінімум
    #    Виправлення #5: є подача і обратка
    # ================================================================
    DN_AIR = 15

    # Подача (тепле повітря вгору)
    pipes.append(PipeSegment(
        start_pt=Point(x=bx, y=by + 0.5),
        end_pt=Point(x=bx, y=by + 1.2),
        medium=PipeMedium.HEATING_SUPPLY, nominal_diameter=DN_AIR,
        flow_direction="forward",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=bx - 0.5, y=by),
        end_pt=Point(x=bx - 1.8, y=by),
        medium=PipeMedium.HEATING_SUPPLY, nominal_diameter=DN_AIR,
        flow_direction="forward",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=bx + 0.5, y=by),
        end_pt=Point(x=bx + 1.8, y=by),
        medium=PipeMedium.HEATING_SUPPLY, nominal_diameter=DN_AIR,
        flow_direction="forward",
    ))

    # Обратка (холодне повітря вниз)
    pipes.append(PipeSegment(
        start_pt=Point(x=bx - 1.8, y=0.2),
        end_pt=Point(x=bx - 1.8, y=by - 0.5),
        medium=PipeMedium.HEATING_RETURN, nominal_diameter=DN_AIR,
        flow_direction="forward",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=bx + 1.8, y=0.2),
        end_pt=Point(x=bx + 1.8, y=by - 0.5),
        medium=PipeMedium.HEATING_RETURN, nominal_diameter=DN_AIR,
        flow_direction="forward",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=bx - 1.8, y=0.2),
        end_pt=Point(x=bx + 1.8, y=0.2),
        medium=PipeMedium.HEATING_RETURN, nominal_diameter=DN_AIR,
        flow_direction="forward",
    ))

    # ================================================================
    # 6. МЕБЛІ (з правильними відступами)
    #    Виправлення #8: ліжко далеко від печі
    # ================================================================
    # Ліжко — у малій кімнаті, далеко від димаря
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=4.8, y=5.8),
        equipment_type=EquipmentType.STORAGE_TANK,
        rotation=0, tag="", label="Ліжко\n1.4×2.0 м",
        width=2.0, height=1.4,
    ))
    # Стіл — у дальньому куті великої кімнати
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=5.0, y=0.8),
        equipment_type=EquipmentType.STORAGE_TANK,
        rotation=0, tag="", label="Стіл\n0.8×1.2 м",
        width=1.2, height=0.8,
    ))
    # Шафа — біля правої стіни
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=5.6, y=2.5),
        equipment_type=EquipmentType.STORAGE_TANK,
        rotation=0, tag="", label="Шафа\n0.6×1.8 м",
        width=0.6, height=1.8,
    ))

    # ================================================================
    # 7. ВІКНА ТА ДВЕРІ
    # ================================================================
    # Вікно на лівій стіні (велика кімната)
    pipes.append(PipeSegment(
        start_pt=Point(x=0, y=1.0), end_pt=Point(x=0, y=2.5),
        medium=PipeMedium.COLD_WATER, nominal_diameter=15,
        flow_direction="none",
    ))
    # Вікно на правій стіні (мала кімната)
    pipes.append(PipeSegment(
        start_pt=Point(x=6, y=4.5), end_pt=Point(x=6, y=6.0),
        medium=PipeMedium.COLD_WATER, nominal_diameter=15,
        flow_direction="none",
    ))
    # Вхідні двері (нижня стіна)
    pipes.append(PipeSegment(
        start_pt=Point(x=2.5, y=0), end_pt=Point(x=3.5, y=0),
        medium=PipeMedium.CUSTOM, nominal_diameter=20,
        flow_direction="none", custom_color=vent_color,
    ))
    # Міжкімнатні двері (у перегородці)
    pipes.append(PipeSegment(
        start_pt=Point(x=4.5, y=3.5), end_pt=Point(x=5.5, y=3.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=20,
        flow_direction="none", custom_color=vent_color,
    ))

    # ================================================================
    # 8. ДАТЧИКИ БЕЗПЕКИ
    #    Виправлення #9: CO та дим
    # ================================================================
    # Датчик CO — на стіні біля печі, висота ~1.5 м
    instruments.append(InstrumentSymbol(
        center_pt=Point(x=bx - 0.8, y=2.8),
        measured_variable="A",  # Analysis (CO)
        suffix="A",             # Alarm
        tag_number="001",
        in_dcs=False,
    ))
    # Датчик диму — на стелі над піччю
    instruments.append(InstrumentSymbol(
        center_pt=Point(x=bx + 0.5, y=3.2),
        measured_variable="L",  # Level/smoke
        suffix="A",             # Alarm
        tag_number="002",
        in_dcs=False,
    ))

    # ================================================================
    # 9. РОЗМІРНІ ЛІНІЇ
    # ================================================================
    # 6 м ширина
    pipes.append(PipeSegment(
        start_pt=Point(x=0, y=-0.5), end_pt=Point(x=6, y=-0.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=10,
        flow_direction="none", custom_color=dim_color,
    ))
    # 7 м довжина
    pipes.append(PipeSegment(
        start_pt=Point(x=6.5, y=0), end_pt=Point(x=6.5, y=7),
        medium=PipeMedium.CUSTOM, nominal_diameter=10,
        flow_direction="none", custom_color=dim_color,
    ))
    # Відступ від печі до стіни (ліворуч)
    pipes.append(PipeSegment(
        start_pt=Point(x=0, y=1.3), end_pt=Point(x=bx - 0.28, y=1.3),
        medium=PipeMedium.CUSTOM, nominal_diameter=8,
        flow_direction="none", custom_color=safe_color,
    ))
    # Відступ від печі до стіни (вниз)
    pipes.append(PipeSegment(
        start_pt=Point(x=bx - 0.28 - 0.5, y=0),
        end_pt=Point(x=bx - 0.28 - 0.5, y=by - 0.175),
        medium=PipeMedium.CUSTOM, nominal_diameter=8,
        flow_direction="none", custom_color=safe_color,
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
        title="Розміщення булер'яна «Вогонь» у хаті 6×7 м (v2)",
        project_number="БЖ-002",
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
    plan = build_bulerian_plan_v2()

    png = render_pipeline_schematic(plan, output_format="png")
    with open("bulerian_placement_v2.png", "wb") as f:
        f.write(png)
    print(f"PNG: bulerian_placement_v2.png ({len(png)} bytes)")

    svg = render_pipeline_schematic(plan, output_format="svg")
    with open("bulerian_placement_v2.svg", "wb") as f:
        f.write(svg)
    print(f"SVG: bulerian_placement_v2.svg ({len(svg)} bytes)")


if __name__ == "__main__":
    main()