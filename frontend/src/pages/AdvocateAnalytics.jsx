import { useEffect, useState } from "react";
import { CurrencyCircleDollar, ShieldCheck, TrendDown, UsersThree, Wallet, Warning } from "@phosphor-icons/react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useAuth } from "../auth/AuthContext";
import { Card, DataTable, KpiCard, Skeleton, StatusBadge } from "../components/ui";
import { analyticsData, isDemoMode } from "../mocks/data";
import { ChartCard, ChartTooltip, DemoNotice, EndpointUnavailable, Page, chartColors, formatPKR } from "./shared";

export default function AdvocateAnalytics({ focus }) {
  const { api } = useAuth();
  const demo = isDemoMode();
  const [state, setState] = useState({ loading: true, error: "", kpis: null, platforms: [], zones: [] });

  async function load() {
    if (demo) {
      setState({ loading: false, error: "", kpis: analyticsData.kpis, platforms: analyticsData.platforms, zones: analyticsData.zones });
      return;
    }
    setState((current) => ({ ...current, loading: true, error: "" }));
    try {
      const [kpis, platforms, zones] = await Promise.all([
        api.get("analytics", "/kpis"),
        api.get("analytics", "/platforms"),
        api.get("analytics", "/city-zones"),
      ]);
      setState({ loading: false, error: "", kpis, platforms: platforms.groups || [], zones: zones.groups || [] });
    } catch (error) {
      setState({ loading: false, error: error.message, kpis: null, platforms: [], zones: [] });
    }
  }

  useEffect(() => { load(); }, [demo]);

  return (
    <Page eyebrow="K-anonymous evidence" title={focus === "income" ? "Income trends" : "Advocate analytics"} description="Compare income and deductions without exposing individual workers.">
      {demo && <DemoNotice />}
      <div className="privacy-note"><ShieldCheck size={22} weight="fill" /><div><strong>Privacy threshold enforced</strong><span>Aggregate groups only appear when they contain at least five distinct workers.</span></div></div>
      {state.loading && <div className="kpi-grid"><Skeleton height="9.5rem" /><Skeleton height="9.5rem" /><Skeleton height="9.5rem" /><Skeleton height="9.5rem" /></div>}
      {!state.loading && state.error && <EndpointUnavailable title="Analytics service is unavailable" message={state.error} retry={load} />}
      {!state.loading && !state.error && state.kpis?.suppressed && <EndpointUnavailable title="Aggregate results are suppressed" message={`Fewer than ${state.kpis.minimum_group_size || 5} workers are present, so FairGig has hidden this group.`} />}
      {!state.loading && !state.error && state.kpis && !state.kpis.suppressed && <>
        <div className="kpi-grid">
          <KpiCard label="Workers represented" value={state.kpis.worker_count} trend={`Minimum group size ${state.kpis.minimum_group_size || 5}`} icon={UsersThree} />
          <KpiCard label="Total net income" value={formatPKR(state.kpis.total_net_received)} icon={CurrencyCircleDollar} />
          <KpiCard label="Median monthly income" value={formatPKR(state.kpis.median_monthly_income)} icon={Wallet} />
          <KpiCard label="Effective deductions" value={`${Number(state.kpis.effective_deduction_percent).toFixed(1)}%`} icon={TrendDown} />
        </div>

        <section className="page-section chart-grid">
          <ChartCard title="Commission by platform" subtitle="Effective deductions for privacy-eligible platform groups."><ResponsiveContainer width="100%" height="100%"><BarChart data={state.platforms} accessibilityLayer><CartesianGrid stroke={chartColors.grid} vertical={false} /><XAxis dataKey="platform" tickLine={false} axisLine={false} /><YAxis tickFormatter={(value) => `${value}%`} tickLine={false} axisLine={false} width={38} /><Tooltip content={<ChartTooltip formatter={(value) => `${value}%`} />} /><Bar dataKey="effective_deduction_percent" name="Deductions" fill={chartColors.secondary} radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer></ChartCard>
          <ChartCard title="Income by city zone" subtitle="Median monthly income for privacy-eligible zones."><ResponsiveContainer width="100%" height="100%"><BarChart layout="vertical" data={state.zones} accessibilityLayer margin={{ left: 18 }}><CartesianGrid stroke={chartColors.grid} horizontal={false} /><XAxis type="number" tickFormatter={(value) => `${Math.round(value / 1000)}k`} tickLine={false} axisLine={false} /><YAxis type="category" dataKey="city_zone" width={126} tickLine={false} axisLine={false} /><Tooltip content={<ChartTooltip formatter={formatPKR} />} /><Bar dataKey="median_monthly_income" name="Median income" fill={chartColors.primary} radius={[0, 5, 5, 0]} /></BarChart></ResponsiveContainer></ChartCard>
        </section>

        {demo ? <>
          <section className="page-section chart-grid">
            <ChartCard title="Median income over time" subtitle="City-wide median monthly net income."><ResponsiveContainer width="100%" height="100%"><LineChart data={analyticsData.trend} accessibilityLayer><CartesianGrid stroke={chartColors.grid} vertical={false} /><XAxis dataKey="month" tickLine={false} axisLine={false} /><YAxis tickFormatter={(value) => `${Math.round(value / 1000)}k`} tickLine={false} axisLine={false} width={40} /><Tooltip content={<ChartTooltip formatter={formatPKR} />} /><Line dataKey="median" name="Median income" stroke={chartColors.primary} strokeWidth={3} /></LineChart></ResponsiveContainer></ChartCard>
            <ChartCard title="Common grievance categories" subtitle="Recurring concerns across privacy-eligible groups."><ResponsiveContainer width="100%" height="100%"><BarChart layout="vertical" data={analyticsData.grievances} accessibilityLayer margin={{ left: 16 }}><CartesianGrid stroke={chartColors.grid} horizontal={false} /><XAxis type="number" tickLine={false} axisLine={false} /><YAxis type="category" dataKey="category" width={118} tickLine={false} axisLine={false} /><Tooltip content={<ChartTooltip />} /><Bar dataKey="count" name="Grievances" fill={chartColors.secondary} radius={[0, 5, 5, 0]} /></BarChart></ResponsiveContainer></ChartCard>
          </section>
          <section className="page-section">
            <div className="section-head"><div><h2>Month-on-month movement</h2><p>Aggregate median income changes, not individual worker changes.</p></div></div>
            <Card padded={false}><DataTable rowKey="month" rows={[{ month: "August", median: 58350, change: "+2.7%", direction: "verified" }, { month: "September", median: 57450, change: "-1.5%", direction: "flagged" }]} columns={[{ key: "month", label: "Month" }, { key: "median", label: "Median income", render: (row) => formatPKR(row.median) }, { key: "change", label: "Change" }, { key: "direction", label: "Indicator", render: (row) => <StatusBadge status={row.direction}>{row.direction === "flagged" ? "Decline" : "Increase"}</StatusBadge> }]} /></Card>
          </section>
          <section className="page-section">
            <div className="section-head"><div><h2>Vulnerability flags</h2><p>Group-level signals only. No individual worker records are exposed.</p></div></div>
            <Card padded={false}><DataTable rowKey="group" rows={analyticsData.vulnerabilityFlags} columns={[{ key: "group", label: "Eligible group" }, { key: "workers", label: "Workers" }, { key: "signal", label: "Signal" }, { key: "change", label: "Change" }, { key: "severity", label: "Review", render: (row) => <StatusBadge status={row.severity}>{row.severity === "flagged" ? "Priority" : "Monitor"}</StatusBadge> }]} /></Card>
          </section>
        </> : <div className="data-note page-section"><Warning size={18} /><span>Time-series, grievance-category, month-on-month decline, and vulnerability aggregates are not available in the current analytics contract. Ask the Backend Services teammate to add k-anonymous endpoints before these sections can display real data.</span></div>}

        <section className="page-section">
          <div className="section-head"><div><h2>Platform comparison</h2><p>Only platforms meeting the privacy threshold are returned.</p></div></div>
          <Card padded={false}><DataTable rows={state.platforms} columns={[{ key: "platform", label: "Platform" }, { key: "worker_count", label: "Workers" }, { key: "median_monthly_income", label: "Median monthly income", render: (row) => formatPKR(row.median_monthly_income) }, { key: "effective_deduction_percent", label: "Effective deductions", render: (row) => `${Number(row.effective_deduction_percent).toFixed(1)}%` }]} /></Card>
        </section>
        <section className="page-section">
          <div className="section-head"><div><h2>City-zone comparison</h2><p>Median income for zones with at least five represented workers.</p></div></div>
          <Card padded={false}><DataTable rows={state.zones} rowKey="city_zone" columns={[{ key: "city_zone", label: "City zone" }, { key: "worker_count", label: "Workers" }, { key: "median_monthly_income", label: "Median monthly income", render: (row) => formatPKR(row.median_monthly_income) }]} /></Card>
        </section>
      </>}
    </Page>
  );
}
