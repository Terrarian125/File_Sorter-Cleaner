
# 進捗表示対応版（全文）
import os
import shutil
import time
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import send2trash


def log_message(message, log_file_path):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(full_message + "\n")


def execute_sorting(
    target_dir,
    delete_zip,
    delete_exe,
    threshold_seconds,
    progress_var,
    status_var,
    root,
    run_button
):
    if not target_dir or not os.path.exists(target_dir):
        messagebox.showerror("エラー", "有効なフォルダを選択してください。")
        return

    run_button.config(state="disabled")

    try:
        log_file_path = os.path.join(target_dir, "sort_log.txt")

        file_types = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
            "Documents": [".pdf", ".docx", ".xlsx", ".txt", ".pptx", ".csv"],
            "Archives": [".zip", ".tar", ".gz", ".rar"]
        }

        counts = {"moved": 0, "trash_zip": 0, "trash_exe": 0, "empty_dir": 0}
        current_time = time.time()

        log_message("=== 自動仕分け・掃除を開始します ===", log_file_path)

        files = os.listdir(target_dir)

        target_files = [
            f for f in files
            if os.path.isfile(os.path.join(target_dir, f))
            and f != "sort_log.txt"
        ]

        total_files = max(len(target_files), 1)
        processed = 0

        for filename in target_files:

            processed += 1

            file_path = os.path.join(target_dir, filename)

            percent = (processed / total_files) * 100
            progress_var.set(percent)

            status_var.set(
                f"処理中: {filename} ({processed}/{total_files})"
            )
            root.update_idletasks()

            file_mtime = os.path.getmtime(file_path)

            if (current_time - file_mtime) < threshold_seconds:
                continue

            name_without_ext, ext = os.path.splitext(filename)
            ext = ext.lower()
            filename_lower = filename.lower()

            if delete_zip and ext == ".zip":
                corresponding_dir = os.path.join(
                    target_dir,
                    name_without_ext
                )

                if (
                    os.path.exists(corresponding_dir)
                    and os.path.isdir(corresponding_dir)
                ):
                    status_var.set(
                        f"[ZIP削除] {filename} ({processed}/{total_files})"
                    )
                    root.update_idletasks()

                    send2trash.send2trash(file_path)

                    log_message(
                        f"[ゴミ箱] 解凍済みZIPを移動しました: {filename}",
                        log_file_path
                    )

                    counts["trash_zip"] += 1
                    continue

            if delete_exe and ext in [".exe", ".msi"]:

                if any(
                    keyword in filename_lower
                    for keyword in ["setup", "installer", "install"]
                ):

                    status_var.set(
                        f"[インストーラー削除] {filename} ({processed}/{total_files})"
                    )
                    root.update_idletasks()

                    send2trash.send2trash(file_path)

                    log_message(
                        f"[ゴミ箱] インストーラーを移動しました: {filename}",
                        log_file_path
                    )

                    counts["trash_exe"] += 1
                    continue

            moved = False

            for category, extensions in file_types.items():

                if ext in extensions:

                    status_var.set(
                        f"[仕分け] {filename} → {category} ({processed}/{total_files})"
                    )
                    root.update_idletasks()

                    dest_dir = os.path.join(target_dir, category)
                    os.makedirs(dest_dir, exist_ok=True)

                    dest_file_path = os.path.join(dest_dir, filename)

                    counter = 1
                    new_filename = filename

                    while os.path.exists(dest_file_path):
                        new_filename = (
                            f"{name_without_ext}_copy{counter}{ext}"
                        )
                        dest_file_path = os.path.join(
                            dest_dir,
                            new_filename
                        )
                        counter += 1

                    shutil.move(file_path, dest_file_path)

                    log_message(
                        f"[仕分け] {filename} -> {category}/{new_filename}",
                        log_file_path
                    )

                    counts["moved"] += 1
                    moved = True
                    break

            if not moved:

                status_var.set(
                    f"[仕分け] {filename} → Others ({processed}/{total_files})"
                )
                root.update_idletasks()

                dest_dir = os.path.join(target_dir, "Others")
                os.makedirs(dest_dir, exist_ok=True)

                dest_file_path = os.path.join(dest_dir, filename)

                counter = 1
                new_filename = filename

                while os.path.exists(dest_file_path):
                    new_filename = (
                        f"{name_without_ext}_copy{counter}{ext}"
                    )
                    dest_file_path = os.path.join(
                        dest_dir,
                        new_filename
                    )
                    counter += 1

                shutil.move(file_path, dest_file_path)

                log_message(
                    f"[仕分け] {filename} -> Others/{new_filename}",
                    log_file_path
                )

                counts["moved"] += 1

        for dirname in os.listdir(target_dir):

            dir_path = os.path.join(target_dir, dirname)

            if (
                os.path.isdir(dir_path)
                and dirname not in file_types.keys()
                and dirname != "Others"
            ):

                try:
                    if len(os.listdir(dir_path)) == 0:

                        status_var.set(
                            f"[空フォルダ掃除] {dirname}"
                        )
                        root.update_idletasks()

                        os.rmdir(dir_path)

                        log_message(
                            f"[お掃除] 空のフォルダを削除しました: {dirname}",
                            log_file_path
                        )

                        counts["empty_dir"] += 1

                except Exception:
                    pass

        progress_var.set(100)
        status_var.set("処理完了")
        root.update_idletasks()

        log_message("=== 処理が完了しました ===\n", log_file_path)

        result_msg = (
            f"処理が完了しました！\n\n"
            f"・仕分けたファイル: {counts['moved']} 個\n"
            f"・ゴミ箱に送った解凍済ZIP: {counts['trash_zip']} 個\n"
            f"・ゴミ箱に送ったインストーラー: {counts['trash_exe']} 個\n"
            f"・削除した空フォルダ: {counts['empty_dir']} 個\n\n"
            f"※詳細は sort_log.txt をご覧ください。"
        )

        messagebox.showinfo("完了", result_msg)

    finally:
        run_button.config(state="normal")


