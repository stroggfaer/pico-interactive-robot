import tkinter as tk
import copy

# Начальные размеры сетки для экрана 320x240
GRID_X, GRID_Y = 320 // 25, 240 // 20
PIXEL_SIZE = 50
MARGIN = 20

# Инициализация окна
root = tk.Tk()
root.title("Pixel Art Editor")

# Матрица из 0 и 1
pixel_art = [[0 for _ in range(GRID_X)] for _ in range(GRID_Y)]
# История изменений
history = []
# Указатель текущего состояния в истории
history_index = -1

# Состояние для включения/выключения стирания
eraser_mode = False

def save_to_history():
    """Сохраняет текущее состояние в историю"""
    global history, history_index
    # Удаляем будущие состояния, если они есть
    if history_index < len(history) - 1:
        history = history[:history_index + 1]
    # Добавляем новое состояние
    history.append(copy.deepcopy(pixel_art))
    history_index += 1
    # Ограничиваем размер истории (например, 50 шагов)
    if len(history) > 50:
        history.pop(0)
        history_index -= 1

def undo():
    """Отменяет последнее изменение"""
    global pixel_art, history_index
    if history_index > 0:
        history_index -= 1
        pixel_art = copy.deepcopy(history[history_index])
        draw_grid()

def redo():
    """Повторяет отмененное изменение"""
    global pixel_art, history_index
    if history_index < len(history) - 1:
        history_index += 1
        pixel_art = copy.deepcopy(history[history_index])
        draw_grid()

def import_template():
    """Импортирует предустановленный шаблон"""
    global pixel_art, GRID_X, GRID_Y
    template = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0],
    [0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0],
    [0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0],
    [0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    ]
    # Приводим шаблон к текущему размеру сетки
    pixel_art = [[0 for _ in range(GRID_X)] for _ in range(GRID_Y)]
    for y in range(min(len(template), GRID_Y)):
        for x in range(min(len(template[0]), GRID_X)):
            pixel_art[y][x] = template[y][x]
    save_to_history()
    draw_grid()

def toggle_pixel(x, y):
    """Рисует или стирает пиксель"""
    if 0 <= x < GRID_X and 0 <= y < GRID_Y:
        if eraser_mode:
            pixel_art[y][x] = 0
        else:
            pixel_art[y][x] = 1
        save_to_history()
        draw_grid()

def draw_grid():
    """Перерисовывает сетку"""
    canvas.delete("all")
    for y in range(GRID_Y):
        for x in range(GRID_X):
            color = "black" if pixel_art[y][x] == 1 else "white"
            canvas.create_rectangle(MARGIN + x * PIXEL_SIZE, MARGIN + y * PIXEL_SIZE,
                                  MARGIN + (x + 1) * PIXEL_SIZE, MARGIN + (y + 1) * PIXEL_SIZE,
                                  fill=color, outline="gray",
                                  tags=f"pixel_{x}_{y}")

def save_matrix_consol():
    """Сохраняет текущую матрицу в консоль"""
    for row in pixel_art:
        print(row)

def save_matrix():
    """Сохраняет текущую матрицу в файл .txt с заданной константой"""
    matrix_name = name_entry.get().strip()  # Получаем имя из поля ввода
    if not matrix_name:  # Если поле пустое
        matrix_name = "MY_MATRIX"  # Используем имя по умолчанию

    with open("my_design.txt", "w", encoding="utf-8") as file:
        file.write(f"{matrix_name} = [\n")
        for row in pixel_art:
            row_str = "    [" + ", ".join(str(x) for x in row) + "],"
            file.write(row_str + "\n")
        file.write("]\n")
    print(f"Матрица сохранена в файл my_design.txt как {matrix_name}")


        

def toggle_eraser():
    """Переключает режим стирания"""
    global eraser_mode
    eraser_mode = not eraser_mode
    eraser_button.config(text=f"Режим удаления: {'ON' if eraser_mode else 'OFF'}")

def zoom_in():
    """Увеличивает размер пикселей"""
    global PIXEL_SIZE, GRID_X, GRID_Y
    if PIXEL_SIZE < 100:
        PIXEL_SIZE += 10
        GRID_X = 320 // PIXEL_SIZE
        GRID_Y = 240 // PIXEL_SIZE
        draw_grid()

def zoom_out():
    """Уменьшает размер пикселей"""
    global PIXEL_SIZE, GRID_X, GRID_Y
    if PIXEL_SIZE > 10:
        PIXEL_SIZE -= 10
        GRID_X = 320 // PIXEL_SIZE
        GRID_Y = 240 // PIXEL_SIZE
        draw_grid()

# Создание интерфейса
canvas = tk.Canvas(root, width=(GRID_X * PIXEL_SIZE) + 2 * MARGIN, height=(GRID_Y * PIXEL_SIZE) + 2 * MARGIN)
canvas.pack()

# Привязка событий
canvas.bind("<Button-1>", lambda event: toggle_pixel((event.x - MARGIN) // PIXEL_SIZE, (event.y - MARGIN) // PIXEL_SIZE))

# Фрейм для кнопок и ввода
button_frame = tk.Frame(root)
button_frame.pack()

# Поле ввода названия матрицы
name_label = tk.Label(button_frame, text="Имя матрицы:")
name_label.pack(side=tk.LEFT)

name_entry = tk.Entry(button_frame, width=15)
name_entry.pack(side=tk.LEFT)
name_entry.insert(0, "MY_MATRIX")  # Значение по умолчанию в поле ввода

# Кнопки
button_frame = tk.Frame(root)
button_frame.pack()

save_button = tk.Button(button_frame, text="Сохранить матрицу", command=save_matrix)
save_button.pack(side=tk.LEFT)

eraser_button = tk.Button(button_frame, text="Режим удаления: OFF", command=toggle_eraser)
eraser_button.pack(side=tk.LEFT)

import_button = tk.Button(button_frame, text="Импорт шаблона", command=import_template)
import_button.pack(side=tk.LEFT)

undo_button = tk.Button(button_frame, text="Отменить", command=undo)
undo_button.pack(side=tk.LEFT)

redo_button = tk.Button(button_frame, text="Повторить", command=redo)
redo_button.pack(side=tk.LEFT)

zoom_in_button = tk.Button(button_frame, text="Zoom +", command=zoom_in)
zoom_in_button.pack(side=tk.LEFT)

zoom_out_button = tk.Button(button_frame, text="Zoom -", command=zoom_out)
zoom_out_button.pack(side=tk.LEFT)

# Инициализация
draw_grid()
save_to_history()

root.mainloop()