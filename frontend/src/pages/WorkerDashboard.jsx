import { Link } from "react-router-dom";
import { Clock, CurrencyCircleDollar, Plus, ShieldCheck, TrendDown, Wallet } from "@phosphor-icons/react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useAuth } from "../auth/AuthContext";
import { Card, KpiCard } from "../components/ui";
import { commissionTrend, hourlyTrend, incomeTrend, isDemoMode, sampleShifts, weeklyIncome, workerAnomalies, workerSummary } from "../mocks/data";
import { ChartCard, ChartTooltip, DemoNotice, EndpointUnavailable, Page, ShiftTable, chartColors, formatPKR } from "./shared";

export default function WorkerDashboard() {
  const { user } = useAuth();
  const demo = isDemoMode();
  const firstName = user.name.split(" ")[0];

  if (!demo) {
    return (
      <Page eyebrow="Worker overview" title={`Good to see you, ${firstName}`} description="Your verified income record and recent changes will appear here.">
        <div className="kpi-grid muted-kpis">
          <KpiCard label="Total earnings" value="Unavailable" icon={Wallet} />
          <KpiCard label="Average hourly rate" value="Unavailable" icon={Clock} />
          <KpiCard label="Verified earnings" value="Unavailable" icon={ShieldCheck} />
          <KpiCard label="Average commission" value="Unavailable" icon={CurrencyCircleDollar} />
        </div>
        <section className="page-section">
          <EndpointUnavailable title="Earnings history endpoint needed" message="The earnings service can create shifts but does not yet provide a worker shift list or summary. Ask the Backend Services teammate to add authenticated GET /shifts and GET /shifts/summary endpoints. Use ?demo=1 during development to inspect this dashboard with labeled sample data." />
        </section>
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
