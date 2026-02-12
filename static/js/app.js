/* Future Wallet — Frontend Logic */

// ==================== CHART INSTANCES ====================
let chartBalance = null;
let chartNetWorth = null;
let chartCredit = null;
let chartAssets = null;
let chartBranchBalance = null;
let chartBranchNetWorth = null;

// ==================== CHART.JS GLOBAL DEFAULTS ====================
// Guard against Chart.js not loading (offline, CDN blocked, etc.)
if (typeof Chart !== 'undefined') {
    Chart.defaults.color = '#8a8fb5';
    Chart.defaults.borderColor = '#1e2352';
    Chart.defaults.font.family = "'Segoe UI', system-ui, sans-serif";
    Chart.defaults.plugins.legend.labels.boxWidth = 12;
    Chart.defaults.animation.duration = 800;
} else {
    console.warn('Chart.js not available; charts will be disabled.');
}

const COLORS = {
    blue: '#4e7cff',
    green: '#00d4aa',
    yellow: '#ffd600',
    red: '#ff4757',
    purple: '#a855f7',
    orange: '#ff9f43',
    blueAlpha: 'rgba(78,124,255,0.15)',
    greenAlpha: 'rgba(0,212,170,0.15)',
    redAlpha: 'rgba(255,71,87,0.15)',
};

// ==================== SAMPLE DATA PRE-FILL ====================
document.addEventListener('DOMContentLoaded', () => {
    // Pre-fill sample scenario
    addIncomeRow('Salary', 4500, 'USD', 'monthly');
    addIncomeRow('Freelance', 800, 'USD', 'monthly');

    addExpenseRow('Rent', 1500, 'USD', 'monthly', 'housing');
    addExpenseRow('Groceries', 400, 'USD', 'monthly', 'food');
    addExpenseRow('Utilities', 150, 'USD', 'monthly', 'utilities');
    addExpenseRow('Subscriptions', 50, 'USD', 'monthly', 'entertainment');
    addExpenseRow('Transport', 200, 'USD', 'monthly', 'transport');

    addDebtRow('Student Loan', 15000, 0.055, 300);
    addDebtRow('Credit Card', 3000, 0.19, 150);

    addAssetRow('Savings Account', 8000, 'liquid', 0.01, 0.035, 0, 0);
    addAssetRow('Stock Portfolio', 12000, 'volatile', 0.35, 0.0, 0, 0.01);
    addAssetRow('Bond Fund', 5000, 'yield-generating', 0.05, 0.045, 0, 0.005);
    addAssetRow('Real Estate REIT', 10000, 'illiquid', 0.15, 0.06, 180, 0.03);

    // Horizon slider label
    const horizon = document.getElementById('horizon');
    const label = document.getElementById('horizonLabel');
    if (horizon && label) {
        horizon.addEventListener('input', () => { label.textContent = horizon.value; });
    }
});

// ==================== INTRO OVERLAY, CURSOR & SCROLL EFFECTS ====================
document.addEventListener('DOMContentLoaded', () => {
    const overlay = document.getElementById('helloOverlay');
    const header = document.getElementById('siteHeader');
    const scrollLine = document.getElementById('scrollLine');
    const cursorDot = document.getElementById('cursorDot');
    const cursorRing = document.getElementById('cursorRing');

    // Slide intro overlay away after a short delay
    setTimeout(() => {
        if (overlay) overlay.classList.add('hidden');
        if (header) header.classList.add('visible');
    }, 1400);

    // Custom cursor
    if (cursorDot && cursorRing) {
        document.addEventListener('mousemove', (e) => {
            const x = e.clientX;
            const y = e.clientY;
            cursorDot.style.left = `${x}px`;
            cursorDot.style.top = `${y}px`;
            cursorRing.style.left = `${x}px`;
            cursorRing.style.top = `${y}px`;
        });

        // Enlarge ring when hovering interactive elements
        const hoverSelectors = 'a, button, [role="button"], input, select, textarea';
        document.querySelectorAll(hoverSelectors).forEach((el) => {
            el.addEventListener('mouseenter', () => {
                document.body.classList.add('cursor-hover');
            });
            el.addEventListener('mouseleave', () => {
                document.body.classList.remove('cursor-hover');
            });
        });
    }

    // Scroll progress line
    if (scrollLine) {
        const updateScrollLine = () => {
            const doc = document.documentElement;
            const scrollTop = window.scrollY || doc.scrollTop;
            const scrollHeight = doc.scrollHeight - window.innerHeight;
            const progress = scrollHeight > 0 ? scrollTop / scrollHeight : 0;
            scrollLine.style.height = `${progress * 100}%`;
        };
        window.addEventListener('scroll', updateScrollLine);
        updateScrollLine();
    }

    // Reveal animations for elements with .reveal or .stagger-reveal
    const revealEls = document.querySelectorAll('.reveal, .stagger-reveal');
    if ('IntersectionObserver' in window && revealEls.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.15 });

        revealEls.forEach((el) => observer.observe(el));
    } else {
        // Fallback: make everything visible
        revealEls.forEach((el) => el.classList.add('visible'));
    }
});

