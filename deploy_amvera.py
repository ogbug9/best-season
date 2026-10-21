"""Выкладка на Amvera снимком текущего коммита (21.10.2026).

Amvera упаковывает репозиторий целиком вместе с .git: полная история (2 ГБ) и
оригиналы фото домов (1,4 ГБ) давали ~30 минут простоя на каждую выкладку.
Теперь в Amvera живёт отдельная короткая история «снимков»: каждый снимок —
дерево HEAD без того, что сайту в работе не нужно (EXCLUDE). GitHub (origin)
хранит полную историю как раньше.

    python deploy_amvera.py            # обычная выкладка (fast-forward)
    python deploy_amvera.py --first    # первый снимок: заменяет историю Amvera
    python deploy_amvera.py --dry-run  # только показать, что уйдёт

Фото домов уже в медиа на постоянном диске Amvera (/data); import_archive_photos
без оригиналов пропускает шаг. Новый архив фото — заливать из полной копии.
"""
import os
import subprocess
import sys
import tempfile

REMOTE, BRANCH = "amvera", "master"
EXCLUDE = [
    "tmp", "visual_qa", "output", "design", "claude", "Claude outputs",
    ":(glob)config/static/img/content-gallery/*/originals/**",
]


def git(*args, env=None, check=True):
    result = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", env=env)
    if check and result.returncode:
        sys.exit(f"git {' '.join(args)}\n{result.stderr}")
    return result.stdout.strip()


def main():
    first, dry = "--first" in sys.argv, "--dry-run" in sys.argv
    if git("status", "--porcelain", "--untracked-files=no"):
        print("Внимание: есть незакоммиченные правки — в снимок уйдёт только последний коммит.")
    head = git("rev-parse", "HEAD")
    subject = git("log", "-1", "--format=%s")
    with tempfile.TemporaryDirectory() as folder:
        env = {**os.environ, "GIT_INDEX_FILE": os.path.join(folder, "index")}
        git("read-tree", "HEAD", env=env)
        git("rm", "--cached", "-r", "-q", "--ignore-unmatch", "--", *EXCLUDE, env=env)
        tree = git("write-tree", env=env)
        size = sum(int(line.split()[3]) for line in git("ls-tree", "-r", "-l", tree).splitlines() if line.split()[3] != "-")
    print(f"Снимок {head[:7]} «{subject}»: {size / 1048576:.0f} МБ")

    git("fetch", "-q", REMOTE, BRANCH)
    remote = git("rev-parse", f"{REMOTE}/{BRANCH}")
    parents = [] if first else ["-p", remote]
    if not first:
        if not git("log", "-1", "--format=%s", remote).startswith("snapshot "):
            sys.exit("В Amvera ещё полная история — первый раз запустите с --first.")
        if git("rev-parse", f"{remote}^{{tree}}") == tree:
            print("В Amvera уже этот код — выкладывать нечего.")
            return
    commit = git("commit-tree", tree, *parents, "-m", f"snapshot {head[:12]}: {subject}")
    if dry:
        print(f"Пробный запуск: снимок {commit[:7]} не отправлен.")
        return
    push = ["push", REMOTE, f"{commit}:refs/heads/{BRANCH}"]
    if first:
        push.insert(1, f"--force-with-lease={BRANCH}:{remote}")
    git(*push)
    git("update-ref", "refs/amvera/last", commit)
    print(f"Отправлено в {REMOTE}/{BRANCH}: {commit[:7]}. Сборка на Amvera запущена.")


if __name__ == "__main__":
    main()
