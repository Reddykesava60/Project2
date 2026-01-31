'use client';

import type { MenuCategory, MenuItem } from '@/lib/types';
import { MenuItemCard } from './menu-item-card';

interface MenuCategorySectionProps {
  category: MenuCategory;
  vegFilter?: 'all' | 'veg' | 'non-veg';
}

export function MenuCategorySection({ category, vegFilter = 'all' }: MenuCategorySectionProps) {
  const filteredItems = category.items.filter((item) => {
    if (!item.is_available) return false;
    // Don't hide 0 stock items - show badge instead
    // if (item.stock_quantity === 0) return false;

    if (vegFilter === 'veg') return item.is_vegetarian;
    if (vegFilter === 'non-veg') return !item.is_vegetarian;
    return true;
  });

  if (filteredItems.length === 0) {
    return null;
  }

  return (
    <section>
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-foreground">{category.name}</h2>
        {category.description && (
          <p className="mt-1 text-sm text-muted-foreground">{category.description}</p>
        )}
      </div>
      <div className="grid gap-4">
        {filteredItems.map((item) => (
          <MenuItemCard key={item.id} item={item} />
        ))}
      </div>
    </section>
  );
}