// ==================== ROW MANAGEMENT ====================
let rowCounter = 0;

function addRow(type) {
    if (type === 'income') addIncomeRow();
    else if (type === 'expense') addExpenseRow();
    else if (type === 'debt') addDebtRow();
    else if (type === 'asset') addAssetRow();
}

function removeRow(id) {
    document.getElementById(id)?.remove();
}

function addIncomeRow(name = '', amount = 0, currency = 'USD', frequency = 'monthly') {
    const id = 'row_' + (++rowCounter);
    const html = `
    <div class="input-row" id="${id}">
        <button class="btn-remove" onclick="removeRow('${id}')">&times;</button>
        <div class="row g-1">
            <div class="col-5"><input type="text" class="form-control form-control-sm inc-name" placeholder="Name" value="${name}"></div>
            <div class="col-3"><input type="number" class="form-control form-control-sm inc-amount" placeholder="Amount" value="${amount}"></div>
            <div class="col-2"><select class="form-select form-select-sm inc-currency">${currencyOpts(currency)}</select></div>
            <div class="col-2"><select class="form-select form-select-sm inc-freq">${freqOpts(frequency)}</select></div>
        </div>
    </div>`;
    document.getElementById('incomeRows').insertAdjacentHTML('beforeend', html);
}

function addExpenseRow(name = '', amount = 0, currency = 'USD', frequency = 'monthly', category = 'general') {
    const id = 'row_' + (++rowCounter);
    const html = `
    <div class="input-row" id="${id}">
        <button class="btn-remove" onclick="removeRow('${id}')">&times;</button>
        <div class="row g-1">
            <div class="col-4"><input type="text" class="form-control form-control-sm exp-name" placeholder="Name" value="${name}"></div>
            <div class="col-2"><input type="number" class="form-control form-control-sm exp-amount" placeholder="Amt" value="${amount}"></div>
            <div class="col-2"><select class="form-select form-select-sm exp-currency">${currencyOpts(currency)}</select></div>
            <div class="col-2"><select class="form-select form-select-sm exp-freq">${freqOpts(frequency)}</select></div>
            <div class="col-2"><input type="text" class="form-control form-control-sm exp-cat" placeholder="Cat" value="${category}"></div>
        </div>
    </div>`;
    document.getElementById('expenseRows').insertAdjacentHTML('beforeend', html);
}

function addDebtRow(name = '', principal = 0, rate = 0.05, minPay = 100) {
    const id = 'row_' + (++rowCounter);
    const html = `
    <div class="input-row" id="${id}">
        <button class="btn-remove" onclick="removeRow('${id}')">&times;</button>
        <div class="row g-1">
            <div class="col-4"><input type="text" class="form-control form-control-sm debt-name" placeholder="Name" value="${name}"></div>
            <div class="col-3"><input type="number" class="form-control form-control-sm debt-principal" placeholder="Principal" value="${principal}"></div>
            <div class="col-2"><input type="number" class="form-control form-control-sm debt-rate" placeholder="Rate" step="0.01" value="${rate}"></div>
            <div class="col-3"><input type="number" class="form-control form-control-sm debt-minpay" placeholder="Min Pay" value="${minPay}"></div>
        </div>
    </div>`;
    document.getElementById('debtRows').insertAdjacentHTML('beforeend', html);
}