def start_gui():
    root = tk.Tk()
    root.title("自動ファイル仕分けツール")
    root.geometry("550x450")
    root.resizable(False, False)

    folder_path_var = tk.StringVar()
    zip_clean_var = tk.BooleanVar(value=False)
    exe_clean_var = tk.BooleanVar(value=False)
    period_var = tk.StringVar(value="86400")

    progress_var = tk.DoubleVar(value=0)
    status_var = tk.StringVar(value="待機中")

    def select_folder():
        folder = filedialog.askdirectory()
        if folder:
            folder_path_var.set(folder)

    frame_dir = tk.LabelFrame(root, text="1. 対象フォルダ")
    frame_dir.pack(fill="x", padx=15, pady=10)

    tk.Entry(
        frame_dir,
        textvariable=folder_path_var
    ).pack(side="left", fill="x", expand=True, padx=5)

    tk.Button(
        frame_dir,
        text="参照",
        command=select_folder
    ).pack(side="right", padx=5)

    frame_period = tk.LabelFrame(root, text="2. 経過期間")
    frame_period.pack(fill="x", padx=15, pady=5)

    periods = [
        ("すべて", "0"),
        ("1日", "86400"),
        ("1週間", "604800"),
        ("1か月", "2592000"),
        ("半年", "15552000"),
        ("1年", "31536000")
    ]

    for i, (label, val) in enumerate(periods):
        tk.Radiobutton(
            frame_period,
            text=label,
            variable=period_var,
            value=val
        ).grid(row=i // 3, column=i % 3, sticky="w", padx=10)

    frame_opt = tk.LabelFrame(root, text="3. オプション")
    frame_opt.pack(fill="x", padx=15, pady=10)

    tk.Checkbutton(
        frame_opt,
        text="解凍済みZIPを削除",
        variable=zip_clean_var
    ).pack(anchor="w")

    tk.Checkbutton(
        frame_opt,
        text="setup/install系EXE・MSIを削除",
        variable=exe_clean_var
    ).pack(anchor="w")

    ttk.Progressbar(
        root,
        variable=progress_var,
        maximum=100
    ).pack(fill="x", padx=15, pady=10)

    tk.Label(
        root,
        textvariable=status_var,
        anchor="w"
    ).pack(fill="x", padx=15)

    def on_run():
        progress_var.set(0)

        execute_sorting(
            folder_path_var.get(),
            zip_clean_var.get(),
            exe_clean_var.get(),
            int(period_var.get()),
            progress_var,
            status_var,
            root,
            btn_run
        )

    btn_run = tk.Button(
        root,
        text="仕分けと掃除を実行する",
        height=2,
        command=on_run
    )
    btn_run.pack(fill="x", padx=15, pady=15)

    root.mainloop()


if __name__ == "__main__":
    start_gui()