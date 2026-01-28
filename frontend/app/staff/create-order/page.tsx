'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { AppLayout } from '@/components/layout/app-layout'
import { withAuth } from '@/components/auth/with-auth'
import { useAuth } from '@/contexts/auth-context'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { MenuItem, MenuCategory } from '@/types'
import { formatCurrency, cn } from '@/lib/utils'
import { Plus, ShoppingCart, Search, Banknote, ShieldAlert, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react'
import { menuService, MenuItem as APIMenuItem, MenuCategory as APICategory } from '@/lib/api-service'

interface CartItem {
  menuItem: MenuItem
  quantity: number
}

function CreateCashOrderPage() {
  const { user } = useAuth()
  const router = useRouter()
  const [categories, setCategories] = useState<MenuCategory[]>([])
  const [menuItems, setMenuItems] = useState<MenuItem[]>([])
  const [cart, setCart] = useState<CartItem[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successOrderNumber, setSuccessOrderNumber] = useState<string | null>(null)

  // Check if user can collect cash (owners always can, staff need permission)
  const canCollectCash = user?.role === 'restaurant_owner' || user?.can_collect_cash === true

  // Get restaurant ID from user context
  const getRestaurantId = useCallback(() => {
    if (user?.role === 'restaurant_owner' && user?.restaurant_id) {
      return user.restaurant_id
    }
    if (user?.role === 'staff' && user?.restaurant_id) {
      return user.restaurant_id
    }
    return null
  }, [user])

  useEffect(() => {
    const fetchMenu = async () => {
      const restaurantId = getRestaurantId()
      if (!restaurantId) {
        setError('Restaurant not found. Please contact support.')
        setLoading(false)
        return
      }

      try {
        // Fetch categories and items from API
        const [categoriesData, itemsData] = await Promise.all([
          menuService.getCategories(restaurantId),
          menuService.getItems(restaurantId)
        ])

        // Transform API response to component format
        const transformedCategories: MenuCategory[] = categoriesData.map((cat: APICategory) => ({
          id: cat.id,
          name: cat.name,
          restaurantId: cat.restaurant,
          displayOrder: cat.display_order,
          isActive: cat.is_active,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }))

        const transformedItems: MenuItem[] = itemsData
          .filter((item: APIMenuItem) => item.is_available && item.is_active)
          .map((item: APIMenuItem) => ({
            id: item.id,
            name: item.name,
            description: item.description || '',
            price: item.price,
            categoryId: item.category,
            categoryName: item.category_name || '',
            restaurantId: item.restaurant,
            isAvailable: item.is_available,
            timesOrdered: item.times_ordered || 0,
            displayOrder: item.display_order,
            version: 1,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }))

        setCategories(transformedCategories)
        setMenuItems(transformedItems)
      } catch (err) {
        console.error('Error fetching menu:', err)
        setError(err instanceof Error ? err.message : 'Failed to load menu')
      } finally {
        setLoading(false)
      }
    }

    if (canCollectCash) {
      fetchMenu()
    } else {
      setLoading(false)
    }
  }, [canCollectCash, getRestaurantId])

  if (!canCollectCash) {
    return (
      <AppLayout title="Create Order" showBack>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center max-w-md px-4">
            <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-4">
              <ShieldAlert className="w-8 h-8 text-destructive" />
            </div>
            <h2 className="text-xl font-semibold mb-2">Cash Permission Required</h2>
            <p className="text-muted-foreground mb-6">
              You don&apos;t have permission to create cash orders. Only staff members with cash collection permission can perform this action.
            </p>
            <p className="text-sm text-muted-foreground">
              Please contact your restaurant owner to enable cash permissions for your account.
            </p>
          </div>
        </div>
      </AppLayout>
    )
  }

  if (loading) {
    return (
      <AppLayout title="New Order" showBack>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-primary" />
            <p className="mt-4 text-muted-foreground">Loading menu...</p>
          </div>
        </div>
      </AppLayout>
    )
  }

  if (error) {
    return (
      <AppLayout title="New Order" showBack>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center max-w-md px-4">
            <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-8 h-8 text-destructive" />
            </div>
            <h2 className="text-xl font-semibold mb-2">Unable to Load Menu</h2>
            <p className="text-muted-foreground mb-6">{error}</p>
            <Button onClick={() => window.location.reload()}>Try Again</Button>
          </div>
        </div>
      </AppLayout>
    )
  }

  if (successOrderNumber) {
    return (
      <AppLayout title="Order Created" showBack>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center max-w-md px-4">
            <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="w-10 h-10 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Order Created!</h2>
            <p className="text-7xl font-bold text-primary my-6">{successOrderNumber}</p>
            <p className="text-muted-foreground mb-6">
              Cash order has been created successfully.
            </p>
            <div className="flex flex-col gap-3">
              <Button onClick={() => { setSuccessOrderNumber(null); setCart([]) }}>
                Create Another Order
              </Button>
              <Button variant="outline" onClick={() => router.push('/staff/orders')}>
                View All Orders
              </Button>
            </div>
          </div>
        </div>
      </AppLayout>
    )
  }

  const addToCart = (item: MenuItem) => {
    const existingItem = cart.find((cartItem) => cartItem.menuItem.id === item.id)
    if (existingItem) {
      setCart(
        cart.map((cartItem) =>
          cartItem.menuItem.id === item.id
            ? { ...cartItem, quantity: cartItem.quantity + 1 }
            : cartItem
        )
      )
    } else {
      setCart([...cart, { menuItem: item, quantity: 1 }])
    }
  }

  const updateQuantity = (itemId: string, delta: number) => {
    setCart(
      cart
        .map((cartItem) =>
          cartItem.menuItem.id === itemId
            ? { ...cartItem, quantity: cartItem.quantity + delta }
            : cartItem
        )
        .filter((cartItem) => cartItem.quantity > 0)
    )
  }

  const filteredItems = menuItems.filter((item) => {
    if (!item.isAvailable) return false
    if (selectedCategory !== 'all' && item.categoryId !== selectedCategory) return false
    if (searchQuery && !item.name.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false
    }
    return true
  })

  const total = cart.reduce((sum, item) => sum + item.menuItem.price * item.quantity, 0)

  const handleSubmitOrder = async () => {
    if (cart.length === 0 || isSubmitting) return
    
    const restaurantId = getRestaurantId()
    if (!restaurantId) {
      setError('Restaurant not found')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      const response = await fetch('/api/orders/staff/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: JSON.stringify({
          restaurant: restaurantId,
          items: cart.map(item => ({
            menu_item_id: item.menuItem.id,
            quantity: item.quantity,
          })),
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || errorData.detail || 'Failed to create order')
      }

      const orderData = await response.json()
      setSuccessOrderNumber(orderData.order_number)
    } catch (err) {
      console.error('Error creating order:', err)
      setError(err instanceof Error ? err.message : 'Failed to create order')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AppLayout title="New Order" showBack>
      <div className="space-y-5 pb-32">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
          <Input
            placeholder="Search menu..."
            className="pl-12 h-14 text-lg rounded-2xl"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Category Pills */}
        <div className="scroll-container">
          <Button
            variant={selectedCategory === 'all' ? 'default' : 'outline'}
            className="flex-shrink-0 min-h-touch rounded-full px-5"
            onClick={() => setSelectedCategory('all')}
          >
            All
          </Button>
          {categories.map((cat) => (
            <Button
              key={cat.id}
              variant={selectedCategory === cat.id ? 'default' : 'outline'}
              className="flex-shrink-0 min-h-touch rounded-full px-5"
              onClick={() => setSelectedCategory(cat.id)}
            >
              {cat.name}
            </Button>
          ))}
        </div>
        {/* Menu Items Grid */}
        <div className="space-y-3">
          {filteredItems.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-lg text-muted-foreground">No items found</p>
            </div>
          ) : (
            filteredItems.map((item) => {
              const inCart = cart.find(c => c.menuItem.id === item.id)
              return (
                <button
                  key={item.id}
                  onClick={() => addToCart(item)}
                  className={cn(
                    "w-full text-left surface-card p-4 transition-all touch-action-manipulation",
                    inCart && "ring-2 ring-primary"
                  )}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-lg truncate">{item.name}</h3>
                        {inCart && (
                          <Badge className="bg-primary text-primary-foreground">
                            {inCart.quantity} in cart
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{item.description}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <div className="text-xl font-bold text-primary">{formatCurrency(item.price)}</div>
                      <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center mt-2 ml-auto">
                        <Plus className="w-5 h-5 text-primary" />
                      </div>
                    </div>
                  </div>
                </button>
              )
            })
          )}
        </div>
      </div>

      {/* Sticky Cart Footer - Mobile optimized */}
      {cart.length > 0 && (
        <div className="sticky-action">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                <ShoppingCart className="w-5 h-5 text-primary" />
              </div>
              <div>
                <div className="font-semibold">
                  {cart.reduce((sum, item) => sum + item.quantity, 0)} items
                </div>
                <div className="text-sm text-muted-foreground">Cash Order</div>
              </div>
            </div>
            <div className="text-2xl font-bold">{formatCurrency(total)}</div>
          </div>

          <Button
            className="w-full min-h-[56px] text-lg"
            onClick={handleSubmitOrder}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-6 h-6 mr-2 animate-spin" />
                Creating Order...
              </>
            ) : (
              <>
                <Banknote className="w-6 h-6 mr-2" />
                Complete Order
              </>
            )}
          </Button>
        </div>
      )}

      {/* Empty cart hint - only on mobile */}
      {cart.length === 0 && (
        <div className="sticky-action md:hidden">
          <div className="text-center text-muted-foreground py-2">
            <p className="text-base">Tap items to add to order</p>
          </div>
        </div>
      )}
    </AppLayout>
  )
}

// Owners have all staff features, so they can also access this page
export default withAuth(CreateCashOrderPage, ['staff', 'restaurant_owner'])
