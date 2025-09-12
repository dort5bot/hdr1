# utils/excel_processor.py - TAMAMEN YENİ VERSİYON
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
    
    # String'e çevir ve temizle
    text_str = str(text).strip().upper()
    
    # Türkçe karakterleri düzelt
    turkish_chars = {
        'İ': 'I', 'Ğ': 'G', 'Ü': 'U', 'Ş': 'S', 'Ö': 'O', 'Ç': 'C',
        'ı': 'I', 'ğ': 'G', 'ü': 'U', 'ş': 'S', 'ö': 'O', 'ç': 'C'
    }
    
    for old, new in turkish_chars.items():
        text_str = text_str.replace(old, new)
    
    # Fazla boşlukları temizle
    text_str = re.sub(r'\s+', ' ', text_str).strip()
    
    return text_str

async def process_excel_files() -> dict:
    """Process all Excel files in temp directory and group by cities"""
    results = {}
    
    logger.info(f"Excel işleme başladı. Temp'deki dosyalar: {os.listdir(TEMP_DIR)}")
    
    for filename in os.listdir(TEMP_DIR):
        if not filename.lower().endswith(('.xlsx', '.xls')):
            continue
            
        filepath = os.path.join(TEMP_DIR, filename)
        logger.info(f"Excel işleniyor: {filename}")
        
        try:
            # Read Excel file
            df = pd.read_excel(filepath)
            logger.info(f"Dosya: {filename}, Sütunlar: {list(df.columns)}")
            
            # Find the city column - TÜM SÜTUNLARI DENE
            city_column = find_city_column_advanced(df, filename)
            if not city_column:
                logger.warning(f"{filename} için şehir sütunu bulunamadı")
                continue
            
            # Process each row
            process_rows_advanced(df, city_column, results, filename)
        
        except Exception as e:
            logger.error(f"{filename} işlenirken hata: {e}")
    
    logger.info(f"Excel işleme tamamlandı. Sonuç: {results}")
    return results

def find_city_column_advanced(df, filename):
    """Gelişmiş şehir sütunu bulma - TÜM sütunları dene"""
    # 1. Önce sütun isimlerinde ara
    for col in df.columns:
        col_normalized = normalize_text(col)
        
        # Şehir anahtar kelimeleri (büyük harf)
        city_keywords = ['SEHIR', 'CITY', 'IL', 'LOCATION', 'CITY_NAME', 'ILLER', 'PROVINCE', 'SEHIRLER', 'ILCE', 'DISTRICT', 'YER']
        if any(keyword in col_normalized for keyword in city_keywords):
            logger.info(f"Şehir anahtarlı sütun bulundu: {col}")
            return col
        
        # Sütun isminde şehir ismi ara
        if any(normalize_text(city) in col_normalized for city in TURKISH_CITIES):
            logger.info(f"Şehir isimli sütun bulundu: {col}")
            return col
    
    # 2. Sütun ismi bulunamazsa, TÜM sütunlardaki değerlerde ara
    logger.info(f"Sütun isminde şehir bulunamadı, TÜM sütunlarda değerler aranacak: {filename}")
    
    # Her sütunu kontrol et
    for col in df.columns:
        try:
            # İlk 20 satırı kontrol et
            city_count = 0
            for i in range(min(20, len(df))):
                cell_value = str(df.iloc[i][col]) if pd.notna(df.iloc[i][col]) else ""
                cell_normalized = normalize_text(cell_value)
                
                # Hücrede şehir ismi var mı?
                for city in TURKISH_CITIES:
                    city_normalized = normalize_text(city)
                    if city_normalized and city_normalized in cell_normalized:
                        city_count += 1
                        if city_count >= 3:  # 3'ten fazla şehir bulunduysa
                            logger.info(f"Şehir verisi bulunan sütun: {col} ({city_count} şehir)")
                            return col
                        break
            
            if city_count > 0:
                logger.info(f"{col} sütununda {city_count} şehir bulundu")
                
        except Exception as e:
            logger.warning(f"{col} sütunu kontrol edilirken hata: {e}")
    
    logger.warning(f"Hiçbir sütunda şehir verisi bulunamadı: {filename}")
    return None

