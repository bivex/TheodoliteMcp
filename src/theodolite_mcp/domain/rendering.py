import io
import math
import os
from typing import List, Optional, Tuple, Dict, Union
import matplotlib

matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import matplotlib.patches as patches
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_svg import FigureCanvasSVG
import textwrap

from theodolite_mcp.domain.models import (
    PlotPlan,
    Point,
    Zone,
    AsBuiltPoint,
    VolumeGrid,
    ProfilePlan,
    ProfilePoint,
    InteriorPlan,
    Wall,
    Opening,
    Room,
    FurnitureItem,
    EngineeringItem,
    DimensionLine,
)
from .logic import calculate_azimuth_from_points, calculate_area

# --- ISO 128-20:1996 & ISO 128-23:1999 Standards Constants ---
# Line Group 0.7 (Table 2, ISO 128-23)
# All units in points (1 pt = 1/72 inch). 1 mm = 72/25.4 pt ≈ 2.835 pt.
MM_TO_PT = 72 / 25.4

# ISO 5457:1999 Paper Formats (in mm)
PAPER_SIZES = {
    "A0": (1189, 841),
    "A1": (841, 594),
    "A2": (594, 420),
    "A3": (420, 297),
    "A4": (297, 210),
}

# ISO 5457 Margins (mm)
MARGIN_LEFT = 20.0
MARGIN_OTHER = 10.0

# ISO 7200:2004 Title Block (Stamp) Constants (mm)
STAMP_WIDTH = 185.0
STAMP_HEIGHT = 55.0

# Font handling (ISO 3098)
# Use DejaVu Sans (bundled with matplotlib) for broad language support.
# It includes Cyrillic, Greek, and many glyphs. CJK languages use specific fallbacks.


def _format_coord_value(value: Optional[float], max_val: float = 5000.0) -> str:
    """
    Format coordinate values intelligently to avoid clutter.
    For small/medium values: show 1 decimal (0.0-9999.9)
    For large values: show integer (10000+) or k notation for extreme values.
    """
    if value is None:
        return "?"
    abs_val = abs(value)
    # Local/regional coordinates (typical cadastral): show 1 decimal if under 10000
    if abs_val < 10000:
        return f"{value:.1f}"
    # Large coordinates (UTM, military grid): show integer to reduce digits
    elif abs_val < 1000000:
        return f"{value:.0f}"
    # Extreme/million-scale: use k notation
    else:
        return f"{value / 1000:.0f}k"


def _get_font(
    size: float = 7,
    bold: bool = False,
    italic: bool = False,
    m_per_pt: float = 0.1,
    lang: str = "ru",
):
    """
    Returns font properties for drawing text.
    Includes fallback for CJK languages (zh, ja, ko) to avoid square boxes.
    """
    # Clamp to reasonable limits for readability
    adjusted_size = max(3.0, min(24.0, size))
    weight = "bold" if bold else "normal"
    style = "italic" if italic else "normal"

    # CJK Fallback logic
    if lang in ["zh", "ja", "ko"]:
        # Try to find a common CJK font
        cjk_families = [
            "SimSun",
            "WenQuanYi Micro Hei",
            "Noto Sans CJK JP",
            "MS Gothic",
            "AppleGothic",
            "sans-serif",
        ]
        return FontProperties(
            family=cjk_families, size=adjusted_size, weight=weight, style=style
        )

    # Use DejaVu Sans (bundled with matplotlib) for broad coverage (Cyrillic, Greek, etc.)
    # This is portable and works in pip-installed environments.
    return FontProperties(
        family="DejaVu Sans", size=adjusted_size, weight=weight, style=style
    )


D = 0.35 * MM_TO_PT  # Narrow (d)
D_WIDE = 0.7 * MM_TO_PT  # Wide (2d)
D_EXTRA_WIDE = 1.4 * MM_TO_PT  # Extra-wide (4d)
D_SYMBOL = 0.5 * MM_TO_PT  # Graphical Symbols

# ISO 128-20:1996 Dash/Gap Proportions
# Long dash = 24d, Dash = 12d, Gap = 3d, Dot = 0.5d
LD = 24 * D
DS = 12 * D
GP = 3 * D
DT = 0.5 * D

# Line Types (ISO 128-20 numbers)
TYPE_01 = "-"  # Continuous
TYPE_02 = (0, (DS, GP))  # Dashed
TYPE_04 = (0, (LD, GP, DT, GP))  # Long dashed dotted
TYPE_05 = (0, (LD, GP, DT, GP, DT, GP))  # Long dashed double-dotted
# ISO 128-25: 01+03 (Railway line) for tight bulkheads - approximated as a wide dashed-dotted or similar
TYPE_RAILWAY = (0, (DS, DT, DS, DT))


# Localization Dictionary
class LabelTracker:
    """Rectangle-based collision tracker for label placement.
    Uses bounding box overlap instead of point-distance checks
    to properly handle multi-character text labels.
    """

    def __init__(self):
        self.boxes: List[Tuple[float, float, float, float]] = []

    def text_bounds(
        self, x: float, y: float, text: str, fontsize: float, m_per_pt: float
    ) -> Tuple[float, float, float, float]:
        char_w = fontsize * 0.5 * MM_TO_PT * m_per_pt
        char_h = fontsize * MM_TO_PT * m_per_pt
        lines = text.split("\n")
        max_len = max(len(line) for line in lines) if lines else 1
        half_w = max_len * char_w / 2
        half_h = len(lines) * char_h / 2
        return (x - half_w, y - half_h, x + half_w, y + half_h)

    def collides(self, box: Tuple[float, float, float, float]) -> bool:
        x1, y1, x2, y2 = box
        for bx1, by1, bx2, by2 in self.boxes:
            if x1 < bx2 and x2 > bx1 and y1 < by2 and y2 > by1:
                return True
        return False

    def add(self, box: Tuple[float, float, float, float]) -> None:
        self.boxes.append(box)

    def add_text(
        self, x: float, y: float, text: str, fontsize: float, m_per_pt: float
    ) -> None:
        self.add(self.text_bounds(x, y, text, fontsize, m_per_pt))