function addAssetRow(name = '', value = 0, type = 'liquid', volatility = 0, yieldRate = 0, lockDays = 0, penalty = 0) {
    const id = 'row_' + (++rowCounter);
    const html = `
    <div class="input-row" id="${id}">
        <button class="btn-remove" onclick="removeRow('${id}')">&times;</button>
        <div class="row g-1 mb-1">
            <div class="col-4"><input type="text" class="form-control form-control-sm asset-name" placeholder="Name" value="${name}"></div>
            <div class="col-3"><input type="number" class="form-control form-control-sm asset-value" placeholder="Value" value="${value}"></div>
            <div class="col-5">
                <select class="form-select form-select-sm asset-type">
                    <option value="liquid" ${type === 'liquid' ? 'selected' : ''}>Liquid</option>
                    <option value="illiquid" ${type === 'illiquid' ? 'selected' : ''}>Illiquid</option>
                    <option value="yield-generating" ${type === 'yield-generating' ? 'selected' : ''}>Yield-Gen</option>
                    <option value="volatile" ${type === 'volatile' ? 'selected' : ''}>Volatile</option>
                </select>
            </div>
        </div>
        <div class="row g-1">
            <div class="col-4"><input type="number" class="form-control form-control-sm asset-vol" placeholder="Volatility" step="0.01" min="0" max="1" value="${volatility}"></div>
            <div class="col-3"><input type="number" class="form-control form-control-sm asset-yield" placeholder="Yield" step="0.01" value="${yieldRate}"></div>
            <div class="col-3"><input type="number" class="form-control form-control-sm asset-lock" placeholder="Lock(d)" value="${lockDays}"></div>
            <div class="col-2"><input type="number" class="form-control form-control-sm asset-penalty" placeholder="Pen%" step="0.01" value="${penalty}"></div>
        </div>
    </div>`;
    document.getElementById('assetRows').insertAdjacentHTML('beforeend', html);
}

function currencyOpts(selected) {
    return ['USD', 'EUR', 'GBP', 'PKR', 'JPY'].map(c =>
        `<option value="${c}" ${c === selected ? 'selected' : ''}>${c}</option>`
    ).join('');
}

function freqOpts(selected) {
    return ['daily', 'weekly', 'monthly'].map(f =>
        `<option value="${f}" ${f === selected ? 'selected' : ''}>${f}</option>`
    ).join('');
}

// ==================== GATHER FORM DATA ====================
function gatherInputs() {
    const incomes = [];
    document.querySelectorAll('#incomeRows .input-row').forEach(row => {
        incomes.push({
            name: row.querySelector('.inc-name').value || 'Income',
            amount: parseFloat(row.querySelector('.inc-amount').value) || 0,
            currency: row.querySelector('.inc-currency').value,
            frequency: row.querySelector('.inc-freq').value,
        });
    });

    const expenses = [];
    document.querySelectorAll('#expenseRows .input-row').forEach(row => {
        expenses.push({
            name: row.querySelector('.exp-name').value || 'Expense',
            amount: parseFloat(row.querySelector('.exp-amount').value) || 0,
            currency: row.querySelector('.exp-currency').value,
            frequency: row.querySelector('.exp-freq').value,
            category: row.querySelector('.exp-cat').value || 'general',
        });
    });

    const debts = [];
    document.querySelectorAll('#debtRows .input-row').forEach(row => {
        debts.push({
            name: row.querySelector('.debt-name').value || 'Debt',
            principal: parseFloat(row.querySelector('.debt-principal').value) || 0,
            interest_rate: parseFloat(row.querySelector('.debt-rate').value) || 0,
            min_payment: parseFloat(row.querySelector('.debt-minpay').value) || 0,
        });
    });

    const assets = [];
    document.querySelectorAll('#assetRows .input-row').forEach(row => {
        assets.push({
            name: row.querySelector('.asset-name').value || 'Asset',
            value: parseFloat(row.querySelector('.asset-value').value) || 0,
            asset_type: row.querySelector('.asset-type').value,
            volatility: parseFloat(row.querySelector('.asset-vol').value) || 0,
            yield_rate: parseFloat(row.querySelector('.asset-yield').value) || 0,
            lock_period_days: parseInt(row.querySelector('.asset-lock').value) || 0,
            sale_penalty_pct: parseFloat(row.querySelector('.asset-penalty').value) || 0,
        });
    });

    return {
        balance: parseFloat(document.getElementById('balance').value) || 5000,
        currency: document.getElementById('currency').value,
        horizon_days: parseInt(document.getElementById('horizon').value) || 365,
        seed: parseInt(document.getElementById('seed').value) || 42,
        income_streams: incomes,
        expenses: expenses,
        debts: debts,
        assets: assets,
    };
}

