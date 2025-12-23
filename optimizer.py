import random
import json
import numpy as np
from deap import base, creator, tools, algorithms
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd


class ResourceOptimizerUI:
    def __init__(self, tasks=None, employees=None, calendar=None):
        self.tasks = tasks or []
        self.employees = employees or []
        self.calendar = calendar or {}
        self.optimization_history = []
        self.best_solution = None
        self.logbook = None

    def setup_ga_parameters(self, pop_size=100, generations=50,
                            cx_prob=0.7, mut_prob=0.2, tournament_size=3):
        """Настройка параметров генетического алгоритма"""
        self.POP_SIZE = pop_size
        self.GENERATIONS = generations
        self.CX_PROB = cx_prob
        self.MUT_PROB = mut_prob
        self.TOURNAMENT_SIZE = tournament_size

        # Создаем структуры для DEAP
        if hasattr(creator, 'FitnessMax'):
            del creator.FitnessMax
        if hasattr(creator, 'Individual'):
            del creator.Individual

        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        self.toolbox = base.Toolbox()
        self._setup_genetic_algorithm()

    def _setup_genetic_algorithm(self):
        """Настройка генетического алгоритма"""
        if not self.employees:
            raise ValueError("Список исполнителей пуст")

        self.toolbox.register("attr_employee",
                              lambda: random.randint(0, len(self.employees) - 1))

        self.toolbox.register("individual", tools.initRepeat,
                              creator.Individual,
                              self.toolbox.attr_employee,
                              len(self.tasks))

        self.toolbox.register("population", tools.initRepeat,
                              list, self.toolbox.individual)

        self.toolbox.register("evaluate", self._fitness)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutUniformInt,
                              low=0, up=len(self.employees) - 1, indpb=0.1)
        self.toolbox.register("select", tools.selTournament,
                              tournsize=self.TOURNAMENT_SIZE)

    def _fitness(self, individual):
        """Целевая функция с расширенной логикой"""
        if not self.tasks or not self.employees:
            return (0.0,)

        total_penalty = 0
        total_cost = 0
        skill_mismatches = 0
        deadline_violations = 0

        # Расчет приоритетных коэффициентов
        priority_weights = {"high": 3, "medium": 2, "low": 1}

        for task_idx, emp_idx in enumerate(individual):
            if emp_idx >= len(self.employees):
                continue

            task = self.tasks[task_idx]
            emp = self.employees[emp_idx]

            # Проверка соответствия навыков
            skill_match_score = 0
            for skill in task.get("skills", []):
                if skill in emp.get("skills", {}):
                    skill_match_score += emp["skills"][skill] / 10.0
                else:
                    skill_mismatches += 1
                    total_penalty += 500

            if skill_match_score < len(task.get("skills", [])) * 0.5:
                total_penalty += 300

            # Стоимость выполнения
            hours = task.get("hours", 0)
            cost_per_hour = emp.get("cost_per_hour", 0)
            total_cost += hours * cost_per_hour

            # Штраф за назначение senior на простые задачи
            if hours < 20 and emp.get("cost_per_hour", 0) > 1500:
                total_penalty += 100

            # Поощрение за соответствие приоритету
            if task.get("priority") == "high" and emp.get("cost_per_hour", 0) > 1400:
                total_penalty -= 50  # Бонус за назначение senior на важные задачи

        # Нормализация fitness
        base_fitness = 10000
        fitness_value = base_fitness / (1.0 + total_penalty + total_cost / 1000 + skill_mismatches * 100)

        # Записываем метрики для истории
        metrics = {
            "fitness": fitness_value,
            "penalty": total_penalty,
            "cost": total_cost,
            "skill_mismatches": skill_mismatches
        }

        self.optimization_history.append(metrics)
        return (fitness_value,)

    def optimize(self, progress_callback=None):
        """Запуск оптимизации с callback для прогресса"""
        if not self.tasks or not self.employees:
            return None, None

        pop = self.toolbox.population(n=self.POP_SIZE)
        hof = tools.HallOfFame(1)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("min", np.min)
        stats.register("max", np.max)

        # Сбор статистики по поколениям
        logbook = tools.Logbook()
        logbook.header = ["gen", "nevals", "avg", "min", "max"]

        for gen in range(self.GENERATIONS):
            # Эволюция поколения
            offspring = algorithms.varAnd(pop, self.toolbox,
                                          cxpb=self.CX_PROB,
                                          mutpb=self.MUT_PROB)

            fits = self.toolbox.map(self.toolbox.evaluate, offspring)
            for fit, ind in zip(fits, offspring):
                ind.fitness.values = fit

            pop = self.toolbox.select(offspring, k=len(pop))
            hof.update(pop)

            # Запись статистики
            record = stats.compile(pop)
            logbook.record(gen=gen, nevals=len(offspring), **record)

            # Callback для прогресса
            if progress_callback:
                progress_callback(gen + 1, self.GENERATIONS,
                                  record["max"], record["avg"])

        self.best_solution = hof[0]
        self.logbook = logbook
        return self.best_solution, logbook

    def get_assignment_analysis(self, solution):
        """Детальный анализ назначений"""
        if solution is None:
            return []

        analysis = []
        for task_idx, emp_idx in enumerate(solution):
            if task_idx >= len(self.tasks) or emp_idx >= len(self.employees):
                continue

            task = self.tasks[task_idx]
            emp = self.employees[emp_idx]

            # Расчет соответствия навыков
            matched_skills = []
            missing_skills = []
            skill_score = 0

            for skill in task.get("skills", []):
                if skill in emp.get("skills", {}):
                    matched_skills.append(skill)
                    skill_score += emp["skills"][skill]
                else:
                    missing_skills.append(skill)

            skill_match_percent = (len(matched_skills) / len(task.get("skills", []))) * 100 if task.get(
                "skills") else 100

            analysis.append({
                "task_id": task.get("id", task_idx + 1),
                "task_name": task.get("name", f"Задача {task_idx + 1}"),
                "task_hours": task.get("hours", 0),
                "task_priority": task.get("priority", "medium"),
                "employee_id": emp.get("id", emp_idx + 1),
                "employee_name": emp.get("name", f"Исполнитель {emp_idx + 1}"),
                "employee_cost": emp.get("cost_per_hour", 0),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "skill_match_percent": skill_match_percent,
                "estimated_cost": task.get("hours", 0) * emp.get("cost_per_hour", 0),
                "efficiency_score": self._calculate_efficiency_score(task, emp)
            })

        return analysis

    def _calculate_efficiency_score(self, task, emp):
        """Расчет эффективности назначения"""
        if not task or not emp:
            return 0

        # Веса факторов
        weights = {
            "skill_match": 0.4,
            "cost_efficiency": 0.3,
            "experience": 0.2,
            "workload": 0.1
        }

        score = 0

        # Соответствие навыков
        skill_match = 0
        for skill in task.get("skills", []):
            if skill in emp.get("skills", {}):
                skill_match += emp["skills"][skill] / 10.0
        skill_match /= len(task.get("skills", [])) if task.get("skills") else 1
        score += skill_match * weights["skill_match"]

        # Эффективность по стоимости
        avg_cost = sum(e.get("cost_per_hour", 0) for e in self.employees) / len(self.employees) if self.employees else 0
        if avg_cost > 0:
            cost_ratio = avg_cost / emp.get("cost_per_hour", avg_cost)
            score += min(cost_ratio, 1.5) * weights["cost_efficiency"]

        # Опыт (стоимость как proxy для опыта)
        experience = emp.get("cost_per_hour", 0) / 2000  # Нормализация
        score += min(experience, 1.0) * weights["experience"]

        return round(score * 100, 2)

    def get_optimization_plot(self):
        """Создание графика сходимости алгоритма"""
        if not self.logbook:
            return None

        gens = self.logbook.select("gen")
        avg_fits = self.logbook.select("avg")
        max_fits = self.logbook.select("max")
        min_fits = self.logbook.select("min")

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=gens, y=max_fits,
            mode='lines+markers',
            name='Лучшее решение',
            line=dict(color='green', width=3)
        ))

        fig.add_trace(go.Scatter(
            x=gens, y=avg_fits,
            mode='lines',
            name='Среднее значение',
            line=dict(color='blue', width=2, dash='dash')
        ))

        fig.add_trace(go.Scatter(
            x=gens, y=min_fits,
            mode='lines',
            name='Худшее решение',
            line=dict(color='red', width=1)
        ))

        fig.update_layout(
            title='Сходимость генетического алгоритма',
            xaxis_title='Поколение',
            yaxis_title='Значение fitness',
            hovermode='x unified',
            template='plotly_white',
            height=400
        )

        return fig

    def get_skill_distribution_plot(self, analysis):
        """Визуализация распределения навыков"""
        if not analysis:
            return None

        skill_data = []
        for item in analysis:
            for skill in item["matched_skills"]:
                skill_data.append({
                    "skill": skill,
                    "employee": item["employee_name"],
                    "task": item["task_name"]
                })

        if not skill_data:
            return None

        df = pd.DataFrame(skill_data)
        skill_counts = df["skill"].value_counts().reset_index()
        skill_counts.columns = ["skill", "count"]

        fig = px.bar(skill_counts,
                     x="skill",
                     y="count",
                     title="Распределение использования навыков",
                     color="count",
                     color_continuous_scale="Viridis")

        fig.update_layout(height=400)
        return fig