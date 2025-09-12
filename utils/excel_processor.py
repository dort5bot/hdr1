# utils/excel_processor.py - ÇALIŞAN VERSİYON
import pandas as pd
import datetime
import os
import logging
import re
from config import TURKISH_CITIES, groups, TEMP_DIR

logger = logging.getLogger(__name__)

def normalize_text(text):
    """Metni normalize et: büyük harf, Türkçe karakter düzeltme"""
    if pd.isna(text):
        return ""
    
    text_str = str(text).strip().upper()
    
    turkish_chars = {
        'İ': 'I', 'Ğ': 'G', 'Ü': 'U', 'Ş': 'S', 'Ö': 'O', 'Ç': 'C',
        'ı': 'I', 'ğ': 'G', 'ü': 'U', 'ş': 'S', 'ö': 'O', 'ç': 'C'
    }
    
    for old, new in turkish_chars.items():
        text_str = text_str.replace(old, new)
    
    text_str = re.sub(r'\s+', ' ', text_str).strip()
    return text_str

async def process_excel_files() -> dict:
    """Process all Excel files in temp directory and group by cities"""
    results = {}
    
    for filename in os.listdir(TEMP_DIR):
        if not filename.lower().endswith(('.xlsx', '.xls')):
            continue
            
        filepath = os.path.join(TEMP_DIR, filename)
        
        try:
            df = pd.read_excel(filepath)
            city_column = find_city_column_advanced(df, filename)
            if not city_column:
                continue
            
            process_rows_advanced(df, city_column, results, filename)
        
        except Exception as e:
            logger.error(f"{filename} işlenirken hata: {e}")
    
    return results

def find_city_column_advanced(df, filename):
    """Gelişmiş şehir sütunu bulma"""
    for col in df.columns:
        col_normalized = normalize_text(col)
        
        city_keywords = ['SEHIR', 'CITY', 'IL', 'LOCATION', 'CITY_NAME', 'ILLER', 'PROVINCE', 'SEHIRLER', 'ILCE', 'DISTRICT', 'YER']
        if any(keyword in col_normalized for keyword in city_keywords):
            return col
        
        if any(normalize_text(city) in col_normalized for city in TURKISH_CITIES):
            return col
    
    for col in df.columns:
        try:
            city_count = 0
            for i in range(min(20, len(df))):
                cell_value = str(df.iloc[i][col]) if pd.notna(df.iloc[i][col]) else ""
                cell_normalized = normalize_text(cell_value)
                
                for city in TURKISH_CITIES:
                    city_normalized = normalize_text(city)
                    if city_normalized and city_normalized in cell_normalized:
                        city_count += 1
                        if city_count >= 3:
                            return col
                        break
                
        except Exception:
            continue
    
    return None

def process_rows_advanced(df, city_column, results, filename):
    """Gelişmiş satır işleme"""
    for index, row in df.iterrows():
        city = row[city_column] if pd.notna(row[city_column]) else ""
        if not city:
            continue
            
        city_str = normalize_text(city)
        
        for group in groups:
            group_iller = [normalize_text(il.strip()) for il in group["iller"].split(",")]
            
            for il in group_iller:
                if il == city_str:
                    if group["no"] not in results:
                        results[group["no"]] = []
                    if filename not in results[group["no"]]:
                        results[group["no"]].append(filename)
                    break

async def create_group_excel(group_no: str, filepaths: list) -> str:
    """Basit ve garantili Excel oluşturma - ÇALIŞAN VERSİYON"""
    try:
        logger.info(f"🔄 create_group_excel başladı: {group_no}")
        
        if not filepaths:
            logger.error("❌ Dosya listesi boş")
            return None
        
        # Tüm dosyaları birleştir
        all_dfs = []
        for filepath in filepaths:
            full_path = os.path.join(TEMP_DIR, filepath)
            if not os.path.exists(full_path):
                logger.error(f"❌ Dosya bulunamadı: {full_path}")
                continue
                
            try:
                df = pd.read_excel(full_path)
                all_dfs.append(df)
                logger.info(f"✅ {filepath} okundu: {len(df)} satır")
            except Exception as e:
                logger.error(f"❌ {filepath} okunamadı: {e}")
                continue
        
        if not all_dfs:
            logger.error("❌ Hiçbir dosya okunamadı")
            return None
        
        # DataFrameleri birleştir
        try:
            combined_df = pd.concat(all_dfs, ignore_index=True)
            logger.info(f"✅ {len(all_dfs)} dosya birleştirildi: {len(combined_df)} satır")
        except Exception as e:
            logger.error(f"❌ DataFrame birleştirme hatası: {e}")
            return None
        
        # Çıktı dosyasını oluştur
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        output_filename = f"{group_no}_{timestamp}.xlsx"
        output_path = os.path.join(TEMP_DIR, output_filename)
        
        # Excel'i kaydet
        try:
            combined_df.to_excel(output_path, index=False, engine='openpyxl')
            logger.info(f"✅ Excel kaydedildi: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"❌ Excel kaydetme hatası: {e}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Beklenmeyen hata: {e}")
        return None
