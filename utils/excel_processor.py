import pandas as pd
import datetime
import os
import logging
from config import TURKISH_CITIES, groups, TEMP_DIR

logger = logging.getLogger(__name__)

async def process_excel_files() -> dict:
    """Process all Excel files in temp directory and group by cities"""
    results = {}
    
    for filename in os.listdir(TEMP_DIR):
        if not any(filename.endswith(ext) for ext in ['.xlsx', '.xls']):
            continue
            
        filepath = os.path.join(TEMP_DIR, filename)
        try:
            # Read Excel file
            df = pd.read_excel(filepath)
            logger.info(f"Processing file: {filename} with columns: {list(df.columns)}")
            
            # Find the city column (case insensitive)
            city_column = None
            for col in df.columns:
                col_lower = col.lower()
                if any(city.lower() in col_lower for city in TURKISH_CITIES):
                    city_column = col
                    break
                elif any(keyword in col_lower for keyword in ['şehir', 'city', 'il', 'location', 'city_name']):
                    city_column = col
                    break
            
            if not city_column:
                logger.warning(f"No city column found in {filename}, trying all columns")
                # Tüm sütunlarda şehir arama
                for col in df.columns:
                    for _, row in df.iterrows():
                        cell_value = str(row[col]) if not pd.isna(row[col]) else ""
                        if any(city.lower() in cell_value.lower() for city in TURKISH_CITIES):
                            city_column = col
                            break
                    if city_column:
                        break
            
            if not city_column:
                logger.warning(f"No city data found in {filename}")
                continue
            
            logger.info(f"Using city column: {city_column}")
            
            # Process each row
            for index, row in df.iterrows():
                city = row[city_column] if not pd.isna(row[city_column]) else ""
                if not city:
                    continue
                    
                # Find which group this city belongs to
                city_str = str(city).strip()
                city_added = False
                
                for group in groups:
                    group_iller = [il.strip() for il in group["iller"].split(",")]
                    for il in group_iller:
                        if il.lower() in city_str.lower():
                            if group["no"] not in results:
                                results[group["no"]] = []
                            if filepath not in results[group["no"]]:
                                results[group["no"]].append(filepath)
                            city_added = True
                            logger.debug(f"City '{city_str}' added to group {group['no']}")
                            break
                    if city_added:
                        break
                
                if not city_added:
                    logger.debug(f"City '{city_str}' not found in any group")
        
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
    
    logger.info(f"Processing completed. Results: {results}")
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
