from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)

# Inicializa Firebase
if not firebase_admin._apps:
    try:
        firebase_json = os.environ.get("FIREBASE_CREDENTIALS")
        if firebase_json:
            cred_dict = json.loads(firebase_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase conectado com sucesso")
        else:
            print("❌ FIREBASE_CREDENTIALS não definida")
    except Exception as e:
        print("❌ Erro ao inicializar Firebase:", e)

db = firestore.client()
colecao = 'dbSolicitacoes'

def enviar_email_denuncia(dados_denuncia):
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")
    receiver_email = os.environ.get("EMAIL_RECEIVER") 

    if not all([sender_email, sender_password, receiver_email]):
        print("❌ Variáveis de e-mail não definidas")
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Nova Solicitação de Atendimento"

    body = "Uma nova solicitação foi registrada no sistema:\n\n"
    for key, value in dados_denuncia.items():
        if key == 'dataEnvio' and value == firestore.SERVER_TIMESTAMP:
            body += f"{key}: (definido pelo servidor Firestore)\n"
        else:
            body += f"{key}: {value}\n"

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("✅ E-mail enviado com sucesso")
        return True
    except Exception as e:
        print("❌ Erro ao enviar e-mail:", e)
        return False

@app.route("/api/solicite", methods=["POST"])
def solicite():
    try:
        dados = request.json
        if not dados:
            return jsonify({"status": "erro", "mensagem": "Nenhum dado JSON fornecido"}), 400

        # Adiciona timestamp do servidor
        dados['dataEnvio'] = firestore.SERVER_TIMESTAMP

        # Salva no Firestore
        doc_ref = db.collection(colecao).add(dados)

        # Envia e-mail
        enviar_email_denuncia(dados.copy())

        # Retorna sucesso com ID do documento
        return jsonify({"status": "sucesso", "id": doc_ref[1].id}), 201

    except Exception as e:
        print("❌ Erro ao processar solicitação:", e)
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
