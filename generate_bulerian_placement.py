#!/usr/bin/env python3
"""
Схема розміщення булер'яна «Вогонь» (4000 Вт, 60 м²) у хаті.
План приміщення 6×7 м з димоходом та безпечними зонами.

Використовує theodolite_mcp render_pipeline_schematic.
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


def build_bulerian_plan() -> PipelineSchematic:
    """
    План хати 6×7 м з булер'яном.

    Координатна сітка: 1 одиниця = 1 метр.
    Початок (0,0) — лівий нижній кут.

    Розміри печі: 0.35 × 0.56 м (ширина × глибина)
    Вага: 45 кг, потужність 4-9 кВт, площа обігріву до 60 м²
    Димар: Ø108 мм, заднє підключення
    """

    pipes = []
    valves = []
    equipment = []
    fittings = []
    instruments = []
    supports = []

    # === СТІНИ ПРИМІЩЕННЯ (контур кімнати 6×7) ===
    # Малюємо як труби з medium=CUSTOM (чорний колір)
    wall_color = "#333333"

    # Нижня стіна (фронтальна)
    pipes.append(PipeSegment(
        start_pt=Point(x=0, y=0), end_pt=Point(x=6, y=0),
        medium=PipeMedium.CUSTOM, nominal_diameter=100,
        flow_direction="none", custom_color=wall_color,
    ))
    # Верхня стіна
    pipes.append(PipeSegment(
        start_pt=Point(x=0, y=7), end_pt=Point(x=6, y=7),
        medium=PipeMedium.CUSTOM, nominal_diameter=100,
        flow_direction="none", custom_color=wall_color,
    ))
    # Ліва стіна
    pipes.append(PipeSegment(
        start_pt=Point(x=0, y=0), end_pt=Point(x=0, y=7),
        medium=PipeMedium.CUSTOM, nominal_diameter=100,
        flow_direction="none", custom_color=wall_color,
    ))
    # Права стіна
    pipes.append(PipeSegment(
        start_pt=Point(x=6, y=0), end_pt=Point(x=6, y=7),
        medium=PipeMedium.CUSTOM, nominal_diameter=100,
        flow_direction="none", custom_color=wall_color,
    ))

    # Внутрішня перегородка (розділення кімнат) — горизонтальна на y=3.5
    pipes.append(PipeSegment(
        start_pt=Point(x=0, y=3.5), end_pt=Point(x=2.5, y=3.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=80,
        flow_direction="none", custom_color="#666666",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=3.5, y=3.5), end_pt=Point(x=6, y=3.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=80,
        flow_direction="none", custom_color="#666666",
    ))

    # === ВХІДНИХ ДВЕРЕЙ (позначка на стіні) ===
    # Головні двері — нижня стіна, по центру
    pipes.append(PipeSegment(
        start_pt=Point(x=2.5, y=0), end_pt=Point(x=3.5, y=0),
        medium=PipeMedium.CUSTOM, nominal_diameter=20,
        flow_direction="none", custom_color="#00AA00",
    ))

    # === БУЛЕР'ЯН (центр великої кімнати) ===
    # Розміри: 0.35 (Ш) × 0.56 (Г) м
    # Розташування: ближче до внутрішньої перегородки,
    # задньою сторою (димар) до перегородки
    bx, by = 2.0, 1.8  # центр печі
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=bx, y=by),
        equipment_type=EquipmentType.BOILER,
        rotation=0, tag="Булер'ян",
        label='"Вогонь" 4 кВт\n350×550×560 мм\n45 кг',
        width=0.56, height=0.35,
    ))

    # === ДИМОХІД (заднє підключення, Ø108 мм) ===
    # Від задньої стінки печі вгору до стелі → через стелю → на даху
    # Задня стінка: bx + 0.28 (половина глибини)
    chimney_x = bx + 0.28
    pipes.append(PipeSegment(
        start_pt=Point(x=chimney_x, y=by),
        end_pt=Point(x=chimney_x, y=3.5),
        medium=PipeMedium.CUSTOM, nominal_diameter=50,
        flow_direction="forward", custom_color="#8B4513",
        insulated=True,
    ))
    # Через перегородку (отвор)
    pipes.append(PipeSegment(
        start_pt=Point(x=chimney_x, y=3.5),
        end_pt=Point(x=chimney_x, y=5.0),
        medium=PipeMedium.CUSTOM, nominal_diameter=50,
        flow_direction="forward", custom_color="#8B4513",
        insulated=True,
    ))
    # Димар на даху (вище стелі)
    pipes.append(PipeSegment(
        start_pt=Point(x=chimney_x, y=5.0),
        end_pt=Point(x=chimney_x, y=7.0),
        medium=PipeMedium.CUSTOM, nominal_diameter=50,
        flow_direction="forward", custom_color="#8B4513",
        insulated=True,
    ))

    # Заслінка (шибер) на димоході
    valves.append(ValveSymbol(
        center_pt=Point(x=chimney_x, y=by + 0.5),
        valve_type=ValveType.BUTTERFLY,
        rotation=90, nominal_diameter=100,
        tag="Шибер",
    ))

    # === БЕЗПЕЧНА ЗОНА (0.5 м навколо печі) ===
    # Малюємо як пунктирний прямокутник
    safe_margin = 0.5
    safe_color = "#FF6600"
    # Нижня межа
    pipes.append(PipeSegment(
        start_pt=Point(x=bx - 0.28 - safe_margin, y=by - 0.175 - safe_margin),
        end_pt=Point(x=bx + 0.28 + safe_margin, y=by - 0.175 - safe_margin),
        medium=PipeMedium.CUSTOM, nominal_diameter=15,
        flow_direction="none", custom_color=safe_color,
    ))
    # Верхня межа
    pipes.append(PipeSegment(
        start_pt=Point(x=bx - 0.28 - safe_margin, y=by + 0.175 + safe_margin),
        end_pt=Point(x=bx + 0.28 + safe_margin, y=by + 0.175 + safe_margin),
        medium=PipeMedium.CUSTOM, nominal_diameter=15,
        flow_direction="none", custom_color=safe_color,
    ))
    # Ліва межа
    pipes.append(PipeSegment(
        start_pt=Point(x=bx - 0.28 - safe_margin, y=by - 0.175 - safe_margin),
        end_pt=Point(x=bx - 0.28 - safe_margin, y=by + 0.175 + safe_margin),
        medium=PipeMedium.CUSTOM, nominal_diameter=15,
        flow_direction="none", custom_color=safe_color,
    ))
    # Права межа
    pipes.append(PipeSegment(
        start_pt=Point(x=bx + 0.28 + safe_margin, y=by - 0.175 - safe_margin),
        end_pt=Point(x=bx + 0.28 + safe_margin, y=by + 0.175 + safe_margin),
        medium=PipeMedium.CUSTOM, nominal_diameter=15,
        flow_direction="none", custom_color=safe_color,
    ))

    # === МЕБЛІ (орієнтовно) ===
    # Ліжко у малій кімнаті
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=4.5, y=5.5),
        equipment_type=EquipmentType.STORAGE_TANK,
        rotation=0, tag="", label="Ліжко\n1.4×2.0 м",
        width=2.0, height=1.4,
    ))
    # Стіл у великій кімнаті
    equipment.append(EquipmentSymbol(
        center_pt=Point(x=4.5, y=1.5),
        equipment_type=EquipmentType.SHELL_TUBE_HX,
        rotation=0, tag="", label="Стіл\n0.8×1.2 м",
        width=1.2, height=0.8,
    ))

    # === ВІКНА ===
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

    # === ПІДПИРКИ ДЛЯ ДИМОХОДУ ===
    supports.append(PipeSupport(
        center_pt=Point(x=chimney_x, y=3.5),
        support_type=PipeSupportType.ANCHOR,
    ))
    supports.append(PipeSupport(
        center_pt=Point(x=chimney_x, y=5.0),
        support_type=PipeSupportType.GUIDE,
    ))

    # === РОЗМІРНІ ЛІНІЇ ===
    # Ширина кімнати 6 м
    pipes.append(PipeSegment(
        start_pt=Point(x=0, y=-0.3), end_pt=Point(x=6, y=-0.3),
        medium=PipeMedium.CUSTOM, nominal_diameter=10,
        flow_direction="none", custom_color="#999999",
    ))
    # Глибина кімнати 7 м
    pipes.append(PipeSegment(
        start_pt=Point(x=6.3, y=0), end_pt=Point(x=6.3, y=7),
        medium=PipeMedium.CUSTOM, nominal_diameter=10,
        flow_direction="none", custom_color="#999999",
    ))

    # === ТЕМПЕРАТУРНА ЗОНА (конвекційні потоки) ===
    # Стрілки конвекції від печі
    pipes.append(PipeSegment(
        start_pt=Point(x=bx, y=by + 0.5),
        end_pt=Point(x=bx, y=by + 1.5),
        medium=PipeMedium.HEATING_SUPPLY, nominal_diameter=15,
        flow_direction="forward",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=bx - 0.5, y=by - 0.3),
        end_pt=Point(x=bx - 1.5, y=by - 0.3),
        medium=PipeMedium.HEATING_SUPPLY, nominal_diameter=15,
        flow_direction="forward",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=bx + 0.5, y=by - 0.3),
        end_pt=Point(x=bx + 1.5, y=by - 0.3),
        medium=PipeMedium.HEATING_SUPPLY, nominal_diameter=15,
        flow_direction="forward",
    ))

    # === ПРИЛАВОК / ЗАВАНТАЖУВАЛЬНА ЗОНА ===
    # Зона перед топкою (завантаження дров)
    pipes.append(PipeSegment(
        start_pt=Point(x=bx - 0.28 - 0.3, y=by - 0.175 - 0.8),
        end_pt=Point(x=bx - 0.28 - 0.3, y=by - 0.175),
        medium=PipeMedium.CUSTOM, nominal_diameter=10,
        flow_direction="none", custom_color="#00AA00",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=bx - 0.28 - 0.3, y=by - 0.175 - 0.8),
        end_pt=Point(x=bx + 0.28 + 0.3, y=by - 0.175 - 0.8),
        medium=PipeMedium.CUSTOM, nominal_diameter=10,
        flow_direction="none", custom_color="#00AA00",
    ))
    pipes.append(PipeSegment(
        start_pt=Point(x=bx + 0.28 + 0.3, y=by - 0.175 - 0.8),
        end_pt=Point(x=bx + 0.28 + 0.3, y=by - 0.175),
        medium=PipeMedium.CUSTOM, nominal_diameter=10,
        flow_direction="none", custom_color="#00AA00",
    ))

    return PipelineSchematic(
        title="Розміщення булер'яна «Вогонь» у хаті 6×7 м",
        project_number="БЖ-001",
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
    plan = build_bulerian_plan()

    # PNG
    png_bytes = render_pipeline_schematic(plan, output_format="png")
    with open("bulerian_placement.png", "wb") as f:
        f.write(png_bytes)
    print(f"PNG: bulerian_placement.png ({len(png_bytes)} bytes)")

    # SVG
    svg_bytes = render_pipeline_schematic(plan, output_format="svg")
    with open("bulerian_placement.svg", "wb") as f:
        f.write(svg_bytes)
    print(f"SVG: bulerian_placement.svg ({len(svg_bytes)} bytes)")


if __name__ == "__main__":
    main()