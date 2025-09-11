#handlers/dar_handler.py
from __future__ import annotations

import os
import re
import zipfile
import logging
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

# Load environment
load_dotenv()
TELEGRAM_NAME: str = os.getenv("TELEGRAM_NAME", "xbot")

# Constants
ROOT_DIR = Path(".").resolve()
TELEGRAM_MSG_LIMIT = 4000
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB limit for uploads
HANDLERS_DIR = ROOT_DIR / "handlers"
CACHE_DURATION = 30  # 30 saniye önbellekleme

LOG: logging.Logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# COMMAND INFO
COMMAND_INFO: Dict[str, str] = {
    "dar": "/dar: Dosya tree, /dar k: komut listesi, /dar z:repo zip, /dar t: tüm içerik txt",
    "/kay" : " Kaynak mail adreslerini listeler",
    "/kayek" : " Kaynak mail adresi ekler",
    "/kaysil" : " Kaynak mail adresi siler",
    "/gr" : " Grupları listeler",
    "/grek" : " Yeni grup ekler",
    "/grsil" : " Grup siler",
    "/checkmail" : " Manuel olarak mail kontrolü yapar",
    "/process" : " Sadece Excel işleme yapar (mail kontrolü yapmaz)",
    "/cleanup" : " Temp klasörünü manuel temizler",
    "/stats" : " Bot istatistiklerini gösterir",
    "/proc" : " Excel dosyalarını işler",
    "komut": "tınak_içi_açıklama_ sonrasında VİRGÜL",
}

# 👇 Tek tip isim: router
router = Router(name="dar_handler")


class DarService:
    _instance: Optional["DarService"] = None

    def __new__(cls) -> "DarService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            LOG.debug("DarService: yeni örnek oluşturuldu")
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "initialized"):
            self.root_dir: Path = ROOT_DIR
            self.handlers_dir: Path = HANDLERS_DIR
            self.command_cache: Optional[Dict[str, str]] = None
            self.cache_time: Optional[float] = None
            self.initialized = True
            LOG.debug("DarService: başlatıldı (singleton)")

    def format_tree(self) -> Tuple[str, List[Path]]:
        tree_lines: List[str] = []
        valid_files: List[Path] = []

        def walk(dir_path: Path, prefix: str = "") -> None:
            try:
                items = sorted([p.name for p in dir_path.iterdir()])
            except Exception as e:
                LOG.warning(f"Dizin okunamadı {dir_path}: {e}")
                return

            for i, item in enumerate(items):
                path = dir_path / item
                connector = "└── " if i == len(items) - 1 else "├── "

                if path.is_dir():
                    if item.startswith("__") or (item.startswith(".") and item not in [".gitignore", ".env"]):
                        continue
                    tree_lines.append(f"{prefix}{connector}{item}/")
                    walk(path, prefix + ("    " if i == len(items) - 1 else "│   "))
                else:
                    tree_lines.append(f"{prefix}{connector}{item}")
                    valid_files.append(path)

        walk(self.root_dir)
        return "\n".join(tree_lines), valid_files

    async def scan_handlers_for_commands(self, force_refresh: bool = False) -> Dict[str, str]:
        if (not force_refresh and self.command_cache and self.cache_time and
            (time.time() - self.cache_time) < CACHE_DURATION):
            LOG.debug("Önbellekten komut listesi döndürülüyor")
            return self.command_cache

        self.command_cache = await self._scan_handlers()
        self.cache_time = time.time()
        return self.command_cache

    async def _scan_handlers(self) -> Dict[str, str]:
        commands: Dict[str, str] = {}
        patterns = [
            r'@\w+\.message\(Command\([\'"](\w+)[\'"]\)\)',
            r'Command\([\'"](\w+)[\'"]\)',
        ]

        if not self.handlers_dir.exists():
            LOG.error("Handlers dizini bulunamadı")
            return commands

        for fname in os.listdir(self.handlers_dir):
            if not fname.endswith("_handler.py"):
                continue
            fpath = self.handlers_dir / fname
            try:
                content = await asyncio.to_thread(fpath.read_text, encoding="utf-8")
            except Exception as e:
                LOG.warning(f"{fname} okunamadı: {e}")
                continue

            found_commands = set()
            for pattern in patterns:
                try:
                    matches = re.findall(pattern, content, flags=re.IGNORECASE)
                    found_commands.update(matches)
                except re.error as e:
                    LOG.warning(f"Regex hatası {pattern}: {e}")

            for cmd in found_commands:
                desc = COMMAND_INFO.get(cmd.lower(), "(açıklama yok)")
                commands[f"/{cmd}"] = f"{desc} ({fname})"

        LOG.info(f"{len(commands)} komut bulundu")
        return commands

    def create_zip(self, tree_text: str, valid_files: List[Path]) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = Path(f"{TELEGRAM_NAME}_{timestamp}.zip")
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr("tree.txt", tree_text)
            for fpath in valid_files:
                try:
                    zipf.write(fpath, fpath.relative_to(self.root_dir))
                except Exception as e:
                    LOG.warning(f"Zip eklenemedi {fpath}: {e}")
            for extra in [".env", ".gitignore"]:
                extra_path = self.root_dir / extra
                if extra_path.exists():
                    zipf.write(extra_path, extra)
        return zip_filename

    def create_all_txt(self, valid_files: List[Path]) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_filename = Path(f"{TELEGRAM_NAME}_all_{timestamp}.txt")
        with txt_filename.open("w", encoding="utf-8") as f:
            for fpath in valid_files:
                try:
                    content = fpath.read_text(encoding="utf-8")
                except Exception as e:
                    LOG.warning(f"{fpath} okunamadı: {e}")
                    continue
                f.write(f"\n\n{'='*50}\n{fpath}\n{'='*50}\n\n")
                f.write(content)
        return txt_filename

    async def clear_cache(self) -> None:
        self.command_cache = None
        self.cache_time = None
        LOG.info("Komut önbelleği temizlendi")


