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
            
            # Find the city column (case insensitive)
            city_column = None
            for col in df.columns:
                if any(city.lower() in col.lower() for city in TURKISH_CITIES):
                    city_column = col
                    break
            
            if not city_column:
                logger.warning(f"No city column found in {filename}")
                continue
            
            # Process each row
            for _, row in df.iterrows():
                city = row[city_column]
                if pd.isna(city):
                    continue
                    
                # Find which group this city belongs to
                for group in groups:
                    if any(c.lower() in str(city).lower() for c in group["cities"]):
                        if group["name"] not in results:
                            results[group["name"]] = []
                        results[group["name"]].append(filepath)
                        break
        
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
    
    return results

async def create_group_excel(group_name: str, filepaths: list) -> str:
    """Create a combined Excel file for a group"""
    try:
        # Combine all data for this group
        all_dfs = []
        for filepath in filepaths:
            df = pd.read_excel(filepath)
            all_dfs.append(df)
        
        if not all_dfs:
            return None
            
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # Generate filename with timestamp
        now = datetime.datetime.now()
        timestamp = now.strftime("%m%d_%H%M")
        filename = f"{group_name}_{timestamp}.xlsx"
        filepath = os.path.join(TEMP_DIR, filename)
        
        # Save the combined Excel
        combined_df.to_excel(filepath, index=False)
        return filepath
        
    except Exception as e:
        logger.error(f"Error creating group Excel for {group_name}: {e}")
        return None