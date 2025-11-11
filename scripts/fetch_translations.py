import json
import requests
import time
from datetime import datetime
import os
import urllib.parse

# --- GGG API 端點 (用於 Stats 和 Static) ---
EN_GGG_BASE = "https://www.pathofexile.com/api/trade/data"
TW_GGG_BASE = "https://pathofexile.tw/api/trade/data"

# --- RePoE API 端點 (*** 新增 Uniques ***) ---
REPOE_URLS = {
    'en_items': "https://repoe-fork.github.io/base_items.json",
    'zh_items': "https://repoe-fork.github.io/Traditional%20Chinese/base_items.json",
    'en_uniques': "https://repoe-fork.github.io/uniques.json",
    'zh_uniques': "https://repoe-fork.github.io/Traditional%20Chinese/uniques.json"
}

def fetch_api(url, max_retries=3):
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
            sleep_time = 1.0 if "pathofexile" in url else 0.5
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
    en_map, tw_map, translations = {}, {}, {}
    if not en_data or 'result' not in en_data:
        print("警告: 英文 GGG API 資料格式不正確，已跳過 stats。")
        return {}
    if not tw_data or 'result' not in tw_data:
        print("警告: 中文 GGG API 資料格式不正確，已跳過 stats。")
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

def build_repoe_translation_map(en_items_dict, zh_items_dict, item_type_name):
    translations = {}
    if not en_items_dict or not isinstance(en_items_dict, dict):
        print(f"警告: 英文 RePoE {item_type_name} 資料格式不正確，已跳過。")
        return {}
    if not zh_items_dict or not isinstance(zh_items_dict, dict):
        print(f"警告: 中文 RePoE {item_type_name} 資料格式不正確，已跳過。")
        return {}

    print(f"{item_type_name}: 找到 {len(en_items_dict)} 個英文項目, {len(zh_items_dict)} 個中文項目")
    for item_id, en_data in en_items_dict.items():
        if not isinstance(en_data, dict): continue 
        
        en_name = en_data.get('name')
        
        if item_id in zh_items_dict:
            zh_data = zh_items_dict[item_id]
            if not isinstance(zh_data, dict): continue 
            
            # RePoE 的 uniques.json 中文檔案可能沒有 'name'，而是 'translations'
            zh_name = zh_data.get('name')
            if not zh_name and 'translations' in zh_data:
                zh_name = zh_data['translations'].get('zh-TW')

            if en_name and zh_name and en_name.strip() and zh_name.strip() and en_name != zh_name:
                translations[en_name] = zh_name
                
    return translations


def main():
    print("=" * 60)
    print("POE Trade Translations (產生 英->中 和 中->英)")
    print("=" * 60)
    
    all_translations_en_to_zh = {}
    
    try:
        for endpoint in ['stats', 'static']:
            print(f"\n處理 GGG API {endpoint} (ID 配對)...")
            en_url = f"{EN_GGG_BASE}/{endpoint}"
            tw_url = f"{TW_GGG_BASE}/{endpoint}"
            en_data, tw_data = fetch_api(en_url), fetch_api(tw_url)
            stats_translations = build_ggg_stats_translation_map(en_data, tw_data)
            print(f"建立了 {len(stats_translations)} 個翻譯項目 (來自 {endpoint})")
            all_translations_en_to_zh.update(stats_translations)
            
        print(f"\n處理 RePoE Base Items (ID 配對)...")
        en_items_data = fetch_api(REPOE_URLS['en_items'])
        zh_items_data = fetch_api(REPOE_URLS['zh_items'])
        item_translations = build_repoe_translation_map(en_items_data, zh_items_data, "Base Items")
        print(f"建立了 {len(item_translations)} 個翻譯項目 (來自 RePoE Base Items)")
        all_translations_en_to_zh.update(item_translations)

        print(f"\n處理 RePoE Uniques (ID 配對)...")
        en_uniques_data = fetch_api(REPOE_URLS['en_uniques'])
        zh_uniques_data = fetch_api(REPOE_URLS['zh_uniques'])
        unique_translations = build_repoe_translation_map(en_uniques_data, zh_uniques_data, "Uniques")
        print(f"建立了 {len(unique_translations)} 個翻譯項目 (來自 RePoE Uniques)")
        all_translations_en_to_zh.update(unique_translations)


    except Exception as e:
        print(f"\n" + "!" * 60)
        print(f"處理過程中發生嚴重錯誤: {e}")
        print("!" * 60)
        return 

    print("\n" + "=" * 60)
    print("步驟 4: 產生正向與反向字典...")
    
    os.makedirs('translations', exist_ok=True)
    
    sorted_en_to_zh = dict(sorted(all_translations_en_to_zh.items()))
    print(f"總共建立了 {len(sorted_en_to_zh)} 個 (英->中) 翻譯項目")
    
    all_translations_zh_to_en = {}
    for en, zh in all_translations_en_to_zh.items():
        if zh and zh.strip():
            all_translations_zh_to_en[zh] = en
            
    sorted_zh_to_en = dict(sorted(all_translations_zh_to_en.items()))
    print(f"總共建立了 {len(sorted_zh_to_en)} 個 (中->英) 翻譯項目")

    now = datetime.now()
    version_str = now.strftime("%Y%m%d_%H%M%S")
    time_str = now.isoformat()

    output_en_to_zh = {
        "version": version_str, "updateTime": time_str,
        "count": len(sorted_en_to_zh), "translations": sorted_en_to_zh
    }
    with open('translations/latest.json', 'w', encoding='utf-8') as f:
        json.dump(output_en_to_zh, f, ensure_ascii=False, indent=2)
    print("✓ 已儲存到 translations/latest.json")
    
    output_zh_to_en = {
        "version": version_str, "updateTime": time_str,
        "count": len(sorted_zh_to_en), "translations": sorted_zh_to_en
    }
    with open('translations/latest_reverse.json', 'w', encoding='utf-8') as f:
        json.dump(output_zh_to_en, f, ensure_ascii=False, indent=2)
    print("✓ 已儲存到 translations/latest_reverse.json")
    
    print("\n完成！")

if __name__ == "__main__":
    main()