#!/bin/bash
# create_products_structure.sh

# الألوان للـ output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# التحقق من المسار
if [ ! -d "products" ]; then
    echo -e "${RED}خطأ: يجب تشغيل السكريبت من المجلد الرئيسي للمشروع${NC}"
    exit 1
fi

cd products

# إنشاء المجلد الرئيسي
mkdir -p templates/products
cd templates/products

# قائمة المجلدات
directories=(
    "base"
    "components"
    "includes"
    "modals"
    "ajax"
    "emails"
)

# قائمة الملفات
declare -A files
files[base]="_product_card.html _product_list_item.html _product_grid.html _filters_sidebar.html _sorting_bar.html _pagination.html _breadcrumbs.html _search_bar.html"
files[components]="_product_gallery.html _product_variants.html _product_info.html _product_specs.html _product_tabs.html _price_display.html _stock_status.html _add_to_cart_form.html _review_item.html _review_form.html _review_list.html _rating_stars.html _rating_breakdown.html _share_buttons.html _product_actions.html _quick_view_modal.html"
files[includes]="_related_products.html _recently_viewed.html _product_schema.html _category_sidebar.html _brand_filter.html _price_range_filter.html _active_filters.html _no_products_found.html"
files[modals]="_size_guide_modal.html _360_view_modal.html _notify_modal.html _zoom_modal.html"
files[ajax]="product_quick_view.html load_more_products.html filter_results.html search_suggestions.html"
files[emails]="price_drop_notification.html back_in_stock.html review_approved.html"

# إنشاء المجلدات
for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo -e "${GREEN}✅ تم إنشاء مجلد: $dir${NC}"
    else
        echo -e "${YELLOW}⏭️  المجلد موجود: $dir${NC}"
    fi
done

# إنشاء الملفات في كل مجلد
for dir in "${!files[@]}"; do
    for file in ${files[$dir]}; do
        filepath="$dir/$file"
        if [ ! -f "$filepath" ]; then
            touch "$filepath"
            echo -e "${GREEN}✅ تم إنشاء: $filepath${NC}"
        else
            echo -e "${YELLOW}⏭️  موجود: $filepath${NC}"
        fi
    done
done

# الملفات الرئيسية
main_files=(
    "product_list.html"
    "product_detail.html"
    "category_list.html"
    "category_detail.html"
    "wishlist.html"
    "comparison.html"
    "special_offers.html"
    "advanced_search.html"
    "tag_products.html"
    "_base_product.html"
)

for file in "${main_files[@]}"; do
    if [ ! -f "$file" ]; then
        touch "$file"
        echo -e "${GREEN}✅ تم إنشاء: $file${NC}"
    else
        echo -e "${YELLOW}⏭️  موجود: $file${NC}"
    fi
done

echo -e "\n${GREEN}✅ اكتملت عملية إنشاء البنية!${NC}"
echo -e "${GREEN}📊 إحصائيات:${NC}"
echo -e "   - عدد الملفات الكلي: $(find . -name "*.html" | wc -l)"
echo -e "   - عدد المجلدات: ${#directories[@]}"