'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { useAuthStore } from '@/lib/store';
import { menuApi, restaurantApi } from '@/lib/api';
import type { MenuCategory, MenuItem } from '@/lib/types';
import { Button, buttonVariants } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { SkeletonCard, LoadingSpinner } from '@/components/ui/loading-states';
import { ErrorState, EmptyState } from '@/components/ui/error-states';
import {
  Plus,
  Pencil,
  Trash2,
  GripVertical,
  UtensilsCrossed,
  AlertCircle,
  ChevronRight,
} from 'lucide-react';

export default function OwnerMenuPage() {
  const user = useAuthStore((state) => state.user);
  const restaurantId = user?.restaurant_id;

  const [editingCategory, setEditingCategory] = useState<MenuCategory | null>(null);
  const [editingItem, setEditingItem] = useState<{ item: MenuItem; categoryId: string } | null>(null);
  const [isCreatingCategory, setIsCreatingCategory] = useState(false);
  const [isCreatingItem, setIsCreatingItem] = useState<string | null>(null); // categoryId
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [categoryForm, setCategoryForm] = useState({ name: '', description: '' });
  const [itemForm, setItemForm] = useState({
    name: '',
    description: '',
    price: '',
    image_url: '',
    is_available: true,
    is_vegetarian: true,
    is_vegan: false,
    stock_quantity: '',
  });

  const {
    data: menuData,
    error: fetchError,
    isLoading,
    mutate,
  } = useSWR(
    restaurantId ? ['menu', restaurantId] : null,
    () => menuApi.getCategories(restaurantId!)
  );

  // menuApi.getCategories returns MenuCategory[] directly in data
  const categories = (Array.isArray(menuData?.data)
    ? menuData?.data
    : []) as MenuCategory[];

  // Category handlers
  const handleCreateCategory = async () => {
    if (!restaurantId || !categoryForm.name.trim()) return;
    setIsSubmitting(true);
    setError(null);

    const response = await menuApi.createCategory(restaurantId, {
      name: categoryForm.name.trim(),
      description: categoryForm.description.trim() || undefined,
    });

    if (!response.success) {
      setError(response.error || 'Failed to create category');
      setIsSubmitting(false);
      return;
    }

    setCategoryForm({ name: '', description: '' });
    setIsCreatingCategory(false);
    setIsSubmitting(false);
    mutate();
  };

  const handleUpdateCategory = async () => {
    if (!editingCategory || !categoryForm.name.trim()) return;
    setIsSubmitting(true);
    setError(null);

    const response = await menuApi.updateCategory(editingCategory.id, {
      name: categoryForm.name.trim(),
      description: categoryForm.description.trim() || undefined,
    });

    if (!response.success) {
      setError(response.error || 'Failed to update category');
      setIsSubmitting(false);
      return;
    }

    setEditingCategory(null);
    setCategoryForm({ name: '', description: '' });
    setIsSubmitting(false);
    mutate();
  };

  const handleDeleteCategory = async (categoryId: string) => {
    if (!confirm('Delete this category and all its items?')) return;

    const response = await menuApi.deleteCategory(categoryId);
    if (!response.success) {
      alert(response.error || 'Failed to delete category');
      return;
    }
    mutate();
  };

  // Item handlers
  const handleCreateItem = async () => {
    if (!isCreatingItem || !itemForm.name.trim() || !itemForm.price) return;
    setIsSubmitting(true);
    setError(null);

    const response = await menuApi.createItem(isCreatingItem, {
      name: itemForm.name.trim(),
      description: itemForm.description.trim() || undefined,
      price: parseFloat(itemForm.price),
      image_url: itemForm.image_url.trim() || undefined,
      is_available: itemForm.is_available,
      is_vegetarian: itemForm.is_vegetarian,
      is_vegan: itemForm.is_vegan,
      stock_quantity: itemForm.stock_quantity ? parseInt(itemForm.stock_quantity) : null,
    });

    if (!response.success) {
      setError(response.error || 'Failed to create item');
      setIsSubmitting(false);
      return;
    }

    resetItemForm();
    setIsCreatingItem(null);
    setIsSubmitting(false);
    mutate();
  };

  const handleUpdateItem = async () => {
    if (!editingItem || !itemForm.name.trim() || !itemForm.price) return;
    setIsSubmitting(true);
    setError(null);

    const response = await menuApi.updateItem(editingItem.item.id, {
      name: itemForm.name.trim(),
      description: itemForm.description.trim() || undefined,
      price: parseFloat(itemForm.price),
      image_url: itemForm.image_url.trim() || undefined,
      is_available: itemForm.is_available,
      is_vegetarian: itemForm.is_vegetarian,
      is_vegan: itemForm.is_vegan,
      stock_quantity: itemForm.stock_quantity ? parseInt(itemForm.stock_quantity) : null,
    });

    if (!response.success) {
      setError(response.error || 'Failed to update item');
      setIsSubmitting(false);
      return;
    }

    resetItemForm();
    setEditingItem(null);
    setIsSubmitting(false);
    mutate();
  };

  const handleDeleteItem = async (itemId: string) => {
    if (!confirm('Delete this menu item?')) return;

    const response = await menuApi.deleteItem(itemId);
    if (!response.success) {
      alert(response.error || 'Failed to delete item');
      return;
    }
    mutate();
  };

  const handleToggleAvailability = async (item: MenuItem) => {
    const response = await menuApi.toggleAvailability(item.id, !item.is_available);
    if (!response.success) {
      alert(response.error || 'Failed to update availability');
      return;
    }
    mutate();
  };

  const resetItemForm = () => {
    setItemForm({
      name: '',
      description: '',
      price: '',
      image_url: '',
      is_available: true,
      is_vegetarian: true,
      is_vegan: false,
      stock_quantity: '',
    });
  };

  const openEditCategory = (category: MenuCategory) => {
    setEditingCategory(category);
    setCategoryForm({ name: category.name, description: category.description || '' });
  };

  const openEditItem = (item: MenuItem, categoryId: string) => {
    setEditingItem({ item, categoryId });
    setItemForm({
      name: item.name,
      description: item.description || '',
      price: item.price.toString(),
      image_url: item.image_url || '',
      is_available: item.is_available,
      is_vegetarian: item.is_vegetarian || false,
      is_vegan: item.is_vegan || false,
      stock_quantity: item.stock_quantity !== null && item.stock_quantity !== undefined ? item.stock_quantity.toString() : '',
    });
  };

  const openCreateItem = (categoryId: string) => {
    setIsCreatingItem(categoryId);
    resetItemForm();
  };

  if (!restaurantId) {
    return (
      <div className="p-4 lg:p-6">
        <ErrorState title="No Restaurant" message="You are not assigned to a restaurant." />
      </div>
    );
  }

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border bg-background">
        <div className="flex items-center justify-between px-4 py-4 lg:px-6">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Menu Management</h1>
            <p className="text-sm text-muted-foreground">
              {categories.length} categories, {categories.reduce((sum, c) => sum + c.items.length, 0)} items
            </p>
          </div>
          <Button onClick={() => setIsCreatingCategory(true)} className="min-h-[44px]">
            <Plus className="h-4 w-4 mr-2" />
            Add Category
          </Button>
        </div>
      </header>

      <div className="p-4 lg:p-6">
        {isLoading ? (
          <div className="space-y-4">
            <SkeletonCard />
            <SkeletonCard />
          </div>
        ) : fetchError || !menuData?.success ? (
          <ErrorState
            title="Failed to Load Menu"
            message="Unable to fetch menu data."
            onRetry={() => mutate()}
          />
        ) : categories.length === 0 ? (
          <EmptyState
            icon={<UtensilsCrossed className="h-8 w-8 text-muted-foreground" />}
            title="No Categories"
            message="Create your first menu category to get started."
            action={
              <Button onClick={() => setIsCreatingCategory(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Category
              </Button>
            }
          />
        ) : (
          <Accordion type="multiple" className="space-y-4">
            {categories.map((category) => (
              <AccordionItem
                key={category.id}
                value={category.id}
                className="rounded-lg border border-border bg-card"
              >
                <AccordionTrigger className="px-4 py-3 hover:no-underline">
                  <div className="flex flex-1 items-center justify-between pr-2">
                    <div className="flex items-center gap-3">
                      <GripVertical className="h-5 w-5 text-muted-foreground" />
                      <div className="text-left">
                        <p className="font-semibold text-foreground">{category.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {category.items.length} item{category.items.length !== 1 && 's'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div
                        role="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          openEditCategory(category);
                        }}
                        className={cn(
                          buttonVariants({ variant: 'ghost', size: 'sm' }),
                          "min-h-[44px] min-w-[44px] cursor-pointer"
                        )}
                      >
                        <Pencil className="h-4 w-4" />
                      </div>
                      <div
                        role="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteCategory(category.id);
                        }}
                        className={cn(
                          buttonVariants({ variant: 'ghost', size: 'sm' }),
                          "min-h-[44px] min-w-[44px] text-destructive hover:text-destructive cursor-pointer"
                        )}
                      >
                        <Trash2 className="h-4 w-4" />
                      </div>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-4 pb-4">
                  <div className="space-y-3">
                    {category.items.map((item) => (
                      <div
                        key={item.id}
                        className="flex items-center justify-between rounded-lg border border-border bg-background p-3"
                      >
                        <div className="flex items-center gap-3">
                          {item.image_url ? (
                            <img
                              src={item.image_url || "/placeholder.svg"}
                              alt={item.name}
                              className="h-12 w-12 rounded-lg object-cover"
                            />
                          ) : (
                            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted">
                              <UtensilsCrossed className="h-5 w-5 text-muted-foreground" />
                            </div>
                          )}
                          <div>
                            <p className="font-medium text-foreground">{item.name}</p>
                            <p className="text-sm text-primary font-semibold">
                              ${Number(item.price).toFixed(2)}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2">
                            <Label
                              htmlFor={`avail-${item.id}`}
                              className="text-sm text-muted-foreground"
                            >
                              Available
                            </Label>
                            <Switch
                              id={`avail-${item.id}`}
                              checked={item.is_available}
                              onCheckedChange={() => handleToggleAvailability(item)}
                            />
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditItem(item, category.id)}
                            className="min-h-[44px] min-w-[44px]"
                          >
                            <Pencil className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteItem(item.id)}
                            className="min-h-[44px] min-w-[44px] text-destructive hover:text-destructive"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                    <Button
                      variant="outline"
                      onClick={() => openCreateItem(category.id)}
                      className="w-full"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add Item to {category.name}
                    </Button>
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        )}
      </div>

      {/* Category Dialog */}
      <Dialog
        open={isCreatingCategory || !!editingCategory}
        onOpenChange={(open) => {
          if (!open) {
            setIsCreatingCategory(false);
            setEditingCategory(null);
            setCategoryForm({ name: '', description: '' });
            setError(null);
          }
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingCategory ? 'Edit Category' : 'New Category'}
            </DialogTitle>
            <DialogDescription>
              {editingCategory
                ? 'Update the category details'
                : 'Create a new menu category'}
            </DialogDescription>
          </DialogHeader>

          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="cat-name">Name</Label>
              <Input
                id="cat-name"
                value={categoryForm.name}
                onChange={(e) => setCategoryForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="e.g. Main Dishes"
                className="h-12"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="cat-desc">Description (optional)</Label>
              <Textarea
                id="cat-desc"
                value={categoryForm.description}
                onChange={(e) => setCategoryForm((f) => ({ ...f, description: e.target.value }))}
                placeholder="Brief description of this category"
                rows={2}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsCreatingCategory(false);
                setEditingCategory(null);
                setError(null);
              }}
              disabled={isSubmitting}
              className="min-h-[44px]"
            >
              Cancel
            </Button>
            <Button
              onClick={editingCategory ? handleUpdateCategory : handleCreateCategory}
              disabled={isSubmitting || !categoryForm.name.trim()}
              className="min-h-[44px]"
            >
              {isSubmitting ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Saving...
                </>
              ) : editingCategory ? (
                'Update'
              ) : (
                'Create'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Item Dialog */}
      <Dialog
        open={!!isCreatingItem || !!editingItem}
        onOpenChange={(open) => {
          if (!open) {
            setIsCreatingItem(null);
            setEditingItem(null);
            resetItemForm();
            setError(null);
          }
        }}
      >
        <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingItem ? 'Edit Item' : 'New Item'}
            </DialogTitle>
            <DialogDescription>
              {editingItem ? 'Update the menu item details' : 'Create a new menu item'}
            </DialogDescription>
          </DialogHeader>

          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="item-name">Name</Label>
              <Input
                id="item-name"
                value={itemForm.name}
                onChange={(e) => setItemForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="e.g. Grilled Salmon"
                className="h-12"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="item-desc">Description (optional)</Label>
              <Textarea
                id="item-desc"
                value={itemForm.description}
                onChange={(e) => setItemForm((f) => ({ ...f, description: e.target.value }))}
                placeholder="Describe the dish..."
                rows={2}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="item-price">Price ($)</Label>
              <Input
                id="item-price"
                type="number"
                step="0.01"
                min="0"
                value={itemForm.price}
                onChange={(e) => setItemForm((f) => ({ ...f, price: e.target.value }))}
                placeholder="0.00"
                className="h-12"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="item-stock">Stock Quantity</Label>
              <Input
                id="item-stock"
                type="number"
                min="0"
                value={itemForm.stock_quantity}
                onChange={(e) => setItemForm((f) => ({ ...f, stock_quantity: e.target.value }))}
                placeholder="Unlimited"
                className="h-12"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="item-image">Image URL (optional)</Label>
              <Input
                id="item-image"
                type="url"
                value={itemForm.image_url}
                onChange={(e) => setItemForm((f) => ({ ...f, image_url: e.target.value }))}
                placeholder="https://..."
                className="h-12"
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="item-avail">Available for ordering</Label>
              <Switch
                id="item-avail"
                checked={itemForm.is_available}
                onCheckedChange={(checked) =>
                  setItemForm((f) => ({ ...f, is_available: checked }))
                }
              />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="item-nonveg">Non-Vegetarian</Label>
                <p className="text-xs text-muted-foreground">Contains meat or fish</p>
              </div>
              <Switch
                id="item-nonveg"
                checked={!itemForm.is_vegetarian}
                onCheckedChange={(checked) =>
                  setItemForm((f) => ({ ...f, is_vegetarian: !checked, is_vegan: false }))
                }
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsCreatingItem(null);
                setEditingItem(null);
                setError(null);
              }}
              disabled={isSubmitting}
              className="min-h-[44px]"
            >
              Cancel
            </Button>
            <Button
              onClick={editingItem ? handleUpdateItem : handleCreateItem}
              disabled={isSubmitting || !itemForm.name.trim() || !itemForm.price}
              className="min-h-[44px]"
            >
              {isSubmitting ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Saving...
                </>
              ) : editingItem ? (
                'Update'
              ) : (
                'Create'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </main >
  );
}