// ==================== RUN SIMULATION ====================
async function runSimulation() {
    const btn = document.getElementById('runBtn');
    btn.disabled = true;
    btn.textContent = 'Simulating...';

    try {
        const payload = gatherInputs();
        const resp = await fetch('/api/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!resp.ok) {
            const err = await resp.json();
            alert('Simulation error: ' + (err.error || 'Unknown'));
            return;
        }

        const data = await resp.json();
        renderResults(data);
    } catch (e) {
        alert('Request failed: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Run Simulation';
    }
}

// ==================== RENDER RESULTS ====================
function renderResults(data) {
    // Reveal results + analytics sections in the new layout
    const resultsSection = document.getElementById('results');
    if (resultsSection) resultsSection.style.display = '';

    const chartMarquee = document.getElementById('chartMarquee');
    if (chartMarquee) chartMarquee.style.display = '';

    const chartsSection = document.getElementById('charts');
    if (chartsSection) chartsSection.style.display = '';

    const branchSection = document.getElementById('branch');
    if (branchSection) branchSection.style.display = '';

    const eventsSection = document.getElementById('events');
    if (eventsSection) eventsSection.style.display = '';

    const s = data.summary;

    // Summary cards
    setCardValue('summFinalBalance', formatMoney(s.final_balance), s.final_balance >= 0 ? 'val-positive' : 'val-negative');
    setCardValue('summCollapseProb', s.collapse_probability + '%', s.collapse_probability > 20 ? 'val-negative' : 'val-positive');
    setCardValue('summCollapseTiming', s.collapse_timing !== null ? 'Day ' + s.collapse_timing : 'Never', s.collapse_timing !== null ? 'val-negative' : 'val-positive');
    setCardValue('summNetWorth', formatMoney(s.final_net_worth), s.final_net_worth >= 0 ? 'val-positive' : 'val-negative');
    setCardValue('summVibe', s.financial_vibe, '');
    setCardValue('summPet', s.pet_state, '');

    const csClass = s.final_credit_score >= 700 ? 'credit-green' : s.final_credit_score >= 500 ? 'credit-yellow' : 'credit-red';
    setCardValue('summCreditScore', Math.round(s.final_credit_score), csClass);
    setCardValue('summSRI', s.shock_resilience_index + ' / 100', s.shock_resilience_index >= 60 ? 'val-positive' : 'val-negative');

    // Charts
    renderBalanceChart(data.daily_data);
    renderNetWorthChart(data.daily_data);
    renderCreditChart(data.daily_data);
    renderAssetsChart(data.daily_data);

    // Events
    renderEvents(data.events);

    // Update branch day max
    document.getElementById('branchDay').max = data.daily_data.length - 1;
}

function setCardValue(id, value, className) {
    const el = document.getElementById(id);
    el.textContent = value;
    el.className = 'summary-value' + (className ? ' ' + className : '');
}

function formatMoney(val) {
    if (val === null || val === undefined) return '—';
    const sign = val < 0 ? '-' : '';
    return sign + '$' + Math.abs(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ==================== CHART RENDERERS ====================
function sampleData(arr, maxPoints) {
    if (arr.length <= maxPoints) return arr;
    const step = Math.ceil(arr.length / maxPoints);
    const result = [];
    for (let i = 0; i < arr.length; i += step) result.push(arr[i]);
    if (result[result.length - 1] !== arr[arr.length - 1]) result.push(arr[arr.length - 1]);
    return result;
}

function renderBalanceChart(dailyData) {
    const sampled = sampleData(dailyData, 500);
    const labels = sampled.map(d => d.day);
    const balances = sampled.map(d => d.balance);

    if (chartBalance) chartBalance.destroy();
    chartBalance = new Chart(document.getElementById('chartBalance'), {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Balance',
                data: balances,
                borderColor: COLORS.blue,
                backgroundColor: COLORS.blueAlpha,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2,
            }, {
                label: 'Zero Line',
                data: labels.map(() => 0),
                borderColor: COLORS.red,
                borderDash: [5, 5],
                borderWidth: 1,
                pointRadius: 0,
                fill: false,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } },
            scales: {
                x: { title: { display: true, text: 'Day' } },
                y: { title: { display: true, text: 'Balance' } },
            },
        },
    });
}

