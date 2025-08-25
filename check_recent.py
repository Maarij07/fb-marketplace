from core.json_manager import JSONDataManager

jm = JSONDataManager()
products = jm.get_recent_products(10)

print("📋 Recent Products in Dashboard:")
print("=" * 60)
for i, p in enumerate(products):
    title = p.get('title', 'NO TITLE')[:45]
    price = p.get('price', {}).get('amount', '0')
    currency = p.get('price', {}).get('currency', 'SEK')
    added_at = p.get('added_at', 'Unknown')[:19]
    hot_reload = '🔥' if p.get('hot_reload') else ''
    
    print(f"{i+1:2}. {hot_reload} {title}... - {price} {currency} - {added_at}")
