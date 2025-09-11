utils/excel_processor.py

import pandas as pd
import datetime
import os
import logging
from config import TURKISH_CITIES, groups, TEMP_DIR

logger = logging.getLogger(__name__)

async def process_excel_files() -> dict:
    """Process all Excel files in temp directory and group by cities"""
    results = {}
    
    logger.info(f"Excel işleme başladı. Temp'deki dosyalar: {os.listdir(TEMP_DIR)}")
    
    for filename in os.listdir(TEMP_DIR):
        if not any(filename.endswith(ext) for ext in ['.xlsx', '.xls']):
            logger.debug(f"Excel dosyası değil: {filename}")
            continue
            
        filepath = os.path.join(TEMP_DIR, filename)
        logger.info(f"Excel işleniyor: {filename}")
        
        try:
            # Read Excel file
            df = pd.read_excel(filepath)
            logger.info(f"Dosya: {filename}, Sütunlar: {list(df.columns)}")
            logger.info(f"İlk 3 satır:\n{df.head(3)}")
            
            # Find the city column (case insensitive)
            city_column = None
            for col in df.columns:
                col_lower = col.lower()
                if any(city.lower() in col_lower for city in TURKISH_CITIES):
                    city_column = col
                    logger.info(f"Şehir sütunu bulundu: {col}")
                    break
                elif any(keyword in col_lower for keyword in ['şehir', 'city', 'il', 'location', 'city_name', 'iller']):
                    city_column = col
                    logger.info(f"Şehir anahtarlı sütun bulundu: {col}")
                    break
            
            if not city_column:
                logger.warning(f"Şehir sütunu bulunamadı, tüm sütunlar taranacak: {filename}")
                # Tüm sütunlarda şehir arama
                for col in df.columns:
                    for _, row in df.iterrows():
                        cell_value = str(row[col]) if not pd.isna(row[col]) else ""
                        if any(city.lower() in cell_value.lower() for city in TURKISH_CITIES):
                            city_column = col
                            logger.info(f"Şehir verisi bulunan sütun: {col}")
                            break
                    if city_column:
                        break
            
            if not city_column:
                logger.warning(f"{filename} dosyasında hiç şehir verisi bulunamadı")
                continue
            
            logger.info(f"{filename} için kullanılacak şehir sütunu: {city_column}")
            
            # Process each row
            city_count = 0
            for index, row in df.iterrows():
                city = row[city_column] if not pd.isna(row[city_column]) else ""
                if not city:
                    continue
                    
                city_str = str(city).strip()
                city_count += 1
                
                # Find which group this city belongs to
                city_added = False
                
                for group in groups:
                    group_iller = [il.strip() for il in group["iller"].split(",")]
                    for il in group_iller:
                        if il.lower() in city_str.lower():
                            if group["no"] not in results:
                                results[group["no"]] = []
                            if filepath not in results[group["no"]]:
                                results[group["no"]].append(filepath)
                                logger.debug(f"Şehir '{city_str}' -> Grup: {group['no']}")
                            city_added = True
                            break
                    if city_added:
                        break
                
                if not city_added:
                    logger.debug(f"Şehir '{city_str}' hiçbir gruba eklenemedi")
            
            logger.info(f"{filename} işlendi: {city_count} şehir bulundu")
        
        except Exception as e:
            logger.error(f"{filename} işlenirken hata: {e}")
    
    logger.info(f"Excel işleme tamamlandı. Sonuç: {len(results)} grup bulundu")
    return results

async def create_group_excel(group_no: str, filepaths: list) -> str:
    """Create a combined Excel file for a group"""
    try:
        # Grup bilgilerini bul
        grup_info = None
        for grup in groups:
            if grup["no"] == group_no:
                grup_info = grup
                break
        
        if not grup_info:
            logger.error(f"Group {group_no} not found")
            return None
            
        # Combine all data for this group
        all_dfs = []
        for filepath in filepaths:
            try:
                df = pd.read_excel(filepath)
                all_dfs.append(df)
            except Exception as e:
                logger.error(f"Error reading {filepath}: {e}")
        
        if not all_dfs:
            return None
            
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # Generate filename with timestamp and group info
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"{group_no}_{grup_info['ad']}_{timestamp}.xlsx"
        filepath = os.path.join(TEMP_DIR, filename)
        
        # Save the combined Excel
        combined_df.to_excel(filepath, index=False)
        logger.info(f"Group Excel created: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error creating group Excel for {group_no}: {e}")
        return None
