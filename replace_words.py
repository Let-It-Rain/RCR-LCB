#!/usr/bin/env python3
"""
replace_words.py

Минимальная GUI-программа (tkinter) для рекурсивной замены слов в файлах папки.
Особенности (обновлённые):
- Авто-подстановка пути к ./localize (если найдёт в репозитории/рабочей папке)
- Опция "только целые слова" и чувствительность к регистру
- Пропуск бинарных файлов
- Попытка чтения в UTF-8, затем CP1251/latin-1
- Лог в окне
- После завершения — окно со списком изменённых файлов (копирование в буфер)
- По умолчанию бекапы отключены (согласно вашему запросу)
"""
import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Optional, Tuple

# ---------------------------
# Утилиты
# ---------------------------
def is_binary_file(path: Path, check_bytes: int = 1024) -> bool:
    try:
        with path.open('rb') as f:
            chunk = f.read(check_bytes)
            if not chunk:
                return False
            if b'\x00' in chunk:
                return True
            text_chars = bytes(range(32, 127)) + b'\n\r\t\b'
            nontext = sum(1 for b in chunk if b not in text_chars)
            if nontext / len(chunk) > 0.30:
                return True
    except Exception:
        return True
    return False

def read_text_file(path: Path) -> Optional[Tuple[str,str]]:
    encodings = ['utf-8', 'cp1251', 'latin-1']
    for enc in encodings:
        try:
            with path.open('r', encoding=enc, errors='strict') as f:
                return f.read(), enc
        except UnicodeDecodeError:
            continue
        except Exception:
            return None
    try:
        with path.open('r', encoding='latin-1', errors='replace') as f:
            return f.read(), 'latin-1'
    except Exception:
        return None

def write_text_file(path: Path, text: str, encoding: str) -> bool:
    try:
        st_mode = path.stat().st_mode
        with path.open('w', encoding=encoding, errors='replace') as f:
            f.write(text)
        os.chmod(path, st_mode)
        return True
    except Exception:
        return False

def find_localize_folder(start_dir: Path, max_depth: int = 4) -> Optional[Path]:
    candidate = start_dir / 'localize'
    if candidate.is_dir():
        return candidate.resolve()
    for root, dirs, files in os.walk(start_dir):
        depth = Path(root).resolve().relative_to(start_dir.resolve()).parts
        if len(depth) > max_depth:
            dirs[:] = []
            continue
        for d in dirs:
            if d.lower() == 'localize':
                return Path(root) / d
    return None

# ---------------------------
# Замена в файле
# ---------------------------
def replace_in_file(path: Path, search: str, replace: str,
                    whole_word: bool, case_sensitive: bool) -> int:
    """
    Возвращает количество подстановок в файле.
    """
    if is_binary_file(path):
        return 0
    data = read_text_file(path)
    if data is None:
        return 0
    text, enc = data
    flags = 0 if case_sensitive else re.IGNORECASE
    if whole_word:
        pattern = re.compile(r'\b' + re.escape(search) + r'\b', flags)
    else:
        pattern = re.compile(re.escape(search), flags)
    new_text, count = pattern.subn(replace, text)
    if count > 0 and new_text != text:
        ok = write_text_file(path, new_text, enc)
        if ok:
            return count
    return 0

