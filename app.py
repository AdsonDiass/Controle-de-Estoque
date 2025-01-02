from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import mysql.connector
from mysql.connector import Error
from babel.numbers import format_currency

app = Flask(__name__)
app.secret_key = "chave-secreta-super-segura"

# Função para conectar ao banco de dados
def conectar_bd():
    try:
        conn = mysql.connector.connect(
            host='localhost',  # Seu host do MySQL
            user='root',       # Seu usuário do MySQL
            password='adson123',  # Sua senha do MySQL
            database='meu_projeto'  # Nome do banco de dados
        )
        if conn.is_connected():
            print("Conectado ao MySQL")
            return conn
        else:
            print("Não foi possível conectar ao MySQL.")
            return None
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

# Função para registrar logs de auditoria no banco
def registrar_log(acao, produto=None):
    # Tenta obter o IP real do cliente
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip = ip.split(',')[0]  # Em caso de múltiplos IPs no cabeçalho, pega o primeiro
    horario = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log = {
        "ip": ip,
        "horario": horario,
        "acao": acao,
        "produto": produto if produto else None
    }

    # Conectar ao banco de dados e salvar log
    conn = conectar_bd()
    if conn is None:
        print("Erro ao tentar registrar o log. Conexão com o banco falhou.")
        return
    
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_logs (ip, horario, acao, produto) VALUES (%s, %s, %s, %s)",
        (log["ip"], log["horario"], log["acao"], log["produto"])
    )
    conn.commit()
    conn.close()

    print(log)  # Imprime no terminal para depuração

# Função para formatar valores como moeda
@app.template_filter('currency')
def format_currency_filter(value, currency='BRL'):
    try:
        # Usando Babel para formatar o valor como moeda
        return format_currency(value, currency, locale='pt_BR')
    except:
        return value  # Retorna o valor original em caso de erro

# Rota de página inicial
@app.route("/")
def home():
    if "user" in session:
        registrar_log("Acesso à página inicial")

        # Conectar ao banco de dados e buscar os produtos
        conn = conectar_bd()
        if conn is None:
            flash("Erro ao conectar ao banco de dados.", "danger")
            return redirect(url_for("login"))

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM produtos")  # Altere conforme o nome da sua tabela
        products = cursor.fetchall()
        conn.close()

        return render_template("home.html", products=products, logged_in=True)  # Passa os produtos recuperados
    return redirect(url_for("login"))

# Rota de login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Verificação de usuário e senha no banco de dados
        conn = conectar_bd()
        if conn is None:
            flash("Erro ao conectar ao banco de dados.", "danger")
            return redirect(url_for("login"))

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and user["senha"] == password:
            session["user"] = username
            flash("Login realizado com sucesso!", "success")
            registrar_log(f"Login realizado por {username}")
            return redirect(url_for("home"))
        else:
            flash("Usuário ou senha inválidos.", "danger")

    return render_template("login.html")

# Rota de logout
@app.route("/logout")
def logout():
    if "user" in session:
        registrar_log(f"Logout realizado por {session['user']}")
    session.pop("user", None)
    flash("Você saiu com sucesso.", "info")
    return redirect(url_for("login"))

# Rota de auditoria
@app.route("/auditoria", methods=["GET", "POST"])
def auditoria():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        senha = request.form.get("password")
        if senha == "0000":  # Senha para visualizar logs de auditoria
            # Conectar ao banco de dados e buscar logs
            conn = conectar_bd()
            if conn is None:
                flash("Erro ao conectar ao banco de dados.", "danger")
                return redirect(url_for("auditoria"))

            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM audit_logs ORDER BY horario DESC")
            audit_logs = cursor.fetchall()
            conn.close()
            return render_template("audit.html", audit_logs=audit_logs)
        else:
            flash("Senha incorreta!", "danger")

    return render_template("audit_login.html")

# Rota para adicionar produto
@app.route("/add-product", methods=["GET", "POST"])
def add_product():
    if "user" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        name = request.form.get("name")
        quantity = int(request.form.get("quantity"))
        price = float(request.form.get("price"))

        # Conectar ao banco de dados e adicionar produto
        conn = conectar_bd()
        if conn is None:
            flash("Erro ao conectar ao banco de dados.", "danger")
            return redirect(url_for("add_product"))

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO produtos (nome, quantidade, preco) VALUES (%s, %s, %s)", 
            (name, quantity, price)
        )
        conn.commit()
        conn.close()

        registrar_log(f"Produto adicionado: {name}, Quantidade: {quantity}, Preço: {price}")
        flash("Produto adicionado com sucesso!", "success")
        return redirect(url_for("home"))
    
    return render_template("add_product.html")

# Rota para excluir produto
@app.route("/delete-product/<int:product_id>")
def delete_product(product_id):
    if "user" not in session:
        return redirect(url_for("login"))

    # Conectar ao banco de dados e excluir produto
    conn = conectar_bd()
    if conn is None:
        flash("Erro ao conectar ao banco de dados.", "danger")
        return redirect(url_for("home"))

    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = %s", (product_id,))
    conn.commit()
    conn.close()

    registrar_log(f"Produto excluído: {product_id}")
    flash("Produto excluído com sucesso!", "success")
    return redirect(url_for("home"))

# Rota para editar produto
@app.route("/edit-product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    if "user" not in session:
        return redirect(url_for("login"))

    # Conectar ao banco de dados e buscar o produto
    conn = conectar_bd()
    if conn is None:
        flash("Erro ao conectar ao banco de dados.", "danger")
        return redirect(url_for("home"))

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM produtos WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if not product:
        flash("Produto não encontrado!", "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("name")
        quantity = int(request.form.get("quantity"))
        price = float(request.form.get("price"))

        # Atualizar produto no banco de dados
        cursor.execute(
            "UPDATE produtos SET nome = %s, quantidade = %s, preco = %s WHERE id = %s", 
            (name, quantity, price, product_id)
        )
        conn.commit()
        conn.close()

        registrar_log(f"Produto editado: {name}, Quantidade: {quantity}, Preço: {price}")
        flash("Produto atualizado com sucesso!", "success")
        return redirect(url_for("home"))

    return render_template("edit_product.html", product=product)

if __name__ == "__main__":
    app.run(debug=True)
