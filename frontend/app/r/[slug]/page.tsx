'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import useSWR from 'swr';
import { restaurantApi } from '@/lib/api';
import { useCartStore } from '@/lib/store';
import type { Restaurant, MenuCategory, MenuItem } from '@/lib/types';
import { LoadingPage } from '@/components/ui/loading-states';
import { ErrorState, NotFoundError } from '@/components/ui/error-states';
import { MenuHeader } from '@/components/customer/menu-header';
import { MenuCategorySection } from '@/components/customer/menu-category';
import { CartFloatingButton } from '@/components/customer/cart-floating-button';

export default function RestaurantMenuPage() {
  const params = useParams();
  const slug = params.slug as string;
  const router = useRouter();
  const { setRestaurant, getItemCount } = useCartStore();
  const [vegFilter, setVegFilter] = useState<'all' | 'veg' | 'non-veg'>('all');

  // Fetch restaurant details
  const {
    data: restaurantData,
    error: restaurantError,
    isLoading: restaurantLoading,
  } = useSWR(
    slug ? `/restaurant/${slug}` : null,
    () => restaurantApi.getBySlug(slug),
    { revalidateOnFocus: false }
  );

  // Fetch menu once we have restaurant
  const restaurant = restaurantData?.data;
  const {
    data: menuData,
    error: menuError,
    isLoading: menuLoading,
  } = useSWR(
    restaurant?.id ? `/menu/${restaurant.id}` : null,
    () => restaurantApi.getMenu(restaurant!.id),
    { revalidateOnFocus: false }
  );

  // Set restaurant in cart store
  useEffect(() => {
    if (restaurant) {
      setRestaurant(restaurant.id, restaurant.slug);
    }
  }, [restaurant, setRestaurant]);

  const categories = menuData?.data || [];
  const itemCount = getItemCount();

  if (restaurantLoading || menuLoading) {
    return <LoadingPage message="Loading menu..." />;
  }

  if (restaurantError || !restaurantData?.success) {
    return (
      <div className="min-h-screen bg-background">
        <NotFoundError resourceName="Restaurant" />
      </div>
    );
  }

  if (!restaurant || !restaurant.is_active) {
    return (
      <div className="min-h-screen bg-background">
        <ErrorState
          title="Restaurant Unavailable"
          message="This restaurant is currently not accepting orders."
        />
      </div>
    );
  }

  if (menuError || !menuData?.success) {
    return (
      <div className="min-h-screen bg-background">
        <ErrorState
          title="Menu Unavailable"
          message="Unable to load the menu. Please try again."
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-background pb-24">
      <MenuHeader restaurant={restaurant} />

      {/* Veg/Non-Veg Filter */}
      <div className="sticky top-14 z-30 bg-background/80 backdrop-blur-md border-b border-border">
        <div className="mx-auto max-w-2xl px-4 py-3 flex gap-2">
          {(['all', 'veg', 'non-veg'] as const).map((filter) => (
            <button
              key={filter}
              onClick={() => setVegFilter(filter)}
              className={`flex-1 h-10 rounded-full text-xs font-bold uppercase tracking-wider transition-all border-2 ${vegFilter === filter
                ? "bg-primary border-primary text-primary-foreground shadow-lg shadow-primary/20 scale-[1.02]"
                : "bg-muted/50 border-transparent text-muted-foreground hover:bg-muted"
                }`}
            >
              {filter === 'veg' ? '🌿 Veg' : filter === 'non-veg' ? '🍗 Non-Veg' : '🍴 All'}
            </button>
          ))}
        </div>
      </div>

      {/* Menu Categories */}
      <div className="mx-auto max-w-2xl px-4 py-6">
        {categories.length === 0 ? (
          <div className="py-12 text-center">
            <p className="text-muted-foreground">No menu items available at this time.</p>
          </div>
        ) : (
          <div className="space-y-8">
            {categories.map((category) => (
              <MenuCategorySection
                key={category.id}
                category={category}
                vegFilter={vegFilter}
              />
            ))}
          </div>
        )}
      </div>

      {/* Floating Cart Button */}
      {itemCount > 0 && (
        <CartFloatingButton
          itemCount={itemCount}
          onClick={() => router.push(`/r/${slug}/checkout`)}
        />
      )}
    </main>
  );
}
