import json
import requests
import time
from datetime import datetime
import os
import urllib.parse

# --- GGG API 端點 (用於 Stats 和 Static) ---
EN_GGG_BASE = "https://www.pathofexile.com/api/trade/data"
TW_GGG_BASE = "https://pathofexile.tw/api/trade/data"

# --- RePoE API 端點 (用於 Items) ---
REPOE_URLS = {
    'en_items': "https://repoe-fork.github.io/base_items.json",
    'zh_items': "https://repoe-fork.github.io/Traditional%20Chinese/base_items.json"
}


def fetch_api(url, max_retries=3):
    """
    請求 API 並回傳 JSON 資料
    """
    for i in range(max_retries):
        try:
            decoded_url = urllib.parse.unquote(url)
            print(f"正在請求: {decoded_url}")
            headers = {
                'User-Agent': 'POE-Trade-Translation-Bot/1.0 (Contact: your-email@example.com)'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            print(f"成功")

            sleep_time = 1.0 if "pathofexile.com" in url or "pathofexile.tw" in url else 0.5
            time.sleep(sleep_time)
            return response.json()
        except Exception as e:
            print(f"失敗 (嘗試 {i+1}/{max_retries}): {e}")
            if i < max_retries - 1:
                time.sleep(2)
            else:
                raise
    return None

def build_ggg_stats_translation_map(en_data, tw_data):
    """
    (來自版本 2)
    使用 GGG API 的 'id' 欄位來建立 'stats' 和 'static' 端點的翻譯地圖。
    """
    en_map = {}
    tw_map = {}
    translations = {}

    if not en_data or not tw_data or 'result' not in en_data or 'result' not in tw_data:
        return {}

    for category in en_data['result']:
        if 'entries' in category:
            for entry in category['entries']:
                if 'id' in entry and 'text' in entry:
                    en_map[entry['id']] = entry['text']
        if 'id' in category and 'text' in category:
            en_map[category['id']] = category['text']

    for category in tw_data['result']:
        if 'entries' in category:
            for entry in category['entries']:
                if 'id' in entry and 'text' in entry:
                    tw_map[entry['id']] = entry['text']
        if 'id' in category and 'text' in category:
            tw_map[category['id']] = category['text']

    for entry_id, en_text in en_map.items():
        if entry_id in tw_map:
            tw_text = tw_map[entry_id]
            if en_text and tw_text and en_text.strip() and tw_text.strip() and en_text != tw_text:
                translations[en_text] = tw_text
                
    return translations

def build_repoe_items_translation_map(en_items_dict, zh_items_dict):
    """
    (來自版本 3)
    使用 RePoE 的 base_items.json 字典 (dict) 建立翻譯地圖。
    """
    translations = {}
    
    print(f"Items: 找到 {len(en_items_dict)} 個英文項目, {len(zh_items_dict)} 個中文項目")

    for item_id, en_data in en_items_dict.items():
        en_name = en_data.get('name')
        
        if item_id in zh_items_dict:
            zh_data = zh_items_dict[item_id]
            zh_name = zh_data.get('name')
            
            if en_name and zh_name and en_name.strip() and zh_name.strip() and en_name != zh_name:
                translations[en_name] = zh_name
                
    return translations


def main():

    print("=" * 60)
    print("POE Trade Translations English to Chinese (混合策略模式)")
    print("=" * 60)
    print()
    
    all_translations = {}
    
    try:
        for endpoint in ['stats', 'static']:
            print(f"\n處理 GGG API {endpoint} (ID 配對)...")
            print("-" * 40)
            
            en_url = f"{EN_GGG_BASE}/{endpoint}"
            en_data = fetch_api(en_url)
            
            tw_url = f"{TW_GGG_BASE}/{endpoint}"
            tw_data = fetch_api(tw_url)
            
            stats_translations = build_ggg_stats_translation_map(en_data, tw_data)
            print(f"建立了 {len(stats_translations)} 個翻譯項目 (來自 {endpoint})")
            all_translations.update(stats_translations)
            
        print(f"\n處理 RePoE Items (ID 配對)...")
        print("-" * 40)
        
        en_items_data = fetch_api(REPOE_URLS['en_items'])
        zh_items_data = fetch_api(REPOE_URLS['zh_items'])
        
        item_translations = build_repoe_items_translation_map(en_items_data, zh_items_data)
        print(f"建立了 {len(item_translations)} 個翻譯項目 (來自 RePoE items)")
        all_translations.update(item_translations)

    except Exception as e:
        print(f"\n" + "!" * 60)
        print(f"處理過程中發生嚴重錯誤: {e}")
        print("腳本已終止。")
        print("!" * 60)
        return

    print("\n" + "=" * 60)
    print("步驟 3: 儲存翻譯檔案...")
    
    os.makedirs('translations', exist_ok=True)
    
    sorted_translations = dict(sorted(all_translations.items()))
    
    print(f"總共建立了 {len(sorted_translations)} 個翻譯項目")
    
    output = {
        "version": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "updateTime": datetime.now().isoformat(),
        "count": len(sorted_translations),
        "translations": sorted_translations
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