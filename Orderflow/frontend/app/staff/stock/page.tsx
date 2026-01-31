'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { useAuth } from '@/contexts/auth-context';
import { menuApi } from '@/lib/api';
import type { MenuItem } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { SkeletonCard, LoadingSpinner } from '@/components/ui/loading-states';
import { ErrorState, EmptyState } from '@/components/ui/error-states';
import { Search, Package, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';

export default function StaffStockPage() {
    const { user } = useAuth();
    const [searchQuery, setSearchQuery] = useState('');
    const [editingStock, setEditingStock] = useState<MenuItem | null>(null);
    const [newStockQuantity, setNewStockQuantity] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Fetch all items (Staff with can_manage_stock permission receives all items)
    const {
        data: categoriesData,
        error,
        isLoading,
        mutate
    } = useSWR(
        user?.restaurant_id && user.can_manage_stock ? ['staff-menu', user.restaurant_id] : null,
        () => menuApi.getCategories(user!.restaurant_id!)
    );

    // Flatten items for easier searching
    const allItems = categoriesData?.data?.flatMap(cat => cat.items) || [];

    const filteredItems = allItems.filter(item =>
        item.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const handleToggleAvailability = async (item: MenuItem) => {
        // Optimistic Update could go here
        try {
            await menuApi.toggleAvailability(item.id, !item.is_available);
            mutate();
        } catch (err) {
            alert('Failed to update availability');
        }
    };

    const handleUpdateStock = async () => {
        if (!editingStock) return;
        setIsSubmitting(true);

        try {
            const stock = newStockQuantity === '' ? null : parseInt(newStockQuantity);
            await menuApi.updateItem(editingStock.id, {
                stock_quantity: stock
            });
            setEditingStock(null);
            mutate();
        } catch (err) {
            alert('Failed to update stock');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleOpenEdit = (item: MenuItem) => {
        setEditingStock(item);
        setNewStockQuantity(item.stock_quantity === null ? '' : item.stock_quantity.toString());
    };

    if (!user?.can_manage_stock) {
        return (
            <div className="p-4">
                <ErrorState title="Access Denied" message="You do not have permission to manage stock." />
            </div>
        );
    }

    return (
        <div className="min-h-screen pb-20 bg-background">
            <header className="sticky top-0 z-10 bg-background border-b border-border p-4">
                <h1 className="text-xl font-bold mb-4">Stock Control</h1>
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search menu items..."
                        className="pl-9"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
            </header>

            <div className="p-4 space-y-4">
                {isLoading ? (
                    <>
                        <SkeletonCard />
                        <SkeletonCard />
                        <SkeletonCard />
                    </>
                ) : error ? (
                    <ErrorState title="Error" message="Failed to load menu items" onRetry={() => mutate()} />
                ) : filteredItems.length === 0 ? (
                    <EmptyState
                        icon={<Package className="h-8 w-8 text-muted-foreground" />}
                        title="No Items Found"
                        message={searchQuery ? "No items match your search." : "No menu items available."}
                    />
                ) : (
                    filteredItems.map(item => (
                        <Card key={item.id} className="overflow-hidden">
                            <CardContent className="p-4">
                                <div className="flex justify-between items-start gap-4">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <h3 className="font-semibold">{item.name}</h3>
                                            {!item.is_active && <Badge variant="destructive" className="text-[10px] h-5">Inactive</Badge>}
                                        </div>

                                        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                                            <span>Stock:</span>
                                            <Badge variant={item.stock_quantity === 0 ? "destructive" : "secondary"}>
                                                {item.stock_quantity === null ? 'Unlimited' : item.stock_quantity}
                                            </Badge>
                                        </div>
                                    </div>

                                    <Switch
                                        checked={item.is_available}
                                        onCheckedChange={() => handleToggleAvailability(item)}
                                    />
                                </div>

                                <div className="flex gap-2 mt-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="flex-1 h-9"
                                        onClick={() => handleOpenEdit(item)}
                                    >
                                        Adjust Stock
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    ))
                )}
            </div>

            <Dialog open={!!editingStock} onOpenChange={(open) => !open && setEditingStock(null)}>
                <DialogContent className="sm:max-w-xs">
                    <DialogHeader>
                        <DialogTitle>Update Stock</DialogTitle>
                        <DialogDescription>
                            Set stock quantity for {editingStock?.name}
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 py-2">
                        <div className="space-y-2">
                            <Label>Quantity</Label>
                            <Input
                                type="number"
                                placeholder="Leave empty for Unlimited"
                                value={newStockQuantity}
                                onChange={(e) => setNewStockQuantity(e.target.value)}
                            />
                            <p className="text-xs text-muted-foreground">
                                Enter a number or leave blank for unlimited stock.
                            </p>
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setEditingStock(null)}>Cancel</Button>
                        <Button onClick={handleUpdateStock} disabled={isSubmitting}>
                            {isSubmitting ? <LoadingSpinner size="sm" /> : 'Save Update'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