I18N: Dict[str, Dict[str, str]] = {
    "ru": {
        "project": "Проект:",
        "project_no": "№ Проекта:",
        "org": "Орг.:",
        "date": "Дата:",
        "stage": "Стадия:",
        "scale": "Масштаб:",
        "draft": "Чертеж (П)",
        "explication": "ЭКСПЛИКАЦИЯ ЗОН",
        "total_area": "Общая площадь:",
        "sotki": "сот.",
        "num": "№",
        "name": "Наименование",
        "area_sqm": "S, м²",
        "north": "С",
        "others": "... и другие",
        "unit_m": "м",
        "bow": "НОС",
        "stern": "КОРМА",
        "prof_depth": "Глубина заложения",
        "prof_slope": "Уклоны / Длина",
        "prof_design": "Проектная отметка",
        "prof_ground": "Отметка земли",
        "prof_dist": "Расстояние",
        "prof_station": "Пикет",
    },
    "uk": {
        "project": "Проєкт:",
        "project_no": "№ Проєкту:",
        "org": "Орг.:",
        "date": "Дата:",
        "stage": "Стадія:",
        "scale": "Масштаб:",
        "draft": "Креслення (Р)",
        "explication": "ЕКСПЛІКАЦІЯ ЗОН",
        "total_area": "Загальна площа:",
        "sotki": "сот.",
        "num": "№",
        "name": "Найменування",
        "area_sqm": "S, м²",
        "north": "Пн",
        "others": "... та інші",
        "unit_m": "м",
        "bow": "НІС",
        "stern": "КОРМА",
        "prof_depth": "Глибина закладання",
        "prof_slope": "Ухили / Довжина",
        "prof_design": "Проєктна позначка",
        "prof_ground": "Позначка землі",
        "prof_dist": "Відстань",
        "prof_station": "Пікет",
    },
    "uk": {
        "project": "Проєкт:",
        "project_no": "№ Проєкту:",
        "org": "Орг.:",
        "date": "Дата:",
        "stage": "Стадія:",
        "scale": "Масштаб:",
        "draft": "Креслення (П)",
        "explication": "ЕКСПЛІКАЦІЯ ЗОН",
        "total_area": "Загальна площа:",
        "sotki": "сот.",
        "num": "№",
        "name": "Найменування",
        "area_sqm": "S, м²",
        "north": "Пн",
        "others": "... та інші",
        "unit_m": "м",
        "bow": "НІС",
        "stern": "КОРМА",
        "prof_depth": "Глибина закладення",
        "prof_slope": "Ухили / Довжина",
        "prof_design": "Проєктна позначка",
        "prof_ground": "Позначка землі",
        "prof_dist": "Відстань",
        "prof_station": "Пікет",
    },
    "en": {
        "project": "Project:",
        "project_no": "Proj No:",
        "org": "Org:",
        "date": "Date:",
        "stage": "Stage:",
        "scale": "Scale:",
        "draft": "Draft (P)",
        "explication": "ZONE EXPLICATION",
        "total_area": "Total Area:",
        "sotki": "units",
        "num": "No.",
        "name": "Description",
        "area_sqm": "S, m²",
        "north": "N",
        "others": "... and others",
        "unit_m": "m",
        "bow": "BOW",
        "stern": "STERN",
        "prof_depth": "Burial Depth",
        "prof_slope": "Slopes / Length",
        "prof_design": "Design Level",
        "prof_ground": "Ground Level",
        "prof_dist": "Distance",
        "prof_station": "Station",
    },
    "de": {
        "project": "Projekt:",
        "project_no": "Proj.-Nr.:",
        "org": "Org.:",
        "date": "Datum:",
        "stage": "Phase:",
        "scale": "Maßstab:",
        "draft": "Entwurf (P)",
        "explication": "ZONEN-LEGENDE",
        "total_area": "Gesamtfläche:",
        "sotki": "Einheiten",
        "num": "Nr.",
        "name": "Bezeichnung",
        "area_sqm": "S, m²",
        "north": "N",
        "others": "... und andere",
        "unit_m": "m",
        "bow": "BUG",
        "stern": "HECK",
        "prof_depth": "Verlegetiefe",
        "prof_slope": "Gefälle / Länge",
        "prof_design": "Planumshöhe",
        "prof_ground": "Geländehöhe",
        "prof_dist": "Abstand",
        "prof_station": "Station",
    },
    "fr": {
        "project": "Projet :",
        "project_no": "N° de projet :",
        "org": "Org. :",
        "date": "Date :",
        "stage": "Étape :",
        "scale": "Échelle :",
        "draft": "Dessin (P)",
        "explication": "LÉGENDE DES ZONES",
        "total_area": "Surface totale :",
        "sotki": "unités",
        "num": "N°",
        "name": "Désignation",
        "area_sqm": "S, m²",
        "north": "N",
        "others": "... et autres",
        "unit_m": "m",
        "bow": "PROUE",
        "stern": "POUPE",
        "prof_depth": "Profondeur d'enfouissement",
        "prof_slope": "Pentes / Longueur",
        "prof_design": "Niveau de conception",
        "prof_ground": "Niveau du sol",
        "prof_dist": "Distance",
        "prof_station": "Piquet",
    },
    "es": {
        "project": "Proyecto:",
        "project_no": "Nº de proyecto:",
        "org": "Org.:",
        "date": "Fecha:",
        "stage": "Etapa:",
        "scale": "Escala:",
        "draft": "Plano (P)",
        "explication": "LEYENDA DE ZONAS",
        "total_area": "Área total:",
        "sotki": "unidades",
        "num": "Nº",
        "name": "Descripción",
        "area_sqm": "S, m²",
        "north": "N",
        "others": "... y otros",
        "unit_m": "m",
        "bow": "PROA",
        "stern": "POPA",
        "prof_depth": "Profundidad de entierro",
        "prof_slope": "Pendientes / Longitud",
        "prof_design": "Nivel de diseño",
        "prof_ground": "Nivel del suelo",
        "prof_dist": "Distancia",
        "prof_station": "Estación",
    },
    "it": {
        "project": "Progetto:",
        "project_no": "N° progetto:",
        "org": "Org.:",
        "date": "Data:",
        "stage": "Fase:",
        "scale": "Scala:",
        "draft": "Disegno (P)",
        "explication": "LEGENDA ZONE",
        "total_area": "Area totale:",
        "sotki": "unità",
        "num": "N°",
        "name": "Descrizione",
        "area_sqm": "S, m²",
        "north": "N",
        "others": "... e altri",
        "unit_m": "m",
        "bow": "PRUA",
        "stern": "POPPIA",
        "prof_depth": "Profondità di interramento",
        "prof_slope": "Pendenze / Lunghezza",
        "prof_design": "Livello di progetto",
        "prof_ground": "Livello del suolo",
        "prof_dist": "Distanza",
        "prof_station": "Stazione",
    },
    "pt": {
        "project": "Projeto:",
        "project_no": "Nº do projeto:",
        "org": "Org.:",
        "date": "Data:",
        "stage": "Etapa:",
        "scale": "Escala:",
        "draft": "Desenho (P)",
        "explication": "LEGENDA DE ZONAS",
        "total_area": "Área total:",
        "sotki": "unidades",
        "num": "Nº",
        "name": "Descrição",
        "area_sqm": "S, m²",
        "north": "N",
        "others": "... e outros",
        "unit_m": "m",
        "bow": "PROA",
        "stern": "POPA",
        "prof_depth": "Profundidade de enterro",
        "prof_slope": "Inclinações / Comprimento",
        "prof_design": "Nível de projeto",
        "prof_ground": "Nível do solo",
        "prof_dist": "Distância",
        "prof_station": "Estação",
    },
    "pl": {
        "project": "Projekt:",
        "project_no": "Nr projektu:",
        "org": "Org.:",
        "date": "Data:",
        "stage": "Etap:",
        "scale": "Skala:",
        "draft": "Rysunek (P)",
        "explication": "LEGENDA STREF",
        "total_area": "Powierzchnia całk.:",
        "sotki": "jedn.",
        "num": "Nr",
        "name": "Nazwa",
        "area_sqm": "S, m²",
        "north": "Pн",
        "others": "... i inne",
        "unit_m": "m",
        "bow": "DZIOB",
        "stern": "RUFA",
        "prof_depth": "Głębokość posadowienia",
        "prof_slope": "Nachylenia / Długość",
        "prof_design": "Rzędna projektowana",
        "prof_ground": "Rzędna terenu",
        "prof_dist": "Odległość",
        "prof_station": "Pikieta",
    },
    "tr": {
        "project": "Proje:",
        "project_no": "Proje No:",
        "org": "Kurum:",
        "date": "Tarih:",
        "stage": "Aşama:",
        "scale": "Ölçek:",
        "draft": "Taslak (P)",
        "explication": "BÖLGE AÇIKLAMASI",
        "total_area": "Toplam Alan:",
        "sotki": "birim",
        "num": "No.",
        "name": "Açıklama",
        "area_sqm": "S, m²",
        "north": "K",
        "others": "... ve diğerleri",
        "unit_m": "m",
        "bow": "BAŞ",
        "stern": "KIÇ",
        "prof_depth": "Gömme Derinliği",
        "prof_slope": "Eğimler / Uzunluk",
        "prof_design": "Tasarım Kotu",
        "prof_ground": "Zemin Kotu",
        "prof_dist": "Mesafe",
        "prof_station": "İstasyon",
    },
    "zh": {
        "project": "项目:",
        "project_no": "项目编号:",
        "org": "单位:",
        "date": "日期:",
        "stage": "阶段:",
        "scale": "比例:",
        "draft": "图纸 (P)",
        "explication": "区域说明",
        "total_area": "总面积:",
        "sotki": "单位",
        "num": "编号",
        "name": "名称",
        "area_sqm": "S, m²",
        "north": "北",
        "others": "... 及其他",
        "unit_m": "米",
        "bow": "船首",
        "stern": "船尾",
        "prof_depth": "埋深",
        "prof_slope": "坡度 / 长度",
        "prof_design": "设计高程",
        "prof_ground": "地面高程",
        "prof_dist": "距离",
        "prof_station": "里程",
    },
    "ja": {
        "project": "プロジェクト:",
        "project_no": "プロジェクト番号:",
        "org": "組織:",
        "date": "日付:",
        "stage": "段階:",
        "scale": "尺度:",
        "draft": "図面 (P)",
        "explication": "ゾーン説明",
        "total_area": "総面積:",
        "sotki": "単位",
        "num": "番号",
        "name": "名称",
        "area_sqm": "S, m²",
        "north": "北",
        "others": "... その他",
        "unit_m": "m",
        "bow": "船首",
        "stern": "船尾",
        "prof_depth": "埋設深さ",
        "prof_slope": "勾配 / 延長",
        "prof_design": "設計計画高",
        "prof_ground": "地盤高",
        "prof_dist": "距離",
        "prof_station": "追加距離",
    },
    "ko": {
        "project": "프로젝트:",
        "project_no": "프로젝트 번호:",
        "org": "기관:",
        "date": "날짜:",
        "stage": "단계:",
        "scale": "축척:",
        "draft": "도면 (P)",
        "explication": "구역 설명",
        "total_area": "총 면적:",
        "sotki": "단위",
        "num": "번호",
        "name": "명칭",
        "area_sqm": "S, m²",
        "north": "북",
        "others": "... 외",
        "unit_m": "m",
        "bow": "선수",
        "stern": "선미",
        "prof_depth": "매설 깊이",
        "prof_slope": "경사 / 길이",
        "prof_design": "설계 고도",
        "prof_ground": "지반 고도",
        "prof_dist": "거리",
        "prof_station": "측점",
    },
    "nl": {
        "project": "Project:",
        "project_no": "Proj. nr.:",
        "org": "Org.:",
        "date": "Datum:",
        "stage": "Fase:",
        "scale": "Schaal:",
        "draft": "Ontwerp (P)",
        "explication": "ZONE LEGENDA",
        "total_area": "Totale opp.:",
        "sotki": "eenheden",
        "num": "Nr.",
        "name": "Omschrijving",
        "area_sqm": "S, m²",
        "north": "N",
        "others": "... en andere",
        "unit_m": "m",
        "bow": "BOEG",
        "stern": "STEVEN",
    },
    "sv": {
        "project": "Projekt:",
        "project_no": "Proj.nr:",
        "org": "Org:",
        "date": "Datum:",
        "stage": "Fas:",
        "scale": "Skala:",
        "draft": "Ritning (P)",
        "explication": "ZONFÖRKLARING",
        "total_area": "Total yta:",
        "sotki": "enheter",
        "num": "Nr",
        "name": "Beskrivning",
        "area_sqm": "S, m²",
        "north": "N",
        "others": "... och andra",
        "unit_m": "m",
        "bow": "FÖR",
        "stern": "AKTER",
        "prof_depth": "Förläggningsdjup",
        "prof_slope": "Lutningar / Längd",
        "prof_design": "Projekterad nivå",
        "prof_ground": "Marknivå",
        "prof_dist": "Avstånd",
        "prof_station": "Sektion",
    },
    "no": {
        "project": "Prosjekt:",
        "project_no": "Prosjekt nr:",
        "org": "Org:",
        "date": "Dato:",
        "stage": "Fase:",
        "scale": "Skala:",
        "draft": "Tegning (P)",
        "explication": "SONEFORKLARING",
        "total_area": "Totalt areal:",
        "sotki": "enheter",
        "num": "Nr.",
        "name": "Beskrivelse",
        "area_sqm": "S, m²",
        "north": "N",
        "others": "... og andre",
        "unit_m": "m",
        "bow": "BAV",
        "stern": "HEKK",
        "prof_depth": "Nedgravingdybde",
        "prof_slope": "Hellinger / Lengde",
        "prof_design": "Prosjektert nivå",
        "prof_ground": "Terrengnivå",
        "prof_dist": "Avstand",
        "prof_station": "Stasjon",
    },
    "da": {
        "project": "Projekt:",
        "project_no": "Projekt nr:",
        "org": "Org:",
        "date": "Dato:",
        "stage": "Fase:",
        "scale": "Skala:",
        "draft": "Tegning (P)",
        "explication": "ZONEFORKLARING",
        "total_area": "Samlet areal:",
        "sotki": "enheder",
        "num": "Nr.",
        "name": "Beskrivelse",
        "area_sqm": "S, m²",
        "north": "N",
        "others": "... og andre",
        "unit_m": "m",
        "bow": "BOV",
        "stern": "AGTER",
        "prof_depth": "Nedgravningsdybde",
        "prof_slope": "Hældninger / Længde",
        "prof_design": "Projekteret niveau",
        "prof_ground": "Terrænniveau",
        "prof_dist": "Afstand",
        "prof_station": "Station",
    },
    "fi": {
        "project": "Projekti:",
        "project_no": "Projektin nro:",
        "org": "Org:",
        "date": "Päivämäärä:",
        "stage": "Vaihe:",
        "scale": "Mittakaava:",
        "draft": "Piirustus (P)",
        "explication": "ALUESELITYS",
        "total_area": "Kokonaisala:",
        "sotki": "yksikköä",
        "num": "Nro",
        "name": "Kuvaus",
        "area_sqm": "S, m²",
        "north": "P",
        "others": "... ja muut",
        "unit_m": "m",
        "bow": "KEULA",
        "stern": "PERÄ",
        "prof_depth": "Upotussyvyys",
        "prof_slope": "Kaltevuudet / Pituus",
        "prof_design": "Suunnittelutaso",
        "prof_ground": "Maanpinnan taso",
        "prof_dist": "Etäisyys",
        "prof_station": "Paalu",
    },
    "el": {
        "project": "Έργο:",
        "project_no": "Αρ. Έργου:",
        "org": "Οργ:",
        "date": "Ημερομηνία:",
        "stage": "Στάδιο:",
        "scale": "Κλίμακα:",
        "draft": "Σχέδιο (P)",
        "explication": "ΥΠΟΜΝΗΜΑ ΖΩΝΩΝ",
        "total_area": "Συνολικό Εμβαδόν:",
        "sotki": "μονάδες",
        "num": "Αρ.",
        "name": "Περιγραφή",
        "area_sqm": "S, m²",
        "north": "Β",
        "others": "... και άλλα",
        "unit_m": "m",
        "bow": "ΠΛΩΡΗ",
        "stern": "ΠΡΥΜΝΗ",
        "prof_depth": "Βάθος Ταφής",
        "prof_slope": "Κλίσεις / Μήκος",
        "prof_design": "Στάθμη Σχεδιασμού",
        "prof_ground": "Στάθμη Εδάφους",
        "prof_dist": "Απόσταση",
        "prof_station": "Σταθμός",
    },
    "cs": {
        "project": "Projekt:",
        "project_no": "Č. proj:",
        "org": "Org:",
        "date": "Datum:",
        "stage": "Fáze:",
        "scale": "Měřítko:",
        "draft": "Výkres (P)",
        "explication": "LEGENDA ZÓN",
        "total_area": "Celková plocha:",
        "sotki": "jedn.",
        "num": "Č.",
        "name": "Popis",
        "area_sqm": "S, m²",
        "north": "S",
        "others": "... a další",
        "unit_m": "m",
        "bow": " příď",
        "stern": "záď",
        "prof_depth": "Hloubka uložení",
        "prof_slope": "Spády / Délka",
        "prof_design": "Projektovaná úroveň",
        "prof_ground": "Úroveň terénu",
        "prof_dist": "Vzdálenost",
        "prof_station": "Staničení",
    },
    "hu": {
        "project": "Projekt:",
        "project_no": "Proj.sz:",
        "org": "Szerv:",
        "date": "Dátum:",
        "stage": "Szakasz:",
        "scale": "Lépték:",
        "draft": "Rajz (P)",
        "explication": "ZÓNA JELMAGYARÁZAT",
        "total_area": "Összterület:",
        "sotki": "egységek",
        "num": "Sz.",
        "name": "Megnevezés",
        "area_sqm": "S, m²",
        "north": "É",
        "others": "... és egyebek",
        "unit_m": "m",
        "bow": "ORR",
        "stern": "FAR",
        "prof_depth": "Fektetési mélység",
        "prof_slope": "Lejtések / Hossz",
        "prof_design": "Tervezett szint",
        "prof_ground": "Terepszint",
        "prof_dist": "Távolság",
        "prof_station": "Szelvény",
    },
    "ro": {
        "project": "Proiect:",
        "project_no": "Nr. Proj:",
        "org": "Org:",
        "date": "Data:",
        "stage": "Stadiu:",
        "scale": "Scara:",
        "draft": "Desen (P)",
        "explication": "LEGENDĂ ZONE",
        "total_area": "Suprafață totală:",
        "sotki": "unități",
        "num": "Nr.",
        "name": "Descriere",
        "area_sqm": "S, m²",
        "north": "N",
        "others": "... și altele",
        "unit_m": "m",
        "bow": "PROVĂ",
        "stern": "PUPĂ",
        "prof_depth": "Adâncime de îngropare",
        "prof_slope": "Pante / Lungime",
        "prof_design": "Nivel proiectat",
        "prof_ground": "Nivelul solului",
        "prof_dist": "Distanță",
        "prof_station": "Stație",
    },
    "bg": {
        "project": "Проект:",
        "project_no": "№ Проект:",
        "org": "Орг:",
        "date": "Дата:",
        "stage": "Етап:",
        "scale": "Мащаб:",
        "draft": "Чертеж (П)",
        "explication": "ЛЕГЕНДА ЗОНИ",
        "total_area": "Обща площ:",
        "sotki": "ед.",
        "num": "№",
        "name": "Наименование",
        "area_sqm": "S, m²",
        "north": "С",
        "others": "... и други",
        "unit_m": "m",
        "bow": "НОС",
        "stern": "КЪРМА",
    },
}

SHIP_SYMBOLS = {
    "cl": "CL",  # Center Line
    "bl": "BL",  # Base Line
    "wl": "WL",  # Water Line
    "fr": "FR",  # Frame
}

ZONE_COLORS = [
    "#F5F5DC",
    "#E8F5E9",
    "#FFF3E0",
    "#E3F2FD",
    "#FCE4EC",
    "#F3E5F5",
    "#EFEBE9",
    "#FAFAFA",
]


def _auto_color(index: int) -> str:
    return ZONE_COLORS[index % len(ZONE_COLORS)]


def _polygon_coords(points: List[Point]) -> Tuple[List[float], List[float]]:
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    xs.append(points[0].x)
    ys.append(points[0].y)
    return xs, ys


