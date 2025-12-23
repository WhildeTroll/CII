import json
import pandas as pd
from datetime import datetime, timedelta

def validate_task_data(task):
    """Валидация данных задачи"""
    required_fields = ["name", "hours"]
    for field in required_fields:
        if field not in task:
            return False, f"Отсутствует поле: {field}"
    
    if not isinstance(task.get("hours", 0), (int, float)) or task["hours"] <= 0:
        return False, "Часы должны быть положительным числом"
    
    if "priority" in task and task["priority"] not in ["high", "medium", "low"]:
        return False, "Приоритет должен быть high, medium или low"
    
    return True, "OK"

def validate_employee_data(employee):
    """Валидация данных исполнителя"""
    required_fields = ["name", "daily_hours", "cost_per_hour"]
    for field in required_fields:
        if field not in employee:
            return False, f"Отсутствует поле: {field}"
    
    if not isinstance(employee.get("daily_hours", 0), (int, float)) or employee["daily_hours"] <= 0:
        return False, "Рабочие часы должны быть положительным числом"
    
    if not isinstance(employee.get("cost_per_hour", 0), (int, float)) or employee["cost_per_hour"] <= 0:
        return False, "Стоимость часа должна быть положительным числом"
    
    return True, "OK"

def calculate_project_stats(tasks, employees):
    """Расчет статистики проекта"""
    stats = {
        "total_tasks": len(tasks),
        "total_employees": len(employees),
        "total_hours": sum(t.get("hours", 0) for t in tasks),
        "avg_task_hours": sum(t.get("hours", 0) for t in tasks) / len(tasks) if tasks else 0,
        "avg_employee_cost": sum(e.get("cost_per_hour", 0) for e in employees) / len(employees) if employees else 0,
        "estimated_project_cost": sum(
            t.get("hours", 0) * 
            (sum(e.get("cost_per_hour", 0) for e in employees) / len(employees) if employees else 0)
            for t in tasks
        )
    }
    return stats

def export_to_jira_format(assignments, filename="jira_import.csv"):
    """Экспорт в формат для импорта в Jira"""
    jira_data = []
    
    for assignment in assignments:
        jira_data.append({
            "Summary": assignment["task_name"],
            "Assignee": assignment["employee_name"],
            "Story Points": assignment["task_hours"] / 8,  # Предполагаем 8 часов на день
            "Priority": assignment["task_priority"].upper(),
            "Labels": ",".join(assignment.get("matched_skills", [])),
            "Description": f"Назначено системой оптимизации. Эффективность: {assignment['efficiency_score']}%"
        })
    
    df = pd.DataFrame(jira_data)
    return df.to_csv(index=False, encoding='utf-8-sig')

def get_color_for_efficiency(efficiency):
    """Получение цвета для индикатора эффективности"""
    if efficiency >= 80:
        return "#10B981"  # green
    elif efficiency >= 60:
        return "#F59E0B"  # yellow
    else:
        return "#EF4444"  # red