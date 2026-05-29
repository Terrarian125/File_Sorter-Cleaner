import os
import sys
import shutil
import time
from datetime import datetime


import tkinter as tk
from tkinter import filedialog, messagebox


#ログ出力関数
def log_message(message, log_file_path):
    """日時付きでログファイルにメッセージを出力する関数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(full_message + "\n")


#仕分け＆削除のコアロジック
def execute_sorting(target_dir, delete_zip, delete_exe, threshold_seconds):
    if not target_dir or not os.path.exists(target_dir):
        messagebox.showerror("エラー", "有効なフォルダを選択してください。")
        return

    log_file_path = os.path.join(target_dir, "sort_log.txt")

    file_types = {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
        "Documents": [".pdf", ".docx", ".xlsx", ".txt", ".pptx", ".csv"],
        "Archives": [".zip", ".tar", ".gz", ".rar"]
    }

    counts = {"moved": 0, "trash_zip": 0, "trash_exe": 0, "empty_dir": 0}
    current_time = time.time()

    log_message("=== 自動仕分け・掃除を開始します ===", log_file_path)

    try:
        files = os.listdir(target_dir)
    except Exception as e:
        messagebox.showerror("エラー", f"フォルダの読み込みに失敗しました: {e}")
        return

    for filename in files:
        file_path = os.path.join(target_dir, filename)
        
        if os.path.isdir(file_path) or filename == "sort_log.txt":
            continue
            
        file_mtime = os.path.getmtime(file_path)
        if (current_time - file_mtime) < threshold_seconds:
            continue

        name_without_ext, ext = os.path.splitext(filename)
        ext = ext.lower()
        filename_lower = filename.lower()

        if delete_zip and ext == ".zip":
            corresponding_dir = os.path.join(target_dir, name_without_ext)
            if os.path.exists(corresponding_dir) and os.path.isdir(corresponding_dir):
                send2trash.send2trash(file_path)
                log_message(f"[ゴミ箱] 解凍済みZIPを移動しました: {filename}", log_file_path)
                counts["trash_zip"] += 1
                continue

        if delete_exe and ext in [".exe", ".msi"]:
            if any(keyword in filename_lower for keyword in ["setup", "installer", "install"]):
                send2trash.send2trash(file_path)
                log_message(f"[ゴミ箱] インストーラーを移動しました: {filename}", log_file_path)
                counts["trash_exe"] += 1
                continue

        moved = False
        for category, extensions in file_types.items():
            if ext in extensions:
                dest_dir = os.path.join(target_dir, category)
                os.makedirs(dest_dir, exist_ok=True)
                
                dest_file_path = os.path.join(dest_dir, filename)
                counter = 1
                new_filename = filename
                while os.path.exists(dest_file_path):
                    new_filename = f"{name_without_ext}_copy{counter}{ext}"
                    dest_file_path = os.path.join(dest_dir, new_filename)
                    counter += 1

                shutil.move(file_path, dest_file_path)
                log_message(f"[仕分け] {filename} -> {category}/{new_filename}", log_file_path)
                counts["moved"] += 1
                moved = True
                break
        
        if not moved:
            dest_dir = os.path.join(target_dir, "Others")
            os.makedirs(dest_dir, exist_ok=True)
            
            dest_file_path = os.path.join(dest_dir, filename)
            counter = 1
            new_filename = filename
            while os.path.exists(dest_file_path):
                new_filename = f"{name_without_ext}_copy{counter}{ext}"
                dest_file_path = os.path.join(dest_dir, new_filename)
                counter += 1

            shutil.move(file_path, dest_file_path)
            log_message(f"[仕分け] {filename} -> Others/{new_filename}", log_file_path)
            counts["moved"] += 1

    for dirname in os.listdir(target_dir):
        dir_path = os.path.join(target_dir, dirname)
        if os.path.isdir(dir_path) and dirname not in file_types.keys() and dirname != "Others":
            try:
                if len(os.listdir(dir_path)) == 0:
                    os.rmdir(dir_path)
                    log_message(f"[お掃除] 空のフォルダを削除しました: {dirname}", log_file_path)
                    counts["empty_dir"] += 1
            except Exception:
                pass

    log_message("=== 処理が完了しました ===\n", log_file_path)

    result_msg = (
        f"処理が完了しました！\n\n"
        f"・仕分けたファイル: {counts['moved']} 個\n"
        f"・ゴミ箱に送った解凍済ZIP: {counts['trash_zip']} 個\n"
        f"・ゴミ箱に送ったインストーラー: {counts['trash_exe']} 個\n"
        f"・削除した空フォルダ: {counts['empty_dir']} 個\n\n"
        f"※詳細はフォルダ内の 'sort_log.txt' をご覧ください。"
    )
    messagebox.showinfo("完了", result_msg)


#GUIの構築
def start_gui():
    root = tk.Tk()
    root.title("自動ファイル仕分けツール")
    root.geometry("500x380")
    root.resizable(False, False)

    def select_folder():
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            folder_path_var.set(folder_selected)

    def on_run():
        execute_sorting(
            folder_path_var.get(),
            zip_clean_var.get(),
            exe_clean_var.get(),
            int(period_var.get())
        )

    folder_path_var = tk.StringVar()
    zip_clean_var = tk.BooleanVar(value=False)
    exe_clean_var = tk.BooleanVar(value=False)
    period_var = tk.StringVar(value="86400")

    frame_dir = tk.LabelFrame(root, text=" 1. 対象フォルダを選択 ", padx=10, pady=10)
    frame_dir.pack(fill="x", padx=15, pady=10)

    entry_dir = tk.Entry(frame_dir, textvariable=folder_path_var, width=40)
    entry_dir.pack(side="left", padx=5, expand=True, fill="x")

    btn_browse = tk.Button(frame_dir, text="参照...", command=select_folder)
    btn_browse.pack(side="right", padx=5)

    frame_period = tk.LabelFrame(root, text=" 2. 対象とするファイルの経過期間 ", padx=10, pady=10)
    frame_period.pack(fill="x", padx=15, pady=5)

    periods = [
        ("すべて", "0"),
        ("1日経過", "86400"),
        ("1週間経過", "604800"),
        ("ひと月", "2592000"),
        ("半年", "15552000"),
        ("年", "31536000")
    ]

    for i, (label, val) in enumerate(periods):
        row = i // 3
        col = i % 3
        r_btn = tk.Radiobutton(frame_period, text=label, variable=period_var, value=val)
        r_btn.grid(row=row, column=col, sticky="w", padx=15, pady=5)

    frame_opt = tk.LabelFrame(root, text=" 3. お掃除オプション ", padx=10, pady=10)
    frame_opt.pack(fill="x", padx=15, pady=10)

    chk_zip = tk.Checkbutton(
        frame_opt, 
        text="解凍済みのZIPファイルをゴミ箱へ捨てる (同名フォルダがある場合)", 
        variable=zip_clean_var
    )
    chk_zip.pack(anchor="w", pady=2)

    chk_exe = tk.Checkbutton(
        frame_opt, 
        text="インストーラーをゴミ箱へ捨てる (setup, install等を含む.exe/.msi)", 
        variable=exe_clean_var
    )
    chk_exe.pack(anchor="w", pady=2)

    btn_run = tk.Button(
        root, 
        text="仕分けと掃除を実行する", 
        font=("MS Gothic", 11, "bold"),
        bg="#4CAF50", 
        fg="white", 
        height=2, 
        command=on_run
    )
    btn_run.pack(fill="x", padx=15, pady=10)

    root.mainloop()

if __name__ == "__main__":
    start_gui()