def _centroid(points: List[Point]) -> Tuple[float, float]:
    n = len(points)
    if n == 0:
        return 0, 0
    return sum(p.x for p in points) / n, sum(p.y for p in points) / n


def _edge_midpoint(p1: Point, p2: Point) -> Tuple[float, float]:
    return (p1.x + p2.x) / 2, (p1.y + p2.y) / 2


def _perpendicular_offset(
    p1: Point, p2: Point, distance: float = 1.0
) -> Tuple[float, float]:
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    length = math.hypot(dx, dy)
    if length == 0:
        return 0, 0
    nx, ny = -dy / length * distance, dx / length * distance
    return nx, ny


def _get_hatch(name: str) -> Optional[str]:
    """ISO 128-50 & GOST 2.306-68: Material hatching patterns."""
    name = name.lower()

    # === 1. MATERIAL SECTION SYMBOLS (Materials in cut) ===

    # Concrete: ISO 128-50 pattern 02 + 09. 'o.' perfectly simulates concrete with stones/dots.
    if any(
        k in name
        for k in ["бетон", "concrete", "фундамент", "foundation", "жб", "железобетон"]
    ):
        return "o."

    # Sand / Fill: Only dots.
    if any(k in name for k in ["песок", "sand", "засыпка"]):
        return "..."

    # Soil / Earth: Grid pattern for earth in section.
    if any(k in name for k in ["грунт", "земля", "earth", "soil", "почва"]):
        return "+x"

    # Brick / Masonry: ISO 128-50 pattern 01 (Diagonal lines).
    if any(k in name for k in ["кирпич", "brick", "камень", "stone", "кладка"]):
        return "//"

    # Metal: ISO 128-50 pattern 03. Frequent diagonal lines.
    if any(k in name for k in ["металл", "metal", "сталь", "steel", "железо", "iron"]):
        return "////"

    # Non-metals / Plastics: ISO 128-50 pattern 04 (Cross-hatching).
    if any(k in name for k in ["пластик", "plastic", "резина", "rubber", "полимер"]):
        return "xx"

    # Wood (Cross-section): Concentric circles/grain.
    if any(k in name for k in ["дерево", "wood", "timber", "брус", "доска"]):
        return "O"

    # Glass / Transparent: ISO 128-50 pattern 08. Rare reverse diagonal.
    if any(k in name for k in ["стекло", "glass", "окно", "window"]):
        return "\\"

    # Water / Liquid: ISO 128-50 pattern 07 (Horizontal lines).
    if any(k in name for k in ["вода", "water", "бассейн", "pool", "пруд"]):
        return "--"

    # === 2. SITE PLAN ZONING (View from above) ===

    # Buildings (generic top view)
    if any(k in name for k in ["дом", "house", "building", "здание"]):
        return "///"

    # Paving / Parking / Paths
    if any(
        k in name
        for k in ["парковка", "parking", "paving", "дорожка", "асфальт", "asphalt"]
    ):
        return "xx"

    # Landscaping: Grass / Garden
    if any(
        k in name for k in ["огород", "garden", "planting", "теплица", "газон", "grass"]
    ):
        return ".."

    # Landscaping: Trees / Orchard
    if any(k in name for k in ["сад", "orchard", "trees", "цветник", "лес", "forest"]):
        return "o"

    return None


def _draw_boundary(
    ax, points: List[Point], color: str = "black", standard: str = "construction"
):
    # ISO 128-23 vs ISO 128-25
    if standard == "shipbuilding":
        # ISO 128-25, 01.2: Continuous wide line for outer plating/hull
        lw = D_WIDE
        ls = TYPE_01
    else:
        # ISO 128-23, 04.3: Long dashed dotted extra-wide line (Boundary lines)
        lw = D_EXTRA_WIDE
        ls = TYPE_04

    xs, ys = _polygon_coords(points)
    ax.plot(xs, ys, color=color, linewidth=lw, linestyle=ls, zorder=3)


def _draw_zones(
    ax,
    zones: List[Zone],
    show_areas: bool = False,
    standard: str = "construction",
    m_per_pt: float = 0.1,
    tracker: Optional[LabelTracker] = None,
):
    # Determine drawing center for leader direction logic
    all_pts = []
    for zone in zones:
        all_pts.extend(zone.points)
    if all_pts:
        draw_cx = sum(p.x for p in all_pts) / len(all_pts)
        draw_cy = sum(p.y for p in all_pts) / len(all_pts)
    else:
        draw_cx, draw_cy = 0, 0

    for i, zone in enumerate(zones):
        color = zone.fill_color or _auto_color(i)
        hatch = _get_hatch(zone.name)
        xs, ys = _polygon_coords(zone.points)
        area = calculate_area(zone.points) or 0
        name_lower = zone.name.lower()

        # 1. Color fill (ISO 128-50 toning)
        ax.fill(xs, ys, color=color, alpha=0.12, zorder=1)

        # 2. Hatching (ISO 128-50)
        if hatch:
            h_density = hatch if area < 300 else hatch[0]
            ax.fill(
                xs,
                ys,
                fill=False,
                hatch=h_density,
                edgecolor="black",
                linewidth=0,
                alpha=0.15,
                zorder=2,
            )

        # 3. Line Style (ISO 128-23 vs ISO 128-25)
        is_building = any(
            k in name_lower for k in ["дом", "здание", "building", "house"]
        )
        is_bulkhead = any(
            k in name_lower for k in ["переборка", "bulkhead", "deck", "палуба"]
        )
        is_tight = any(k in name_lower for k in ["tight", "непрониц"])

        if standard == "shipbuilding":
            if is_tight:
                lw = D_WIDE
                ls = TYPE_RAILWAY
            elif is_bulkhead:
                lw = D_WIDE
                ls = TYPE_01
            else:
                lw = D
                ls = TYPE_01
        else:
            if is_building:
                lw = D_WIDE
                ls = TYPE_01
            else:
                lw = D_EXTRA_WIDE
                ls = TYPE_04

        ax.plot(xs, ys, color="black", linewidth=lw, linestyle=ls, zorder=3)

        # 4. Inscriptions & Labels
        zx, zy = _centroid(zone.points)

        if area < 0.5 or standard == "shipbuilding":
            leader_len = 5.0 * MM_TO_PT * m_per_pt
            label = str(i + 1)
            dx = zx - draw_cx
            dy = zy - draw_cy
            dist = math.hypot(dx, dy)
            base_angle = math.atan2(dy, dx) if dist > 0 else i * 2.4

            # Pre-select leader angle to avoid shelf text collisions
            shelf_len = (len(label) * 1.8 + 2.0) * MM_TO_PT * m_per_pt
            d_m = D * m_per_pt
            best_angle = base_angle
            if tracker:
                for ao in [0, 0.4, -0.4, 0.8, -0.8, 1.2, -1.2, math.pi]:
                    a = base_angle + ao
                    ox = math.cos(a) * leader_len
                    oy = math.sin(a) * leader_len
                    lx, ly = zx + ox, zy + oy
                    sdir = 1 if ox >= 0 else -1
                    tx = lx + sdir * shelf_len / 2
                    ty = ly + 2 * d_m
                    tb = tracker.text_bounds(tx, ty, label, 8, m_per_pt)
                    if not tracker.collides(tb):
                        best_angle = a
                        break

            off_x = math.cos(best_angle) * leader_len
            off_y = math.sin(best_angle) * leader_len

            _draw_leader(
                ax,
                zx,
                zy,
                label,
                offset_x=off_x,
                offset_y=off_y,
                terminator="dot",
                m_per_pt=m_per_pt,
                fontsize=8,
                tracker=tracker,
            )
        else:
            label_text = str(i + 1)
            if tracker:
                box = tracker.text_bounds(zx, zy, label_text, 8.5, m_per_pt)
                if tracker.collides(box):
                    # Fall back to leader with predictive angle selection
                    leader_len = 5.0 * MM_TO_PT * m_per_pt
                    dx = zx - draw_cx
                    dy = zy - draw_cy
                    dist = math.hypot(dx, dy)
                    base_angle = math.atan2(dy, dx) if dist > 0 else i * 2.4

                    shelf_len = (len(label_text) * 1.8 + 2.0) * MM_TO_PT * m_per_pt
                    d_m = D * m_per_pt
                    best_angle = base_angle
                    for ao in [0, 0.4, -0.4, 0.8, -0.8, 1.2, -1.2, math.pi]:
                        a = base_angle + ao
                        ox = math.cos(a) * leader_len
                        oy = math.sin(a) * leader_len
                        lx, ly = zx + ox, zy + oy
                        sdir = 1 if ox >= 0 else -1
                        tx = lx + sdir * shelf_len / 2
                        ty = ly + 2 * d_m
                        tb = tracker.text_bounds(tx, ty, label_text, 8, m_per_pt)
                        if not tracker.collides(tb):
                            best_angle = a
                            break

                    off_x = math.cos(best_angle) * leader_len
                    off_y = math.sin(best_angle) * leader_len
                    _draw_leader(
                        ax,
                        zx,
                        zy,
                        label_text,
                        offset_x=off_x,
                        offset_y=off_y,
                        terminator="dot",
                        m_per_pt=m_per_pt,
                        fontsize=8,
                        tracker=tracker,
                    )
                    continue

            ax.text(
                zx,
                zy,
                str(i + 1),
                fontproperties=_get_font(8.5, bold=True, m_per_pt=m_per_pt),
                ha="center",
                va="center",
                zorder=10,
                bbox=dict(
                    boxstyle="circle,pad=0.2",
                    facecolor="white",
                    edgecolor="black",
                    linewidth=D_SYMBOL,
                    alpha=1.0,
                ),
            )
            if tracker:
                tracker.add_text(zx, zy, str(i + 1), 8.5, m_per_pt)

        if show_areas and area >= 0.5:
            area_offset = 1.2 * (m_per_pt / 0.1)
            ax.text(
                zx,
                zy - area_offset,
                f"{area:.1f} m²",
                fontproperties=_get_font(7, m_per_pt=m_per_pt),
                ha="center",
                va="top",
                zorder=10,
                bbox=dict(
                    boxstyle="round,pad=0.15",
                    facecolor="white",
                    edgecolor="none",
                    alpha=1.0,
                ),
            )


def _draw_leader(
    ax,
    target_x: float,
    target_y: float,
    text: str,
    offset_x: float = 5.0,
    offset_y: float = 5.0,
    terminator: str = "dot",
    m_per_pt: float = 0.1,
    fontsize: float = 7,
    tracker: Optional[LabelTracker] = None,
):
    """
    ISO 128-22: Leader and reference lines.
    terminator: 'dot' (area), 'arrow' (edge/line), or 'none'.
    tracker: optional LabelTracker to avoid shelf text collisions.
    """
    d_m = D * m_per_pt
    # Shelf length adapted to text (approx 1.8mm per char + margins)
    shelf_len = (len(text) * 1.8 + 2.0) * MM_TO_PT * m_per_pt

    # Leader end (start of shelf)
    lx, ly = target_x + offset_x, target_y + offset_y

    # 1. Leader line (Narrow 01.1)
    ax.plot(
        [target_x, lx],
        [target_y, ly],
        color="black",
        linewidth=D,
        linestyle=TYPE_01,
        zorder=6,
    )

    # 2. Terminator
    if terminator == "dot":
        # ISO 128-22: dot dia = 5 * line width
        dot_radius = 2.5 * D * m_per_pt
        circle = patches.Circle(
            (target_x, target_y), dot_radius, color="black", zorder=7
        )
        ax.add_patch(circle)
    elif terminator == "arrow":
        # ISO 128-22: 15 deg arrowhead
        angle = math.atan2(ly - target_y, lx - target_x)
        # Small vector for annotation head orientation
        ax.annotate(
            "",
            xy=(target_x, target_y),
            xytext=(
                target_x + math.cos(angle) * 0.01,
                target_y + math.sin(angle) * 0.01,
            ),
            arrowprops=dict(
                arrowstyle="-|>",
                color="black",
                mutation_scale=10,
                linewidth=D,
                shrinkA=0,
                shrinkB=0,
            ),
            zorder=7,
        )

    # 3. Reference line (Shelf) - strictly horizontal
    shelf_dir = 1 if offset_x >= 0 else -1

    # Check shelf text collision — only flip shelf direction, never shift vertically
    # (caller pre-screens leader angles to avoid collisions)
    text_x = lx + shelf_dir * shelf_len / 2
    text_y = ly + 2 * d_m
    if tracker:
        text_box = tracker.text_bounds(text_x, text_y, text, fontsize, m_per_pt)
        if tracker.collides(text_box):
            alt_dir = -shelf_dir
            alt_text_x = lx + alt_dir * shelf_len / 2
            alt_box = tracker.text_bounds(alt_text_x, text_y, text, fontsize, m_per_pt)
            if not tracker.collides(alt_box):
                shelf_dir = alt_dir
                text_x = alt_text_x

    ax.plot(
        [lx, lx + shelf_dir * shelf_len],
        [ly, ly],
        color="black",
        linewidth=D,
        linestyle=TYPE_01,
        zorder=6,
    )

    # 4. Text - preferably above shelf, gap = 2 * line width
    ax.text(
        text_x,
        text_y,
        text,
        fontproperties=_get_font(fontsize, m_per_pt=m_per_pt),
        ha="center",
        va="bottom",
        zorder=10,
    )
    if tracker:
        tracker.add_text(text_x, text_y, text, fontsize, m_per_pt)


