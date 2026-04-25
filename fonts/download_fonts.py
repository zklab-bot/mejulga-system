import urllib.request, os, shutil
BASE = os.path.dirname(__file__)

FONTS = {
    "Lora-Regular.ttf":           "https://github.com/google/fonts/raw/main/ofl/lora/Lora%5Bwght%5D.ttf",
    "Lora-Bold.ttf":              "https://github.com/google/fonts/raw/main/ofl/lora/Lora%5Bwght%5D.ttf",
    "InstrumentSans-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/instrumentsans/InstrumentSans%5Bwdth%2Cwght%5D.ttf",
    "InstrumentSans-Bold.ttf":    "https://github.com/google/fonts/raw/main/ofl/instrumentsans/InstrumentSans%5Bwdth%2Cwght%5D.ttf",
}

for nome, url in FONTS.items():
    dest = os.path.join(BASE, nome)
    if not os.path.exists(dest):
        print(f"Baixando {nome}...")
        urllib.request.urlretrieve(url, dest)
        print(f"  OK: {dest}")

# Italic aliases — mesma fonte variável, sem italic real
for src, dst in [("Lora-Regular.ttf", "Lora-Italic.ttf"),
                 ("Lora-Bold.ttf",    "Lora-BoldItalic.ttf")]:
    dest = os.path.join(BASE, dst)
    if not os.path.exists(dest):
        shutil.copy(os.path.join(BASE, src), dest)
        print(f"  alias: {dst}")
