import json

# Load and check JSON data
with open('products.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

products = data['products']
print(f"Total products: {len(products)}")
print("\nFirst 10 titles:")
for i, product in enumerate(products[:10]):
    title = product.get('title', 'NO TITLE')
    print(f"{i+1}: '{title[:60]}'")

# Check for any remaining invalid titles
print("\nLooking for invalid titles:")
invalid_count = 0
for i, product in enumerate(products):
    title = product.get('title', '')
    if not title or title.startswith('SEK') or title == 'Create new listing' or title.replace(',','').isdigit():
        print(f"Invalid title at index {i}: '{title}'")
        invalid_count += 1

if invalid_count == 0:
    print("✅ No invalid titles found!")
else:
    print(f"❌ Found {invalid_count} invalid titles")
