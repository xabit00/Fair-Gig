import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Clock, CurrencyCircleDollar, Plus, ShieldCheck, TrendDown, Wallet } from "@phosphor-icons/react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useAuth } from "../auth/AuthContext";
import { Card, KpiCard, Skeleton } from "../components/ui";
import { commissionTrend, hourlyTrend, incomeTrend, isDemoMode, sampleShifts, weeklyIncome, workerAnomalies, workerSummary } from "../mocks/data";
import { ChartCard, ChartTooltip, DemoNotice, EndpointUnavailable, Page, ShiftTable, chartColors, formatPKR } from "./shared";

export default function WorkerDashboard() {
  const { user, api } = useAuth();
  const demo = isDemoMode();
  const firstName = user.name.split(" ")[0];
  const [live, setLive] = useState({ loading: !demo, error: "", summary: null, shifts: [], anomalies: [] });

  async function loadLiveData() {
    if (demo) return;
    setLive((current) => ({ ...current, loading: true, error: "" }));
    try {
      const [summary, shiftResponse] = await Promise.all([
        api.get("earnings", "/earnings/summary"),
        api.get("earnings", "/shifts"),
      ]);
      const shifts = shiftResponse.shifts || [];
      let anomalies = [];
      if (shifts.length) {
        const result = await api.post("anomaly", "/detect", {
          worker_id: user.id,
          earnings: shifts.map(({ date, platform, gross_earned, deductions, net_received }) => ({ date, platform, gross_earned, deductions, net_received })),
        });
        anomalies = result.anomalies || [];
      }
      setLive({ loading: false, error: "", summary, shifts, anomalies });
    } catch (error) {
      setLive({ loading: false, error: error.message, summary: null, shifts: [], anomalies: [] });
    }
  }

  useEffect(() => { loadLiveData(); }, [demo, user.id]);

  if (!demo) {
    const verifiedIncome = live.shifts.filter((shift) => shift.verification_status === "confirmed").reduce((sum, shift) => sum + Number(shift.net_received), 0);
    const deductionPercent = Number(live.summary?.total_gross) > 0
      ? Number(live.summary.total_deductions) / Number(live.summary.total_gross) * 100
      : 0;
    return (
      <Page eyebrow="Worker overview" title={`Good to see you, ${firstName}`} description="Your persisted income record, verification progress, and unusual changes." action={<Link className="ui-button ui-button--primary" to="/earnings"><Plus size={18} />Log a shift</Link>}>
        {live.loading && <div className="kpi-grid"><Skeleton height="9.5rem" /><Skeleton height="9.5rem" /><Skeleton height="9.5rem" /><Skeleton height="9.5rem" /></div>}
        {!live.loading && live.error && <EndpointUnavailable title="Worker data is unavailable" message={live.error} retry={loadLiveData} />}
        {!live.loading && !live.error && <>
          <div className="kpi-grid">
            <KpiCard label="Total earnings" value={formatPKR(live.summary?.total_net || 0)} trend={`${live.summary?.total_shifts || 0} shifts recorded`} icon={Wallet} />
            <KpiCard label="Average hourly rate" value={formatPKR(live.summary?.effective_hourly_rate || 0)} trend={`${Number(live.summary?.total_hours || 0).toFixed(1)} hours recorded`} icon={Clock} />
            <KpiCard label="Verified earnings" value={formatPKR(verifiedIncome)} trend={`${live.shifts.filter((shift) => shift.verification_status === "confirmed").length} confirmed shifts`} icon={ShieldCheck} />
            <KpiCard label="Effective deductions" value={`${deductionPercent.toFixed(1)}%`} icon={CurrencyCircleDollar} />
          </div>
          {live.anomalies.length > 0 && <section className="page-section"><Card className="anomaly-card"><div className="section-head"><div><h2>Needs attention</h2><p>Patterns detected from your persisted earnings.</p></div></div><div className="anomaly-list">{live.anomalies.map((item, index) => <article className="anomaly-item anomaly-item--warning" key={`${item.type}-${index}`}><TrendDown size={22} /><div><strong>{item.type === "high_deduction" ? "Unusually high deduction" : "Income decline"}</strong><p>{item.explanation}</p></div></article>)}</div></Card></section>}
          <section className="page-section"><div className="section-head"><div><h2>Recent shifts</h2><p>Your latest persisted earnings records.</p></div><Link className="text-link" to="/earnings">View all</Link></div><Card padded={false}><ShiftTable shifts={live.shifts.slice(0, 5)} /></Card></section>
        </>}
      </Page>
    );
  }

  return (
    <Page eyebrow="Worker overview" title={`Good to see you, ${firstName}`} description="A practical view of your earnings, working time, and unusual deductions." action={<Link className="ui-button ui-button--primary" to="/earnings?demo=1"><Plus size={18} />Log a shift</Link>}>
      <DemoNotice />
      <div className="kpi-grid">
        <KpiCard label="Total earnings" value={formatPKR(workerSummary.monthlyNet)} trend="This month, 6% above August" trendTone="positive" icon={Wallet} />
        <KpiCard label="Average hourly rate" value={formatPKR(workerSummary.averageHourlyRate)} trend={`${workerSummary.hoursWorked} hours recorded`} icon={Clock} />
        <KpiCard label="Verified earnings" value={`${workerSummary.verifiedPercent}%`} trend={`${formatPKR(workerSummary.verifiedIncome)} confirmed`} icon={ShieldCheck} />
        <KpiCard label="Average commission" value={`${workerSummary.averageCommission}%`} trend="1.6 points above August" trendTone="negative" icon={CurrencyCircleDollar} />
      </div>

      <section className="page-section two-column">
        <ChartCard title="Income trend" subtitle="Monthly net income compared with the city-wide median.">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={incomeTrend} accessibilityLayer margin={{ top: 12, right: 10, left: 0, bottom: 0 }}>
              <defs><linearGradient id="incomeFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={chartColors.primary} stopOpacity={0.28} /><stop offset="100%" stopColor={chartColors.primary} stopOpacity={0.02} /></linearGradient></defs>
              <CartesianGrid stroke={chartColors.grid} vertical={false} />
              <XAxis dataKey="month" tickLine={false} axisLine={false} />
              <YAxis tickFormatter={(value) => `${Math.round(value / 1000)}k`} tickLine={false} axisLine={false} width={42} />
              <Tooltip content={<ChartTooltip formatter={formatPKR} />} />
              <Legend />
              <Area type="monotone" dataKey="net" name="Your income" stroke={chartColors.primary} strokeWidth={3} fill="url(#incomeFill)" />
              <Line type="monotone" dataKey="cityMedian" name="City median" stroke={chartColors.secondary} strokeWidth={2} strokeDasharray="5 5" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
        <Card className="anomaly-card">
          <div className="section-head"><div><h2>Needs attention</h2><p>Patterns found in your sample earnings.</p></div></div>
          <div className="anomaly-list">
            {workerAnomalies.map((item) => <article className={`anomaly-item anomaly-item--${item.tone}`} key={item.id}><TrendDown size={22} /><div><strong>{item.title}</strong><p>{item.detail}</p></div></article>)}
          </div>
        </Card>
      </section>

      <section className="page-section chart-grid">
        <ChartCard title="Weekly earnings" subtitle="Net income across the current month.">
          <ResponsiveContainer width="100%" height="100%"><BarChart data={weeklyIncome} accessibilityLayer><CartesianGrid stroke={chartColors.grid} vertical={false} /><XAxis dataKey="week" tickLine={false} axisLine={false} /><YAxis tickFormatter={(value) => `${Math.round(value / 1000)}k`} tickLine={false} axisLine={false} width={38} /><Tooltip content={<ChartTooltip formatter={formatPKR} />} /><Bar dataKey="net" name="Net income" fill={chartColors.primary} radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Hourly earnings" subtitle="Net earnings per hour.">
          <ResponsiveContainer width="100%" height="100%"><LineChart data={hourlyTrend} accessibilityLayer><CartesianGrid stroke={chartColors.grid} vertical={false} /><XAxis dataKey="month" tickLine={false} axisLine={false} /><YAxis tickLine={false} axisLine={false} width={38} /><Tooltip content={<ChartTooltip formatter={(value) => `PKR ${value}`} />} /><Line type="monotone" dataKey="rate" name="Hourly rate" stroke={chartColors.primary} strokeWidth={3} /></LineChart></ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Effective deductions" subtitle="Deductions as a share of gross earnings.">
          <ResponsiveContainer width="100%" height="100%"><BarChart data={commissionTrend} accessibilityLayer><CartesianGrid stroke={chartColors.grid} vertical={false} /><XAxis dataKey="month" tickLine={false} axisLine={false} /><YAxis tickFormatter={(value) => `${value}%`} tickLine={false} axisLine={false} width={38} /><Tooltip content={<ChartTooltip formatter={(value) => `${value}%`} />} /><Bar dataKey="percent" name="Deduction rate" fill={chartColors.secondary} radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer>
        </ChartCard>
      </section>

      <section className="page-section">
        <div className="section-head"><div><h2>Recent shifts</h2><p>Your latest sample earnings records.</p></div><Link className="text-link" to="/earnings?demo=1">View all</Link></div>
        <Card padded={false}><ShiftTable shifts={sampleShifts.slice(0, 3)} /></Card>
      </section>
    </Page>
  );
}
