import random
import json
import numpy as np
from deap import base, creator, tools, algorithms
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class ResourceOptimizer:
    def __init__(self, tasks, employees, calendar):
        self.tasks = tasks
        self.employees = employees
        self.calendar = calendar
        
        # Параметры генетического алгоритма
        self.POP_SIZE = 100
        self.GENERATIONS = 50
        self.CX_PROB = 0.7
        self.MUT_PROB = 0.2
        
        # Создаем структуры для DEAP
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
        
        self.toolbox = base.Toolbox()
        self._setup_genetic_algorithm()
    
    def _setup_genetic_algorithm(self):
        """Настройка генетического алгоритма"""
        # Ген - индекс исполнителя для задачи
        self.toolbox.register("attr_employee", 
                            lambda: random.randint(0, len(self.employees)-1))
        
        # Создание индивида (решения)
        self.toolbox.register("individual", tools.initRepeat, 
                            creator.Individual, 
                            self.toolbox.attr_employee, 
                            len(self.tasks))
        
        # Создание популяции
        self.toolbox.register("population", tools.initRepeat, 
                            list, self.toolbox.individual)
        
        # Регистрация операторов
        self.toolbox.register("evaluate", self._fitness)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutUniformInt, 
                            low=0, up=len(self.employees)-1, indpb=0.1)
        self.toolbox.register("select", tools.selTournament, tournsize=3)
    
    def _fitness(self, individual):
        """Целевая функция (fitness)"""
        total_penalty = 0
        total_cost = 0
        
        # Проверяем каждое назначение
        for task_idx, emp_idx in enumerate(individual):
            task = self.tasks[task_idx]
            emp = self.employees[emp_idx]
            
            # Штраф за несоответствие навыков
            skill_match = all(skill in emp["skills"] and emp["skills"][skill] >= 5 
                            for skill in task["skills"])
            if not skill_match:
                total_penalty += 1000
            
            # Стоимость выполнения задачи
            task_cost = task["hours"] * emp["cost_per_hour"]
            total_cost += task_cost
            
            # Штраф за приоритет (чем выше приоритет, тем раньше должна быть задача)
            if task["priority"] == "high":
                total_penalty += emp_idx * 10  # Назначаем senior'ам
        
        # Инвертируем штрафы (чем меньше штрафов - тем лучше fitness)
        fitness_value = 1.0 / (1.0 + total_penalty + total_cost / 10000)
        return (fitness_value,)
    
    def optimize(self):
        """Запуск оптимизации"""
        pop = self.toolbox.population(n=self.POP_SIZE)
        hof = tools.HallOfFame(1)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("min", np.min)
        stats.register("max", np.max)
        
        # Запуск генетического алгоритма
        pop, logbook = algorithms.eaSimple(pop, self.toolbox, 
                                          cxpb=self.CX_PROB, 
                                          mutpb=self.MUT_PROB, 
                                          ngen=self.GENERATIONS, 
                                          stats=stats, 
                                          halloffame=hof, 
                                          verbose=True)
        
        best_solution = hof[0]
        return best_solution, logbook
    
    def get_assignment(self, solution):
        """Получение читаемого назначения задач"""
        assignment = []
        for task_idx, emp_idx in enumerate(solution):
            task = self.tasks[task_idx]
            emp = self.employees[emp_idx]
            
            # Проверка соответствия навыков
            skill_match = all(skill in emp["skills"] 
                            for skill in task["skills"])
            match_status = "✓" if skill_match else "✗"
            
            assignment.append({
                "task_id": task["id"],
                "task_name": task["name"],
                "employee_id": emp["id"],
                "employee_name": emp["name"],
                "skills_match": match_status,
                "estimated_hours": task["hours"]
            })
        
        return assignment