def _draw_vertex_labels(
    ax,
    points: List[Point],
    fontsize: float = 8,
    standard: str = "construction",
    m_per_pt: float = 0.1,
    show_coords: bool = False,
    tracker: Optional[LabelTracker] = None,
):
    cx, cy = _centroid(points)
    used_points = []

    for i, p in enumerate(points):
        # Skip if we already labeled this coordinate (e.g. closed loop closing point)
        if any(math.hypot(p.x - ox, p.y - oy) < 0.001 for ox, oy in used_points):
            continue
        used_points.append((p.x, p.y))

        name = p.name
        if show_coords:
            x_str = _format_coord_value(p.x)
            y_str = _format_coord_value(p.y)
            name += f"\n({x_str}, {y_str})"

        if standard == "shipbuilding" and name.isdigit():
            name = f"FR{name}"

        dx, dy = p.x - cx, p.y - cy
        dist = math.hypot(dx, dy)

        off_val = 3.5
        vx, vy = (
            (dx / dist * off_val, dy / dist * off_val)
            if dist > 0
            else (off_val, off_val)
        )

        pos_x, pos_y = p.x + vx, p.y + vy

        # Check collision using rectangle-based tracker
        collision = False
        if tracker:
            text_box = tracker.text_bounds(pos_x, pos_y, name, fontsize, m_per_pt)
            collision = tracker.collides(text_box)
            if collision:
                # Try alternative radial positions (8 directions)
                for angle_off in [0.8, -0.8, 1.6, -1.6, 2.4, -2.4, math.pi]:
                    base_angle = math.atan2(vy, vx)
                    alt_angle = base_angle + angle_off
                    alt_vx = math.cos(alt_angle) * off_val
                    alt_vy = math.sin(alt_angle) * off_val
                    alt_pos_x, alt_pos_y = p.x + alt_vx, p.y + alt_vy
                    alt_box = tracker.text_bounds(
                        alt_pos_x, alt_pos_y, name, fontsize, m_per_pt
                    )
                    if not tracker.collides(alt_box):
                        pos_x, pos_y = alt_pos_x, alt_pos_y
                        vx, vy = alt_vx, alt_vy
                        collision = False
                        break

        if collision:
            _draw_leader(
                ax,
                p.x,
                p.y,
                name,
                offset_x=vx * 3,
                offset_y=vy * 3,
                terminator="none",
                m_per_pt=m_per_pt,
                fontsize=fontsize - 1,
                tracker=tracker,
            )
        else:
            ax.text(
                pos_x,
                pos_y,
                name,
                fontproperties=_get_font(fontsize, m_per_pt=m_per_pt),
                ha="center",
                va="center",
                zorder=5,
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=0.05),
            )
            if tracker:
                tracker.add_text(pos_x, pos_y, name, fontsize, m_per_pt)


def _draw_distances(
    ax,
    points: List[Point],
    standard: str = "construction",
    fontsize: float = 7,
    show_azimuths: bool = False,
    m_per_pt: float = 0.1,
):
    # Calculate centroid to determine 'inside' direction
    cx, cy = _centroid(points)

    overshoot = 8 * D * m_per_pt
    gap = 2 * D * m_per_pt
    text_offset = 1.2 * MM_TO_PT * m_per_pt
    dim_offset_m = 8.0 * MM_TO_PT * m_per_pt

    for i in range(len(points)):
        p1, p2 = points[i], points[(i + 1) % len(points)]
        dist = math.hypot(p2.x - p1.x, p2.y - p1.y)
        if dist < 0.1:
            continue

        mx, my = _edge_midpoint(p1, p2)
        ox_unit, oy_unit = _perpendicular_offset(p1, p2, distance=1.0)

        # ISO 129-1: Dimensions should be outside.
        # Check if (mx + ox_unit, my + oy_unit) is closer to centroid than (mx, my)
        dist_to_centroid_before = math.hypot(mx - cx, my - cy)
        dist_to_centroid_after = math.hypot(mx + ox_unit - cx, my + oy_unit - cy)

        if dist_to_centroid_after < dist_to_centroid_before:
            # We are pointing inside, flip it
            ox_unit, oy_unit = -ox_unit, -oy_unit

        ox_line, oy_line = ox_unit * dim_offset_m, oy_unit * dim_offset_m

        # 1. Dimension line
        ax.plot(
            [p1.x + ox_line, p2.x + ox_line],
            [p1.y + oy_line, p2.y + oy_line],
            color="black",
            linewidth=D,
            linestyle=TYPE_01,
            zorder=4,
        )

        # 2. Extension lines
        p1_start_x, p1_start_y = p1.x + ox_unit * gap, p1.y + oy_unit * gap
        p1_end_x, p1_end_y = (
            p1.x + ox_line + ox_unit * overshoot,
            p1.y + oy_line + oy_unit * overshoot,
        )
        ax.plot(
            [p1_start_x, p1_end_x],
            [p1_start_y, p1_end_y],
            color="black",
            linewidth=D,
            linestyle=TYPE_01,
            zorder=4,
        )

        p2_start_x, p2_start_y = p2.x + ox_unit * gap, p2.y + oy_unit * gap
        p2_end_x, p2_end_y = (
            p2.x + ox_line + ox_unit * overshoot,
            p2.y + oy_line + oy_unit * overshoot,
        )
        ax.plot(
            [p2_start_x, p2_end_x],
            [p2_start_y, p2_end_y],
            color="black",
            linewidth=D,
            linestyle=TYPE_01,
            zorder=4,
        )

        if standard == "shipbuilding":
            angle = math.atan2(p2.y - p1.y, p2.x - p1.x)
            # Arrow scale
            ascl = 5 * MM_TO_PT * m_per_pt
            ax.annotate(
                "",
                xy=(p1.x + ox_line, p1.y + oy_line),
                xytext=(
                    p1.x + ox_line + math.cos(angle) * ascl,
                    p1.y + oy_line + math.sin(angle) * ascl,
                ),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color="black",
                    mutation_scale=10,
                    linewidth=D,
                    shrinkA=0,
                    shrinkB=0,
                ),
                zorder=5,
            )
            ax.annotate(
                "",
                xy=(p2.x + ox_line, p2.y + oy_line),
                xytext=(
                    p2.x + ox_line - math.cos(angle) * ascl,
                    p2.y + oy_line - math.sin(angle) * ascl,
                ),
                arrowprops=dict(
                    arrowstyle="-|>",
                    color="black",
                    mutation_scale=10,
                    linewidth=D,
                    shrinkA=0,
                    shrinkB=0,
                ),
                zorder=5,
            )
        else:
            tick_len = 2.0 * MM_TO_PT * m_per_pt
            for p_base in [
                (p1.x + ox_line, p1.y + oy_line),
                (p2.x + ox_line, p2.y + oy_line),
            ]:
                t_angle = math.atan2(p2.y - p1.y, p2.x - p1.x) + math.pi / 4
                tx, ty = math.cos(t_angle) * tick_len, math.sin(t_angle) * tick_len
                ax.plot(
                    [p_base[0] - tx, p_base[0] + tx],
                    [p_base[1] - ty, p_base[1] + ty],
                    color="black",
                    linewidth=D_WIDE,
                    linestyle=TYPE_01,
                    zorder=5,
                )

        angle_deg = math.degrees(math.atan2(p2.y - p1.y, p2.x - p1.x))
        if angle_deg > 90:
            angle_deg -= 180
        if angle_deg < -90:
            angle_deg += 180

        tx_off, ty_off = ox_unit * text_offset, oy_unit * text_offset

        # Distance (ISO 129-1: placement)
        # Check if distance text fits between dimension lines
        # Approx 2mm per digit + padding, also account for font scaling
        char_width_scaled = 2.0 * (m_per_pt / 0.1)  # Scale with drawing
        text_width_mm = len(f"{dist:.2f}") * char_width_scaled + 2.0
        text_fits = (dist / m_per_pt / MM_TO_PT) > text_width_mm

        if text_fits:
            ax.text(
                mx + ox_line + tx_off,
                my + oy_line + ty_off,
                f"{dist:.2f}",
                fontproperties=_get_font(fontsize, italic=True, m_per_pt=m_per_pt),
                ha="center",
                va="bottom",
                rotation=angle_deg,
                zorder=10,
                bbox=dict(facecolor="white", edgecolor="none", alpha=1.0, pad=0.1),
            )
        else:
            # ISO 129-1: Small gap - move text outside using leader
            _draw_leader(
                ax,
                mx + ox_line,
                my + oy_line,
                f"{dist:.2f}",
                offset_x=ox_unit * 10,
                offset_y=oy_unit * 10,
                terminator="none",
                m_per_pt=m_per_pt,
                fontsize=fontsize - 0.5,
            )

        # Azimuth (placed on opposite side, scaled separation)
        if show_azimuths:
            az = calculate_azimuth_from_points(p1, p2)
            az_separation = 2.2 if text_fits else 3.0  # scaled separation factor
            ax.text(
                mx + ox_line - tx_off * az_separation,
                my + oy_line - ty_off * az_separation,
                f"{az:.1f}°",
                fontproperties=_get_font(fontsize - 0.5, m_per_pt=m_per_pt),
                ha="center",
                va="top",
                rotation=angle_deg,
                zorder=10,
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.9, pad=0.1),
            )


def _draw_scale_bar(
    ax, x_span: float, width_inches: float, lang: str = "ru", m_per_pt: float = 0.1
):
    texts = I18N.get(lang, I18N["ru"])
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    # Position: Bottom right of the main plot
    sb_len_m = 10.0
    if x_span > 200:
        sb_len_m = 50.0
    if x_span > 1000:
        sb_len_m = 200.0
    if x_span < 20:
        sb_len_m = 5.0

    x_pos = xlim[1] - (xlim[1] - xlim[0]) * 0.25
    y_pos = ylim[0] + (ylim[1] - ylim[0]) * 0.08

    ax.plot(
        [x_pos, x_pos + sb_len_m],
        [y_pos, y_pos],
        color="black",
        linewidth=D_WIDE,
        zorder=10,
    )
    ax.plot(
        [x_pos, x_pos],
        [y_pos, y_pos + (ylim[1] - ylim[0]) * 0.015],
        color="black",
        linewidth=D_WIDE,
        zorder=10,
    )
    ax.plot(
        [x_pos + sb_len_m, x_pos + sb_len_m],
        [y_pos, y_pos + (ylim[1] - ylim[0]) * 0.015],
        color="black",
        linewidth=D_WIDE,
        zorder=10,
    )

    ax.text(
        x_pos + sb_len_m / 2,
        y_pos - (ylim[1] - ylim[0]) * 0.02,
        f"{int(sb_len_m)}{texts['unit_m']}",
        fontproperties=_get_font(7, bold=True, m_per_pt=m_per_pt),
        ha="center",
        va="top",
    )


def _calculate_auto_scale(x_span: float, available_width_mm: float) -> int:
    """ISO 5455:1981 - Strict standard scales."""
    if available_width_mm <= 0:
        return 100
    raw_scale = (x_span * 1000) / available_width_mm
    # Standard engineering scales (ISO 5455)
    std_scales = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
    # Add common construction scales
    std_scales.extend([2.5, 25, 250, 2500, 25000])
    std_scales.sort()

    for s in std_scales:
        if s >= raw_scale:
            return int(s)
    return int(raw_scale)


