import os
import time
import requests
from ddgs import DDGS
from PIL import Image
from io import BytesIO
from app import app, Vinho, db, gerar_nome_imagem

# Configurações
PASTA_IMAGENS = "static/img/vinhos"
TAMANHO_PADRAO = (600, 600)  # tamanho final fixo sem distorcer
os.makedirs(PASTA_IMAGENS, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


# ---------- Funções ----------

def limpar_url(url):
    """Remove ? e parâmetros finais da URL."""
    return url.split("?")[0]


def inserir_letterbox(img, largura_final=600, altura_final=600):
    """Insere a imagem proporcional dentro de um quadrado sem distorcer."""
    img.thumbnail((largura_final, altura_final), Image.Resampling.LANCZOS)

    fundo = Image.new("RGB", (largura_final, altura_final), (255, 255, 255))
    x = (largura_final - img.width) // 2
    y = (altura_final - img.height) // 2
    fundo.paste(img, (x, y))

    return fundo


def baixar_imagem(url, caminho):
    """Baixa e salva a imagem *sem distorcer* dentro de um quadrado 600x600."""
    try:
        resp = requests.get(limpar_url(url), timeout=10, headers=HEADERS)
        resp.raise_for_status()

        img = Image.open(BytesIO(resp.content))

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img_final = inserir_letterbox(img, 600, 600)
        img_final.save(caminho)

        return True

    except Exception as e:
        print("Erro ao baixar imagem:", e)
        return False


def buscar_imagens_duckduckgo(query, max_results=5):
    """Retorna uma lista de URLs de imagens do DuckDuckGo."""
    urls = []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=max_results))
            urls = [r["image"] for r in results]
    except Exception as e:
        print("Erro na busca:", e)
    return urls


def redimensionar_com_letterbox(caminho):
    """Redimensiona imagem existente com letterbox 600x600 sem distorção."""
    try:
        img = Image.open(caminho)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img_final = inserir_letterbox(img, 600, 600)
        img_final.save(caminho)

        print(f"[AJUSTADA] {caminho}")

    except Exception as e:
        print("Erro ao redimensionar:", e)


def redimensionar_todas_imagens_existentes():
    """Padroniza todas as imagens já salvas."""
    for arquivo in os.listdir(PASTA_IMAGENS):
        caminho = os.path.join(PASTA_IMAGENS, arquivo)
        if os.path.isfile(caminho):
            redimensionar_com_letterbox(caminho)


# ---------- Função principal ----------

def main():
    # Primeiro padroniza todas as imagens antigas
    redimensionar_todas_imagens_existentes()

    vinhos = Vinho.query.all()

    for vinho in vinhos:
        nome_arquivo = gerar_nome_imagem(vinho.name, vinho.vintage)
        caminho_final = os.path.join(PASTA_IMAGENS, nome_arquivo)

        if os.path.exists(caminho_final):
            print(f"[OK] Já existe → {nome_arquivo}")
            continue

        query = f"{vinho.name} {vinho.vintage} wine bottle"

        print(f"\n🔍 Buscando imagem para: {vinho.name} ({vinho.vintage})")

        urls = buscar_imagens_duckduckgo(query)
        if not urls:
            print(f"⚠ Sem resultados para {vinho.name}")
            continue

        sucesso = False
        for url in urls:
            print(f"➡ Tentando baixar: {url}")
            if baixar_imagem(url, caminho_final):
                print(f"✅ Sucesso → {nome_arquivo}")
                sucesso = True
                break
            else:
                print("⚠ Falha, tentando outra imagem...")

        if not sucesso:
            print(f"❌ Não foi possível baixar nenhuma imagem para {vinho.name}")

        time.sleep(1)

    print("\n🏁 Finalizado!")


# ---------- Executar ----------

if __name__ == "__main__":
    with app.app_context():
        main()
