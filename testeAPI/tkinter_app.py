import requests
import tkinter as tk
from tkinter import messagebox

# Dicionário para armazenar o status de cada número
status_cache = {}

def update_result_label(status):
    """Atualiza o rótulo de resultado com base no status."""
    if status == 'concluido_frios':
        result_label.config(text="Pode ir pegar na tenda de frios!", bg="#42CE8B")
    elif status == 'concluido_cesta':
        result_label.config(text="Pode ir pegar na tenda de cesta!", bg="#42CE8B")
    elif status == 'ja_pegou_frios':
        result_label.config(text="Você já pegou na tenda de frios", bg="#FFFF00")
    elif status == 'ja_pegou_cesta':
        result_label.config(text="Você já pegou na tenda de cesta", bg="#FFFF00")
    else:
        result_label.config(text="Acesso a suprimentos negado", bg="#CE4245")

def validate_number(number, tenda):
    """Valida o número e retorna o status correspondente."""
    try:
        response = requests.post('http://localhost:5000/validate', json={'number': number, 'tenda': tenda})
        if response.status_code == 200:
            result = response.json()
            status = result.get('status', 'erro')
            return status
        else:
            return 'erro'
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return 'erro'

def on_entry_change(tenda):
    """Verifica o número inserido e atualiza o rótulo de resultado."""
    number = entry.get()
    if len(number) >= 4:  # Verifica se há pelo menos 4 dígitos
        if not number.isdigit():
            messagebox.showerror("Erro", "Por favor, insira um número válido.")
            return

        number = int(number)

        # Verifica o status armazenado
        if number in status_cache:
            if (tenda == 'frios' and status_cache[number] == 'concluido_frios') or (tenda == 'cesta' and status_cache[number] == 'concluido_cesta'):
                update_result_label(f'ja_pegou_{tenda}')
                return

        # Valida o número e atualiza o status
        status = validate_number(number, tenda)
        if status in ['concluido_frios', 'ja_pegou_frios', 'concluido_cesta', 'ja_pegou_cesta']:
            status_cache[number] = status

        update_result_label(status)

        # Limpa o campo após submissão
        entry.delete(0, tk.END)

def monitor_entry(tenda):
    """Monitora o campo de entrada e verifica alterações."""
    on_entry_change(tenda)  # Verifica se a entrada tem dígitos suficientes
    root.after(100, lambda: monitor_entry(tenda))  # Agenda a próxima verificação

def setup_gui():
    """Configura a interface gráfica do Tkinter."""
    global result_label, entry, root, tenda_frame, btn_frios, btn_cesta
    root = tk.Tk()
    root.title("Validação de Acesso")

    def on_tenda_button_click(tenda):
        tenda_frame.pack_forget()  # Esconde os botões de escolha da tenda
        entry.pack(pady=10)
        entry.focus()
        # Inicia o monitoramento do campo de entrada
        root.after(100, lambda: monitor_entry(tenda))

    tenda_frame = tk.Frame(root)
    tenda_frame.pack(pady=10)

    btn_frios = tk.Button(tenda_frame, text="Frios", command=lambda: on_tenda_button_click('frios'), font=("Helvetica", 18))
    btn_frios.pack(side=tk.LEFT, padx=10)

    btn_cesta = tk.Button(tenda_frame, text="Cesta de Natal", command=lambda: on_tenda_button_click('cesta'), font=("Helvetica", 18))
    btn_cesta.pack(side=tk.LEFT, padx=10)

    result_label = tk.Label(root, text="", width=50, height=20, font=("Helvetica", 22))
    result_label.pack(pady=20)

    entry = tk.Entry(root, width=10, font=("Helvetica", 24))
    # Ocultar a entrada até que a tenda seja selecionada
    entry.pack_forget()

    root.mainloop()

if __name__ == "__main__":
    setup_gui()