function renderNetWorthChart(dailyData) {
    const sampled = sampleData(dailyData, 500);
    const labels = sampled.map(d => d.day);

    if (chartNetWorth) chartNetWorth.destroy();
    chartNetWorth = new Chart(document.getElementById('chartNetWorth'), {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Net Worth',
                data: sampled.map(d => d.net_worth),
                borderColor: COLORS.green,
                backgroundColor: COLORS.greenAlpha,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } },
            scales: {
                x: { title: { display: true, text: 'Day' } },
                y: { title: { display: true, text: 'Net Worth' } },
            },
        },
    });
}

function renderCreditChart(dailyData) {
    const sampled = sampleData(dailyData, 500);
    const labels = sampled.map(d => d.day);

    if (chartCredit) chartCredit.destroy();
    chartCredit = new Chart(document.getElementById('chartCredit'), {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Credit Score',
                data: sampled.map(d => d.credit_score),
                borderColor: COLORS.yellow,
                backgroundColor: 'rgba(255,214,0,0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } },
            scales: {
                x: { title: { display: true, text: 'Day' } },
                y: { min: 300, max: 850, title: { display: true, text: 'Score' } },
            },
        },
    });
}

function renderAssetsChart(dailyData) {
    const sampled = sampleData(dailyData, 500);
    const labels = sampled.map(d => d.day);

    if (chartAssets) chartAssets.destroy();
    chartAssets = new Chart(document.getElementById('chartAssets'), {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Total Assets (NAV)',
                data: sampled.map(d => d.nav),
                borderColor: COLORS.purple,
                backgroundColor: 'rgba(168,85,247,0.12)',
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2,
            }, {
                label: 'Total Debt',
                data: sampled.map(d => d.total_debt),
                borderColor: COLORS.red,
                backgroundColor: COLORS.redAlpha,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } },
            scales: {
                x: { title: { display: true, text: 'Day' } },
                y: { title: { display: true, text: 'Value' } },
            },
        },
    });
}

// ==================== EVENTS LOG ====================
function renderEvents(events) {
    const container = document.getElementById('eventsLog');
    if (events.length === 0) {
        container.innerHTML = '<p class="text-muted">No notable events occurred.</p>';
        return;
    }
    // Show latest 200 events max
    const display = events.slice(-200);
    container.innerHTML = display.map(e => `
        <div class="event-item severity-${e.severity}">
            <span class="event-day">Day ${e.day}</span>
            <span class="event-type">${e.event_type}</span>
            ${e.description}
            ${e.amount ? ' <strong>(' + formatMoney(e.amount) + ')</strong>' : ''}
        </div>
    `).join('');
}

// ==================== WHAT-IF BRANCHING ====================
async function runBranch() {
    const branchDay = parseInt(document.getElementById('branchDay').value) || 90;
    const balanceMod = parseFloat(document.getElementById('branchBalance').value) || 0;
    const removeExp = document.getElementById('branchRemoveExpense').value.trim();

    const modifications = {};
    if (balanceMod !== 0) modifications.balance_delta = balanceMod;
    if (removeExp) modifications.remove_expense = removeExp;

    // Build modifications for the API
    const apiMods = {};
    if (removeExp) apiMods.remove_expense = removeExp;

    try {
        const resp = await fetch('/api/branch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                branch_day: branchDay,
                modifications: apiMods,
            }),
        });

        if (!resp.ok) {
            const err = await resp.json();
            alert('Branch error: ' + (err.error || 'Unknown'));
            return;
        }

        const data = await resp.json();
        renderBranchResults(data);
    } catch (e) {
        alert('Branch request failed: ' + e.message);
    }
}

