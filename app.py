from flask import Flask, request, render_template, redirect, url_for, flash, send_file
import os
import pandas as pd
import random
import time
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "your_secret_key"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Verifica se o arquivo é válido
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Processa o arquivo Excel e realiza análises
def process_excel(file_path):
    try:
        # Lê o Excel
        data = pd.read_excel(file_path)
        
        # Limpando e processando os dados
        data = data.iloc[1:]  # Ignorar cabeçalhos não relevantes
        data.columns = ["Concurso", "Data", "Bola 1", "Bola 2", "Bola 3", "Bola 4", "Bola 5", "Bola 6"]

        # Garantindo que os valores são numéricos e limpando valores inválidos
        for col in ["Concurso", "Bola 1", "Bola 2", "Bola 3", "Bola 4", "Bola 5", "Bola 6"]:
            data[col] = pd.to_numeric(data[col], errors='coerce')  

        # Remove linhas com valores ausentes (NaN)
        data = data.dropna()

        # Determinar o último concurso e o próximo
        last_contest = int(data["Concurso"].max())
        next_contest = last_contest + 1
        
        # Frequência dos números sorteados
        all_balls = pd.concat([data["Bola 1"], data["Bola 2"], data["Bola 3"],
                               data["Bola 4"], data["Bola 5"], data["Bola 6"]])
        frequency = all_balls.value_counts().sort_index()
        
        # Jogo mais provável (6 números mais frequentes)
        most_frequent = [int(num) for num in frequency.sort_values(ascending=False).head(6).index.tolist()]
        
        # Outros jogos prováveis (usando aleatoriedade baseada em frequência)
        other_games = []
        for _ in range(3):  
            game = [int(num) for num in random.sample(frequency.index.tolist(), 6)]
            other_games.append(game)
        
        return {
            "frequency": frequency.to_dict(),
            "most_frequent": most_frequent,
            "other_games": other_games,
            "last_contest": last_contest,
            "next_contest": next_contest
        }
    except Exception as e:
        print(f"Erro ao processar o arquivo: {e}")
        return None

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Nenhum arquivo enviado!')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('Nenhum arquivo selecionado!')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Simula processamento longo
        time.sleep(12)

        # Processar o Excel
        results = process_excel(file_path)
        if results:
            # Salva os dados da análise
            app.config['ANALYSIS_RESULTS'] = results
            return render_template('results.html', results=results)
        else:
            flash('Erro ao processar o arquivo!')
            return redirect(request.url)
    else:
        flash('Formato de arquivo inválido! Use um arquivo .xlsx.')
        return redirect(request.url)

@app.route('/analysis')
def analysis():
    results = app.config.get('ANALYSIS_RESULTS')
    if not results:
        flash('Nenhuma análise disponível. Faça o upload de um arquivo primeiro!')
        return redirect('/')
    
    # Gráfico de Frequência dos Números
    frequency = results['frequency']
    plt.figure(figsize=(10, 6))
    plt.bar(frequency.keys(), frequency.values(), color='green')
    plt.title('Frequência dos Números Sorteados')
    plt.xlabel('Números')
    plt.ylabel('Frequência')
    plt.savefig('static/frequency_plot.png')
    plt.close()

    # Gráfico de Distribuição por Década
    decade_bins = [1, 11, 21, 31, 41, 51, 61]
    labels = ['1-10', '11-20', '21-30', '31-40', '41-50', '51-60']
    numbers = list(frequency.keys())
    bins = pd.cut(numbers, bins=decade_bins, labels=labels, include_lowest=True)
    decade_counts = bins.value_counts()

    plt.figure(figsize=(8, 5))
    plt.bar(labels, decade_counts, color='blue')
    plt.title('Distribuição por Década')
    plt.xlabel('Faixas de Números')
    plt.ylabel('Frequência')
    plt.savefig('static/decade_plot.png')
    plt.close()

    return render_template(
        'analysis.html',
        results=results,
        plot_url='/static/frequency_plot.png',
        decade_plot_url='/static/decade_plot.png'
    )

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
