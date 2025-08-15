import git
import os
from typing import List, Optional

class GitHelper:
    def __init__(self, path: str = "."):
        self.path = path
        self.repo: Optional[git.Repo] = None
        if os.path.exists(os.path.join(path, '.git')):
            self.repo = git.Repo(path)

    def init(self, path: str):
        """Инициализировать новый репозиторий"""
        self.repo = git.Repo.init(path)
        self.path = path

    def clone(self, url: str, path: str):
        """Клонировать репозиторий"""
        self.repo = git.Repo.clone_from(url, path)
        self.path = path

    # === Browse ===
    def status(self) -> str:
        """Получить статус репозитория"""
        if not self.repo:
            return "Repository not initialized"
        return self.repo.git.status()

    def log(self, limit: int = 10) -> str:
        """Получить лог коммитов"""
        if not self.repo:
            return "Repository not initialized"
        return self.repo.git.log(f"--oneline", f"-{limit}")

    def show(self, commit: str) -> str:
        """Показать изменения в коммите"""
        if not self.repo:
            return "Repository not initialized"
        return self.repo.git.show(commit)

    def diff(self, staged: bool = False) -> str:
        """Показать различия"""
        if not self.repo:
            return "Repository not initialized"
        if staged:
            return self.repo.git.diff("--staged")
        return self.repo.git.diff()

    def branches(self) -> List[str]:
        """Получить список веток"""
        if not self.repo:
            return []
        return [b.name for b in self.repo.branches]

    # === Change ===
    def add(self, files: List[str] = ["."]) -> str:
        """Добавить файлы в индекс"""
        if not self.repo:
            return "Repository not initialized"
        return self.repo.git.add(*files)

    def add_all(self) -> str:
        """Добавить все изменения"""
        if not self.repo:
            return "Repository not initialized"
        return self.repo.git.add(".")

    # === Revert ===
    def reset(self, commit: str = "HEAD", hard: bool = False) -> str:
        """Сброс изменений"""
        if not self.repo:
            return "Repository not initialized"
        if hard:
            return self.repo.git.reset("--hard", commit)
        return self.repo.git.reset(commit)

    def checkout(self, target: str) -> str:
        """Переключиться на ветку или коммит"""
        if not self.repo:
            return "Repository not initialized"
        return self.repo.git.checkout(target)

    def revert_commit(self, commit: str) -> str:
        """Отменить коммит"""
        if not self.repo:
            return "Repository not initialized"
        return self.repo.git.revert(commit, "-n")

    # === Update ===
    def pull(self, remote: str = "origin", branch: str = "") -> str:
        """Затянуть изменения"""
        if not self.repo:
            return "Repository not initialized"
        if branch:
            return self.repo.git.pull(remote, branch)
        return self.repo.git.pull()

    def fetch(self, remote: str = "origin") -> str:
        """Получить изменения с удаленного репозитория"""
        if not self.repo:
            return "Repository not initialized"
        return self.repo.git.fetch(remote)

    def merge(self, branch: str) -> str:
        """Слить ветку"""
        if not self.repo:
            return "Repository not initialized"
        return self.repo.git.merge(branch)

    # === Branch ===
    def create_branch(self, name: str) -> str:
        """Создать новую ветку"""
        if not self.repo:
            return "Repository not initialized"
        return self.repo.git.branch(name)

    def switch_branch(self, name: str) -> str:
        """Переключиться на ветку"""
        if not self.repo:
            return "Repository not initialized"
        return self.repo.git.checkout(name)

    # === Commit ===
    def commit(self, message: str) -> str:
        """Сделать коммит"""
        if not self.repo:
            return "Repository not initialized"
        return self.repo.git.commit("-m", message)

    # === Publish ===
    def push(self, remote: str = "origin", branch: str = "") -> str:
        """Отправить изменения"""
        if not self.repo:
            return "Repository not initialized"
        if branch:
            return self.repo.git.push(remote, branch)
        return self.repo.git.push()

    def get_current_branch(self) -> str:
        """Получить текущую ветку"""
        if not self.repo:
            return "No branch"
        return self.repo.active_branch.name if self.repo.active_branch else "Detached HEAD"