def get_dar_service() -> DarService:
    return DarService()


@router.message(Command("dar"))
async def handle_dar_command(message: Message) -> None:
    service = get_dar_service()
    args = message.text.split()[1:] if message.text else []
    mode = args[0].lower() if args else ""
    force_refresh = "f" in args

    try:
        tree_text, valid_files = service.format_tree()

        # /dar k - komut listesi
        if mode == "k":
            scanned = await service.scan_handlers_for_commands(force_refresh=force_refresh)
            if not scanned:
                await message.answer("Komut bulunamadı.")
                return
            lines = [f"{cmd} → {desc}" for cmd, desc in sorted(scanned.items())]
            text = "\n".join(lines)
            if len(text) > TELEGRAM_MSG_LIMIT:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                txt_filename = Path(f"{TELEGRAM_NAME}_commands_{timestamp}.txt")
                txt_filename.write_text(text, encoding="utf-8")
                try:
                    with txt_filename.open("rb") as file:
                        await message.answer_document(document=file, filename=txt_filename.name)
                finally:
                    txt_filename.unlink(missing_ok=True)
            else:
                await message.answer(f"<pre>{text}</pre>", parse_mode="HTML")
            return

        # /dar z - zip gönder
        if mode == "z":
            zip_path = service.create_zip(tree_text, valid_files)
            if zip_path.stat().st_size > MAX_FILE_SIZE:
                await message.answer("⚠️ Zip dosyası çok büyük, gönderilemiyor.")
                zip_path.unlink(missing_ok=True)
                return
            try:
                with zip_path.open("rb") as file:
                    await message.answer_document(document=file, filename=zip_path.name)
            finally:
                zip_path.unlink(missing_ok=True)
            return

        # /dar t - tüm dosyaları txt gönder
        if mode == "t":
            txt_path = service.create_all_txt(valid_files)
            if txt_path.stat().st_size > MAX_FILE_SIZE:
                await message.answer("⚠️ Dosya çok büyük, gönderilemiyor.")
                txt_path.unlink(missing_ok=True)
                return
            try:
                with txt_path.open("rb") as file:
                    await message.answer_document(document=file, filename=txt_path.name)
            finally:
                txt_path.unlink(missing_ok=True)
            return

        # /dar f - cache temizle
        if mode == "f":
            await service.clear_cache()
            await message.answer("✅ Önbellek temizlendi. Tekrar deneyin.")
            return

        # Varsayılan: sadece tree göster
        if len(tree_text) > TELEGRAM_MSG_LIMIT:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            txt_filename = Path(f"{TELEGRAM_NAME}_tree_{timestamp}.txt")
            txt_filename.write_text(tree_text, encoding="utf-8")
            try:
                with txt_filename.open("rb") as file:
                    await message.answer_document(document=file, filename=txt_filename.name)
            finally:
                txt_filename.unlink(missing_ok=True)
        else:
            await message.answer(f"<pre>{tree_text}</pre>", parse_mode="HTML")

    except Exception as e:
        LOG.error(f"Dar komutu işlenirken hata: {e}")
        await message.answer(f"❌ Hata: {str(e)}")


# Handler loader compatibility
async def register_handlers(router_instance: Router):
    """Register handlers with the router - required for handler_loader"""
    router_instance.include_router(router)