# ---------------------------
# GUI
# ---------------------------
class App:
    def __init__(self, root):
        self.root = root
        root.title("Replace Words — минимальный тёмный инструмент")
        root.geometry("760x480")
        root.configure(bg='#2b2b2b')

        # Variables
        self.path_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.replace_var = tk.StringVar()
        self.whole_word_var = tk.BooleanVar(value=True)
        self.case_sensitive_var = tk.BooleanVar(value=True)
        self.exclude_dirs_var = tk.StringVar(
            value=",".join(sorted({
            '.git',
            'node_modules',
            '__pycache__',
            'venv',
            '.venv',
            'env',
            'ENV',
            'env.bak',
            'venv.bak',
            'build',
            'dist',
            '.eggs',
            '.egg-info',
            '.ipynb_checkpoints',
            '.pytest_cache',
            '.mypy_cache',
            '.pyre',
            '.pytype',
            '.ruff_cache',
            '.reference',
            'cython_debug',
            '.tox',
            '.nox'
            }))
        )


        # auto-find localize
        self.auto_set_localize()

        self._build_ui()

    def auto_set_localize(self):
        cwd = Path.cwd()
        script_dir = Path(__file__).parent
        folder = find_localize_folder(cwd) or find_localize_folder(script_dir) or find_localize_folder(script_dir.parent)
        if folder:
            self.path_var.set(str(folder))
        else:
            self.path_var.set(str(cwd))

    def _build_ui(self):
        padx = 8
        pady = 6
        bg = '#2b2b2b'
        fg = '#e6e6e6'
        entry_bg = '#3a3a3a'
        btn_bg = '#444444'
        btn_fg = fg

        top = tk.Frame(self.root, bg=bg)
        top.pack(fill='x', padx=10, pady=8)

        tk.Label(top, text="Папка (path):", bg=bg, fg=fg).grid(row=0, column=0, sticky='w', padx=padx, pady=pady)
        path_entry = tk.Entry(top, textvariable=self.path_var, bg=entry_bg, fg=fg, insertbackground=fg, width=60)
        path_entry.grid(row=0, column=1, sticky='w', padx=padx, pady=pady)
        tk.Button(top, text="Обзор", command=self.browse, bg=btn_bg, fg=btn_fg).grid(row=0, column=2, padx=padx)

        tk.Label(top, text="Что искать:", bg=bg, fg=fg).grid(row=1, column=0, sticky='w', padx=padx, pady=pady)
        tk.Entry(top, textvariable=self.search_var, bg=entry_bg, fg=fg, insertbackground=fg, width=30).grid(row=1, column=1, sticky='w', padx=padx)
        tk.Label(top, text="Заменить на:", bg=bg, fg=fg).grid(row=2, column=0, sticky='w', padx=padx, pady=pady)
        tk.Entry(top, textvariable=self.replace_var, bg=entry_bg, fg=fg, insertbackground=fg, width=30).grid(row=2, column=1, sticky='w', padx=padx)

        opts = tk.Frame(self.root, bg=bg)
        opts.pack(fill='x', padx=10)
        tk.Checkbutton(opts, text="Только целые слова (whole word)", bg=bg, fg=fg, selectcolor=bg, variable=self.whole_word_var).grid(row=0, column=0, sticky='w', padx=padx)
        tk.Checkbutton(opts, text="Чувствительно к регистру", bg=bg, fg=fg, selectcolor=bg, variable=self.case_sensitive_var).grid(row=0, column=1, sticky='w')
        tk.Label(opts, text="Игнорировать папки (через запятую):", bg=bg, fg=fg).grid(row=1, column=0, sticky='w', pady=6, padx=padx)
        tk.Entry(opts, textvariable=self.exclude_dirs_var, bg=entry_bg, fg=fg, insertbackground=fg, width=60).grid(row=1, column=1, columnspan=2, sticky='w', padx=padx)

        buttons = tk.Frame(self.root, bg=bg)
        buttons.pack(fill='x', padx=10, pady=6)
        tk.Button(buttons, text="Запустить замену", command=self.run_replace, bg='#5a9bd4', fg='#ffffff', padx=10, pady=6).pack(side='left', padx=6)
        tk.Button(buttons, text="Очистить лог", command=lambda: self.log_text.delete(1.0, tk.END), bg=btn_bg, fg=btn_fg).pack(side='left', padx=6)
        tk.Button(buttons, text="Открыть папку", command=self.open_folder, bg=btn_bg, fg=btn_fg).pack(side='left', padx=6)

        self.log_text = scrolledtext.ScrolledText(self.root, height=14, bg='#1e1e1e', fg=fg, insertbackground=fg)
        self.log_text.pack(fill='both', expand=True, padx=10, pady=(0,10))

    def browse(self):
        d = filedialog.askdirectory()
        if d:
            self.path_var.set(d)

    def open_folder(self):
        path = self.path_var.get()
        if not path:
            return
        try:
            if os.name == 'nt':
                os.startfile(path)
            else:
                import subprocess
                subprocess.run(['xdg-open', path])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку: {e}")

    def log(self, *args):
        self.log_text.insert(tk.END, " ".join(str(a) for a in args) + "\n")
        self.log_text.see(tk.END)

    def run_replace(self):
        folder = self.path_var.get().strip()
        search = self.search_var.get()
        repl = self.replace_var.get()
        whole = bool(self.whole_word_var.get())
        case_sens = bool(self.case_sensitive_var.get())
        excludes = {d.strip() for d in self.exclude_dirs_var.get().split(",") if d.strip()}

        if not folder:
            messagebox.showwarning("Папка не указана", "Укажите папку для поиска.")
            return
        if not search:
            messagebox.showwarning("Что искать", "Укажите слово/фразу для поиска.")
            return

        folder_path = Path(folder)
        if not folder_path.is_dir():
            messagebox.showerror("Ошибка", "Папка не найдена.")
            return

        if not messagebox.askyesno("Подтверждение", f"Заменить '{search}' -> '{repl}' в папке:\n{folder}\nРекурсивно? Да"):
            return

        total_files = 0
        total_changes = 0
        skipped_binary = 0
        failed = 0
        changed_files = []

        self.log(f"Старт: папка={folder}, search='{search}', replace='{repl}', whole_word={whole}, case_sensitive={case_sens}")

        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d not in excludes]
            for fname in files:
                fpath = Path(root) / fname
                total_files += 1
                try:
                    if is_binary_file(fpath):
                        skipped_binary += 1
                        self.log(f"Пропущен бинарный файл: {fpath}")
                        continue
                    cnt = replace_in_file(fpath, search, repl, whole, case_sens)
                    if cnt > 0:
                        total_changes += cnt
                        changed_files.append(str(fpath))
                        self.log(f"Изменено ({cnt}) в файле: {fpath}")
                except Exception as e:
                    failed += 1
                    self.log(f"Ошибка при обработке {fpath}: {e}")

        self.log("=== Итог ===")
        self.log(f"Файлов обработано: {total_files}")
        self.log(f"Изменений сделано (подстановок): {total_changes}")
        self.log(f"Бинарных файлов пропущено: {skipped_binary}")
        self.log(f"Файлов с ошибкой: {failed}")

        # После завершения — показать отдельное окно со списком изменённых файлов
        self.show_changed_files_window(changed_files, total_changes)

        messagebox.showinfo("Готово", f"Завершено. Изменений: {total_changes}. Окно со списком изменённых файлов открыто.")

    def show_changed_files_window(self, changed_files, total_changes):
        win = tk.Toplevel(self.root)
        win.title(f"Изменённые файлы — {len(changed_files)}")
        win.geometry("760x360")
        win.configure(bg='#2b2b2b')

        fg = '#e6e6e6'
        entry_bg = '#1e1e1e'

        lbl = tk.Label(win, text=f"Изменённых файлов: {len(changed_files)}  |  Всего подстановок: {total_changes}", bg='#2b2b2b', fg=fg)
        lbl.pack(anchor='w', padx=8, pady=(8,4))

        text = scrolledtext.ScrolledText(win, height=14, bg=entry_bg, fg=fg)
        text.pack(fill='both', expand=True, padx=8, pady=(0,8))
        text.configure(state='normal')
        if changed_files:
            text.insert(tk.END, "\n".join(changed_files))
        else:
            text.insert(tk.END, "(Нет изменённых файлов)")
        text.configure(state='disabled')

        btn_frame = tk.Frame(win, bg='#2b2b2b')
        btn_frame.pack(fill='x', padx=8, pady=(0,8))

        def copy_list():
            s = "\n".join(changed_files)
            self.root.clipboard_clear()
            self.root.clipboard_append(s)
            messagebox.showinfo("Скопировано", "Список изменённых файлов скопирован в буфер обмена.")

        tk.Button(btn_frame, text="Копировать список", command=copy_list, bg='#5a9bd4', fg='#ffffff').pack(side='left', padx=6)
        tk.Button(btn_frame, text="Закрыть", command=win.destroy, bg='#444444', fg=fg).pack(side='left', padx=6)

# ---------------------------
# Запуск
# ---------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
