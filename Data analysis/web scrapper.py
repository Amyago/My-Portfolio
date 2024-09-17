import customtkinter as ctk
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import os
import subprocess
from tkinter import filedialog, messagebox
from threading import Thread

ctk.set_appearance_mode("System")  # Использовать системную тему (темная/светлая)
ctk.set_default_color_theme("blue")  # Тема интерфейса

# Асинхронная функция для загрузки страницы
async def fetch_page(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

def scrape_and_save():
    url = url_entry.get()
    asyncio.run(handle_scraping(url))

async def handle_scraping(url):
    progressbar.set(0.2)
    try:
        page_content = await fetch_page(url)
        progressbar.set(0.6)
    except aiohttp.ClientError as e:
        messagebox.showerror("Ошибка", f"Не удалось получить данные: {e}")
        return

    soup = BeautifulSoup(page_content, 'html.parser')

    if extract_all_var.get():
        body_text = soup.get_text()
    else:
        selected_tags = []
        for tag, var in tag_vars.items():
            if var.get():
                selected_tags.append(tag)

        if not selected_tags:
            messagebox.showwarning("Предупреждение", "Выберите хотя бы один тег для сбора данных.")
            return

        body_text = ""
        for tag in selected_tags:
            elements = soup.find_all(tag)
            for element in elements:
                body_text += element.get_text().strip() + "\n"

    progressbar.set(0.8)
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("JSON files", "*.json")])
    if not file_path:
        return

    try:
        if file_path.endswith('.json'):
            data = {"text": body_text}
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        else:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(body_text)

        progressbar.set(1)
        messagebox.showinfo("Успех", f"Данные сохранены в файл: {file_path}")

        # Автоматическое открытие файла
        if os.name == 'nt':  # Для Windows
            os.startfile(file_path)
        else:  # Для macOS и Linux
            subprocess.run(['open' if os.name == 'posix' else 'xdg-open', file_path])

    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")

def start_scraping():
    # Запуск многопоточного процесса для избежания зависания интерфейса
    Thread(target=scrape_and_save).start()

# Создаем главное окно
root = ctk.CTk()
root.title("Современный Web Scraper")
root.geometry("500x500")

# Элементы интерфейса
url_label = ctk.CTkLabel(root, text="URL:")
url_label.pack(pady=10)

url_entry = ctk.CTkEntry(root, width=400)
url_entry.pack(pady=10)
url_entry.insert(0, 'Введите URL страницы')

# Добавляем флажок "извлечь всю веб-страницу"
extract_all_var = ctk.BooleanVar()
extract_all_check = ctk.CTkCheckBox(root, text="Извлечь всю веб-страницу", variable=extract_all_var)
extract_all_check.pack(pady=10)

# Флажки для выбора тегов
tag_vars = {}
tags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
tag_frame = ctk.CTkFrame(root)
tag_frame.pack(pady=10)

for tag in tags:
    var = ctk.BooleanVar()
    tag_vars[tag] = var
    tag_check = ctk.CTkCheckBox(tag_frame, text=tag, variable=var)
    tag_check.pack(anchor='w')

# Прогресс выполнения
progressbar = ctk.CTkProgressBar(root)
progressbar.pack(pady=10)

# Кнопка для начала парсинга
scrape_button = ctk.CTkButton(root, text="Скачать текст", command=start_scraping)
scrape_button.pack(pady=20)

# Запускаем главный цикл обработки событий
root.mainloop()
