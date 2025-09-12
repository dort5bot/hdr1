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
    """Basit ve garantili Excel oluşturma"""
    try:
        logger.info(f"🔄 create_group_excel başladı: {group_no}")
        
        # Sadece ilk dosyayı kullan (test için)
        if not filepaths:
            return None
            
        first_file = filepaths[0]
        if not os.path.exists(first_file):
            return None
        
        # Dosyayı oku
        df = pd.read_excel(first_file)
        
        # Basit bir çıktı dosyası oluştur
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(TEMP_DIR, f"{group_no}_TEST_{timestamp}.xlsx")
        
        # Kaydet
        df.to_excel(output_file, index=False)
        
        logger.info(f"✅ Basit Excel oluşturuldu: {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"❌ Basit Excel oluşturma hatası: {e}")
        return None