def _draw_stamp(
    fig,
    plan: Union[PlotPlan, ProfilePlan, InteriorPlan],
    scale_str: str,
    pw_mm: float,
    ph_mm: float,
    lang: str = "ru",
):
    texts = I18N.get(lang, I18N["ru"])
    # ISO 7200 Title Block - Absolute positioning in mm
    # Position: Bottom Right of the inner frame
    # Frame is at (MARGIN_LEFT, MARGIN_OTHER) to (pw_mm - MARGIN_OTHER, ph_mm - MARGIN_OTHER)

    left_mm = pw_mm - MARGIN_OTHER - STAMP_WIDTH
    bottom_mm = MARGIN_OTHER

    # Normalize for add_axes
    ax_stamp = fig.add_axes(
        [left_mm / pw_mm, bottom_mm / ph_mm, STAMP_WIDTH / pw_mm, STAMP_HEIGHT / ph_mm]
    )
    ax_stamp.set_xticks([])
    ax_stamp.set_yticks([])
    ax_stamp.set_facecolor("white")
    for spine in ax_stamp.spines.values():
        spine.set_linewidth(D_WIDE)

    # Internal grid (ISO 7200 inspired layout)
    ax_stamp.axhline(0.2, color="black", lw=D)
    ax_stamp.axhline(0.4, color="black", lw=D)
    ax_stamp.axhline(0.6, color="black", lw=D)
    ax_stamp.axvline(0.2, color="black", lw=D)

    # Row 1: Project Number
    ax_stamp.text(
        0.02,
        0.9,
        texts["project_no"],
        fontproperties=_get_font(6.5, italic=True, lang=lang),
        va="center",
    )
    ax_stamp.text(
        0.22,
        0.9,
        plan.project_number,
        fontproperties=_get_font(7.5, bold=True, lang=lang),
        va="center",
    )

    # Row 2: Organization
    ax_stamp.text(
        0.02,
        0.7,
        texts["org"],
        fontproperties=_get_font(6.5, italic=True, lang=lang),
        va="center",
    )
    ax_stamp.text(
        0.22,
        0.7,
        plan.organization,
        fontproperties=_get_font(7.5, bold=True, lang=lang),
        va="center",
    )

    # Row 3: Title (Project)
    ax_stamp.text(
        0.02,
        0.5,
        texts["project"],
        fontproperties=_get_font(6.5, italic=True, lang=lang),
        va="center",
    )
    wrapped_title = "\n".join(textwrap.wrap(plan.title, width=45))
    ax_stamp.text(
        0.22,
        0.5,
        wrapped_title,
        fontproperties=_get_font(7.5, bold=True, lang=lang),
        va="center",
    )

    # Row 4: Date, Stage, Scale
    ax_stamp.text(
        0.02,
        0.3,
        texts["date"],
        fontproperties=_get_font(6.5, italic=True, lang=lang),
        va="center",
    )
    ax_stamp.text(
        0.22, 0.3, plan.date, fontproperties=_get_font(6.5, lang=lang), va="center"
    )

    # Scale box
    ax_stamp.axvline(0.5, ymin=0, ymax=0.4, color="black", lw=D)
    ax_stamp.text(
        0.52,
        0.3,
        texts["scale"],
        fontproperties=_get_font(6.5, italic=True, lang=lang),
        va="center",
    )
    ax_stamp.text(
        0.75,
        0.3,
        scale_str,
        fontproperties=_get_font(7.5, bold=True, lang=lang),
        va="center",
    )

    # Row 5: Drawing Name
    ax_stamp.text(
        0.02,
        0.1,
        texts["draft"],
        fontproperties=_get_font(6.5, italic=True, lang=lang),
        va="center",
    )
    ax_stamp.text(
        0.22,
        0.1,
        plan.title,
        fontproperties=_get_font(7.5, bold=True, lang=lang),
        va="center",
    )


def _draw_explication(
    fig, items: List, total_area: float, pw_mm: float, ph_mm: float, lang: str = "ru"
):
    """
    Renders an engineering/architectural schedule (Explication).
    Dynamically scales font and row height to fit all items.
    """
    texts = I18N.get(lang, I18N["ru"])
    # 1. Base Dimensions
    width_mm = 85.0
    base_row_h = 6.0
    base_font_size = 6.5
    header_area_mm = 18.0  # title_h + header_h

    # 2. Dynamic Scaling logic
    num_items = len(items)
    # Available height is 80% of page height
    max_table_h = ph_mm * 0.8

    # Calculate required row height
    required_h = header_area_mm + (num_items + 1) * base_row_h

    row_h = base_row_h
    font_size = base_font_size

    if required_h > max_table_h:
        # Scale down
        row_h = (max_table_h - header_area_mm) / (num_items + 1)
        # Don't go below 2.5mm for row height (unreadable)
        row_h = max(row_h, 2.5)
        # Font size follows row height (proportional)
        font_size = base_font_size * (row_h / base_row_h)
        font_size = max(font_size, 3.5)  # Minimum readable font

    table_h = header_area_mm + (num_items + 1) * row_h

    left_mm = MARGIN_LEFT
    bottom_mm = MARGIN_OTHER

    ax_leg = fig.add_axes(
        [left_mm / pw_mm, bottom_mm / ph_mm, width_mm / pw_mm, table_h / ph_mm]
    )
    ax_leg.set_xticks([])
    ax_leg.set_yticks([])
    ax_leg.set_facecolor("none")
    for spine in ax_leg.spines.values():
        spine.set_linewidth(D)

    # Column widths
    c1, c2, c3 = 0.12, 0.68, 0.2

    y = 1.0
    # Title
    title_h_norm = 10.0 / table_h
    ax_leg.axhline(y, color="black", lw=D_WIDE)
    ax_leg.text(
        0.5,
        y - title_h_norm / 2,
        texts["explication"],
        fontproperties=_get_font(font_size + 1, bold=True),
        ha="center",
        va="center",
    )
    y -= title_h_norm

    # Header
    header_h_norm = 8.0 / table_h
    ax_leg.axhline(y, color="black", lw=D_WIDE)
    h_y = y - header_h_norm / 2
    ax_leg.text(
        c1 / 2,
        h_y,
        texts["num"],
        fontproperties=_get_font(font_size, bold=True),
        ha="center",
        va="center",
    )
    ax_leg.text(
        c1 + c2 / 2,
        h_y,
        texts["name"],
        fontproperties=_get_font(font_size, bold=True),
        ha="center",
        va="center",
    )
    ax_leg.text(
        c1 + c2 + c3 / 2,
        h_y,
        texts["area_sqm"],
        fontproperties=_get_font(font_size, bold=True),
        ha="center",
        va="center",
    )
    y -= header_h_norm

    # Rows
    row_h_norm = row_h / table_h
    for i in range(num_items):
        item = items[i]
        area = calculate_area(item.points) or 0
        number = getattr(item, "number", str(i + 1))
        ax_leg.axhline(y, color="black", lw=D)
        row_y = y - row_h_norm / 2
        ax_leg.text(
            c1 / 2,
            row_y,
            number,
            fontproperties=_get_font(font_size),
            ha="center",
            va="center",
        )
        ax_leg.text(
            c1 + 0.02,
            row_y,
            item.name[:28],
            fontproperties=_get_font(font_size),
            ha="left",
            va="center",
        )
        ax_leg.text(
            c1 + c2 + c3 / 2,
            row_y,
            f"{area:.2f}",
            fontproperties=_get_font(font_size),
            ha="center",
            va="center",
        )
        y -= row_h_norm

    # Total
    ax_leg.axhline(y, color="black", lw=D_WIDE)
    row_y = y - row_h_norm / 2
    ax_leg.text(
        c1 + c2 / 2,
        row_y,
        texts["total_area"],
        fontproperties=_get_font(font_size, bold=True),
        ha="center",
        va="center",
    )
    ax_leg.text(
        c1 + c2 + c3 / 2,
        row_y,
        f"{total_area:.2f}",
        fontproperties=_get_font(font_size, bold=True),
        ha="center",
        va="center",
    )
    y -= row_h_norm
    ax_leg.axhline(y, color="black", lw=D_WIDE)

    # Vertical lines
    ax_leg.axvline(c1, color="black", lw=D, ymin=0, ymax=1 - title_h_norm)
    ax_leg.axvline(c1 + c2, color="black", lw=D, ymin=0, ymax=1 - title_h_norm)


def _draw_north_arrow(ax, lang: str = "ru", m_per_pt: float = 0.1):
    texts = I18N.get(lang, I18N["ru"])
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    # Position fixed relative to axis viewport
    x, y = xlim[0] + (xlim[1] - xlim[0]) * 0.08, ylim[1] - (ylim[1] - ylim[0]) * 0.1
    arrow_len = (ylim[1] - ylim[0]) * 0.06
    ax.annotate(
        "",
        xy=(x, y + arrow_len),
        xytext=(x, y),
        arrowprops=dict(arrowstyle="fancy", color="black", linewidth=D_SYMBOL),
    )
    ax.text(
        x,
        y + arrow_len + arrow_len * 0.3,
        texts["north"],
        fontproperties=_get_font(9, bold=True, m_per_pt=m_per_pt),
        ha="center",
    )


def _draw_sheet_reference_grid(ax_frame, pw_mm: float, ph_mm: float):
    """ISO 5457:1999 - Reference grid (A-B-C / 1-2-3) and Centering Marks."""
    # 1. Centering Marks (5mm long, Wide line)
    mark_len = 5.0
    # Top
    ax_frame.plot(
        [pw_mm / 2, pw_mm / 2], [ph_mm, ph_mm - mark_len], color="black", lw=D_WIDE
    )
    # Bottom
    ax_frame.plot([pw_mm / 2, pw_mm / 2], [0, mark_len], color="black", lw=D_WIDE)
    # Left
    ax_frame.plot([0, mark_len], [ph_mm / 2, ph_mm / 2], color="black", lw=D_WIDE)
    # Right
    ax_frame.plot(
        [pw_mm, pw_mm - mark_len], [ph_mm / 2, ph_mm / 2], color="black", lw=D_WIDE
    )

    # 2. Reference Grid (approx 50mm segments)
    # Horizontal (Numbers 1, 2, 3...)
    h_segments = int((pw_mm - MARGIN_LEFT - MARGIN_OTHER) / 50) or 1
    h_step = (pw_mm - MARGIN_LEFT - MARGIN_OTHER) / h_segments
    for i in range(h_segments):
        x = MARGIN_LEFT + i * h_step + h_step / 2
        # Top label
        ax_frame.text(
            x,
            ph_mm - MARGIN_OTHER / 2,
            str(i + 1),
            fontproperties=_get_font(5),
            ha="center",
            va="center",
        )
        # Bottom label
        ax_frame.text(
            x,
            MARGIN_OTHER / 2,
            str(i + 1),
            fontproperties=_get_font(5),
            ha="center",
            va="center",
        )
        # Ticks
        if i > 0:
            tx = MARGIN_LEFT + i * h_step
            ax_frame.plot([tx, tx], [ph_mm, ph_mm - MARGIN_OTHER], color="black", lw=D)
            ax_frame.plot([tx, tx], [0, MARGIN_OTHER], color="black", lw=D)

    # Vertical (Letters A, B, C...)
    v_segments = int((ph_mm - 2 * MARGIN_OTHER) / 50) or 1
    v_step = (ph_mm - 2 * MARGIN_OTHER) / v_segments
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"  # ISO 5457 skips I and O
    for i in range(v_segments):
        y = ph_mm - MARGIN_OTHER - i * v_step - v_step / 2
        char = letters[i % len(letters)]
        # Left label
        ax_frame.text(
            MARGIN_LEFT / 2,
            y,
            char,
            fontproperties=_get_font(5),
            ha="center",
            va="center",
        )
        # Right label
        ax_frame.text(
            pw_mm - MARGIN_OTHER / 2,
            y,
            char,
            fontproperties=_get_font(5),
            ha="center",
            va="center",
        )
        # Ticks
        if i > 0:
            ty = ph_mm - MARGIN_OTHER - i * v_step
            ax_frame.plot([0, MARGIN_LEFT], [ty, ty], color="black", lw=D)
            ax_frame.plot([pw_mm, pw_mm - MARGIN_OTHER], [ty, ty], color="black", lw=D)


def _draw_as_built_deviations(ax, points: List[AsBuiltPoint], m_per_pt: float = 0.1):
    """
    Renders standard as-built deviations (arrows and plan/fact text).
    """
    for p in points:
        dx_mm = (p.actual_x - p.design_x) * 1000
        dy_mm = (p.actual_y - p.design_y) * 1000

        # Draw design point (cross/circle)
        ax.plot(p.design_x, p.design_y, "rx", markersize=4, markeredgewidth=1)
        # Draw actual point
        ax.plot(p.actual_x, p.actual_y, "ko", markersize=2)

        # Vector arrow (exaggerated for visibility if small, but let's draw real direction)
        # In construction schemes, we often use text offsets like: ← 12
        if abs(dx_mm) > 1 or abs(dy_mm) > 1:
            # Horizontal deviation text
            h_char = "→" if dx_mm > 0 else "←"
            ax.text(
                p.actual_x,
                p.actual_y + 0.8 * m_per_pt * MM_TO_PT,
                f"{h_char} {abs(dx_mm):.0f}",
                fontproperties=_get_font(6, bold=True, m_per_pt=m_per_pt),
                color="red",
                ha="center",
            )

            # Vertical deviation text
            v_char = "↑" if dy_mm > 0 else "↓"
            ax.text(
                p.actual_x + 1.2 * m_per_pt * MM_TO_PT,
                p.actual_y,
                f"{v_char} {abs(dy_mm):.0f}",
                fontproperties=_get_font(6, bold=True, m_per_pt=m_per_pt),
                color="red",
                va="center",
            )

        # Z deviation if exists
        if p.actual_z is not None and p.design_z is not None:
            dz_mm = (p.actual_z - p.design_z) * 1000
            color = "red" if abs(dz_mm) > 10 else "blue"  # Highlight large Z errors
            ax.text(
                p.actual_x,
                p.actual_y - 0.8 * m_per_pt * MM_TO_PT,
                f"ΔZ: {dz_mm:+.0f}mm",
                fontproperties=_get_font(5.5, m_per_pt=m_per_pt),
                color=color,
                ha="center",
                va="top",
            )


def _draw_volume_grid(ax, grid: VolumeGrid, m_per_pt: float = 0.1):
    """
    Renders an earthwork cartogram grid with working elevations and volumes.
    """
    for cell in grid.cells:
        s2 = cell.size_m / 2
        # Draw cell boundary
        rect = Rectangle(
            (cell.center_x - s2, cell.center_y - s2),
            cell.size_m,
            cell.size_m,
            fill=True,
            facecolor="blue" if cell.volume > 0 else "red",
            alpha=0.05,
            edgecolor="black",
            linewidth=D,
            linestyle=":",
        )
        ax.add_patch(rect)

        # Center: Volume
        color = "blue" if cell.volume > 0 else "red"
        ax.text(
            cell.center_x,
            cell.center_y,
            f"{abs(cell.volume):.1f}",
            fontproperties=_get_font(7, bold=True, m_per_pt=m_per_pt),
            color=color,
            ha="center",
            va="center",
        )

        # Corners/Labels logic (Simplified for demo)
        # Working elevation (actual_z - design_z)
        working_z = cell.actual_z - cell.design_z
        ax.text(
            cell.center_x + s2 * 0.8,
            cell.center_y + s2 * 0.8,
            f"{working_z:+.2f}",
            fontproperties=_get_font(5.5, m_per_pt=m_per_pt),
            color="black",
            ha="right",
            va="top",
        )


