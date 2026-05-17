import json
import os
from theodolite_mcp.infrastructure.mcp_server import draw_interior_plan

# --- ПРОЄКТ: КУХНЯ-ОФІС (БЕЗ ДУШОВОЇ) ---
# Концепція: Робоче місце + зона швидкого приготування їжі (мікрохвильовка, мультиварка, хлібопічка)

def generate_kitchen_office_plan():
    output_path = "output/kitchen_office_plan.png"
    
    # 1. СТІНИ (Будинок 8x5м = 40м2)
    walls = [
        {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 8, "y": 0}, "thickness": 0.3},
        {"start_pt": {"x": 8, "y": 0}, "end_pt": {"x": 8, "y": 5}, "thickness": 0.3, "openings": [{"type": "window", "position": 1.5, "width": 2.0}]}, # Велике вікно в офісі
        {"start_pt": {"x": 8, "y": 5}, "end_pt": {"x": 0, "y": 5}, "thickness": 0.3, "openings": [{"type": "window", "position": 3.0, "width": 1.2}]}, # Вікно на кухні
        {"start_pt": {"x": 0, "y": 5}, "end_pt": {"x": 0, "y": 0}, "thickness": 0.3, "openings": [{"type": "door", "position": 0.5, "width": 0.9}]}, # Вхідні двері
        
        # Розділювальна барна стійка або легка перегородка
        {"start_pt": {"x": 4, "y": 0}, "end_pt": {"x": 4, "y": 3}, "thickness": 0.1, "status": "new"}, 
    ]

    # 2. КІМНАТИ (Зони)
    rooms = [
        {"name": "Робоча зона (Офіс)", "number": "1", "points": [{"x": 0, "y": 0}, {"x": 4, "y": 0}, {"x": 4, "y": 5}, {"x": 0, "y": 5}]},
        {"name": "Зона кухні", "number": "2", "points": [{"x": 4, "y": 0}, {"x": 8, "y": 0}, {"x": 8, "y": 5}, {"x": 4, "y": 5}]},
    ]

    # 3. МЕБЛІ ТА ОБЛАДНАННЯ
    furniture = [
        # --- ОФІСНА ЗОНА ---
        # Робочий стіл (використовуємо 'table' як заглушку, якщо тип підтримується, або 'bed' з іншими розмірами)
        # У поточній версії доступні: wc, bath, sink, stove, bed, sofa. 
        # Використаємо 'bed' як стіл 1.6x0.8м
        {"type": "bed", "center_pt": {"x": 1.0, "y": 2.5}, "width": 0.8, "length": 1.6, "rotation": 90}, # Робочий стіл біля вікна
        {"type": "sofa", "center_pt": {"x": 2.5, "y": 0.6}, "width": 2.0, "length": 0.9}, # Диван для відпочинку
        
        # --- КУХОННА ЗОНА ---
        {"type": "sink", "center_pt": {"x": 7.5, "y": 4.5}, "width": 0.6, "length": 0.6}, # Мийка
        
        # Стіл під дрібну техніку (мікрохвильовка, мультиварка, хлібопічка)
        # Зобразимо це як ряд кухонних тумб (тип 'stove' без конфорок або просто блоки)
        {"type": "stove", "center_pt": {"x": 6.0, "y": 4.5}, "width": 0.6, "length": 0.6}, # Мультиварка / Хлібопічка
        {"type": "stove", "center_pt": {"x": 6.6, "y": 4.5}, "width": 0.6, "length": 0.6}, # Мікрохвильовка
        
        # Обідній стіл
        {"type": "bed", "center_pt": {"x": 6.0, "y": 1.5}, "width": 1.2, "length": 0.8},
    ]

    try:
        res = draw_interior_plan(
            title="План: Офіс-Кухня 40м2",
            walls_json=walls,
            rooms_json=rooms,
            furniture_json=furniture,
            language="uk",
            output_path=output_path
        )
        print(f"Проєкт 'Офіс-Кухня' успішно створено: {output_path}")
    except Exception as e:
        print(f"Помилка: {e}")

if __name__ == "__main__":
    generate_kitchen_office_plan()
