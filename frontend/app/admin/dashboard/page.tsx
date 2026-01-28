'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    Building2,
    Users,
    CreditCard,
    TrendingUp,
    Activity,
    ArrowUpRight,
    ArrowDownRight,
    Plus,
    ArrowRight
} from "lucide-react";
import Link from 'next/link';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    AreaChart,
    Area
} from 'recharts';

// Mock data for the dashboard
const stats = [
    {
        title: "Total Restaurants",
        value: "128",
        change: "+12%",
        trend: "up",
        icon: Building2,
        color: "text-blue-500",
        bg: "bg-blue-500/10"
    },
    {
        title: "Active Subscriptions",
        value: "112",
        change: "+5%",
        trend: "up",
        icon: CreditCard,
        color: "text-emerald-500",
        bg: "bg-emerald-500/10"
    },
    {
        title: "Total Revenue",
        value: "$42,500",
        change: "+18%",
        trend: "up",
        icon: TrendingUp,
        color: "text-violet-500",
        bg: "bg-violet-500/10"
    },
    {
        title: "System Activity",
        value: "99.9%",
        change: "-0.1%",
        trend: "down",
        icon: Activity,
        color: "text-amber-500",
        bg: "bg-amber-500/10"
    },
];

const chartData = [
    { name: 'Jan', revenue: 4000, restaurants: 24 },
    { name: 'Feb', revenue: 3000, restaurants: 18 },
    { name: 'Mar', revenue: 2000, restaurants: 29 },
    { name: 'Apr', revenue: 2780, restaurants: 23 },
    { name: 'May', revenue: 1890, restaurants: 15 },
    { name: 'Jun', revenue: 2390, restaurants: 21 },
    { name: 'Jul', revenue: 3490, restaurants: 34 },
];

const recentActivity = [
    { id: 1, action: "New Restaurant Joined", target: "Gourmet Bites", time: "2 hours ago", type: "success" },
    { id: 2, action: "Subscription Updated", target: "Pizza Palace", time: "5 hours ago", type: "info" },
    { id: 3, action: "System Audit", target: "Security Module", time: "8 hours ago", type: "warning" },
    { id: 4, action: "New Owner Assigned", target: "Beachside Grill", time: "1 day ago", type: "success" },
];

export default function AdminDashboardPage() {
    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h1 className="text-3xl font-extrabold tracking-tight text-foreground lg:text-4xl text-gradient">
                        Platform Overview
                    </h1>
                    <p className="text-muted-foreground mt-2 text-lg">
                        Monitor system health, growth, and restaurant activity.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <Button variant="outline" className="min-h-[48px] px-6">
                        Generate Report
                    </Button>
                    <Button className="min-h-[48px] px-6 gap-2">
                        <Plus className="w-4 h-4" />
                        Add Restaurant
                    </Button>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                {stats.map((stat, index) => (
                    <Card key={index} className="overflow-hidden border-none shadow-sm hover:shadow-md transition-shadow bg-card/50 backdrop-blur-sm">
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div className={`p-3 rounded-2xl ${stat.bg}`}>
                                    <stat.icon className={`w-6 h-6 ${stat.color}`} />
                                </div>
                                <div className={`flex items-center gap-1 text-sm font-medium ${stat.trend === 'up' ? 'text-emerald-500' : 'text-amber-500'}`}>
                                    {stat.change}
                                    {stat.trend === 'up' ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                                </div>
                            </div>
                            <div className="mt-4">
                                <p className="text-sm font-medium text-muted-foreground uppercase tracking-wider">{stat.title}</p>
                                <p className="text-3xl font-bold text-foreground mt-1">{stat.value}</p>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Charts Section */}
            <div className="grid gap-6 lg:grid-cols-7">
                <Card className="lg:col-span-4 border-none shadow-sm bg-card/50 backdrop-blur-sm">
                    <CardHeader>
                        <CardTitle>Growth Analytics</CardTitle>
                        <CardDescription>Monthly platform revenue and restaurant onboarding</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[350px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={chartData}>
                                    <defs>
                                        <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} dy={10} />
                                    <YAxis axisLine={false} tickLine={false} tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '12px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                                        itemStyle={{ color: 'hsl(var(--foreground))' }}
                                    />
                                    <Area type="monotone" dataKey="revenue" stroke="hsl(var(--primary))" strokeWidth={3} fillOpacity={1} fill="url(#colorRevenue)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                <Card className="lg:col-span-3 border-none shadow-sm bg-card/50 backdrop-blur-sm">
                    <CardHeader>
                        <CardTitle>Recent Activity</CardTitle>
                        <CardDescription>Latest actions performed across the system</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-6">
                            {recentActivity.map((item) => (
                                <div key={item.id} className="flex items-start gap-4">
                                    <div className={`mt-1.5 w-2 h-2 rounded-full flex-shrink-0 ${item.type === 'success' ? 'bg-emerald-500' :
                                            item.type === 'warning' ? 'bg-amber-500' : 'bg-blue-500'
                                        }`} />
                                    <div className="flex-1 space-y-1">
                                        <p className="text-sm font-semibold">{item.action}</p>
                                        <p className="text-xs text-muted-foreground">{item.target}</p>
                                        <p className="text-[10px] text-muted-foreground/60 uppercase font-medium">{item.time}</p>
                                    </div>
                                    <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full">
                                        <ArrowRight className="w-4 h-4" />
                                    </Button>
                                </div>
                            ))}
                        </div>
                        <Button variant="ghost" className="w-full mt-6 text-primary hover:text-primary hover:bg-primary/5 font-semibold" asChild>
                            <Link href="/admin/audit-logs">
                                View Full Logs
                            </Link>
                        </Button>
                    </CardContent>
                </Card>
            </div>

            {/* Quick Links */}
            <div className="grid gap-6 md:grid-cols-3">
                <Card className="group cursor-pointer border-none shadow-sm hover:shadow-md transition-all bg-card/50 hover:bg-card">
                    <Link href="/admin/restaurants">
                        <CardContent className="p-6 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="p-3 rounded-xl bg-blue-500/10 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                                    <Building2 className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="font-bold">Manage Restaurants</h3>
                                    <p className="text-sm text-muted-foreground">Approve, suspend, or update info</p>
                                </div>
                            </div>
                            <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                        </CardContent>
                    </Link>
                </Card>

                <Card className="group cursor-pointer border-none shadow-sm hover:shadow-md transition-all bg-card/50 hover:bg-card">
                    <Link href="/admin/subscriptions">
                        <CardContent className="p-6 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="p-3 rounded-xl bg-emerald-500/10 group-hover:bg-emerald-500 group-hover:text-white transition-colors">
                                    <CreditCard className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="font-bold">Subscription Plans</h3>
                                    <p className="text-sm text-muted-foreground">Monitor billing and plan usage</p>
                                </div>
                            </div>
                            <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                        </CardContent>
                    </Link>
                </Card>

                <Card className="group cursor-pointer border-none shadow-sm hover:shadow-md transition-all bg-card/50 hover:bg-card">
                    <Link href="/admin/audit-logs">
                        <CardContent className="p-6 flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="p-3 rounded-xl bg-violet-500/10 group-hover:bg-violet-500 group-hover:text-white transition-colors">
                                    <Activity className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="font-bold">System Health</h3>
                                    <p className="text-sm text-muted-foreground">Review logs and error reports</p>
                                </div>
                            </div>
                            <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                        </CardContent>
                    </Link>
                </Card>
            </div>
        </div>
    );
}