def _draw_profile_table(fig, plan: ProfilePlan, pw_mm: float, ph_mm: float):
    """
    Renders the professional engineering profile table (the 'Podval').
    Contains: Slopes, Design Levels, Ground Levels, Depths, Distances, Stations.
    """
    # Dimensions (mm)
    table_w = pw_mm - MARGIN_LEFT - MARGIN_OTHER - STAMP_WIDTH - 10
    row_h = 8.0
    headers_w = 40.0

    lang = plan.language if plan.language in I18N else "ru"
    txt = I18N[lang]

    rows = [
        {"id": "depth", "label": txt.get("prof_depth", "Depth")},
        {"id": "slope", "label": txt.get("prof_slope", "Slopes")},
        {"id": "design_z", "label": txt.get("prof_design", "Design Z")},
        {"id": "ground_z", "label": txt.get("prof_ground", "Ground Z")},
        {"id": "dist", "label": txt.get("prof_dist", "Distance")},
        {"id": "station", "label": txt.get("prof_station", "Station")},
    ]

    table_h = len(rows) * row_h
    left_mm = MARGIN_LEFT
    bottom_mm = MARGIN_OTHER

    ax_table = fig.add_axes(
        [left_mm / pw_mm, bottom_mm / ph_mm, table_w / pw_mm, table_h / ph_mm]
    )
    ax_table.set_xticks([])
    ax_table.set_yticks([])
    ax_table.set_facecolor("white")
    for spine in ax_table.spines.values():
        spine.set_linewidth(D)

    # Grid lines
    for i in range(len(rows) + 1):
        ax_table.axhline(i / len(rows), color="black", lw=D)
    ax_table.axvline(headers_w / table_w, color="black", lw=D)

    # Labels
    for i, row in enumerate(reversed(rows)):
        ax_table.text(
            2 / table_w,
            (i + 0.5) / len(rows),
            row["label"],
            fontproperties=_get_font(6, bold=True),
            va="center",
        )

    # Data Column Mapping
    s_min = plan.points[0].station
    s_max = plan.points[-1].station
    s_span = s_max - s_min or 1.0
    data_w = table_w - headers_w

    def s_to_x(s):
        return (headers_w + (s - s_min) / s_span * data_w) / table_w

    for i, p in enumerate(plan.points):
        x = s_to_x(p.station)
        # Vertical tick
        ax_table.axvline(x, color="black", lw=D, ymin=0, ymax=1)

        # Ground Z
        ax_table.text(
            x,
            2.5 / len(rows),
            f"{p.ground_z:.2f}",
            fontproperties=_get_font(5.5),
            rotation=90,
            ha="center",
            va="center",
        )

        # Design Z
        if p.design_z is not None:
            ax_table.text(
                x,
                3.5 / len(rows),
                f"{p.design_z:.2f}",
                fontproperties=_get_font(5.5),
                rotation=90,
                ha="center",
                va="center",
                color="red",
            )

            # Depth (Ground - Design)
            depth = p.ground_z - p.design_z
            ax_table.text(
                x,
                5.5 / len(rows),
                f"{depth:.2f}",
                fontproperties=_get_font(5.5),
                rotation=90,
                ha="center",
                va="center",
                color="blue",
            )

        # Station (Picket)
        ax_table.text(
            x,
            0.5 / len(rows),
            f"{p.station:.0f}",
            fontproperties=_get_font(5.5),
            ha="center",
            va="center",
        )

        # Inter-point data (Distances and Slopes)
        if i > 0:
            prev = plan.points[i - 1]
            dx = p.station - prev.station
            mx = (s_to_x(p.station) + s_to_x(prev.station)) / 2

            # Distance
            ax_table.text(
                mx,
                1.5 / len(rows),
                f"{dx:.1f}",
                fontproperties=_get_font(5.5),
                ha="center",
                va="center",
            )

            # Slope (‰)
            if p.design_z is not None and prev.design_z is not None:
                dz = p.design_z - prev.design_z
                slope_promille = (dz / dx) * 1000

                # Draw diagonal slope line
                y_base = 4.5 / len(rows)
                y_delta = 0.3 / len(rows)
                if dz > 0:  # Up
                    ax_table.plot(
                        [s_to_x(prev.station), s_to_x(p.station)],
                        [y_base - y_delta, y_base + y_delta],
                        color="black",
                        lw=D,
                    )
                elif dz < 0:  # Down
                    ax_table.plot(
                        [s_to_x(prev.station), s_to_x(p.station)],
                        [y_base + y_delta, y_base - y_delta],
                        color="black",
                        lw=D,
                    )
                else:  # Horizontal
                    ax_table.axhline(
                        y_base,
                        xmin=s_to_x(prev.station),
                        xmax=s_to_x(p.station),
                        color="black",
                        lw=D,
                    )

                ax_table.text(
                    mx,
                    y_base + y_delta * 1.2,
                    f"{abs(slope_promille):.1f}‰",
                    fontproperties=_get_font(5, italic=True),
                    ha="center",
                    va="bottom",
                )
                ax_table.text(
                    mx,
                    y_base - y_delta * 1.2,
                    f"L={dx:.1f}",
                    fontproperties=_get_font(5),
                    ha="center",
                    va="top",
                )


def render_profile_plan(plan: ProfilePlan, output_format: str = "png") -> bytes:
    """
    Generates a professional longitudinal profile with vertical exaggeration.
    Supports PNG and SVG output formats.
    """
    dpi = plan.dpi
    lang = plan.language or "ru"

    # 1. Sheet Setup
    base_w, base_h = PAPER_SIZES.get(plan.paper_format.upper(), PAPER_SIZES["A3"])
    pw_mm, ph_mm = (
        (base_w, base_h) if plan.orientation == "landscape" else (base_h, base_w)
    )
    fig = Figure(figsize=(pw_mm / 25.4, ph_mm / 25.4), dpi=dpi)

    # Frame & Grid
    ax_frame = fig.add_axes([0, 0, 1, 1])
    ax_frame.set_axis_off()
    ax_frame.set_xlim(0, pw_mm)
    ax_frame.set_ylim(0, ph_mm)
    frame_rect = Rectangle(
        (MARGIN_LEFT, MARGIN_OTHER),
        pw_mm - MARGIN_LEFT - MARGIN_OTHER,
        ph_mm - 2 * MARGIN_OTHER,
        fill=False,
        lw=D_WIDE,
    )
    ax_frame.add_patch(frame_rect)
    _draw_sheet_reference_grid(ax_frame, pw_mm, ph_mm)

    # 2. Calculation of Axes
    table_h_mm = 48.0  # 6 rows * 8mm
    draw_left = MARGIN_LEFT + 10
    draw_bottom = MARGIN_OTHER + table_h_mm + 10
    draw_w = pw_mm - MARGIN_LEFT - MARGIN_OTHER - 20
    draw_h = ph_mm - MARGIN_OTHER - table_h_mm - STAMP_HEIGHT - 20

    ax = fig.add_axes(
        [draw_left / pw_mm, draw_bottom / ph_mm, draw_w / pw_mm, draw_h / ph_mm]
    )

    stations = [p.station for p in plan.points]
    grounds = [p.ground_z for p in plan.points]
    designs = [p.design_z for p in plan.points if p.design_z is not None]
    all_z = grounds + designs

    s_min, s_max = min(stations), max(stations)
    z_min, z_max = min(all_z) - 2, max(all_z) + 5

    ax.set_xlim(s_min, s_max)
    ax.set_ylim(z_min, z_max)
    ax.set_aspect("auto")

    # 3. Plotting lines
    # Ground profile
    ax.plot(stations, grounds, color="black", lw=D, zorder=3)

    # Design profile
    if designs:
        d_stations = [p.station for p in plan.points if p.design_z is not None]
        ax.plot(d_stations, designs, color="red", lw=D_WIDE, zorder=4)

    # Vertical Ordinates (Ordinates)
    # They should drop from points to the bottom of the table
    # Since they cross multiple axes, we can draw them on the frame axes or a separate axes
    # Let's draw them in the plot ax but allow clipping to 'off'
    for p in plan.points:
        # Line from ground to bottom of viewport
        ax.axvline(
            p.station, color="gray", lw=D / 2, linestyle=":", alpha=0.5, zorder=1
        )

    ax.grid(True, linestyle=":", alpha=0.3, zorder=0)
    ax.set_title(plan.title, fontproperties=_get_font(10, bold=True))

    # 4. Table and Stamp
    _draw_profile_table(fig, plan, pw_mm, ph_mm)
    _draw_stamp(
        fig,
        plan,
        f"H 1:{plan.horiz_scale} / V 1:{plan.vert_scale}",
        pw_mm,
        ph_mm,
        lang=lang,
    )

    buf = io.BytesIO()
    if output_format.lower() == "svg":
        fig.patch.set_facecolor("white")
        canvas = FigureCanvasSVG(fig)
        canvas.print_svg(buf)
    else:
        fig.savefig(buf, format="png", dpi=dpi, facecolor="white")
    buf.seek(0)
    return buf.getvalue()


def _draw_walls(ax, walls: List[Wall]):
    """
    Renders architectural walls with thickness and status-based styling.
    """
    for wall in walls:
        p1, p2 = wall.start_pt, wall.end_pt
        dx, dy = p2.x - p1.x, p2.y - p1.y
        length = math.hypot(dx, dy)
        if length == 0:
            continue

        # Style based on status
        color = "black"
        ls = TYPE_01
        alpha = 1.0
        if wall.status == "demolish":
            color = "#E57373"
            ls = TYPE_02
            alpha = 0.6
        elif wall.status == "new":
            color = "#81C784"
            alpha = 0.8

        # Perpendicular vector for thickness
        nx, ny = _perpendicular_offset(p1, p2, wall.thickness / 2)

        # Build 4 corners of the wall segment
        c1 = (p1.x + nx, p1.y + ny)
        c2 = (p2.x + nx, p2.y + ny)
        c3 = (p2.x - nx, p2.y - ny)
        c4 = (p1.x - nx, p1.y - ny)

        wall_poly = [c1, c2, c3, c4, c1]
        w_xs, w_ys = zip(*wall_poly)

        # Fill wall (material)
        hatch = _get_hatch(wall.material)
        ax.fill(
            w_xs,
            w_ys,
            color=color if wall.status != "existing" else "#F5F5F5",
            alpha=0.15 if wall.status == "existing" else 0.4,
            zorder=4,
        )
        if hatch and wall.status != "demolish":
            ax.fill(
                w_xs,
                w_ys,
                fill=False,
                hatch=hatch,
                edgecolor=color,
                linewidth=0,
                alpha=0.2,
                zorder=5,
            )

        # Draw outline
        ax.plot(
            w_xs,
            w_ys,
            color=color,
            linewidth=D_WIDE if wall.status != "demolish" else D,
            linestyle=ls,
            alpha=alpha,
            zorder=6,
        )

        # Draw Openings (Doors/Windows)
        _draw_openings(ax, wall, p1, p2, dx, dy, length, nx, ny)


def _draw_openings(ax, wall, p1, p2, dx, dy, length, nx, ny):
    for op in wall.openings:
        # Calculate opening start and end on the centerline
        ux, uy = dx / length, dy / length
        ox1 = p1.x + ux * op.start_distance
        oy1 = p1.y + uy * op.start_distance
        ox2 = ox1 + ux * op.width
        oy2 = oy1 + uy * op.width

        # Status styling for opening
        op_status = getattr(op, "status", wall.status)
        op_color = "black"
        if op_status == "demolish":
            op_color = "#E57373"
        elif op_status == "new":
            op_color = "#81C784"

        # Clear the wall fill (draw a white background)
        win_c1 = (ox1 + nx, oy1 + ny)
        win_c2 = (ox2 + nx, oy2 + ny)
        win_c3 = (ox2 - nx, oy2 - ny)
        win_c4 = (ox1 - nx, oy1 - ny)
        ax.fill(*zip(win_c1, win_c2, win_c3, win_c4), color="white", zorder=7)

        if op.type == "window":
            # Internal window lines
            ax.plot([ox1, ox2], [oy1, oy2], color=op_color, lw=D, zorder=8)
            ax.plot(
                [ox1 + nx * 0.5, ox2 + nx * 0.5],
                [oy1 + ny * 0.5, oy2 + ny * 0.5],
                color=op_color,
                lw=D / 2,
                zorder=8,
            )
            ax.plot(
                [ox1 - nx * 0.5, ox2 - nx * 0.5],
                [oy1 - ny * 0.5, oy2 - ny * 0.5],
                color=op_color,
                lw=D / 2,
                zorder=8,
            )

        elif op.type == "door":
            # Swing angle and direction
            sa_deg = getattr(op, "swing_angle", 90.0)
            leaf_angle_rad = math.atan2(dy, dx) + (
                math.pi / 2 if op.direction == 1 else -math.pi / 2
            )
            
            # Leaf line
            lx = ox1 + math.cos(leaf_angle_rad) * op.width
            ly = oy1 + math.sin(leaf_angle_rad) * op.width
            ax.plot([ox1, lx], [oy1, ly], color=op_color, lw=D, zorder=9)

            # Arc
            angle_wall = math.degrees(math.atan2(dy, dx))
            theta1 = angle_wall
            theta2 = math.degrees(leaf_angle_rad)
            if theta1 > theta2:
                theta1, theta2 = theta2, theta1

            arc = patches.Arc(
                (ox1, oy1),
                op.width * 2,
                op.width * 2,
                angle=0,
                theta1=theta1,
                theta2=theta2,
                color=op_color,
                lw=D / 2,
                linestyle="--",
                zorder=9,
            )
            ax.add_patch(arc)


