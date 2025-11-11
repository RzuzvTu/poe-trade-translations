import json
import requests
import time
from datetime import datetime
import os


EN_BASE = "https://www.pathofexile.com/api/trade/data"
TW_BASE = "https://pathofexile.tw/api/trade/data"

def fetch_api(url, max_retries=3):

    for i in range(max_retries):
        try:
            print(f"正在請求: {url}")
            headers = {
                'User-Agent': 'POE-Trade-Translation-Bot/1.0'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            print(f"成功")
            time.sleep(1) 
            return response.json()
        except Exception as e:
            print(f"失敗 (嘗試 {i+1}/{max_retries}): {e}")
            if i < max_retries - 1:
                time.sleep(2)
            else:
                raise
    return None

def build_translation_map(en_data, tw_data):
    translations = {}
    
    if not en_data or not tw_data:
        return translations
    
    if 'result' in en_data and 'result' in tw_data:
        en_items = en_data['result']
        tw_items = tw_data['result']
        
        if isinstance(en_items, list) and isinstance(tw_items, list):

            for i, (en_item, tw_item) in enumerate(zip(en_items, tw_items)):

                if 'entries' in en_item and 'entries' in tw_item:
                    for en_entry, tw_entry in zip(en_item['entries'], tw_item['entries']):
                        if 'text' in en_entry and 'text' in tw_entry:
                            en_text = en_entry['text']
                            tw_text = tw_entry['text']
                            if en_text and tw_text and en_text != tw_text:
                                translations[en_text] = tw_text
                

                if 'text' in en_item and 'text' in tw_item:
                    en_text = en_item['text']
                    tw_text = tw_item['text']
                    if en_text and tw_text and en_text != tw_text:
                        translations[en_text] = tw_text
                
                if 'type' in en_item and 'type' in tw_item:
                    en_type = en_item['type']
                    tw_type = tw_item['type']
                    if en_type and tw_type and en_type != tw_type:
                        translations[en_type] = tw_type
                

                if 'label' in en_item and 'label' in tw_item:
                    en_label = en_item['label']
                    tw_label = tw_item['label']
                    if en_label and tw_label and en_label != tw_label:
                        translations[en_label] = tw_label
    
    return translations

def main():

    print("=" * 60)
    print("POE Trade Translations English to Chinese")
    print("=" * 60)
    print()
    
    all_translations = {}
    endpoints = ['items', 'stats', 'static']
    
    for endpoint in endpoints:
        print(f"\n處理 {endpoint}...")
        print("-" * 40)
        
        try:

            en_url = f"{EN_BASE}/{endpoint}"
            en_data = fetch_api(en_url)
            

            tw_url = f"{TW_BASE}/{endpoint}"
            tw_data = fetch_api(tw_url)
            

            translations = build_translation_map(en_data, tw_data)
            print(f"建立了 {len(translations)} 個翻譯項目")


            all_translations.update(translations)
            
        except Exception as e:
            print(f"處理 {endpoint} 時發生錯誤: {e}")
            continue
    

    os.makedirs('translations', exist_ok=True)
    

    print("\n" + "=" * 60)
    print(f"總共建立了 {len(all_translations)} 個翻譯項目")
    

    output = {
        "version": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "updateTime": datetime.now().isoformat(),
        "count": len(all_translations),
        "translations": all_translations
    }
    
    with open('translations/latest.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("✓ 已儲存到 translations/latest.json")
    

    version_info = {
        "version": output["version"],
        "updateTime": output["updateTime"],
        "count": output["count"]
    }
    with open('translations/version.json', 'w', encoding='utf-8') as f:
        json.dump(version_info, f, ensure_ascii=False, indent=2)
    print("已儲存版本資訊到 translations/version.json")
    
    print("\n完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()