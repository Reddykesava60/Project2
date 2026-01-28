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
import { PageLoader } from "@/components/ui/loading-states";
import { ErrorState } from "@/components/ui/error-states";
import {
  ScrollText,
  Search,
  Filter,
  User,
  Building2,
  Clock,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { api } from "@/lib/api";

interface AuditLog {
  id: string;
  action: string;
  actor_id: string;
  actor_name: string;
  actor_role: string;
  resource_type: string;
  resource_id: string;
  resource_name: string;
  details: string | null;
  ip_address: string | null;
  created_at: string;
}

export default function AdminAuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [actionFilter, setActionFilter] = useState<string>("all");
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    loadLogs();
  }, [page, actionFilter]);

  async function loadLogs() {
    setLoading(true);
    setError(null);
    const res = await api.admin.getAuditLogs(page, 20);
    if (res.data) {
      setLogs(res.data.logs);
      setHasMore(res.data.has_more);
    } else {
      setError(res.error || "Failed to load audit logs");
    }
    setLoading(false);
  }

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      log.actor_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.resource_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.action.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesAction =
      actionFilter === "all" || log.action === actionFilter;
    return matchesSearch && matchesAction;
  });

  function getActionColor(action: string) {
    if (action.includes("create") || action.includes("add")) {
      return "bg-success/10 text-success border-success/20";
    }
    if (action.includes("delete") || action.includes("remove") || action.includes("suspend")) {
      return "bg-destructive/10 text-destructive border-destructive/20";
    }
    if (action.includes("update") || action.includes("edit")) {
      return "bg-info/10 text-info border-info/20";
    }
    return "bg-muted text-muted-foreground border-muted";
  }

  function formatAction(action: string) {
    return action
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  }

  function formatTimestamp(timestamp: string) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  }

  if (loading && logs.length === 0) {
    return <PageLoader message="Loading audit logs..." />;
  }

  if (error && logs.length === 0) {
    return (
      <ErrorState
        title="Failed to load audit logs"
        description={error}
        action={{ label: "Try Again", onClick: loadLogs }}
      />
    );
  }

  const uniqueActions = [...new Set(logs.map((l) => l.action))];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl lg:text-3xl font-bold text-foreground">
          Audit Logs
        </h1>
        <p className="text-muted-foreground mt-1">
          Track all system activities and changes
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search logs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 min-h-[48px]"
          />
        </div>
        <Select
          value={actionFilter}
          onValueChange={setActionFilter}
        >
          <SelectTrigger className="w-full sm:w-[200px] min-h-[48px]">
            <Filter className="w-4 h-4 mr-2" />
            <SelectValue placeholder="Filter by action" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Actions</SelectItem>
            {uniqueActions.map((action) => (
              <SelectItem key={action} value={action}>
                {formatAction(action)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Logs List */}
      {filteredLogs.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <ScrollText className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium">No logs found</h3>
            <p className="text-muted-foreground">
              {searchQuery || actionFilter !== "all"
                ? "Try adjusting your filters"
                : "No activity has been recorded yet"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredLogs.map((log) => (
            <Card key={log.id}>
              <CardContent className="p-4">
                <div className="flex flex-col lg:flex-row lg:items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-2">
                      <span
                        className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium border ${getActionColor(log.action)}`}
                      >
                        {formatAction(log.action)}
                      </span>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTimestamp(log.created_at)}
                      </span>
                    </div>
                    <p className="text-sm">
                      <span className="font-medium flex items-center gap-1 inline">
                        <User className="w-4 h-4 inline" />
                        {log.actor_name}
                      </span>
                      <span className="text-muted-foreground">
                        {" "}
                        ({log.actor_role})
                      </span>
                      <span className="text-muted-foreground"> on </span>
                      <span className="font-medium flex items-center gap-1 inline">
                        <Building2 className="w-4 h-4 inline" />
                        {log.resource_name}
                      </span>
                    </p>
                    {log.details && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {log.details}
                      </p>
                    )}
                  </div>
                  {log.ip_address && (
                    <div className="text-xs text-muted-foreground">
                      IP: {log.ip_address}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Page {page}
        </p>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1 || loading}
            className="min-h-[48px]"
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Previous
          </Button>
          <Button
            variant="outline"
            onClick={() => setPage((p) => p + 1)}
            disabled={!hasMore || loading}
            className="min-h-[48px]"
          >
            Next
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </div>
    </div>
  );
}