def process_rows_advanced(df, city_column, results, filename):
    """Gelişmiş satır işleme - Büyük/küçük harf uyumsuzluğunu çöz"""
    city_count = 0
    matched_cities = set()
    unmatched_cities = set()
    
    for index, row in df.iterrows():
        city = row[city_column] if pd.notna(row[city_column]) else ""
        if not city:
            continue
            
        city_str = normalize_text(city)
        city_count += 1
        
        # Find which group this city belongs to
        city_matched = False
        
        for group in groups:
            group_iller = [normalize_text(il.strip()) for il in group["iller"].split(",")]
            
            for il in group_iller:
                # Normalize edilmiş değerleri karşılaştır
                if il == city_str:
                    if group["no"] not in results:
                        results[group["no"]] = []
                    if filename not in results[group["no"]]:
                        results[group["no"]].append(filename)
                        matched_cities.add(f"{city_str}->{il}")
                    city_matched = True
                    logger.debug(f"Şehir eşleşti: '{city_str}' -> Grup: {group['no']} ({il})")
                    break
            
            if city_matched:
                break
        
        if not city_matched:
            unmatched_cities.add(city_str)
            logger.debug(f"Şehir eşleşmedi: '{city_str}'")
    
    logger.info(f"{filename} işlendi: {city_count} şehir, {len(matched_cities)} eşleşme")
    if matched_cities:
        logger.info(f"Eşleşen şehirler: {sorted(matched_cities)}")
    if unmatched_cities:
        logger.warning(f"Eşleşmeyen şehirler: {sorted(unmatched_cities)}")

#create_group_excel Fonksiyonunu Düzeltelim:
# utils/excel_processor.py - create_group_excel fonksiyonunu GÜNCELLEYELİM
# utils/excel_processor.py - create_group_excel fonksiyonunu GÜNCELLEYELİM
async def create_group_excel(group_no: str, filepaths: list) -> str:
    """Create a combined Excel file for a group"""
    logger.info(f"🔄 create_group_excel CALLED for {group_no} with {len(filepaths)} files")
    
    try:
        # Grup bilgilerini bul
        grup_info = None
        for grup in groups:
            if grup["no"] == group_no:
                grup_info = grup
                break
        
        if not grup_info:
            logger.error(f"❌ Group {group_no} not found in groups")
            return None
            
        logger.info(f"📊 Group info found: {grup_info['name']}")
        
        # Combine all data for this group
        all_dfs = []
        for filepath in filepaths:
            try:
                logger.info(f"📖 Reading file: {filepath}")
                df = pd.read_excel(filepath)
                logger.info(f"✅ Loaded: {os.path.basename(filepath)} - Shape: {df.shape}")
                all_dfs.append(df)
            except Exception as e:
                logger.error(f"❌ Error reading {filepath}: {e}")
                return None
        
        if not all_dfs:
            logger.error("❌ No dataframes to combine")
            return None
            
        # Combine dataframes
        try:
            combined_df = pd.concat(all_dfs, ignore_index=True)
            logger.info(f"✅ Combined dataframe shape: {combined_df.shape}")
        except Exception as e:
            logger.error(f"❌ Error concatenating: {e}")
            return None
        
        # Generate filename
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"{group_no}_{grup_info['name']}_{timestamp}.xlsx"
        filepath = os.path.join(TEMP_DIR, filename)
        
        # Save the combined Excel
        try:
            combined_df.to_excel(filepath, index=False, engine='openpyxl')
            logger.info(f"✅ Excel saved successfully: {filename}")
            return filepath
        except Exception as e:
            logger.error(f"❌ Error saving Excel: {e}")
            return None
        
    except Exception as e:
        logger.error(f"❌ Unexpected error in create_group_excel: {e}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Unexpected error in create_group_excel: {e}")
        return None
