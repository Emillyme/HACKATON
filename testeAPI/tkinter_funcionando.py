import requests
import tkinter as tk
from tkinter import messagebox

def update_result_label(status):
    if status == 'concluido':
        result_label.config(text="Acesso a suprimentos concluído", bg="green")
    elif status == 'pendente':
        result_label.config(text="Acesso a suprimentos pendente", bg="yellow")
    else:
        result_label.config(text="Acesso a suprimentos negado", bg="red")

def validate_number(number):
    try:
        response = requests.post('http://localhost:5000/validate', json={'number': number})
        if response.status_code == 200:
            result = response.json()
            return result.get('status', 'erro')
        else:
            return 'erro'
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return 'erro'

def on_entry_change():
    number = entry.get()
    if len(number) >= 4:  # Check if there are at least 6 digits
        if not number.isdigit():
            messagebox.showerror("Erro", "Por favor, insira um número válido.")
            return

        number = int(number)
        status = validate_number(number)
        update_result_label(status)

        # Limpa o campo após submissão
        entry.delete(0, tk.END)

def monitor_entry():
    on_entry_change()  # Check if the entry has enough digits
    root.after(100, monitor_entry)  # Schedule the next check

def setup_gui():
    global result_label, entry, root
    root = tk.Tk()
    root.title("Validação de Acesso")

    result_label = tk.Label(root, text="", width=40, height=20)
    result_label.pack(pady=30)

    entry = tk.Entry(root, width=30)
    entry.pack(pady=10)

    # Start monitoring the entry field
    root.after(100, monitor_entry)

    root.mainloop()

if __name__ == "__main__":
    setup_gui()
