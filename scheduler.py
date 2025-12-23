from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

class ScheduleBuilder:
    def __init__(self, tasks, employees, calendar):
        self.tasks = tasks
        self.employees = employees
        self.calendar = calendar
        self.start_date = datetime.strptime(calendar["start_date"], "%Y-%m-%d")
        
    def build_schedule(self, assignment):
        """Построение детального расписания"""
        schedule = []
        current_date = self.start_date
        
        # Создаем расписание для каждого исполнителя
        for emp in self.employees:
            emp_tasks = [a for a in assignment if a["employee_id"] == emp["id"]]
            
            current_emp_date = self.start_date
            for task_assignment in emp_tasks:
                task = next(t for t in self.tasks if t["id"] == task_assignment["task_id"])
                
                # Рассчитываем дни выполнения
                days_needed = task["hours"] / emp["daily_hours"]
                
                schedule.append({
                    "employee": emp["name"],
                    "task": task["name"],
                    "start_date": current_emp_date.strftime("%Y-%m-%d"),
                    "end_date": (current_emp_date + timedelta(days=days_needed)).strftime("%Y-%m-%d"),
                    "hours": task["hours"],
                    "skills_match": task_assignment["skills_match"]
                })
                
                current_emp_date += timedelta(days=days_needed + 1)  # +1 день между задачами
        
        return schedule
    
    def visualize_gantt(self, schedule, filename="output/schedule.png"):
        """Визуализация расписания в виде диаграммы Ганта"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        colors = plt.cm.Set3(range(len(self.employees)))
        employee_names = [emp["name"] for emp in self.employees]
        
        # Создаем строки для каждого исполнителя
        for i, emp_name in enumerate(employee_names):
            emp_tasks = [s for s in schedule if s["employee"] == emp_name]
            
            for task in emp_tasks:
                start = datetime.strptime(task["start_date"], "%Y-%m-%d")
                end = datetime.strptime(task["end_date"], "%Y-%m-%d")
                duration = (end - start).days
                
                ax.barh(emp_name, duration, left=start, 
                       color=colors[i], edgecolor='black', 
                       height=0.5, alpha=0.7)
                
                # Подписываем задачи
                ax.text(start + timedelta(days=duration/2), i, 
                       task["task"][:20], ha='center', va='center', 
                       fontsize=9, color='black')
        
        # Настройка внешнего вида
        ax.set_xlabel('Дата')
        ax.set_ylabel('Исполнитель')
        ax.set_title('Оптимизированное расписание проекта')
        ax.grid(True, alpha=0.3)
        
        # Форматирование дат
        fig.autofmt_xdate()
        plt.tight_layout()
        plt.savefig(filename, dpi=300)
        plt.show()
        
        print(f"Диаграмма сохранена в {filename}")
    
    def calculate_metrics(self, schedule):
        """Расчет метрик эффективности"""
        df = pd.DataFrame(schedule)
        
        # Преобразуем даты
        df['start'] = pd.to_datetime(df['start_date'])
        df['end'] = pd.to_datetime(df['end_date'])
        
        metrics = {
            "total_duration": (df['end'].max() - df['start'].min()).days,
            "total_tasks": len(df),
            "tasks_per_employee": df.groupby('employee')['task'].count().to_dict(),
            "total_hours": df['hours'].sum(),
            "unmatched_skills": len(df[df['skills_match'] == '✗'])
        }
        
        return metrics