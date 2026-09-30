"""
Crea una copia "scansionata" delle pratiche demo: ogni pagina diventa un'immagine
leggermente ruotata e rumorosa, senza testo selezionabile, come un documento
recuperato con l'accesso agli atti. I ground_truth.json restano gli stessi.

Serve a misurare gli estrattori sul caso reale più difficile.

Uso (richiede pymupdf e pillow, solo per generare):
    pip install pymupdf pillow
    python backend/scripts/genera_scansioni.py
"""
import random
import shutil
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]


def scansiona(src: Path, dst: Path, rng: random.Random):
    pagine = []
    for page in pymupdf.open(src):
        pix = page.get_pixmap(dpi=150, colorspace=pymupdf.csGRAY)
        img = Image.frombytes("L", (pix.width, pix.height), pix.samples)
        img = img.rotate(rng.uniform(-1.2, 1.2), resample=Image.BICUBIC, expand=False, fillcolor=255)
        rumore = Image.effect_noise(img.size, 18)
        img = Image.blend(img, rumore, 0.08).filter(ImageFilter.GaussianBlur(0.4))
        pagine.append(img)
    pagine[0].save(dst, "PDF", resolution=150, save_all=True, append_images=pagine[1:], quality=60)


def main(src_dir: Path, dst_dir: Path):
    rng = random.Random(42)
    for folder in sorted(src_dir.glob("P-*")):
        out = dst_dir / folder.name
        out.mkdir(parents=True, exist_ok=True)
        shutil.copy(folder / "ground_truth.json", out / "ground_truth.json")
        for pdf in sorted(folder.glob("*.pdf")):
            scansiona(pdf, out / pdf.name, rng)
        print(f"{folder.name}: scansionata")


if __name__ == "__main__":
    src = ROOT / "demo_data" / "pratiche"
    dst = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "demo_data" / "pratiche_scansionate"
    main(src, dst)
