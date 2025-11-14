# baixar_imagens.py
import os
import requests
from ddgs import DDGS
from PIL import Image
from io import BytesIO

from app import db, gerar_nome_imagem, Vinho

# Pasta de destino das imagens
PASTA_IMAGENS = "static/img/vinhos"
os.makedirs(PASTA_IMAGENS, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# ------------------------------------------------------------
# UTILITÁRIOS
# ------------------------------------------------------------

def limpar_url(url):
    return url.split("?")[0]


def inserir_letterbox(img, largura=600, altura=600):
    img.thumbnail((largura, altura), Image.Resampling.LANCZOS)

    fundo = Image.new("RGB", (largura, altura), (255, 255, 255))
    x = (largura - img.width) // 2
    y = (altura - img.height) // 2
    fundo.paste(img, (x, y))

    return fundo


def baixar_imagem(url, caminho):
    try:
        resp = requests.get(limpar_url(url), timeout=10, headers=HEADERS)
        resp.raise_for_status()

        img = Image.open(BytesIO(resp.content))

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        final = inserir_letterbox(img, 600, 600)
        final.save(caminho)

        return True

    except Exception as e:
        print("Erro ao baixar:", e)
        return False


def buscar_imagens_duckduckgo(query, max_results=5):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=max_results))
            return [r["image"] for r in results]
    except Exception as e:
        print("Erro ao buscar imagem:", e)
        return []


# ------------------------------------------------------------
# PROCESSAMENTO AUTOMÁTICO
# ------------------------------------------------------------

def processar_imagem_automatica(vinho):
    print(f"\n📥 Processando imagem para: {vinho.name} ({vinho.vintage})")

    nome_arquivo = gerar_nome_imagem(vinho.name, vinho.vintage)
    caminho = os.path.join(PASTA_IMAGENS, nome_arquivo)

    # Se já existe
    if os.path.exists(caminho):
        vinho.image_path = nome_arquivo
        db.session.commit()
        print(f"✔ Imagem já existia")
        return

    query = f"{vinho.name} {vinho.vintage} wine bottle"
    urls = buscar_imagens_duckduckgo(query)

    if not urls:
        print("⚠ Nenhuma imagem encontrada.")
        return

    for url in urls:
        print(f"➡ Tentando baixar: {url}")
        if baixar_imagem(url, caminho):
            vinho.image_path = nome_arquivo
            db.session.commit()
            print(f"✅ Imagem salva: {nome_arquivo}")
            return
        print("⚠ Falhou, tentando outra...")

    print("❌ Nenhuma imagem baixada.")


# ------------------------------------------------------------
# LISTENER AUTOMÁTICO DO SQLALCHEMY
# ------------------------------------------------------------

from sqlalchemy import event

@event.listens_for(Vinho, "after_insert")
def vinho_inserido(mapper, connection, vinho):
    print(f"\n🔔 Novo vinho detectado: {vinho.name}")
    processar_imagem_automatica(vinho)