def _draw_furniture(ax, items: List[FurnitureItem], m_per_pt: float = 0.1):
    """
    Renders 2D furniture and sanitary blocks based on type and dimensions.
    """
    for item in items:
        w, l = item.width, item.length
        cx, cy = item.center_pt.x, item.center_pt.y
        angle = math.radians(item.rotation)
        status = getattr(item, "status", "new")
        color = "black"
        if status == "demolish":
            color = "#E57373"
        elif status == "existing":
            color = "#757575"

        def rot(px, py):
            rx = px * math.cos(angle) - py * math.sin(angle)
            ry = px * math.sin(angle) + py * math.cos(angle)
            return rx + cx, ry + cy

        # Base frame
        corners = [
            rot(-w / 2, -l / 2),
            rot(w / 2, -l / 2),
            rot(w / 2, l / 2),
            rot(-w / 2, l / 2),
            rot(-w / 2, -l / 2),
        ]
        ax.plot(
            *zip(*corners),
            color=color,
            lw=D,
            alpha=0.7 if status == "new" else 0.4,
            zorder=8,
        )

        t = item.type.lower()
        if t == "wc":
            bowl = patches.Circle(
                rot(0, l * 0.1), w * 0.35, color=color, fill=False, lw=D, zorder=9
            )
            ax.add_patch(bowl)
            tank = [
                rot(-w * 0.4, -l * 0.4),
                rot(w * 0.4, -l * 0.4),
                rot(w * 0.4, -l * 0.1),
                rot(-w * 0.4, -l * 0.1),
                rot(-w * 0.4, -l * 0.4),
            ]
            ax.plot(*zip(*tank), color=color, lw=D, zorder=9)
        elif t == "bath":
            inner = patches.Ellipse(
                rot(0, 0),
                w * 0.8,
                l * 0.8,
                angle=item.rotation,
                fill=False,
                lw=D,
                color=color,
                zorder=9,
            )
            ax.add_patch(inner)
        elif t == "bed":
            for dx in [-0.25, 0.25]:
                p = [
                    rot(w * dx - w * 0.15, l * 0.25),
                    rot(w * dx + w * 0.15, l * 0.25),
                    rot(w * dx + w * 0.15, l * 0.4),
                    rot(w * dx - w * 0.15, l * 0.4),
                    rot(w * dx - w * 0.15, l * 0.25),
                ]
                ax.plot(*zip(*p), color=color, lw=D, zorder=9)
        elif t == "stove":
            for dx, dy in [(-0.25, -0.25), (0.25, -0.25), (-0.25, 0.25), (0.25, 0.25)]:
                b = patches.Circle(
                    rot(w * dx, l * dy),
                    w * 0.12,
                    color=color,
                    fill=False,
                    lw=D,
                    zorder=9,
                )
                ax.add_patch(b)
        elif t == "sofa":
            ax.plot(
                *zip(*[rot(-w / 2, l * 0.3), rot(w / 2, l * 0.3)]),
                color=color,
                lw=D,
                zorder=9,
            )
            ax.plot(
                *zip(*[rot(-w * 0.4, -l / 2), rot(-w * 0.4, l / 2)]),
                color=color,
                lw=D,
                zorder=9,
            )
            ax.plot(
                *zip(*[rot(w * 0.4, -l / 2), rot(w * 0.4, l / 2)]),
                color=color,
                lw=D,
                zorder=9,
            )
        elif t in ["fridge", "washer"]:
            # Standard appliance cross
            ax.plot(
                *zip(*[rot(-w / 2, -l / 2), rot(w / 2, l / 2)]),
                color=color,
                lw=D / 2,
                zorder=9,
            )
            ax.plot(
                *zip(*[rot(w / 2, -l / 2), rot(-w / 2, l / 2)]),
                color=color,
                lw=D / 2,
                zorder=9,
            )

        # Label
        label = getattr(item, "label", None)
        if label:
            ax.text(
                cx,
                cy - l / 2 - 0.2,
                label,
                fontproperties=_get_font(6, m_per_pt=m_per_pt),
                ha="center",
                va="top",
                zorder=10,
            )


def _draw_engineering(ax, items: List[EngineeringItem], m_per_pt: float = 0.1):
    """
    Renders engineering symbols: sockets, switches, lamps, etc.
    """
    for item in items:
        x, y = item.point.x, item.point.y
        t = item.type.lower()
        angle = math.radians(item.rotation)
        
        def rot(px, py):
            rx = px * math.cos(angle) - py * math.sin(angle)
            ry = px * math.sin(angle) + py * math.cos(angle)
            return rx + x, ry + y

        if t == "socket":
            # Socket symbol: circle with two lines
            circle = patches.Circle((x, y), 0.12, color="blue", fill=False, lw=D, zorder=11)
            ax.add_patch(circle)
            ax.plot(*zip(*[rot(-0.1, 0.1), rot(-0.2, 0.2)]), color="blue", lw=D, zorder=11)
            ax.plot(*zip(*[rot(0.1, 0.1), rot(0.2, 0.2)]), color="blue", lw=D, zorder=11)
        elif t == "switch":
            # Switch symbol: circle with one L-line
            circle = patches.Circle((x, y), 0.1, color="orange", fill=False, lw=D, zorder=11)
            ax.add_patch(circle)
            ax.plot(*zip(*[rot(0, 0.1), rot(0, 0.2), rot(0.1, 0.2)]), color="orange", lw=D, zorder=11)
        elif t == "lamp":
            # Lamp symbol: cross in circle
            circle = patches.Circle((x, y), 0.15, color="gold", fill=False, lw=D, zorder=11)
            ax.add_patch(circle)
            ax.plot(*zip(*[rot(-0.1, -0.1), rot(0.1, 0.1)]), color="gold", lw=D, zorder=11)
            ax.plot(*zip(*[rot(-0.1, 0.1), rot(0.1, -0.1)]), color="gold", lw=D, zorder=11)
        elif t == "radiator":
            # Radiator: rectangle with zig-zag
            w, l = 0.8, 0.15
            rect = [rot(-w/2, -l/2), rot(w/2, -l/2), rot(w/2, l/2), rot(-w/2, l/2), rot(-w/2, -l/2)]
            ax.plot(*zip(*rect), color="brown", lw=D, zorder=11)
            for i in range(-3, 4):
                ax.plot(*zip(*[rot(i*0.1, -l/2), rot(i*0.1, l/2)]), color="brown", lw=D/2, zorder=11)

        if item.label:
            ax.text(x, y + 0.3, item.label, fontproperties=_get_font(5, m_per_pt=m_per_pt), ha="center", zorder=12)


def _draw_chained_dimensions(ax, dimensions: List[DimensionLine], m_per_pt: float = 0.1):
    """
    Renders professional chained dimension lines.
    """
    for dim in dimensions:
        pts = dim.points
        if len(pts) < 2:
            continue
            
        # Offset direction logic (simplified: assume sequential points)
        for i in range(len(pts) - 1):
            p1, p2 = pts[i], pts[i+1]
            dist = math.hypot(p2.x - p1.x, p2.y - p1.y)
            if dist < 0.01: continue
            
            # Dimension line offset
            nx, ny = _perpendicular_offset(p1, p2, dim.offset)
            d1 = (p1.x + nx, p1.y + ny)
            d2 = (p2.x + nx, p2.y + ny)
            
            # Draw dimension line
            ax.plot([d1[0], d2[0]], [d1[1], d2[1]], color="black", lw=D/2, zorder=15)
            
            # Draw extension lines
            ax.plot([p1.x, d1[0]], [p1.y, d1[1]], color="gray", lw=D/2, linestyle="--", zorder=14)
            ax.plot([p2.x, d2[0]], [p2.y, d2[1]], color="gray", lw=D/2, linestyle="--", zorder=14)
            
            # Draw ticks
            angle = math.atan2(p2.y - p1.y, p2.x - p1.x) + math.pi/4
            tx, ty = math.cos(angle)*0.1, math.sin(angle)*0.1
            ax.plot([d1[0]-tx, d1[0]+tx], [d1[1]-ty, d1[1]+ty], color="black", lw=D, zorder=16)
            ax.plot([d2[0]-tx, d2[0]+tx], [d2[1]-ty, d2[1]+ty], color="black", lw=D, zorder=16)
            
            # Text (converted to mm)
            val = dist * 1000
            txt = dim.label_format.format(val)
            mx, my = (d1[0]+d2[0])/2, (d1[1]+d2[1])/2
            rot_deg = math.degrees(math.atan2(p2.y - p1.y, p2.x - p1.x))
            if rot_deg > 90: rot_deg -= 180
            if rot_deg < -90: rot_deg += 180
            
            ax.text(mx + nx*0.1, my + ny*0.1, txt, fontproperties=_get_font(6, m_per_pt=m_per_pt), 
                    ha="center", va="bottom", rotation=rot_deg, zorder=17,
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=0.1))


