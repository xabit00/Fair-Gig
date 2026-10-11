export const isDemoMode = () => import.meta.env.DEV && (
  import.meta.env.VITE_USE_MOCKS === "true" || new URLSearchParams(window.location.search).get("demo") === "1"
);

export const workerSummary = {
  monthlyNet: 68450,
  verifiedIncome: 54200,
  pendingShifts: 3,
  hoursWorked: 186.5,
  averageHourlyRate: 367,
  verifiedPercent: 79.2,
  averageCommission: 20.4,
};

export const incomeTrend = [
  { month: "Jul", net: 61200, cityMedian: 54700 },
  { month: "Aug", net: 64600, cityMedian: 55900 },
  { month: "Sep", net: 68450, cityMedian: 57100 },
];

export const weeklyIncome = [
  { week: "Week 1", net: 17150 },
  { week: "Week 2", net: 18100 },
  { week: "Week 3", net: 15400 },
  { week: "Week 4", net: 17800 },
];

export const hourlyTrend = [
  { month: "Jul", rate: 329 },
  { month: "Aug", rate: 348 },
  { month: "Sep", rate: 367 },
];

export const commissionTrend = [
  { month: "Jul", percent: 18.1 },
  { month: "Aug", percent: 19.4 },
  { month: "Sep", percent: 23.7 },
];

export const sampleShifts = [
  { id: "9c3d3a2b-a463-4e4f-a513-454047e16961", date: "2026-09-28", platform: "inDrive", hours_worked: 8.5, gross_earned: 4650, deductions: 650, net_received: 4000, verification_status: "confirmed", screenshot_url: "https://example.com/evidence/shift-1" },
  { id: "fcf7e27f-74e1-4d94-9aac-b0fb7d2fb7d5", date: "2026-09-27", platform: "Foodpanda", hours_worked: 7, gross_earned: 3820, deductions: 820, net_received: 3000, verification_status: "pending", screenshot_url: "https://example.com/evidence/shift-2" },
  { id: "e8e0cfb7-9d73-4124-95e7-6962e20c7366", date: "2026-09-25", platform: "Bykea", hours_worked: 9, gross_earned: 5100, deductions: 1450, net_received: 3650, verification_status: "discrepancy_flagged", screenshot_url: "https://example.com/evidence/shift-3" },
  { id: "4712df9f-1522-4398-a82e-7689ae04482a", date: "2026-09-23", platform: "inDrive", hours_worked: 6.5, gross_earned: 3450, deductions: 480, net_received: 2970, verification_status: "confirmed", screenshot_url: "https://example.com/evidence/shift-4" },
];

export const workerAnomalies = [
  { id: "commission", title: "Higher deduction rate", detail: "Foodpanda deductions reached 23.7%, above your recent average of 18.8%.", tone: "warning" },
  { id: "income", title: "Monthly income drop", detail: "Your earnings dropped by 24% compared with last month.", tone: "danger" },
];

export const analyticsData = {
  kpis: { worker_count: 40, total_net_received: 7428900, median_monthly_income: 57450, effective_deduction_percent: 20.8, minimum_group_size: 5 },
  trend: [
    { month: "Jul", median: 56800, deductions: 18.4 },
    { month: "Aug", median: 58350, deductions: 19.1 },
    { month: "Sep", median: 57450, deductions: 20.8 },
  ],
  platforms: [
    { platform: "inDrive", worker_count: 17, median_monthly_income: 63800, effective_deduction_percent: 15.2 },
    { platform: "Foodpanda", worker_count: 14, median_monthly_income: 52100, effective_deduction_percent: 24.1 },
    { platform: "Bykea", worker_count: 12, median_monthly_income: 55800, effective_deduction_percent: 22.7 },
    { platform: "Upwork", worker_count: 8, median_monthly_income: 71900, effective_deduction_percent: 13.6 },
  ],
  zones: [
    { city_zone: "Karachi Central", worker_count: 11, median_monthly_income: 59200 },
    { city_zone: "Lahore North", worker_count: 10, median_monthly_income: 56800 },
    { city_zone: "Islamabad-Rawalpindi", worker_count: 10, median_monthly_income: 62100 },
    { city_zone: "Faisalabad Urban", worker_count: 9, median_monthly_income: 49700 },
  ],
  categories: [
    { category: "Ride hailing", count: 17 },
    { category: "Delivery", count: 14 },
    { category: "Freelancing", count: 9 },
  ],
  grievances: [
    { category: "Commission change", count: 14 },
    { category: "Account deactivation", count: 9 },
    { category: "Payment delay", count: 7 },
    { category: "Safety", count: 5 },
  ],
  vulnerabilityFlags: [
    { group: "Delivery · Faisalabad Urban", workers: 7, signal: "Income decline", change: "-23%", severity: "flagged" },
    { group: "Ride hailing · Karachi Central", workers: 9, signal: "Commission increase", change: "+5.4 pts", severity: "pending" },
    { group: "Freelancing · Lahore North", workers: 6, signal: "Payment delays", change: "8 reports", severity: "pending" },
  ],
};

export const sampleGrievances = [
  { id: "3d639ff8-c017-45ee-9a48-48670c4e80ae", platform: "Foodpanda", category: "commission_change", description: "The deduction increased without a clear notice and reduced my weekly take-home pay.", status: "escalated", cluster_id: "commission-sep-26", tags: ["commission", "notice"], created_at: "2026-09-29T10:30:00Z" },
  { id: "132bf0c9-812c-460d-8ab9-b0443d5e733b", platform: "Bykea", category: "payment_delay", description: "Two completed weeks are still shown as pending in the payout screen.", status: "reviewing", cluster_id: "payout-delay-26", tags: ["payout"], created_at: "2026-09-27T14:15:00Z" },
  { id: "f379761d-62be-4707-bab5-b9185598173a", platform: "inDrive", category: "account_deactivation", description: "My account was paused after a document check and no reason was provided.", status: "submitted", cluster_id: null, tags: [], created_at: "2026-09-25T08:45:00Z" },
];

export const verificationQueue = sampleShifts.map((shift, index) => ({
  ...shift,
  worker_name: ["Ahsan Raza", "Mehwish Noor", "Bilal Ahmed", "Sana Iqbal"][index],
  submitted_at: `${shift.date}T${["17:20", "19:05", "21:10", "16:40"][index]}:00Z`,
}));
