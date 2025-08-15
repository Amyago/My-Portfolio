import flet as ft
from git_helper import GitHelper
import os
import threading


class GitAssistantApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Git Помощник"
        self.page.window_width = 1100
        self.page.window_height = 800
        self.page.theme_mode = ft.ThemeMode.DARK

        self.git_helper = GitHelper(".")
        self.is_working = False

        # Output area
        self.output_area = ft.TextField(
            value="",
            multiline=True,
            read_only=True,
            expand=True,
            text_size=12,
        )

        # Progress bar
        self.progress_bar = ft.ProgressBar(visible=False, width=400)
        self.progress_text = ft.Text("", size=12)

        self.setup_ui()

    def setup_ui(self):
        # Path selection
        path_row = ft.Row([
            ft.Text("Путь к репозиторию:", size=14),
            ft.TextField(
                value=os.getcwd(),
                expand=True,
                on_change=self.on_path_change
            ),
            ft.ElevatedButton("Загрузить", on_click=self.load_repo, tooltip="Загрузить репозиторий по указанному пути")
        ])

        # Status bar
        status_row = ft.Row([
            self.progress_bar,
            self.progress_text
        ])

        # Tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Создать", content=self.create_tab_content()),
                ft.Tab(text="Просмотр", content=self.browse_tab_content()),
                ft.Tab(text="Изменения", content=self.change_tab_content()),
                ft.Tab(text="Откат", content=self.revert_tab_content()),
                ft.Tab(text="Обновление", content=self.update_tab_content()),
                ft.Tab(text="Ветки", content=self.branch_tab_content()),
                ft.Tab(text="Коммит", content=self.commit_tab_content()),
                ft.Tab(text="Публикация", content=self.publish_tab_content()),
                ft.Tab(text="Гайд", content=self.guide_tab_content()),
            ],
            expand=1,
        )

        # Main layout
        self.page.add(
            path_row,
            ft.Divider(),
            self.tabs,
            ft.Divider(),
            status_row,
            ft.Text("Вывод:", size=14),
            self.output_area
        )

    def show_output(self, text: str):
        self.output_area.value = str(text)
        self.page.update()

    def show_progress(self, text: str = "", visible: bool = True):
        self.progress_text.value = text
        self.progress_bar.visible = visible
        self.page.update()

    def run_async_command(self, func, *args):
        """Запуск асинхронной команды с отображением прогресса"""

        def worker():
            try:
                self.is_working = True
                self.show_progress("Выполняется операция...", True)
                result = func(*args)
                self.show_output(result)
            except Exception as e:
                self.show_output(f"Ошибка: {str(e)}")
            finally:
                self.is_working = False
                self.show_progress("", False)

        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()

    def load_repo(self, e):
        path = self.page.controls[0].controls[2].value  # Получаем путь из текстового поля
        try:
            self.git_helper = GitHelper(path)
            self.show_output(f"Репозиторий загружен: {path}")
        except Exception as ex:
            self.show_output(f"Ошибка загрузки репозитория: {str(ex)}")

    def on_path_change(self, e):
        pass

    # === Create Tab ===
    def create_tab_content(self):
        init_path = ft.TextField(label="Путь для инициализации", value=".", width=300)
        clone_url = ft.TextField(label="URL репозитория", width=300)
        clone_path = ft.TextField(label="Локальный путь", width=300)

        return ft.Column([
            ft.Text("Инициализация репозитория", size=16, weight=ft.FontWeight.BOLD),
            init_path,
            ft.ElevatedButton(
                "Инициализировать",
                on_click=lambda e: self.cmd_init(init_path.value),
                tooltip="Создать новый Git репозиторий в указанной папке"
            ),

            ft.Divider(),

            ft.Text("Клонирование репозитория", size=16, weight=ft.FontWeight.BOLD),
            clone_url,
            clone_path,
            ft.ElevatedButton(
                "Клонировать",
                on_click=lambda e: self.cmd_clone(clone_url.value, clone_path.value),
                tooltip="Скачать существующий репозиторий с удаленного сервера"
            ),
        ], scroll=ft.ScrollMode.AUTO)

    def cmd_init(self, path: str):
        try:
            self.git_helper.init(path)
            self.show_output(f"Репозиторий инициализирован в {path}")
        except Exception as e:
            self.show_output(f"Ошибка: {str(e)}")

    def cmd_clone(self, url: str, path: str):
        if not url or not path:
            self.show_output("Пожалуйста, укажите URL и путь")
            return
        self.run_async_command(self._clone_repo, url, path)

    def _clone_repo(self, url: str, path: str):
        self.git_helper.clone(url, path)
        return f"Репозиторий клонирован в {path}"

    # === Browse Tab ===
    def browse_tab_content(self):
        show_commit = ft.TextField(label="Хэш коммита", width=200)
        log_limit = ft.TextField(label="Лимит лога", value="10", width=100)

        return ft.Column([
            ft.Row([
                ft.ElevatedButton(
                    "Статус",
                    on_click=lambda e: self.cmd_status(),
                    tooltip="Показать текущее состояние файлов в репозитории"
                ),
                ft.ElevatedButton(
                    "Лог",
                    on_click=lambda e: self.cmd_log(int(log_limit.value) if log_limit.value.isdigit() else 10),
                    tooltip="Показать историю коммитов"
                ),
                ft.ElevatedButton(
                    "Ветки",
                    on_click=lambda e: self.cmd_branches(),
                    tooltip="Показать список всех веток"
                ),
                ft.ElevatedButton(
                    "Различия",
                    on_click=lambda e: self.cmd_diff(),
                    tooltip="Показать изменения в файлах по сравнению с последним коммитом"
                ),
                ft.ElevatedButton(
                    "Различия (staged)",
                    on_click=lambda e: self.cmd_diff(staged=True),
                    tooltip="Показать изменения, подготовленные для коммита"
                ),
            ]),
            ft.Row([log_limit]),
            ft.Divider(),
            ft.Text("Просмотр коммита:", size=16, weight=ft.FontWeight.BOLD),
            show_commit,
            ft.ElevatedButton(
                "Показать",
                on_click=lambda e: self.cmd_show(show_commit.value),
                tooltip="Показать детали конкретного коммита"
            ),
        ])

    def cmd_status(self):
        result = self.git_helper.status()
        self.show_output(result)

    def cmd_log(self, limit: int = 10):
        result = self.git_helper.log(limit)
        self.show_output(result)

    def cmd_branches(self):
        branches = self.git_helper.branches()
        self.show_output("\n".join(branches) if branches else "Нет веток")

    def cmd_diff(self, staged: bool = False):
        result = self.git_helper.diff(staged=staged)
        self.show_output(result)

    def cmd_show(self, commit: str):
        if not commit:
            self.show_output("Пожалуйста, введите хэш коммита")
            return
        result = self.git_helper.show(commit)
        self.show_output(result)

    # === Change Tab ===
    def change_tab_content(self):
        add_files = ft.TextField(label="Файлы для добавления (через пробел)", width=400)

        return ft.Column([
            ft.Text("Добавление файлов:", size=16, weight=ft.FontWeight.BOLD),
            add_files,
            ft.ElevatedButton(
                "Добавить",
                on_click=lambda e: self.cmd_add(add_files.value.split() if add_files.value else ["."]),
                tooltip="Добавить указанные файлы в индекс для последующего коммита"
            ),
            ft.ElevatedButton(
                "Добавить все",
                on_click=lambda e: self.cmd_add_all(),
                tooltip="Добавить все измененные файлы в индекс"
            ),
        ])

    def cmd_add(self, files: list):
        result = self.git_helper.add(files)
        self.show_output(result)

    def cmd_add_all(self):
        result = self.git_helper.add_all()
        self.show_output(result)

    # === Revert Tab ===
    def revert_tab_content(self):
        reset_commit = ft.TextField(label="Сбросить к коммиту", value="HEAD", width=200)
        checkout_target = ft.TextField(label="Цель для перехода", width=200)
        revert_commit = ft.TextField(label="Отменить коммит", width=200)

        return ft.Column([
            ft.Text("Сброс:", size=16, weight=ft.FontWeight.BOLD),
            reset_commit,
            ft.Row([
                ft.ElevatedButton(
                    "Сброс",
                    on_click=lambda e: self.cmd_reset(reset_commit.value),
                    tooltip="Отменить изменения в индексе, но оставить изменения в файлах"
                ),
                ft.ElevatedButton(
                    "Жесткий сброс",
                    on_click=lambda e: self.cmd_reset(reset_commit.value, hard=True),
                    tooltip="ПОЛНОСТЬЮ отменить все изменения (ОПАСНО!)"
                ),
            ]),

            ft.Divider(),

            ft.Text("Переход:", size=16, weight=ft.FontWeight.BOLD),
            checkout_target,
            ft.ElevatedButton(
                "Перейти",
                on_click=lambda e: self.cmd_checkout(checkout_target.value),
                tooltip="Переключиться на другую ветку или коммит"
            ),

            ft.Divider(),

            ft.Text("Отмена коммита:", size=16, weight=ft.FontWeight.BOLD),
            revert_commit,
            ft.ElevatedButton(
                "Отменить",
                on_click=lambda e: self.cmd_revert_commit(revert_commit.value),
                tooltip="Создать новый коммит, который отменяет указанный коммит"
            ),
        ])

    def cmd_reset(self, commit: str, hard: bool = False):
        result = self.git_helper.reset(commit, hard)
        self.show_output(result)

    def cmd_checkout(self, target: str):
        if not target:
            self.show_output("Пожалуйста, введите цель для перехода")
            return
        result = self.git_helper.checkout(target)
        self.show_output(result)

    def cmd_revert_commit(self, commit: str):
        if not commit:
            self.show_output("Пожалуйста, введите хэш коммита")
            return
        result = self.git_helper.revert_commit(commit)
        self.show_output(result)

    # === Update Tab ===
    def update_tab_content(self):
        merge_branch = ft.TextField(label="Ветка для слияния", width=200)

        return ft.Column([
            ft.ElevatedButton(
                "Получить изменения",
                on_click=lambda e: self.cmd_fetch(),
                tooltip="Получить изменения с удаленного сервера, но не применять их"
            ),
            ft.ElevatedButton(
                "Затянуть изменения",
                on_click=lambda e: self.cmd_pull(),
                tooltip="Получить и применить изменения с удаленного сервера"
            ),

            ft.Divider(),

            ft.Text("Слияние ветки:", size=16, weight=ft.FontWeight.BOLD),
            merge_branch,
            ft.ElevatedButton(
                "Слить",
                on_click=lambda e: self.cmd_merge(merge_branch.value),
                tooltip="Объединить указанную ветку с текущей"
            ),
        ])

    def cmd_fetch(self):
        self.run_async_command(self._fetch_repo)

    def _fetch_repo(self):
        result = self.git_helper.fetch()
        return "Изменения получены успешно"

    def cmd_pull(self):
        self.run_async_command(self._pull_repo)

    def _pull_repo(self):
        result = self.git_helper.pull()
        return "Изменения затянуты успешно"

    def cmd_merge(self, branch: str):
        if not branch:
            self.show_output("Пожалуйста, введите имя ветки")
            return
        result = self.git_helper.merge(branch)
        self.show_output(result)

    # === Branch Tab ===
    def branch_tab_content(self):
        create_branch_name = ft.TextField(label="Имя новой ветки", width=200)
        switch_branch_name = ft.TextField(label="Ветка для перехода", width=200)

        return ft.Column([
            ft.Text("Создание ветки:", size=16, weight=ft.FontWeight.BOLD),
            create_branch_name,
            ft.ElevatedButton(
                "Создать",
                on_click=lambda e: self.cmd_create_branch(create_branch_name.value),
                tooltip="Создать новую ветку с указанным именем"
            ),

            ft.Divider(),

            ft.Text("Переход на ветку:", size=16, weight=ft.FontWeight.BOLD),
            switch_branch_name,
            ft.ElevatedButton(
                "Перейти",
                on_click=lambda e: self.cmd_switch_branch(switch_branch_name.value),
                tooltip="Переключиться на существующую ветку"
            ),
        ])

    def cmd_create_branch(self, name: str):
        if not name:
            self.show_output("Пожалуйста, введите имя ветки")
            return
        result = self.git_helper.create_branch(name)
        self.show_output(result)

    def cmd_switch_branch(self, name: str):
        if not name:
            self.show_output("Пожалуйста, введите имя ветки")
            return
        result = self.git_helper.switch_branch(name)
        self.show_output(result)

    # === Commit Tab ===
    def commit_tab_content(self):
        commit_message = ft.TextField(
            label="Сообщение коммита",
            multiline=True,
            min_lines=3,
            max_lines=5,
            width=400
        )

        return ft.Column([
            ft.Text("Создание коммита:", size=16, weight=ft.FontWeight.BOLD),
            commit_message,
            ft.ElevatedButton(
                "Создать коммит",
                on_click=lambda e: self.cmd_commit(commit_message.value),
                tooltip="Создать новый коммит с указанным сообщением"
            ),
        ])

    def cmd_commit(self, message: str):
        if not message.strip():
            self.show_output("Пожалуйста, введите сообщение коммита")
            return
        result = self.git_helper.commit(message.strip())
        self.show_output(result)

    # === Publish Tab ===
    def publish_tab_content(self):
        push_branch = ft.TextField(label="Ветка для публикации", width=200)

        return ft.Column([
            ft.ElevatedButton(
                "Опубликовать",
                on_click=lambda e: self.cmd_push(),
                tooltip="Отправить текущую ветку на удаленный сервер"
            ),

            ft.Divider(),

            ft.Text("Публикация конкретной ветки:", size=16, weight=ft.FontWeight.BOLD),
            push_branch,
            ft.ElevatedButton(
                "Опубликовать ветку",
                on_click=lambda e: self.cmd_push_branch(push_branch.value),
                tooltip="Отправить указанную ветку на удаленный сервер"
            ),
        ])

    def cmd_push(self):
        self.run_async_command(self._push_repo)

    def _push_repo(self):
        result = self.git_helper.push()
        return "Изменения опубликованы успешно"

    def cmd_push_branch(self, branch: str):
        if not branch:
            self.show_output("Пожалуйста, введите имя ветки")
            return
        self.run_async_command(self._push_branch, branch)

    def _push_branch(self, branch: str):
        result = self.git_helper.push(branch=branch)
        return f"Ветка {branch} опубликована успешно"

    # === Guide Tab ===
    def guide_tab_content(self):
        guide_content = ft.Column([
            ft.Text("Интерактивный гид по Git Помощнику", size=20, weight=ft.FontWeight.BOLD),

            ft.Text("\n🎯 Как пользоваться:", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("• Наведите курсор мыши на любую кнопку, чтобы увидеть подсказку о её назначении"),
            ft.Text("• Все операции выполняются в соответствующих вкладках"),
            ft.Text("• Для начала работы укажите путь к репозиторию и нажмите 'Загрузить'"),

            ft.Text("\n📋 Основные вкладки:", size=16, weight=ft.FontWeight.BOLD),

            ft.Text("\n📁 СОЗДАТЬ:", size=14, weight=ft.FontWeight.BOLD),
            ft.Text("• Инициализация нового репозитория - создать Git репозиторий в папке"),
            ft.Text("• Клонирование - скачать существующий репозиторий с GitHub/другого сервера"),

            ft.Text("\n🔍 ПРОСМОТР:", size=14, weight=ft.FontWeight.BOLD),
            ft.Text("• Статус - текущее состояние файлов (изменены, добавлены, удалены)"),
            ft.Text("• Лог - история коммитов с сообщениями"),
            ft.Text("• Ветки - список всех веток в репозитории"),
            ft.Text("• Различия - изменения в файлах по сравнению с последним коммитом"),
            ft.Text("• Просмотр коммита - детали конкретного коммита"),

            ft.Text("\n✏️ ИЗМЕНЕНИЯ:", size=14, weight=ft.FontWeight.BOLD),
            ft.Text("• Добавить файлы - подготовить файлы к коммиту"),
            ft.Text("• Добавить все - подготовить все измененные файлы к коммиту"),

            ft.Text("\n↩️ ОТКАТ:", size=14, weight=ft.FontWeight.BOLD),
            ft.Text("• Сброс - отменить изменения в индексе"),
            ft.Text("• Жесткий сброс - ПОЛНОСТЬЮ отменить все изменения (ОПАСНО!)"),
            ft.Text("• Переход - переключиться на другую ветку или коммит"),
            ft.Text("• Отменить коммит - создать коммит, отменяющий указанный"),

            ft.Text("\n🔄 ОБНОВЛЕНИЕ:", size=14, weight=ft.FontWeight.BOLD),
            ft.Text("• Получить изменения - загрузить изменения с сервера"),
            ft.Text("• Затянуть изменения - загрузить и применить изменения"),
            ft.Text("• Слить ветку - объединить две ветки"),

            ft.Text("\n🌿 ВЕТКИ:", size=14, weight=ft.FontWeight.BOLD),
            ft.Text("• Создать ветку - создать новую ветку разработки"),
            ft.Text("• Перейти на ветку - переключиться на существующую ветку"),

            ft.Text("\n💾 КОММИТ:", size=14, weight=ft.FontWeight.BOLD),
            ft.Text("• Создать коммит - сохранить изменения с сообщением"),

            ft.Text("\n🚀 ПУБЛИКАЦИЯ:", size=14, weight=ft.FontWeight.BOLD),
            ft.Text("• Опубликовать - отправить изменения на удаленный сервер"),

            ft.Text("\n⚠️ ВАЖНО:", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("• Некоторые операции (клонирование, пуш, пулл) выполняются асинхронно"),
            ft.Text("• Во время выполнения операций отображается индикатор прогресса"),
            ft.Text("• Жесткий сброс удаляет все несохраненные изменения - используйте с осторожностью!"),

            ft.Text("\n💡 СОВЕТЫ:", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("• Начните с вкладки 'Просмотр' → 'Статус', чтобы понять текущее состояние"),
            ft.Text("• Перед пушем всегда делайте пулл, чтобы избежать конфликтов"),
            ft.Text("• Используйте ветки для экспериментов и новой функциональности"),
        ], scroll=ft.ScrollMode.AUTO)

        return guide_content


def main(page: ft.Page):
    GitAssistantApp(page)


if __name__ == "__main__":
    ft.app(target=main)
