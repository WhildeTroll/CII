import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
import io
import time

from optimizer import ResourceOptimizerUI
from scheduler import ScheduleBuilderUI

# Настройка страницы
st.set_page_config(
    page_title="Оптимизация распределения ресурсов",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Стили CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3B82F6;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 5px solid #3B82F6;
    }
    .success-message {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .warning-message {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .stProgress > div > div > div > div {
        background-color: #3B82F6;
    }
</style>
""", unsafe_allow_html=True)


class ResourceOptimizationApp:
    def __init__(self):
        self.optimizer = None
        self.scheduler = None
        self.initialize_session_state()

    def initialize_session_state(self):
        """Инициализация состояния сессии"""
        if 'tasks' not in st.session_state:
            st.session_state.tasks = []
        if 'employees' not in st.session_state:
            st.session_state.employees = []
        if 'calendar' not in st.session_state:
            st.session_state.calendar = {}
        if 'optimization_results' not in st.session_state:
            st.session_state.optimization_results = None
        if 'schedule' not in st.session_state:
            st.session_state.schedule = None
        if 'optimization_history' not in st.session_state:
            st.session_state.optimization_history = []

    def run(self):
        """Запуск основного приложения"""
        # Заголовок
        st.markdown('<h1 class="main-header">🚀 Оптимизация распределения ресурсов в IT-проектах</h1>',
                    unsafe_allow_html=True)

        # Сайдбар с навигацией
        with st.sidebar:
            st.image("https://img.icons8.com/color/96/000000/management.png",
                     width=100)
            st.markdown("### Навигация")

            page = st.radio(
                "Выберите раздел:",
                ["📁 Загрузка данных", "⚙️ Настройка оптимизации",
                 "🧠 Запуск оптимизации", "📊 Результаты",
                 "📋 Расписание", "📈 Аналитика"]
            )

            st.markdown("---")
            st.markdown("### Быстрые действия")

            if st.button("🔄 Сбросить все данные", use_container_width=True):
                self.reset_data()
                st.success("Данные сброшены!")

            if st.button("💾 Сохранить проект", use_container_width=True):
                self.save_project()

            if st.button("📥 Загрузить проект", use_container_width=True):
                self.load_project()

            st.markdown("---")
            st.markdown("**Статус данных:**")
            st.info(f"Задач: {len(st.session_state.tasks)}")
            st.info(f"Исполнителей: {len(st.session_state.employees)}")

        # Основной контент в зависимости от выбранной страницы
        if page == "📁 Загрузка данных":
            self.data_loading_page()
        elif page == "⚙️ Настройка оптимизации":
            self.optimization_settings_page()
        elif page == "🧠 Запуск оптимизации":
            self.optimization_page()
        elif page == "📊 Результаты":
            self.results_page()
        elif page == "📋 Расписание":
            self.schedule_page()
        elif page == "📈 Аналитика":
            self.analytics_page()

    def data_loading_page(self):
        """Страница загрузки данных"""
        st.markdown('<h2 class="sub-header">📁 Загрузка данных проекта</h2>',
                    unsafe_allow_html=True)

        # Вкладки для разных способов загрузки
        tab1, tab2, tab3 = st.tabs(["📝 Ручной ввод", "📤 Загрузка файлов", "🎯 Примеры данных"])

        with tab1:
            self.manual_data_input()

        with tab2:
            self.file_upload_section()

        with tab3:
            self.example_data_section()

        # Предпросмотр загруженных данных
        if st.session_state.tasks or st.session_state.employees:
            st.markdown("---")
            self.show_data_preview()

    def manual_data_input(self):
        """Ручной ввод данных"""
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📋 Задачи проекта")

            with st.form("task_form"):
                task_name = st.text_input("Название задачи")
                task_hours = st.number_input("Часы работы", min_value=1, max_value=500, value=40)

                col1_1, col1_2 = st.columns(2)
                with col1_1:
                    task_priority = st.selectbox(
                        "Приоритет",
                        ["high", "medium", "low"],
                        format_func=lambda x: {"high": "Высокий", "medium": "Средний", "low": "Низкий"}[x]
                    )
                with col1_2:
                    task_deadline = st.date_input("Дедлайн")

                task_skills = st.multiselect(
                    "Требуемые навыки",
                    ["frontend", "backend", "ui/ux", "архитектура",
                     "sql", "testing", "devops", "api", "mobile"],
                    default=["backend"]
                )

                if st.form_submit_button("➕ Добавить задачу"):
                    new_task = {
                        "id": len(st.session_state.tasks) + 1,
                        "name": task_name,
                        "hours": task_hours,
                        "priority": task_priority,
                        "deadline": task_deadline.strftime("%Y-%m-%d"),
                        "skills": task_skills
                    }
                    st.session_state.tasks.append(new_task)
                    st.success(f"Задача '{task_name}' добавлена!")

        with col2:
            st.markdown("#### 👥 Исполнители")

            with st.form("employee_form"):
                emp_name = st.text_input("ФИО исполнителя")
                emp_daily_hours = st.number_input("Рабочих часов в день",
                                                  min_value=1, max_value=12, value=8)
                emp_cost = st.number_input("Стоимость часа работы (руб.)",
                                           min_value=100, max_value=5000, value=1500)

                st.markdown("**Навыки и уровень владения (1-10):**")

                skills_col1, skills_col2, skills_col3 = st.columns(3)
                all_skills = ["frontend", "backend", "ui/ux", "архитектура",
                              "sql", "testing", "devops", "api", "mobile"]

                emp_skills = {}

                for i, skill in enumerate(all_skills):
                    col = skills_col1 if i % 3 == 0 else skills_col2 if i % 3 == 1 else skills_col3
                    with col:
                        level = st.slider(skill, 0, 10, 5 if skill in ["backend", "frontend"] else 3)
                        if level > 0:
                            emp_skills[skill] = level

                if st.form_submit_button("➕ Добавить исполнителя"):
                    new_employee = {
                        "id": len(st.session_state.employees) + 1,
                        "name": emp_name,
                        "daily_hours": emp_daily_hours,
                        "cost_per_hour": emp_cost,
                        "skills": emp_skills
                    }
                    st.session_state.employees.append(new_employee)
                    st.success(f"Исполнитель '{emp_name}' добавлен!")

    def file_upload_section(self):
        """Загрузка данных из файлов"""
        st.markdown("#### 📤 Загрузка из JSON файлов")

        col1, col2, col3 = st.columns(3)

        with col1:
            tasks_file = st.file_uploader("Задачи (tasks.json)",
                                          type=["json"],
                                          help="Загрузите JSON файл с задачами")
            if tasks_file:
                try:
                    tasks_data = json.load(tasks_file)
                    st.session_state.tasks = tasks_data
                    st.success(f"Загружено {len(tasks_data)} задач")
                except Exception as e:
                    st.error(f"Ошибка загрузки файла: {e}")

        with col2:
            employees_file = st.file_uploader("Исполнители (employees.json)",
                                              type=["json"],
                                              help="Загрузите JSON файл с исполнителями")
            if employees_file:
                try:
                    employees_data = json.load(employees_file)
                    st.session_state.employees = employees_data
                    st.success(f"Загружено {len(employees_data)} исполнителей")
                except Exception as e:
                    st.error(f"Ошибка загрузки файла: {e}")

        with col3:
            calendar_file = st.file_uploader("Календарь (calendar.json)",
                                             type=["json"],
                                             help="Загрузите JSON файл с календарем")
            if calendar_file:
                try:
                    calendar_data = json.load(calendar_file)
                    st.session_state.calendar = calendar_data
                    st.success("Календарь загружен")
                except Exception as e:
                    st.error(f"Ошибка загрузки файла: {e}")

        # Шаблоны для скачивания
        st.markdown("#### 📄 Шаблоны файлов")

        template_col1, template_col2, template_col3 = st.columns(3)

        with template_col1:
            st.download_button(
                label="📥 tasks_template.json",
                data=json.dumps([
                    {
                        "id": 1,
                        "name": "Пример задачи",
                        "hours": 40,
                        "priority": "high",
                        "deadline": "2024-12-31",
                        "skills": ["backend", "api"]
                    }
                ], indent=2),
                file_name="tasks_template.json",
                mime="application/json"
            )

        with template_col2:
            st.download_button(
                label="📥 employees_template.json",
                data=json.dumps([
                    {
                        "id": 1,
                        "name": "Пример исполнителя",
                        "daily_hours": 8,
                        "cost_per_hour": 1500,
                        "skills": {"backend": 8, "api": 7}
                    }
                ], indent=2),
                file_name="employees_template.json",
                mime="application/json"
            )

        with template_col3:
            st.download_button(
                label="📥 calendar_template.json",
                data=json.dumps({
                    "start_date": "2024-01-01",
                    "work_days_per_week": [0, 1, 2, 3, 4],
                    "holidays": ["2024-01-01", "2024-01-07"]
                }, indent=2),
                file_name="calendar_template.json",
                mime="application/json"
            )

    def example_data_section(self):
        """Загрузка примеров данных"""
        st.markdown("#### 🎯 Загрузить пример данных для тестирования")

        if st.button("📊 Загрузить демо-проект", use_container_width=True):
            # Пример данных
            example_tasks = [
                {"id": 1, "name": "Разработка архитектуры", "hours": 40,
                 "priority": "high", "deadline": "2024-06-15", "skills": ["архитектура", "sql"]},
                {"id": 2, "name": "Frontend разработка", "hours": 80,
                 "priority": "high", "deadline": "2024-07-10", "skills": ["frontend", "ui/ux"]},
                {"id": 3, "name": "Backend API", "hours": 120,
                 "priority": "high", "deadline": "2024-08-01", "skills": ["backend", "api"]},
                {"id": 4, "name": "Тестирование", "hours": 60,
                 "priority": "medium", "deadline": "2024-08-15", "skills": ["testing"]},
                {"id": 5, "name": "Деплой", "hours": 20,
                 "priority": "medium", "deadline": "2024-08-20", "skills": ["devops"]}
            ]

            example_employees = [
                {"id": 1, "name": "Иван Петров", "daily_hours": 8, "cost_per_hour": 1800,
                 "skills": {"архитектура": 9, "sql": 8, "backend": 7}},
                {"id": 2, "name": "Мария Сидорова", "daily_hours": 8, "cost_per_hour": 1600,
                 "skills": {"frontend": 9, "ui/ux": 8, "testing": 6}},
                {"id": 3, "name": "Алексей Иванов", "daily_hours": 8, "cost_per_hour": 1700,
                 "skills": {"backend": 9, "api": 9, "devops": 7}},
                {"id": 4, "name": "Елена Кузнецова", "daily_hours": 6, "cost_per_hour": 1400,
                 "skills": {"testing": 8, "frontend": 6}},
                {"id": 5, "name": "Дмитрий Смирнов", "daily_hours": 8, "cost_per_hour": 1750,
                 "skills": {"devops": 9, "архитектура": 6}}
            ]

            example_calendar = {
                "start_date": "2024-06-01",
                "work_days_per_week": [0, 1, 2, 3, 4],
                "holidays": ["2024-06-12", "2024-07-01"]
            }

            st.session_state.tasks = example_tasks
            st.session_state.employees = example_employees
            st.session_state.calendar = example_calendar

            st.success("Демо-проект загружен!")
            st.balloons()

    def show_data_preview(self):
        """Отображение предпросмотра загруженных данных"""
        st.markdown("#### 👁️ Предпросмотр данных")

        if st.session_state.tasks:
            with st.expander("📋 Задачи", expanded=True):
                tasks_df = pd.DataFrame(st.session_state.tasks)
                st.dataframe(tasks_df, use_container_width=True)

        if st.session_state.employees:
            with st.expander("👥 Исполнители", expanded=False):
                employees_df = pd.DataFrame(st.session_state.employees)
                st.dataframe(employees_df, use_container_width=True)

        if st.session_state.calendar:
            with st.expander("📅 Календарь", expanded=False):
                st.json(st.session_state.calendar)

    def optimization_settings_page(self):
        """Страница настройки параметров оптимизации"""
        st.markdown('<h2 class="sub-header">⚙️ Настройка параметров оптимизации</h2>',
                    unsafe_allow_html=True)

        if not st.session_state.tasks or not st.session_state.employees:
            st.warning("⚠️ Сначала загрузите данные в разделе 'Загрузка данных'")
            return

        # Параметры генетического алгоритма
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 🧬 Параметры ГА")
            pop_size = st.slider("Размер популяции", 50, 500, 100, 50)
            generations = st.slider("Количество поколений", 10, 200, 50, 10)

        with col2:
            st.markdown("#### ⚙️ Вероятности")
            cx_prob = st.slider("Вероятность скрещивания", 0.1, 1.0, 0.7, 0.1)
            mut_prob = st.slider("Вероятность мутации", 0.01, 0.5, 0.2, 0.01)
            tournament_size = st.slider("Размер турнира", 2, 10, 3)

        with col3:
            st.markdown("#### ⚖️ Веса критериев")
            st.markdown("**Влияние на целевую функцию:**")
            weight_time = st.slider("Время", 0.0, 1.0, 0.4, 0.1)
            weight_cost = st.slider("Стоимость", 0.0, 1.0, 0.3, 0.1)
            weight_skills = st.slider("Навыки", 0.0, 1.0, 0.3, 0.1)

        # Настройки календаря
        st.markdown("---")
        st.markdown("#### 📅 Настройки календаря")

        cal_col1, cal_col2, cal_col3 = st.columns(3)

        with cal_col1:
            start_date = st.date_input(
                "Дата начала проекта",
                value=datetime.strptime(
                    st.session_state.calendar.get("start_date", "2024-01-01"),
                    "%Y-%m-%d"
                )
            )

        with cal_col2:
            work_days = st.multiselect(
                "Рабочие дни недели",
                ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
                default=["Пн", "Вт", "Ср", "Чт", "Пт"],
                format_func=lambda x: x
            )

            # Преобразование в числовой формат (0-Пн, 6-Вс)
            day_mapping = {"Пн": 0, "Вт": 1, "Ср": 2, "Чт": 3, "Пт": 4, "Сб": 5, "Вс": 6}
            work_days_numeric = [day_mapping[day] for day in work_days]

        with cal_col3:
            st.markdown("**Праздничные дни**")
            holidays_input = st.text_area(
                "Введите даты через запятую (YYYY-MM-DD)",
                value=", ".join(st.session_state.calendar.get("holidays", [])),
                height=100
            )
            holidays = [h.strip() for h in holidays_input.split(",") if h.strip()]

        # Сохранение настроек
        if st.button("💾 Сохранить настройки", use_container_width=True):
            st.session_state.calendar = {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "work_days_per_week": work_days_numeric,
                "holidays": holidays
            }

            st.session_state.ga_settings = {
                "pop_size": pop_size,
                "generations": generations,
                "cx_prob": cx_prob,
                "mut_prob": mut_prob,
                "tournament_size": tournament_size,
                "weights": {
                    "time": weight_time,
                    "cost": weight_cost,
                    "skills": weight_skills
                }
            }

            st.success("Настройки сохранены!")

            # Создание объектов оптимизации
            self.optimizer = ResourceOptimizerUI(
                st.session_state.tasks,
                st.session_state.employees,
                st.session_state.calendar
            )

            self.optimizer.setup_ga_parameters(
                pop_size=pop_size,
                generations=generations,
                cx_prob=cx_prob,
                mut_prob=mut_prob,
                tournament_size=tournament_size
            )

    def optimization_page(self):
        """Страница запуска оптимизации"""
        st.markdown('<h2 class="sub-header">🧠 Запуск оптимизации распределения</h2>',
                    unsafe_allow_html=True)

        if not hasattr(st.session_state, 'ga_settings'):
            st.warning("⚠️ Сначала настройте параметры оптимизации")
            return

        if not self.optimizer:
            self.optimizer = ResourceOptimizerUI(
                st.session_state.tasks,
                st.session_state.employees,
                st.session_state.calendar
            )

            settings = st.session_state.ga_settings
            self.optimizer.setup_ga_parameters(
                pop_size=settings["pop_size"],
                generations=settings["generations"],
                cx_prob=settings["cx_prob"],
                mut_prob=settings["mut_prob"],
                tournament_size=settings["tournament_size"]
            )

        # Информация о задаче
        st.markdown("#### 📊 Статистика задачи")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Задач", len(st.session_state.tasks))

        with col2:
            st.metric("Исполнителей", len(st.session_state.employees))

        with col3:
            total_hours = sum(task.get("hours", 0) for task in st.session_state.tasks)
            st.metric("Всего часов", total_hours)

        with col4:
            avg_cost = sum(emp.get("cost_per_hour", 0) for emp in st.session_state.employees) / len(
                st.session_state.employees)
            st.metric("Средняя стоимость часа", f"{avg_cost:.0f} руб.")

        # Запуск оптимизации
        st.markdown("---")
        st.markdown("#### 🚀 Запуск оптимизации")

        if st.button("▶️ Начать оптимизацию", use_container_width=True, type="primary"):
            with st.spinner("Запуск генетического алгоритма..."):
                # Прогресс бар
                progress_bar = st.progress(0)
                status_text = st.empty()

                def update_progress(gen, total, best, avg):
                    progress = int((gen / total) * 100)
                    progress_bar.progress(progress)
                    status_text.text(f"Поколение {gen}/{total} | Лучший fitness: {best:.6f} | Средний: {avg:.6f}")

                # Запуск оптимизации
                start_time = time.time()
                best_solution, logbook = self.optimizer.optimize(
                    progress_callback=update_progress
                )
                end_time = time.time()

                # Анализ результатов
                analysis = self.optimizer.get_assignment_analysis(best_solution)

                # Построение расписания
                self.scheduler = ScheduleBuilderUI(
                    st.session_state.tasks,
                    st.session_state.employees,
                    st.session_state.calendar
                )
                schedule = self.scheduler.build_schedule(analysis)

                # Сохранение результатов
                st.session_state.optimization_results = {
                    "solution": best_solution,
                    "analysis": analysis,
                    "logbook": logbook,
                    "execution_time": end_time - start_time
                }
                st.session_state.schedule = schedule

                # Добавление в историю
                history_entry = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "tasks_count": len(st.session_state.tasks),
                    "employees_count": len(st.session_state.employees),
                    "execution_time": end_time - start_time,
                    "best_fitness": logbook.select("max")[-1] if logbook else 0
                }
                st.session_state.optimization_history.append(history_entry)

                progress_bar.progress(100)
                status_text.text("✅ Оптимизация завершена!")
                st.balloons()

        # Отображение истории оптимизаций
        if st.session_state.optimization_history:
            st.markdown("---")
            st.markdown("#### 📜 История оптимизаций")

            history_df = pd.DataFrame(st.session_state.optimization_history)
            st.dataframe(history_df, use_container_width=True)

    def results_page(self):
        """Страница результатов оптимизации"""
        st.markdown('<h2 class="sub-header">📊 Результаты оптимизации</h2>',
                    unsafe_allow_html=True)

        if not st.session_state.optimization_results:
            st.warning("⚠️ Сначала выполните оптимизацию")
            return

        results = st.session_state.optimization_results
        analysis = results["analysis"]

        if not analysis:
            st.error("Нет данных для отображения")
            return

        # Сводные метрики
        st.markdown("#### 📈 Сводные метрики")

        metric_cols = st.columns(4)

        total_tasks = len(analysis)
        tasks_with_skills = len([a for a in analysis if a["skill_match_percent"] == 100])
        total_cost = sum(a["estimated_cost"] for a in analysis)
        avg_efficiency = sum(a["efficiency_score"] for a in analysis) / total_tasks

        with metric_cols[0]:
            st.metric("Всего назначений", total_tasks)

        with metric_cols[1]:
            st.metric("Задачи с полным соответствием",
                      f"{tasks_with_skills}/{total_tasks}")

        with metric_cols[2]:
            st.metric("Общая стоимость", f"{total_cost:,.0f} руб.")

        with metric_cols[3]:
            st.metric("Средняя эффективность", f"{avg_efficiency:.1f}%")

        # Детализация назначений
        st.markdown("---")
        st.markdown("#### 📋 Детализация назначений")

        analysis_df = pd.DataFrame(analysis)

        # Фильтры
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_employee = st.selectbox(
                "Фильтр по исполнителю",
                ["Все"] + list(analysis_df["employee_name"].unique())
            )

        with col2:
            min_efficiency = st.slider("Минимальная эффективность", 0, 100, 0)

        with col3:
            show_only_matched = st.checkbox("Только полное соответствие навыков", value=False)

        # Применение фильтров
        filtered_df = analysis_df.copy()

        if selected_employee != "Все":
            filtered_df = filtered_df[filtered_df["employee_name"] == selected_employee]

        filtered_df = filtered_df[filtered_df["efficiency_score"] >= min_efficiency]

        if show_only_matched:
            filtered_df = filtered_df[filtered_df["skill_match_percent"] == 100]

        # Отображение таблицы
        display_cols = ["task_name", "employee_name", "task_priority",
                        "skill_match_percent", "efficiency_score", "estimated_cost"]

        st.dataframe(
            filtered_df[display_cols].rename(columns={
                "task_name": "Задача",
                "employee_name": "Исполнитель",
                "task_priority": "Приоритет",
                "skill_match_percent": "Соответствие навыков",
                "efficiency_score": "Эффективность",
                "estimated_cost": "Стоимость"
            }),
            use_container_width=True,
            column_config={
                "Соответствие навыков": st.column_config.ProgressColumn(
                    "Соответствие навыков",
                    help="Процент соответствия требуемых навыков",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                ),
                "Эффективность": st.column_config.ProgressColumn(
                    "Эффективность",
                    help="Общая эффективность назначения",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100
                )
            }
        )

        # Графики
        st.markdown("---")
        st.markdown("#### 📊 Визуализация результатов")

        tab1, tab2, tab3 = st.tabs(["Сходимость алгоритма", "Распределение навыков", "Анализ эффективности"])

        with tab1:
            if hasattr(self.optimizer, 'get_optimization_plot'):
                fig = self.optimizer.get_optimization_plot()
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

        with tab2:
            if hasattr(self.optimizer, 'get_skill_distribution_plot'):
                fig = self.optimizer.get_skill_distribution_plot(analysis)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

        with tab3:
            # Распределение эффективности
            fig = px.histogram(
                analysis_df,
                x="efficiency_score",
                nbins=20,
                title="Распределение эффективности назначений",
                labels={"efficiency_score": "Эффективность (%)"}
            )
            st.plotly_chart(fig, use_container_width=True)

        # Экспорт результатов
        st.markdown("---")
        st.markdown("#### 📤 Экспорт результатов")

        export_col1, export_col2, export_col3 = st.columns(3)

        with export_col1:
            csv_data = analysis_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Скачать как CSV",
                data=csv_data,
                file_name="optimization_results.csv",
                mime="text/csv"
            )

        with export_col2:
            json_data = analysis_df.to_json(orient="records", indent=2, force_ascii=False)
            st.download_button(
                label="📥 Скачать как JSON",
                data=json_data,
                file_name="optimization_results.json",
                mime="application/json"
            )

        with export_col3:
            excel_buffer = io.BytesIO()
            analysis_df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)

            st.download_button(
                label="📥 Скачать как Excel",
                data=excel_buffer,
                file_name="optimization_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    def schedule_page(self):
        """Страница с расписанием"""
        st.markdown('<h2 class="sub-header">📋 Расписание проекта</h2>',
                    unsafe_allow_html=True)

        if not st.session_state.schedule:
            st.warning("⚠️ Сначала выполните оптимизацию")
            return

        schedule = st.session_state.schedule

        if not self.scheduler:
            self.scheduler = ScheduleBuilderUI(
                st.session_state.tasks,
                st.session_state.employees,
                st.session_state.calendar
            )
            self.scheduler.schedule = schedule

        # Диаграмма Ганта
        st.markdown("#### 📅 Диаграмма Ганта")

        gantt_fig = self.scheduler.create_gantt_chart()
        if gantt_fig:
            st.plotly_chart(gantt_fig, use_container_width=True)

        # Метрики проекта
        st.markdown("---")
        st.markdown("#### 📊 Метрики проекта")

        metrics = self.scheduler.calculate_project_metrics()

        if metrics:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Общая длительность", f"{metrics['total_duration']} дней")

            with col2:
                st.metric("Общая стоимость", f"{metrics['total_cost']:,.0f} руб.")

            with col3:
                st.metric("Высокоприоритетных задач", metrics['high_priority_tasks'])

            with col4:
                st.metric("Вероятность выполнения в срок",
                          f"{metrics['on_time_completion'] * 100:.1f}%")

        # Анализ загрузки ресурсов
        st.markdown("---")
        st.markdown("#### 📈 Анализ загрузки ресурсов")

        utilization_fig = self.scheduler.create_resource_utilization_chart()
        if utilization_fig:
            st.plotly_chart(utilization_fig, use_container_width=True)

        # Детальное расписание
        st.markdown("---")
        st.markdown("#### 📋 Детальное расписание")

        schedule_df = pd.DataFrame(schedule)

        if not schedule_df.empty:
            # Форматирование дат
            schedule_df["start_date"] = pd.to_datetime(schedule_df["start_date"]).dt.strftime("%Y-%m-%d")
            schedule_df["end_date"] = pd.to_datetime(schedule_df["end_date"]).dt.strftime("%Y-%m-%d")

            st.dataframe(
                schedule_df[["task_name", "employee_name", "start_date",
                             "end_date", "hours", "cost", "skills_match"]],
                use_container_width=True,
                column_config={
                    "task_name": "Задача",
                    "employee_name": "Исполнитель",
                    "start_date": "Начало",
                    "end_date": "Окончание",
                    "hours": "Часы",
                    "cost": "Стоимость",
                    "skills_match": "Соответствие навыков (%)"
                }
            )

        # Экспорт расписания
        st.markdown("---")
        st.markdown("#### 📤 Экспорт расписания")

        export_format = st.radio(
            "Формат экспорта",
            ["CSV", "Excel", "JSON"],
            horizontal=True
        )

        if st.button(f"📥 Экспортировать расписание как {export_format}",
                     use_container_width=True):
            export_data = self.scheduler.export_schedule(format=export_format.lower())

            if export_data:
                if export_format.lower() == "csv":
                    st.download_button(
                        label="Скачать CSV",
                        data=export_data,
                        file_name="project_schedule.csv",
                        mime="text/csv"
                    )
                elif export_format.lower() == "excel":
                    st.download_button(
                        label="Скачать Excel",
                        data=export_data,
                        file_name="project_schedule.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                elif export_format.lower() == "json":
                    st.download_button(
                        label="Скачать JSON",
                        data=export_data,
                        file_name="project_schedule.json",
                        mime="application/json"
                    )

    def analytics_page(self):
        """Страница аналитики"""
        st.markdown('<h2 class="sub-header">📈 Аналитика и отчеты</h2>',
                    unsafe_allow_html=True)

        if not st.session_state.optimization_results:
            st.warning("⚠️ Сначала выполните оптимизацию")
            return

        analysis = st.session_state.optimization_results["analysis"]
        analysis_df = pd.DataFrame(analysis)

        # Анализ по исполнителям
        st.markdown("#### 👥 Анализ по исполнителям")

        emp_analysis = analysis_df.groupby("employee_name").agg({
            "task_name": "count",
            "estimated_cost": "sum",
            "efficiency_score": "mean",
            "skill_match_percent": "mean"
        }).reset_index()

        emp_analysis.columns = ["Исполнитель", "Задач", "Общая стоимость",
                                "Средняя эффективность", "Среднее соответствие"]

        col1, col2 = st.columns(2)

        with col1:
            # Круговая диаграмма распределения задач
            fig = px.pie(
                emp_analysis,
                values="Задач",
                names="Исполнитель",
                title="Распределение задач по исполнителям"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # График эффективности
            fig = px.bar(
                emp_analysis,
                x="Исполнитель",
                y=["Средняя эффективность", "Среднее соответствие"],
                barmode="group",
                title="Эффективность исполнителей"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Анализ по задачам
        st.markdown("---")
        st.markdown("#### 📊 Анализ по задачам")

        task_analysis = analysis_df.groupby("task_priority").agg({
            "task_name": "count",
            "estimated_cost": "sum",
            "efficiency_score": "mean"
        }).reset_index()

        priority_map = {"high": "Высокий", "medium": "Средний", "low": "Низкий"}
        task_analysis["task_priority"] = task_analysis["task_priority"].map(priority_map)

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                task_analysis,
                x="task_priority",
                y="estimated_cost",
                color="task_priority",
                title="Стоимость по приоритетам",
                labels={"task_priority": "Приоритет", "estimated_cost": "Стоимость"}
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.scatter(
                analysis_df,
                x="estimated_cost",
                y="efficiency_score",
                color="task_priority",
                size="task_hours",
                hover_data=["task_name"],
                title="Стоимость vs Эффективность",
                labels={
                    "estimated_cost": "Стоимость",
                    "efficiency_score": "Эффективность",
                    "task_priority": "Приоритет"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

        # Рекомендации
        st.markdown("---")
        st.markdown("#### 💡 Рекомендации по оптимизации")

        recommendations = self._generate_recommendations(analysis_df)

        for i, rec in enumerate(recommendations, 1):
            if rec["type"] == "warning":
                st.warning(f"**{i}. {rec['title']}**\n\n{rec['description']}")
            elif rec["type"] == "success":
                st.success(f"**{i}. {rec['title']}**\n\n{rec['description']}")
            else:
                st.info(f"**{i}. {rec['title']}**\n\n{rec['description']}")

        # Отчет
        st.markdown("---")
        st.markdown("#### 📄 Генерация отчета")

        if st.button("📊 Сгенерировать полный отчет", use_container_width=True):
            report = self._generate_report(analysis_df)
            st.download_button(
                label="📥 Скачать отчет (HTML)",
                data=report,
                file_name="optimization_report.html",
                mime="text/html"
            )

    def _generate_recommendations(self, analysis_df):
        """Генерация рекомендаций на основе анализа"""
        recommendations = []

        # Проверка низкой эффективности
        low_efficiency = analysis_df[analysis_df["efficiency_score"] < 60]
        if not low_efficiency.empty:
            for _, row in low_efficiency.iterrows():
                recommendations.append({
                    "type": "warning",
                    "title": f"Низкая эффективность назначения",
                    "description": f"Задача '{row['task_name']}' назначена на '{row['employee_name']}' "
                                   f"с эффективностью {row['efficiency_score']:.1f}%. "
                                   f"Рассмотрите перераспределение."
                })

        # Проверка несоответствия навыков
        skill_mismatch = analysis_df[analysis_df["skill_match_percent"] < 80]
        if not skill_mismatch.empty:
            for _, row in skill_mismatch.iterrows():
                recommendations.append({
                    "type": "warning",
                    "title": f"Неполное соответствие навыков",
                    "description": f"Для задачи '{row['task_name']}' исполнитель '{row['employee_name']}' "
                                   f"имеет только {row['skill_match_percent']:.1f}% требуемых навыков. "
                                   f"Недостающие: {', '.join(row['missing_skills'])}"
                })

        # Поиск лучших назначений
        best_assignments = analysis_df.nlargest(3, "efficiency_score")
        for _, row in best_assignments.iterrows():
            recommendations.append({
                "type": "success",
                "title": f"Оптимальное назначение",
                "description": f"Задача '{row['task_name']}' оптимально назначена на "
                               f"'{row['employee_name']}' с эффективностью {row['efficiency_score']:.1f}%"
            })

        return recommendations[:5]  # Ограничиваем 5 рекомендациями

    def _generate_report(self, analysis_df):
        """Генерация HTML отчета"""
        metrics = self.scheduler.calculate_project_metrics() if self.scheduler else {}

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Отчет по оптимизации ресурсов</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; color: #1E3A8A; }}
                .section {{ margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px 20px; }}
                .warning {{ color: #DC2626; }}
                .success {{ color: #059669; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 10px; text-align: left; border: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Отчет по оптимизации распределения ресурсов</h1>
                <p>Сгенерирован: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>

            <div class="section">
                <h2>📊 Сводные метрики</h2>
                <div class="metric">
                    <h3>{len(analysis_df)}</h3>
                    <p>Всего назначений</p>
                </div>
                <div class="metric">
                    <h3>{metrics.get('total_duration', 0)} дней</h3>
                    <p>Длительность проекта</p>
                </div>
                <div class="metric">
                    <h3>{metrics.get('total_cost', 0):,.0f} руб.</h3>
                    <p>Общая стоимость</p>
                </div>
                <div class="metric">
                    <h3>{metrics.get('avg_efficiency', 0):.1f}%</h3>
                    <p>Средняя эффективность</p>
                </div>
            </div>

            <div class="section">
                <h2>📋 Назначения задач</h2>
                <table>
                    <tr>
                        <th>Задача</th>
                        <th>Исполнитель</th>
                        <th>Приоритет</th>
                        <th>Соответствие навыков</th>
                        <th>Эффективность</th>
                        <th>Стоимость</th>
                    </tr>
        """

        for _, row in analysis_df.iterrows():
            priority_ru = {"high": "Высокий", "medium": "Средний", "low": "Низкий"}.get(row["task_priority"],
                                                                                        row["task_priority"])
            skill_class = "warning" if row["skill_match_percent"] < 80 else "success" if row[
                                                                                             "skill_match_percent"] == 100 else ""
            eff_class = "warning" if row["efficiency_score"] < 60 else "success" if row["efficiency_score"] > 80 else ""

            html_content += f"""
                    <tr>
                        <td>{row['task_name']}</td>
                        <td>{row['employee_name']}</td>
                        <td>{priority_ru}</td>
                        <td class="{skill_class}">{row['skill_match_percent']:.1f}%</td>
                        <td class="{eff_class}">{row['efficiency_score']:.1f}%</td>
                        <td>{row['estimated_cost']:,.0f} руб.</td>
                    </tr>
            """

        html_content += """
                </table>
            </div>

            <div class="section">
                <h2>💡 Рекомендации</h2>
        """

        recommendations = self._generate_recommendations(analysis_df)
        for rec in recommendations:
            html_content += f"""
                <div class="recommendation">
                    <h3>{rec['title']}</h3>
                    <p>{rec['description']}</p>
                </div>
            """

        html_content += """
            </div>

            <footer>
                <p>Отчет сгенерирован системой оптимизации распределения ресурсов</p>
            </footer>
        </body>
        </html>
        """

        return html_content

    def reset_data(self):
        """Сброс всех данных"""
        for key in ['tasks', 'employees', 'calendar', 'optimization_results',
                    'schedule', 'optimization_history', 'ga_settings']:
            if key in st.session_state:
                del st.session_state[key]
        self.initialize_session_state()

    def save_project(self):
        """Сохранение проекта"""
        project_data = {
            "tasks": st.session_state.tasks,
            "employees": st.session_state.employees,
            "calendar": st.session_state.calendar,
            "optimization_history": st.session_state.optimization_history,
            "save_date": datetime.now().isoformat()
        }

        if hasattr(st.session_state, 'ga_settings'):
            project_data["ga_settings"] = st.session_state.ga_settings

        json_data = json.dumps(project_data, indent=2, ensure_ascii=False)

        st.download_button(
            label="📥 Скачать проект",
            data=json_data,
            file_name=f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

    def load_project(self):
        """Загрузка проекта"""
        uploaded_file = st.file_uploader("Выберите файл проекта", type=["json"])

        if uploaded_file:
            try:
                project_data = json.load(uploaded_file)

                st.session_state.tasks = project_data.get("tasks", [])
                st.session_state.employees = project_data.get("employees", [])
                st.session_state.calendar = project_data.get("calendar", {})
                st.session_state.optimization_history = project_data.get("optimization_history", [])

                if "ga_settings" in project_data:
                    st.session_state.ga_settings = project_data["ga_settings"]

                st.success("Проект успешно загружен!")

            except Exception as e:
                st.error(f"Ошибка загрузки проекта: {e}")


# Запуск приложения
if __name__ == "__main__":
    app = ResourceOptimizationApp()
    app.run()