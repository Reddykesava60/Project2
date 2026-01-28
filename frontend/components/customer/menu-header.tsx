'use client';

import type { Restaurant } from '@/lib/types';
import { MapPin, Phone } from 'lucide-react';

interface MenuHeaderProps {
  restaurant: Restaurant;
}

export function MenuHeader({ restaurant }: MenuHeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background">
      <div className="mx-auto max-w-2xl px-4 py-4">
        <div className="flex items-center gap-4">
          {restaurant.logo_url ? (
            <img
              src={restaurant.logo_url || "/placeholder.svg"}
              alt={`${restaurant.name} logo`}
              className="h-14 w-14 rounded-lg object-cover"
            />
          ) : (
            <div className="flex h-14 w-14 items-center justify-center rounded-lg bg-primary text-xl font-bold text-primary-foreground">
              {restaurant.name.charAt(0)}
            </div>
          )}
          <div className="flex-1">
            <h1 className="text-xl font-bold text-foreground">{restaurant.name}</h1>
            {restaurant.description && (
              <p className="mt-0.5 text-sm text-muted-foreground line-clamp-1">
                {restaurant.description}
              </p>
            )}
          </div>
        </div>
        
        {/* Contact Info */}
        {(restaurant.address || restaurant.phone) && (
          <div className="mt-3 flex flex-wrap gap-4 text-sm text-muted-foreground">
            {restaurant.address && (
              <div className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                <span>{restaurant.address}</span>
              </div>
            )}
            {restaurant.phone && (
              <div className="flex items-center gap-1">
                <Phone className="h-4 w-4" />
                <span>{restaurant.phone}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