function renderBranchResults(data) {
    const branchResults = document.getElementById('branchResults');
    if (branchResults) branchResults.style.display = '';

    const origDaily = data.original_daily || [];
    const branchDaily = data.branched_daily || [];

    const maxLen = Math.max(origDaily.length, branchDaily.length);
    const sOrig = sampleData(origDaily, 400);
    const sBranch = sampleData(branchDaily, 400);

    // Balance comparison
    if (chartBranchBalance) chartBranchBalance.destroy();
    chartBranchBalance = new Chart(document.getElementById('chartBranchBalance'), {
        type: 'line',
        data: {
            labels: sOrig.map(d => d.day),
            datasets: [{
                label: 'Original',
                data: sOrig.map(d => d.balance),
                borderColor: COLORS.blue,
                pointRadius: 0,
                borderWidth: 2,
                tension: 0.3,
            }, {
                label: 'Branched',
                data: sBranch.map(d => d.balance),
                borderColor: COLORS.green,
                borderDash: [6, 3],
                pointRadius: 0,
                borderWidth: 2,
                tension: 0.3,
            }],
        },
        options: {
            responsive: true,
            plugins: { title: { display: true, text: 'Balance: Original vs Branched' } },
            scales: {
                x: { title: { display: true, text: 'Day' } },
                y: { title: { display: true, text: 'Balance' } },
            },
        },
    });

    // Net Worth comparison
    if (chartBranchNetWorth) chartBranchNetWorth.destroy();
    chartBranchNetWorth = new Chart(document.getElementById('chartBranchNetWorth'), {
        type: 'line',
        data: {
            labels: sOrig.map(d => d.day),
            datasets: [{
                label: 'Original',
                data: sOrig.map(d => d.net_worth),
                borderColor: COLORS.blue,
                pointRadius: 0,
                borderWidth: 2,
                tension: 0.3,
            }, {
                label: 'Branched',
                data: sBranch.map(d => d.net_worth),
                borderColor: COLORS.green,
                borderDash: [6, 3],
                pointRadius: 0,
                borderWidth: 2,
                tension: 0.3,
            }],
        },
        options: {
            responsive: true,
            plugins: { title: { display: true, text: 'Net Worth: Original vs Branched' } },
            scales: {
                x: { title: { display: true, text: 'Day' } },
                y: { title: { display: true, text: 'Net Worth' } },
            },
        },
    });

    // Comparison cards
    const deltas = data.deltas || {};
    const orig = data.original || {};
    const branched = data.branched || {};

    const metrics = [
        { label: 'Final Balance', key: 'final_balance', format: formatMoney },
        { label: 'Net Worth', key: 'final_net_worth', format: formatMoney },
        { label: 'Credit Score', key: 'final_credit_score', format: v => Math.round(v) },
        { label: 'Collapse %', key: 'collapse_probability', format: v => v + '%' },
    ];

    const container = document.getElementById('branchComparison');
    container.innerHTML = metrics.map(m => {
        const origVal = orig[m.key] ?? '—';
        const branchVal = branched[m.key] ?? '—';
        const delta = deltas[m.key];
        const deltaClass = delta > 0 ? 'delta-positive' : delta < 0 ? 'delta-negative' : '';
        const deltaStr = delta !== null ? (delta > 0 ? '+' : '') + (typeof origVal === 'number' && m.format === formatMoney ? formatMoney(delta) : delta) : '';
        return `
            <div class="col-md-3 col-sm-6">
                <div class="branch-card">
                    <div class="small text-muted">${m.label}</div>
                    <div><strong>${m.format(origVal)}</strong> &rarr; <strong>${m.format(branchVal)}</strong></div>
                    <div class="delta ${deltaClass}">${deltaStr}</div>
                </div>
            </div>`;
    }).join('');
}
