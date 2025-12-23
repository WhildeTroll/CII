from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import calendar


class ScheduleBuilderUI:
    def __init__(self, tasks=None, employees=None, calendar_config=None):
        self.tasks = tasks or []
        self.employees = employees or []
        self.calendar_config = calendar_config or {}
        self.schedule = []

    def build_schedule(self, assignment):
        """Построение детального расписания с учетом календаря"""
        if not assignment or not self.tasks or not self.employees:
            return []

        self.schedule = []

        # Преобразуем календарные настройки
        start_date_str = self.calendar_config.get("start_date", "2024-01-01")
        work_days = self.calendar_config.get("work_days_per_week", [0, 1, 2, 3, 4])
        holidays = self.calendar_config.get("holidays", [])

        # Преобразуем даты
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        holiday_dates = [datetime.strptime(h, "%Y-%m-%d") for h in holidays]

        # Инициализируем расписание для каждого исполнителя
        emp_schedules = {}
        for emp in self.employees:
            emp_schedules[emp["id"]] = {
                "current_date": start_date,
                "tasks": []
            }

        # Распределяем задачи
        for task_assignment in assignment:
            task_id = task_assignment["task_id"]
            emp_id = task_assignment["employee_id"]

            task = next((t for t in self.tasks if t["id"] == task_id), None)
            emp = next((e for e in self.employees if e["id"] == emp_id), None)

            if not task or not emp:
                continue

            # Находим дату начала для задачи
            start_date_emp = emp_schedules[emp_id]["current_date"]

            # Рассчитываем дату окончания с учетом рабочих дней и праздников
            hours_needed = task.get("hours", 0)
            daily_hours = emp.get("daily_hours", 8)
            days_needed = hours_needed / daily_hours

            end_date = self._calculate_end_date(
                start_date_emp, days_needed, work_days, holiday_dates
            )

            # Сохраняем задачу в расписании
            schedule_item = {
                "task_id": task_id,
                "task_name": task["name"],
                "task_priority": task.get("priority", "medium"),
                "employee_id": emp_id,
                "employee_name": emp["name"],
                "start_date": start_date_emp,
                "end_date": end_date,
                "duration_days": (end_date - start_date_emp).days,
                "hours": hours_needed,
                "cost": hours_needed * emp.get("cost_per_hour", 0),
                "skills_match": task_assignment.get("skill_match_percent", 0),
                "efficiency": task_assignment.get("efficiency_score", 0)
            }

            self.schedule.append(schedule_item)
            emp_schedules[emp_id]["tasks"].append(schedule_item)

            # Обновляем текущую дату для исполнителя (добавляем 1 день между задачами)
            emp_schedules[emp_id]["current_date"] = end_date + timedelta(days=1)

        return self.schedule

    def _calculate_end_date(self, start_date, days_needed, work_days, holidays):
        """Рассчитывает дату окончания с учетом рабочих дней и праздников"""
        current_date = start_date
        work_days_completed = 0

        while work_days_completed < days_needed:
            current_date += timedelta(days=1)

            # Проверяем, является ли день рабочим
            if current_date.weekday() in work_days and current_date not in holidays:
                work_days_completed += 1

        return current_date

    def create_gantt_chart(self):
        """Создание интерактивной диаграммы Ганта"""
        if not self.schedule:
            return None

        df = pd.DataFrame(self.schedule)

        # Преобразуем даты в строки для Plotly
        df['start_str'] = df['start_date'].dt.strftime('%Y-%m-%d')
        df['end_str'] = df['end_date'].dt.strftime('%Y-%m-%d')

        fig = px.timeline(
            df,
            x_start="start_date",
            x_end="end_date",
            y="employee_name",
            color="task_priority",
            hover_data={
                "task_name": True,
                "duration_days": True,
                "hours": True,
                "cost": ":.0f",
                "skills_match": ":.1f%",
                "efficiency": ":.1f"
            },
            color_discrete_map={
                "high": "red",
                "medium": "orange",
                "low": "green"
            },
            title="Оптимизированное расписание проекта"
        )

        fig.update_yaxes(categoryorder="total ascending")
        fig.update_layout(
            height=500,
            xaxis_title="Дата",
            yaxis_title="Исполнитель",
            legend_title="Приоритет",
            hovermode="closest"
        )

        return fig

    def create_resource_utilization_chart(self):
        """Диаграмма загрузки ресурсов"""
        if not self.schedule:
            return None

        df = pd.DataFrame(self.schedule)

        # Группируем по исполнителям
        utilization = df.groupby("employee_name").agg({
            "hours": "sum",
            "duration_days": "sum",
            "cost": "sum"
        }).reset_index()

        # Добавляем расчет загрузки (часы / (дни * 8 часов))
        utilization["utilization_percent"] = (utilization["hours"] /
                                              (utilization["duration_days"] * 8)) * 100

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Загрузка по часам", "Стоимость работ",
                            "Длительность задач", "Процент загрузки"),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )

        # График 1: Часы работы
        fig.add_trace(
            go.Bar(x=utilization["employee_name"], y=utilization["hours"],
                   name="Часы", marker_color="blue"),
            row=1, col=1
        )

        # График 2: Стоимость
        fig.add_trace(
            go.Bar(x=utilization["employee_name"], y=utilization["cost"],
                   name="Стоимость", marker_color="green"),
            row=1, col=2
        )

        # График 3: Длительность
        fig.add_trace(
            go.Bar(x=utilization["employee_name"], y=utilization["duration_days"],
                   name="Дней", marker_color="orange"),
            row=2, col=1
        )

        # График 4: Процент загрузки
        fig.add_trace(
            go.Bar(x=utilization["employee_name"], y=utilization["utilization_percent"],
                   name="Загрузка %", marker_color="red"),
            row=2, col=2
        )

        fig.update_layout(
            height=600,
            showlegend=False,
            title_text="Анализ загрузки ресурсов"
        )

        return fig

    def calculate_project_metrics(self):
        """Расчет метрик проекта"""
        if not self.schedule:
            return {}

        df = pd.DataFrame(self.schedule)

        if df.empty:
            return {}

        metrics = {
            "total_duration": (df["end_date"].max() - df["start_date"].min()).days,
            "total_hours": df["hours"].sum(),
            "total_cost": df["cost"].sum(),
            "avg_efficiency": df["efficiency"].mean(),
            "avg_skill_match": df["skills_match"].mean(),
            "task_count": len(df),
            "employee_count": df["employee_name"].nunique(),
            "high_priority_tasks": len(df[df["task_priority"] == "high"]),
            "on_time_completion": self._calculate_on_time_completion(df)
        }

        return metrics

    def _calculate_on_time_completion(self, df):
        """Расчет вероятности выполнения в срок"""
        # Упрощенный расчет - можно доработать
        avg_efficiency = df["efficiency"].mean()
        avg_skill_match = df["skills_match"].mean()

        # Комбинированный показатель
        completion_probability = (avg_efficiency * 0.6 + avg_skill_match * 0.4) / 100

        return min(completion_probability, 1.0)

    def export_schedule(self, format="csv"):
        """Экспорт расписания в различных форматах"""
        if not self.schedule:
            return None

        df = pd.DataFrame(self.schedule)

        if format.lower() == "csv":
            return df.to_csv(index=False, encoding='utf-8-sig')
        elif format.lower() == "excel":
            return df.to_excel(index=False)
        elif format.lower() == "json":
            return df.to_json(orient="records", indent=2, force_ascii=False)

        return None