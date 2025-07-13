from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

app = Flask(__name__)
CORS(app)

if not firebase_admin._apps:
    firebase_config = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if not firebase_config:
        raise ValueError("FIREBASE_CREDENTIALS_JSON não encontrada nas variáveis de ambiente.")
    cred = credentials.Certificate(json.loads(firebase_config))
    firebase_admin.initialize_app(cred)

db = firestore.client()
collection = db.collection("denuncias")

@app.route("/api/denuncia", methods=["POST"])
def receber_denuncia():
    data = request.json
    required_fields = ["crimeType", "location", "description"]
    if not all(field in data and data[field] for field in required_fields):
        return jsonify({"success": False, "error": "Campos obrigatórios ausentes."}), 400

    doc_ref = collection.document()
    doc_ref.set({
        "tipo": data["crimeType"],
        "local": data["location"],
        "descricao": data["description"],
        "anonimo": data.get("anonymous", True),
        "timestamp": firestore.SERVER_TIMESTAMP
    })

    return jsonify({"success": True, "message": "Denúncia registrada com sucesso."})