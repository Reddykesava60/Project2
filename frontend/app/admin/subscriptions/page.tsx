"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { PageLoader } from "@/components/ui/loading-states";
import { ErrorState } from "@/components/ui/error-states";
import {
  CreditCard,
  Search,
  Building2,
  Calendar,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";

interface Subscription {
  id: string;
  restaurant_id: string;
  restaurant_name: string;
  plan: "free" | "starter" | "pro" | "enterprise";
  status: "active" | "past_due" | "canceled" | "trialing";
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
}

export default function AdminSubscriptionsPage() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [planFilter, setPlanFilter] = useState<string>("all");

  // Modal states
  const [selectedSub, setSelectedSub] = useState<Subscription | null>(null);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [showReactivateModal, setShowReactivateModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadSubscriptions();
  }, []);

  async function loadSubscriptions() {
    setLoading(true);
    setError(null);
    const res = await api.admin.getSubscriptions();
    if (res.data) {
      setSubscriptions(res.data);
    } else {
      setError(res.error || "Failed to load subscriptions");
    }
    setLoading(false);
  }

  const filteredSubscriptions = subscriptions.filter((s) => {
    const matchesSearch = s.restaurant_name
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    const matchesStatus =
      statusFilter === "all" || s.status === statusFilter;
    const matchesPlan = planFilter === "all" || s.plan === planFilter;
    return matchesSearch && matchesStatus && matchesPlan;
  });

  async function handleCancelSubscription() {
    if (!selectedSub) return;
    setActionLoading(true);
    const res = await api.admin.cancelSubscription(selectedSub.id);
    if (res.data) {
      setSubscriptions((prev) =>
        prev.map((s) =>
          s.id === selectedSub.id
            ? { ...s, cancel_at_period_end: true }
            : s
        )
      );
      setShowCancelModal(false);
    }
    setActionLoading(false);
  }

  async function handleReactivateSubscription() {
    if (!selectedSub) return;
    setActionLoading(true);
    const res = await api.admin.reactivateSubscription(selectedSub.id);
    if (res.data) {
      setSubscriptions((prev) =>
        prev.map((s) =>
          s.id === selectedSub.id
            ? { ...s, cancel_at_period_end: false, status: "active" }
            : s
        )
      );
      setShowReactivateModal(false);
    }
    setActionLoading(false);
  }

  function getStatusBadge(status: string, cancelAtPeriodEnd: boolean) {
    if (cancelAtPeriodEnd) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border bg-warning/10 text-warning-foreground border-warning/20">
          <AlertTriangle className="w-3.5 h-3.5" />
          Canceling
        </span>
      );
    }
    const styles = {
      active: "bg-success/10 text-success border-success/20",
      trialing: "bg-info/10 text-info border-info/20",
      past_due: "bg-warning/10 text-warning-foreground border-warning/20",
      canceled: "bg-destructive/10 text-destructive border-destructive/20",
    };
    const icons = {
      active: <CheckCircle2 className="w-3.5 h-3.5" />,
      trialing: <RefreshCw className="w-3.5 h-3.5" />,
      past_due: <AlertTriangle className="w-3.5 h-3.5" />,
      canceled: <XCircle className="w-3.5 h-3.5" />,
    };
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${styles[status as keyof typeof styles] || ""}`}
      >
        {icons[status as keyof typeof icons]}
        {status.charAt(0).toUpperCase() + status.slice(1).replace("_", " ")}
      </span>
    );
  }

  function getPlanBadge(plan: string) {
    const styles = {
      free: "bg-muted text-muted-foreground",
      starter: "bg-info/10 text-info",
      pro: "bg-primary/10 text-primary",
      enterprise: "bg-accent/10 text-accent",
    };
    return (
      <span
        className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${styles[plan as keyof typeof styles] || ""}`}
      >
        {plan.charAt(0).toUpperCase() + plan.slice(1)}
      </span>
    );
  }

  function formatDate(dateString: string) {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  if (loading) return <PageLoader message="Loading subscriptions..." />;

  if (error) {
    return (
      <ErrorState
        title="Failed to load subscriptions"
        description={error}
        action={{ label: "Try Again", onClick: loadSubscriptions }}
      />
    );
  }

  // Calculate stats
  const stats = {
    total: subscriptions.length,
    active: subscriptions.filter((s) => s.status === "active").length,
    trialing: subscriptions.filter((s) => s.status === "trialing").length,
    pastDue: subscriptions.filter((s) => s.status === "past_due").length,
    mrr: subscriptions.reduce((acc, s) => {
      const prices = { free: 0, starter: 29, pro: 79, enterprise: 199 };
      return s.status === "active" ? acc + prices[s.plan] : acc;
    }, 0),
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-foreground">
          Subscriptions
        </h1>
        <p className="text-muted-foreground mt-1">
          Manage restaurant subscription plans
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-sm text-muted-foreground">Total</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-success">{stats.active}</div>
            <p className="text-sm text-muted-foreground">Active</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-info">{stats.trialing}</div>
            <p className="text-sm text-muted-foreground">Trialing</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-warning">{stats.pastDue}</div>
            <p className="text-sm text-muted-foreground">Past Due</p>
          </CardContent>
        </Card>
        <Card className="col-span-2 lg:col-span-1">
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-primary">
              ${stats.mrr.toLocaleString()}
            </div>
            <p className="text-sm text-muted-foreground">Monthly Revenue</p>
          </CardContent>
        </Card>
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
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[160px] min-h-[48px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="trialing">Trialing</SelectItem>
            <SelectItem value="past_due">Past Due</SelectItem>
            <SelectItem value="canceled">Canceled</SelectItem>
          </SelectContent>
        </Select>
        <Select value={planFilter} onValueChange={setPlanFilter}>
          <SelectTrigger className="w-full sm:w-[140px] min-h-[48px]">
            <SelectValue placeholder="Plan" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Plans</SelectItem>
            <SelectItem value="free">Free</SelectItem>
            <SelectItem value="starter">Starter</SelectItem>
            <SelectItem value="pro">Pro</SelectItem>
            <SelectItem value="enterprise">Enterprise</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Subscriptions List */}
      {filteredSubscriptions.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <CreditCard className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium">No subscriptions found</h3>
            <p className="text-muted-foreground">
              {searchQuery || statusFilter !== "all" || planFilter !== "all"
                ? "Try adjusting your filters"
                : "No subscriptions have been created yet"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filteredSubscriptions.map((sub) => (
            <Card key={sub.id}>
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
                            {sub.restaurant_name}
                          </h3>
                          {getPlanBadge(sub.plan)}
                          {getStatusBadge(sub.status, sub.cancel_at_period_end)}
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground flex-wrap">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {formatDate(sub.current_period_start)} -{" "}
                            {formatDate(sub.current_period_end)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 flex-wrap lg:flex-nowrap">
                    {sub.status !== "canceled" && (
                      <>
                        {sub.cancel_at_period_end ? (
                          <Button
                            variant="default"
                            className="flex-1 lg:flex-none min-h-[48px]"
                            onClick={() => {
                              setSelectedSub(sub);
                              setShowReactivateModal(true);
                            }}
                          >
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Reactivate
                          </Button>
                        ) : (
                          <Button
                            variant="destructive"
                            className="flex-1 lg:flex-none min-h-[48px]"
                            onClick={() => {
                              setSelectedSub(sub);
                              setShowCancelModal(true);
                            }}
                          >
                            <XCircle className="w-4 h-4 mr-2" />
                            Cancel
                          </Button>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Cancel Modal */}
      <Dialog open={showCancelModal} onOpenChange={setShowCancelModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cancel Subscription</DialogTitle>
            <DialogDescription>
              Are you sure you want to cancel the subscription for{" "}
              {selectedSub?.restaurant_name}? They will retain access until the
              end of the current billing period.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setShowCancelModal(false)}
              className="min-h-[48px]"
            >
              Keep Subscription
            </Button>
            <Button
              variant="destructive"
              onClick={handleCancelSubscription}
              disabled={actionLoading}
              className="min-h-[48px]"
            >
              {actionLoading ? "Processing..." : "Cancel Subscription"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reactivate Modal */}
      <Dialog open={showReactivateModal} onOpenChange={setShowReactivateModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reactivate Subscription</DialogTitle>
            <DialogDescription>
              Are you sure you want to reactivate the subscription for{" "}
              {selectedSub?.restaurant_name}? They will continue to be billed at
              the end of the current period.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setShowReactivateModal(false)}
              className="min-h-[48px]"
            >
              Cancel
            </Button>
            <Button
              onClick={handleReactivateSubscription}
              disabled={actionLoading}
              className="min-h-[48px]"
            >
              {actionLoading ? "Processing..." : "Reactivate"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
