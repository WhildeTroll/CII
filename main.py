import json
from optimizer import ResourceOptimizer
from scheduler import ScheduleBuilder


def main():
    print("=" * 60)
    print("ПРОТОТИП СИСТЕМЫ ОПТИМИЗАЦИИ РАСПРЕДЕЛЕНИЯ РЕСУРСОВ")
    print("=" * 60)

    # Загрузка данных
    print("\n Загрузка входных данных...")
    with open('data/tasks.json', 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    with open('data/employees.json', 'r', encoding='utf-8') as f:
        employees = json.load(f)

    with open('data/calendar.json', 'r', encoding='utf-8') as f:
        calendar = json.load(f)

    print(f"Загружено: {len(tasks)} задач, {len(employees)} исполнителей")

    # Оптимизация распределения
    print("\n Запуск генетического алгоритма...")
    optimizer = ResourceOptimizer(tasks, employees, calendar)
    best_solution, logbook = optimizer.optimize()

    # Получение результатов назначения
    assignment = optimizer.get_assignment(best_solution)

    print("\n РЕЗУЛЬТАТЫ ОПТИМИЗАЦИИ:")
    print("-" * 60)
    for assign in assignment:
        status = "СООТВЕТСТВУЕТ" if assign["skills_match"] == "✓" else "НЕ СООТВЕТСТВУЕТ"
        print(f"Задача: {assign['task_name']:30} → "
              f"Исполнитель: {assign['employee_name']:20} "
              f"[{status}]")

    # Построение расписания
    print("\n Построение расписания...")
    scheduler = ScheduleBuilder(tasks, employees, calendar)
    schedule = scheduler.build_schedule(assignment)

    # Расчет метрик
    metrics = scheduler.calculate_metrics(schedule)

    print("\n МЕТРИКИ ЭФФЕКТИВНОСТИ:")
    print("-" * 60)
    print(f"Общая продолжительность проекта: {metrics['total_duration']} дней")
    print(f"Общее количество человеко-часов: {metrics['total_hours']} ч")
    print(f"Задач с несоответствием навыков: {metrics['unmatched_skills']}")

    print(f"\n Распределение задач по исполнителям:")
    for emp, count in metrics['tasks_per_employee'].items():
        print(f"  {emp}: {count} задач")

    # Визуализация
    print("\n Генерация диаграммы Ганта...")
    scheduler.visualize_gantt(schedule)

    # Сохранение результатов в CSV
    import pandas as pd
    df_schedule = pd.DataFrame(schedule)
    df_schedule.to_csv('output/optimized_schedule.csv', index=False, encoding='utf-8-sig')
    print("\n Результаты сохранены в 'output/optimized_schedule.csv'")

    print("\n Оптимизация завершена успешно!")


if __name__ == "__main__":
    main()