def _draw_floor_pattern(ax, room: Room, m_per_pt: float = 0.1):
    """
    Renders floor textures: tiles, parquet, planks.
    """
    if not room.floor_pattern or not room.points:
        return
        
    pts = room.points
    xs, ys = zip(*[(p.x, p.y) for p in pts])
    poly = patches.Polygon(list(zip(xs, ys)), closed=True)
    
    pat = room.floor_pattern.lower()
    tw, tl = room.floor_tile_size or [0.6, 0.6]
    angle = math.radians(room.floor_angle)
    
    # Create a grid of lines covering the bounding box
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    
    # Expand for rotation
    margin = max(tw, tl) * 2
    diag = math.hypot(x_max - x_min, y_max - y_min) + margin
    cx, cy = (x_min + x_max)/2, (y_min + y_max)/2
    
    # Basic grid for tiles/planks
    if pat in ["tiles", "grid", "planks"]:
        # Vertical lines
        num_v = int(diag / tw) + 2
        for i in range(-num_v//2, num_v//2 + 1):
            lx = i * tw
            # Line pts in local space
            p_start = (lx, -diag/2)
            p_end = (lx, diag/2)
            # Rotate and translate
            def rot(px, py):
                return px*math.cos(angle) - py*math.sin(angle) + cx, \
                       px*math.sin(angle) + py*math.cos(angle) + cy
            
            p1 = rot(*p_start)
            p2 = rot(*p_end)
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#DDDDDD", lw=D/4, zorder=2, clip_path=poly, transform=ax.transData)

        # Horizontal lines
        num_h = int(diag / tl) + 2
        for i in range(-num_h//2, num_h//2 + 1):
            ly = i * tl
            offset = 0
            if pat == "planks":
                # Staggered planks logic could go here, but for simplicity just grid
                pass
                
            p_start = (-diag/2, ly)
            p_end = (diag/2, ly)
            p1 = rot(*p_start)
            p2 = rot(*p_end)
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#DDDDDD", lw=D/4, zorder=2, clip_path=poly, transform=ax.transData)

def _calculate_tile_estimate(room: Room) -> Dict[str, int]:
    """
    Rough tile estimation: Area based + 15% for cuts.
    """
    area = calculate_area(room.points)
    if not room.floor_tile_size:
        return {"total": 0, "cut": 0}
    tile_area = room.floor_tile_size[0] * room.floor_tile_size[1]
    if tile_area == 0: return {"total": 0, "cut": 0}
    
    total_whole = int(area / tile_area)
    total_with_waste = int(total_whole * 1.15) + 1
    return {"total": total_with_waste, "whole": total_whole, "cut": total_with_waste - total_whole}

def _draw_ergonomics_warnings(ax, furniture: List[FurnitureItem], walls: List[Wall], m_per_pt: float = 0.1):
    """
    Highlights ergonomics violations (too close to walls or other objects).
    """
    for item in furniture:
        pad = getattr(item, "ergonomics_padding", 0.0)
        if pad <= 0: continue
        
        # Draw transparent red circle for padding
        circle = patches.Circle((item.center_pt.x, item.center_pt.y), 
                                item.width/2 + pad, 
                                color="red", alpha=0.1, zorder=1)
        ax.add_patch(circle)
        
        # Simple check against walls
        for wall in walls:
            # Distance from point to line segment
            p = item.center_pt
            w1, w2 = wall.start_pt, wall.end_pt
            dx, dy = w2.x - w1.x, w2.y - w1.y
            l2 = dx*dx + dy*dy
            if l2 == 0: continue
            t = max(0, min(1, ((p.x - w1.x) * dx + (p.y - w1.y) * dy) / l2))
            proj_x = w1.x + t * dx
            proj_y = w1.y + t * dy
            dist = math.hypot(p.x - proj_x, p.y - proj_y)
            
            if dist < (item.width/2 + pad):
                # Draw warning arrow
                ax.annotate("!", xy=(proj_x, proj_y), xytext=(p.x, p.y),
                            arrowprops=dict(arrowstyle="->", color="red", lw=D),
                            color="red", fontsize=8, fontweight="bold")


def render_interior_plan(plan: InteriorPlan, output_format: str = "png") -> bytes:
    # Ensure hatch linewidth is set for thread safety (constant value)
    matplotlib.rcParams["hatch.linewidth"] = D

    dpi = plan.dpi
    base_w, base_h = PAPER_SIZES.get(plan.paper_format.upper(), PAPER_SIZES["A4"])
    pw_mm, ph_mm = (
        (base_w, base_h) if plan.orientation == "landscape" else (base_h, base_w)
    )
    fig = Figure(figsize=(pw_mm / 25.4, ph_mm / 25.4), dpi=dpi)

    ax_frame = fig.add_axes([0, 0, 1, 1])
    ax_frame.set_axis_off()
    ax_frame.set_xlim(0, pw_mm)
    ax_frame.set_ylim(0, ph_mm)
    ax_frame.add_patch(
        Rectangle(
            (MARGIN_LEFT, MARGIN_OTHER),
            pw_mm - MARGIN_LEFT - MARGIN_OTHER,
            ph_mm - 2 * MARGIN_OTHER,
            fill=False,
            lw=D_WIDE,
        )
    )
    _draw_sheet_reference_grid(ax_frame, pw_mm, ph_mm)

    # Calculate Axis
    draw_w_mm = pw_mm - MARGIN_LEFT - MARGIN_OTHER - 20
    draw_h_mm = ph_mm - 2 * MARGIN_OTHER - STAMP_HEIGHT - 10
    ax = fig.add_axes(
        [
            (MARGIN_LEFT + 10) / pw_mm,
            (MARGIN_OTHER + STAMP_HEIGHT + 5) / ph_mm,
            draw_w_mm / pw_mm,
            draw_h_mm / ph_mm,
        ]
    )
    ax.set_aspect("equal")
    # Bounds
    all_pts = []
    for w in plan.walls:
        all_pts.extend([w.start_pt, w.end_pt])
    for rm in plan.rooms:
        all_pts.extend(rm.points)

    if not all_pts:
        return b""

    xs, ys = [p.x for p in all_pts], [p.y for p in all_pts]
    x_min, x_max, y_min, y_max = min(xs), max(xs), min(ys), max(ys)
    x_span, y_span = x_max - x_min or 1.0, y_max - y_min or 1.0
    cx, cy = (x_min + x_max) / 2, (y_min + y_max) / 2

    # 1. Determine Scale (Support Auto-scale)
    if plan.scale <= 0:
        scale_val = _calculate_auto_scale(
            max(x_span, y_span), min(draw_w_mm, draw_h_mm)
        )
    else:
        scale_val = plan.scale
        # Auto-adjust if units are obviously wrong (e.g. millimeters provided instead of meters)
        m_per_mm_temp = scale_val / 1000.0
        if x_span > (draw_w_mm * m_per_mm_temp * 5):
            scale_val = _calculate_auto_scale(
                max(x_span, y_span), min(draw_w_mm, draw_h_mm)
            )

    m_per_mm = scale_val / 1000.0
    m_per_pt = m_per_mm / MM_TO_PT  # For font scaling
    view_w_m = draw_w_mm * m_per_mm
    view_h_m = draw_h_mm * m_per_mm

    ax.set_xlim(cx - view_w_m / 2, cx + view_w_m / 2)
    ax.set_ylim(cy - view_h_m / 2, cy + view_h_m / 2)

    # 2. Rendering Layers
    layer = getattr(plan, "layer", "full")

    # Layer: Construction (Walls + Demolition)
    if layer in ["full", "construction"]:
        _draw_walls(ax, plan.walls)
        
    # Draw floor patterns for each room
    if layer in ["full", "furniture"]:
        for rm in plan.rooms:
            _draw_floor_pattern(ax, rm, m_per_pt=m_per_pt)

    # Layer: Furniture
    if layer in ["full", "furniture"]:
        if layer == "furniture":
            # Just light outlines for walls
            for w in plan.walls:
                p1, p2 = w.start_pt, w.end_pt
                ax.plot([p1.x, p2.x], [p1.y, p2.y], color="#EEEEEE", lw=D_WIDE, zorder=1)
        
        if plan.furniture:
            _draw_furniture(ax, plan.furniture, m_per_pt=m_per_pt)
            
        # Draw Ergonomics (Clearance zones)
        if getattr(plan, "show_ergonomics", False):
            _draw_ergonomics_warnings(ax, plan.furniture, plan.walls, m_per_pt=m_per_pt)

    # Layer: Engineering (Electrical, Plumbing, HVAC)
    if layer in ["full", "electrical", "engineering"]:
        if plan.engineering:
            _draw_engineering(ax, plan.engineering, m_per_pt=m_per_pt)

    # Layer: Dimensions
    if layer in ["full", "construction", "furniture"]:
        if plan.dimensions:
            _draw_chained_dimensions(ax, plan.dimensions, m_per_pt=m_per_pt)

    # 3. Room Labels and Explication
    for rm in plan.rooms:
        if rm.points:
            rx, ry = _centroid(rm.points)
            area = calculate_area(rm.points) or 0
            label = f"{rm.number}\n{area:.2f} m²"
            if rm.wall_finish:
                label += f"\n({rm.wall_finish})"
            
            ax.text(
                rx,
                ry,
                label,
                fontproperties=_get_font(7, bold=True, m_per_pt=m_per_pt),
                ha="center",
                va="center",
                zorder=20,
                bbox=dict(
                    boxstyle="round,pad=0.2",
                    facecolor="white",
                    alpha=0.8,
                    edgecolor="#CCCCCC",
                    lw=0.5
                ),
            )

    # Calculate Total Area
    total_area = sum(calculate_area(rm.points) or 0 for rm in plan.rooms)
    _draw_explication(fig, plan.rooms, total_area, pw_mm, ph_mm, lang=plan.language)

    _draw_stamp(fig, plan, f"1:{scale_val}", pw_mm, ph_mm, lang=plan.language)

    buf = io.BytesIO()
    if output_format.lower() == "svg":
        fig.patch.set_facecolor("white")
        canvas = FigureCanvasSVG(fig)
        canvas.print_svg(buf)
    else:
        fig.savefig(buf, format="png", dpi=dpi, facecolor="white")
    buf.seek(0)
    return buf.getvalue()


def render_plot_plan(plan: PlotPlan, output_format: str = "png") -> bytes:
    # Ensure hatch linewidth is set for thread safety (constant value)
    matplotlib.rcParams["hatch.linewidth"] = D

    dpi = plan.dpi if plan.dpi >= 150 else 300
    lang = plan.language or "ru"

    # 1. Determine Paper Size (ISO 5457)
    base_w, base_h = PAPER_SIZES.get(plan.paper_format.upper(), PAPER_SIZES["A4"])
    if plan.orientation == "portrait":
        pw_mm, ph_mm = base_h, base_w
    else:
        pw_mm, ph_mm = base_w, base_h

    fig = Figure(figsize=(pw_mm / 25.4, ph_mm / 25.4), dpi=dpi)

    # 2. Draw Frame (ISO 5457)
    ax_frame = fig.add_axes([0, 0, 1, 1])
    ax_frame.set_axis_off()
    ax_frame.set_xlim(0, pw_mm)
    ax_frame.set_ylim(0, ph_mm)

    frame_rect = Rectangle(
        (MARGIN_LEFT, MARGIN_OTHER),
        pw_mm - MARGIN_LEFT - MARGIN_OTHER,
        ph_mm - 2 * MARGIN_OTHER,
        fill=False,
        color="black",
        linewidth=D_WIDE,
    )
    ax_frame.add_patch(frame_rect)

    # 3. Draw Reference Grid (ISO 5457)
    _draw_sheet_reference_grid(ax_frame, pw_mm, ph_mm)

    # 4. Calculate Scale (ISO 5455)
    # Collect all points for bounding box calculation (boundary, zones, as-built, volume grid)
    xs: list[float] = []
    ys: list[float] = []

    for p in plan.boundary_points:
        xs.append(p.x)
        ys.append(p.y)
    for zone in plan.zones:
        for zp in zone.points:
            xs.append(zp.x)
            ys.append(zp.y)
    if plan.as_built_points:
        for ab in plan.as_built_points:
            xs.append(ab.actual_x)
            ys.append(ab.actual_y)
    if plan.volume_grid:
        for cell in plan.volume_grid.cells:
            xs.append(cell.center_x)
            ys.append(cell.center_y)

    if not xs:
        return b""

    x_min, x_max, y_min, y_max = min(xs), max(xs), min(ys), max(ys)
    x_span, y_span = x_max - x_min or 1, y_max - y_min or 1

    # Available area mm
    avail_w_mm = pw_mm - MARGIN_LEFT - MARGIN_OTHER - 20  # 10mm padding each side
    avail_h_mm = ph_mm - 2 * MARGIN_OTHER - STAMP_HEIGHT - 20

    scale_val = _calculate_auto_scale(max(x_span, y_span), min(avail_w_mm, avail_h_mm))
    scale_str = f"1:{scale_val}"

    m_per_mm = scale_val / 1000.0
    m_per_pt = m_per_mm / MM_TO_PT

    # 4. Main Drawing Axis
    # Center object in the available area
    main_w_norm = avail_w_mm / pw_mm
    main_h_norm = avail_h_mm / ph_mm
    main_left_norm = (
        MARGIN_LEFT + (pw_mm - MARGIN_LEFT - MARGIN_OTHER - avail_w_mm) / 2
    ) / pw_mm
    main_bottom_norm = (MARGIN_OTHER + STAMP_HEIGHT + 10) / ph_mm

    ax = fig.add_axes([main_left_norm, main_bottom_norm, main_w_norm, main_h_norm])
    ax.set_aspect("equal")

    cx, cy = (x_min + x_max) / 2, (y_min + y_max) / 2
    view_w_m = avail_w_mm * m_per_mm
    view_h_m = avail_h_mm * m_per_mm
    ax.set_xlim(cx - view_w_m / 2, cx + view_w_m / 2)
    ax.set_ylim(cy - view_h_m / 2, cy + view_h_m / 2)

    ax.grid(
        True, which="both", color="#F8F8F8", linestyle=TYPE_01, linewidth=D, zorder=0
    )
    ax.tick_params(labelsize=6.5)
    ax.set_xlabel("X (m)", fontproperties=_get_font(6.5, italic=True))
    ax.set_ylabel("Y (m)", fontproperties=_get_font(6.5, italic=True))

    label_tracker = LabelTracker()

    if plan.zones:
        _draw_zones(
            ax,
            plan.zones,
            show_areas=plan.show_areas,
            standard=plan.standard,
            m_per_pt=m_per_pt,
            tracker=label_tracker,
        )
    _draw_boundary(ax, plan.boundary_points, standard=plan.standard)

    if plan.show_vertex_labels:
        _draw_vertex_labels(
            ax,
            plan.boundary_points,
            standard=plan.standard,
            m_per_pt=m_per_pt,
            show_coords=plan.coordinate_labels,
            tracker=label_tracker,
        )
    if plan.show_distances:
        _draw_distances(
            ax,
            plan.boundary_points,
            standard=plan.standard,
            fontsize=7,
            show_azimuths=plan.show_azimuths,
            m_per_pt=m_per_pt,
        )

    if plan.as_built_points:
        _draw_as_built_deviations(ax, plan.as_built_points, m_per_pt=m_per_pt)

    if plan.volume_grid:
        _draw_volume_grid(ax, plan.volume_grid, m_per_pt=m_per_pt)

    if plan.show_scale_bar:
        _draw_scale_bar(ax, x_span, pw_mm / 25.4, lang=lang, m_per_pt=m_per_pt)

    if plan.standard == "shipbuilding":
        texts = I18N.get(lang, I18N["ru"])
        ax.text(
            ax.get_xlim()[0],
            cy,
            texts.get("stern", "STERN"),
            fontproperties=_get_font(8, bold=True),
            ha="left",
            va="center",
            rotation=90,
        )
        ax.text(
            ax.get_xlim()[1],
            cy,
            texts.get("bow", "BOW"),
            fontproperties=_get_font(8, bold=True),
            ha="right",
            va="center",
            rotation=-90,
        )
    else:
        _draw_north_arrow(ax, lang=lang, m_per_pt=m_per_pt)

    total_area = calculate_area(plan.boundary_points) or 0
    _draw_explication(fig, plan.zones, total_area, pw_mm, ph_mm, lang=lang)
    _draw_stamp(fig, plan, scale_str, pw_mm, ph_mm, lang=lang)

    buf = io.BytesIO()
    if output_format.lower() == "svg":
        fig.patch.set_facecolor("white")
        canvas = FigureCanvasSVG(fig)
        canvas.print_svg(buf)
    else:
        fig.savefig(buf, format="png", dpi=dpi, facecolor="white")
    buf.seek(0)
    return buf.getvalue()
