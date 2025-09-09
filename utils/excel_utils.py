#utils/excel_utils.py
import pandas as pd
import os
import datetime
import json

# Grup tanımları data/groups.json içinde olacak
GROUPS_FILE = os.path.join("data", "groups.json")
TEMP_DIR = os.path.join("data", "temp")

# Geçici klasör yoksa oluştur
os.makedirs(TEMP_DIR, exist_ok=True)


def load_groups():
    """Grupları JSON'dan yükler"""
    with open(GROUPS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_il_column(df: pd.DataFrame):
    """Excel içindeki il sütununu bulur"""
    for col in df.columns:
        if "il" in col.lower():  # örn: "İL", "il", "Il", "il adı"
            return col
    raise ValueError("Excel dosyasında il sütunu bulunamadı!")


def process_excel(input_file: str):
    """
    Excel dosyasını gruplara göre ayırır ve yeni dosyalar üretir.
    Geriye: {grup_adi: dosya_yolu} döner.
    """
    df = pd.read_excel(input_file)

    # İl sütununu bul
    il_col = detect_il_column(df)

    # Satırların başına il bilgisi eklenecek (standart hale getirme)
    df[il_col] = df[il_col].astype(str).str.strip().str.upper()

    # Grupları yükle
    groups = load_groups()

    output_files = {}

    for group in groups:
        group_name = group["name"]
        group_cities = [c.upper() for c in group["cities"]]
        group_email = group["email"]

        # İlgili illeri filtrele
        group_df = df[df[il_col].isin(group_cities)]

        if not group_df.empty:
            # Sütun sırasını ayarla: İL en başa
            cols = [il_col] + [c for c in df.columns if c != il_col]
            group_df = group_df[cols]

            # Dosya adı oluştur
            now = datetime.datetime.now()
            timestamp = now.strftime("%m%d_%H%M")  # örn: 0910_1054
            filename = f"{group_name.capitalize()}_{timestamp}.xlsx"
            filepath = os.path.join(TEMP_DIR, filename)

            # Excel kaydet
            group_df.to_excel(filepath, index=False)

            # Çıktıya ekle
            output_files[group_name] = {
                "file": filepath,
                "email": group_email,
                "rows": len(group_df),
            }

    return output_files
