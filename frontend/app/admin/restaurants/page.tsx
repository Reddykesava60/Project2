"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PageLoader, CardSkeleton } from "@/components/ui/loading-states";
import { ErrorState } from "@/components/ui/error-states";
import {
  Building2,
  Search,
  UserCircle,
  MapPin,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Restaurant } from "@/lib/types";

type RestaurantStatus = "active" | "suspended" | "pending";

export default function AdminRestaurantsPage() {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<RestaurantStatus | "all">("all");

  // Modal states
  const [selectedRestaurant, setSelectedRestaurant] = useState<Restaurant | null>(null);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [showOwnerModal, setShowOwnerModal] = useState(false);
  const [newStatus, setNewStatus] = useState<RestaurantStatus>("active");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadRestaurants();
  }, []);

  async function loadRestaurants() {
    setLoading(true);
    setError(null);
    const res = await api.admin.getRestaurants();
    if (res.data) {
      setRestaurants(res.data);
    } else {
      setError(res.error || "Failed to load restaurants");
    }
    setLoading(false);
  }

  const filteredRestaurants = restaurants.filter((r) => {
    const matchesSearch =
      r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.address?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || r.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  async function handleStatusChange() {
    if (!selectedRestaurant) return;
    setActionLoading(true);
    const res = await api.admin.updateRestaurantStatus(
      selectedRestaurant.id,
      newStatus
    );
    if (res.data) {
      setRestaurants((prev) =>
        prev.map((r) =>
          r.id === selectedRestaurant.id ? { ...r, status: newStatus } : r
        )
      );
      setShowStatusModal(false);
    }
    setActionLoading(false);
  }

  async function handleAssignOwner() {
    if (!selectedRestaurant || !ownerEmail) return;
    setActionLoading(true);
    const res = await api.admin.assignOwner(selectedRestaurant.id, ownerEmail);
    if (res.data) {
      setRestaurants((prev) =>
        prev.map((r) =>
          r.id === selectedRestaurant.id
            ? { ...r, owner_email: ownerEmail }
            : r
        )
      );
      setShowOwnerModal(false);
      setOwnerEmail("");
    }
    setActionLoading(false);
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case "active":
        return <CheckCircle2 className="w-5 h-5 text-success" />;
      case "suspended":
        return <XCircle className="w-5 h-5 text-destructive" />;
      case "pending":
        return <AlertTriangle className="w-5 h-5 text-warning" />;
      default:
        return null;
    }
  }

  function getStatusBadge(status: string) {
    const styles = {
      active: "bg-success/10 text-success border-success/20",
      suspended: "bg-destructive/10 text-destructive border-destructive/20",
      pending: "bg-warning/10 text-warning-foreground border-warning/20",
    };
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${styles[status as keyof typeof styles] || ""}`}
      >
        {getStatusIcon(status)}
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  }

  if (loading) return <PageLoader message="Loading restaurants..." />;

  if (error) {
    return (
      <ErrorState
        title="Failed to load restaurants"
        description={error}
        action={{ label: "Try Again", onClick: loadRestaurants }}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-foreground">
          Restaurants
        </h1>
        <p className="text-muted-foreground mt-1">
          Manage all registered restaurants
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search restaurants..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 min-h-[48px]"
          />
        </div>
        <Select
          value={statusFilter}
          onValueChange={(v) => setStatusFilter(v as RestaurantStatus | "all")}
        >
          <SelectTrigger className="w-full sm:w-[180px] min-h-[48px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="suspended">Suspended</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{restaurants.length}</div>
            <p className="text-sm text-muted-foreground">Total Restaurants</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-success">
              {restaurants.filter((r) => r.status === "active").length}
            </div>
            <p className="text-sm text-muted-foreground">Active</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-warning">
              {restaurants.filter((r) => r.status === "pending").length}
            </div>
            <p className="text-sm text-muted-foreground">Pending</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-destructive">
              {restaurants.filter((r) => r.status === "suspended").length}
            </div>
            <p className="text-sm text-muted-foreground">Suspended</p>
          </CardContent>
        </Card>
      </div>

      {/* Restaurant List */}
      {filteredRestaurants.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Building2 className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium">No restaurants found</h3>
            <p className="text-muted-foreground">
              {searchQuery || statusFilter !== "all"
                ? "Try adjusting your filters"
                : "No restaurants have been registered yet"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredRestaurants.map((restaurant) => (
            <Card key={restaurant.id}>
              <CardContent className="p-4 lg:p-6">
                <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start gap-3">
                      <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                        <Building2 className="w-6 h-6 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-semibold text-lg truncate">
                            {restaurant.name}
                          </h3>
                          {getStatusBadge(restaurant.status)}
                        </div>
                        {restaurant.address && (
                          <p className="text-sm text-muted-foreground flex items-center gap-1 mt-1">
                            <MapPin className="w-4 h-4" />
                            {restaurant.address}
                          </p>
                        )}
                        {restaurant.owner_email && (
                          <p className="text-sm text-muted-foreground flex items-center gap-1 mt-1">
                            <UserCircle className="w-4 h-4" />
                            {restaurant.owner_email}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 flex-wrap lg:flex-nowrap">
                    <Button
                      variant="outline"
                      className="flex-1 lg:flex-none min-h-[48px] bg-transparent"
                      onClick={() => {
                        setSelectedRestaurant(restaurant);
                        setOwnerEmail(restaurant.owner_email || "");
                        setShowOwnerModal(true);
                      }}
                    >
                      <UserCircle className="w-4 h-4 mr-2" />
                      Assign Owner
                    </Button>
                    <Button
                      variant={
                        restaurant.status === "suspended"
                          ? "default"
                          : "destructive"
                      }
                      className="flex-1 lg:flex-none min-h-[48px]"
                      onClick={() => {
                        setSelectedRestaurant(restaurant);
                        setNewStatus(
                          restaurant.status === "suspended"
                            ? "active"
                            : "suspended"
                        );
                        setShowStatusModal(true);
                      }}
                    >
                      {restaurant.status === "suspended" ? (
                        <>
                          <CheckCircle2 className="w-4 h-4 mr-2" />
                          Activate
                        </>
                      ) : (
                        <>
                          <XCircle className="w-4 h-4 mr-2" />
                          Suspend
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Status Change Modal */}
      <Dialog open={showStatusModal} onOpenChange={setShowStatusModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {newStatus === "suspended"
                ? "Suspend Restaurant"
                : "Activate Restaurant"}
            </DialogTitle>
            <DialogDescription>
              {newStatus === "suspended"
                ? `Are you sure you want to suspend "${selectedRestaurant?.name}"? This will prevent customers from placing orders.`
                : `Are you sure you want to activate "${selectedRestaurant?.name}"? This will allow customers to place orders.`}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setShowStatusModal(false)}
              className="min-h-[48px]"
            >
              Cancel
            </Button>
            <Button
              variant={newStatus === "suspended" ? "destructive" : "default"}
              onClick={handleStatusChange}
              disabled={actionLoading}
              className="min-h-[48px]"
            >
              {actionLoading
                ? "Processing..."
                : newStatus === "suspended"
                  ? "Suspend"
                  : "Activate"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign Owner Modal */}
      <Dialog open={showOwnerModal} onOpenChange={setShowOwnerModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assign Restaurant Owner</DialogTitle>
            <DialogDescription>
              Enter the email address of the user who will manage{" "}
              {selectedRestaurant?.name}.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="ownerEmail">Owner Email</Label>
              <Input
                id="ownerEmail"
                type="email"
                placeholder="owner@example.com"
                value={ownerEmail}
                onChange={(e) => setOwnerEmail(e.target.value)}
                className="min-h-[48px]"
              />
            </div>
          </div>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setShowOwnerModal(false)}
              className="min-h-[48px]"
            >
              Cancel
            </Button>
            <Button
              onClick={handleAssignOwner}
              disabled={actionLoading || !ownerEmail}
              className="min-h-[48px]"
            >
              {actionLoading ? "Assigning..." : "Assign Owner"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
