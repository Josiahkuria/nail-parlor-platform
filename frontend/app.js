const API_BASE_URL = "http://192.168.100.65:8000/api/v1";

// ─── INITIALIZATION ───
document.addEventListener("DOMContentLoaded", () => {
    evaluateSessionState();
});

function evaluateSessionState() {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("userRole");
    const fullName = localStorage.getItem("fullName");
    const techId = localStorage.getItem("techId");

    // Clear visible views
    document.getElementById("loginSection").classList.add("hidden");
    document.getElementById("adminDashboardSection").classList.add("hidden");
    document.getElementById("techDashboardSection").classList.add("hidden");

    if (!token) {
        document.getElementById("loginSection").classList.remove("hidden");
        return;
    }

    if (role === "admin") {
        document.getElementById("adminDashboardSection").classList.remove("hidden");
        refreshAdminDashboard();
    } else {
        document.getElementById("techDashboardSection").classList.remove("hidden");
        document.getElementById("techWelcomeTitle").innerText = `Welcome, ${fullName || 'Team Member'}`;
        document.getElementById("lockedTechId").value = techId;
        refreshTechDashboard();
    }
}

// ─── AUTHENTICATION GATEWAY ───
document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById("loginError");
    errorEl.classList.add("hidden");

    try {
        const formData = new URLSearchParams();
        formData.append("username", document.getElementById("loginUsername").value);
        formData.append("password", document.getElementById("loginPassword").value);

        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData
        });

        if (!response.ok) throw new Error("Invalid credentials setup.");
        const data = await response.json();

        localStorage.setItem("token", data.access_token);
        localStorage.setItem("userRole", data.role);
        localStorage.setItem("techId", data.tech_id || "");
        localStorage.setItem("fullName", data.full_name || "");

        evaluateSessionState();
    } catch (err) {
        errorEl.innerText = err.message;
        errorEl.classList.remove("hidden");
    }
});

// Terminate Session Buttons
document.querySelectorAll(".logoutBtn").forEach(btn => {
    btn.addEventListener("click", () => {
        localStorage.clear();
        evaluateSessionState();
    });
});

// Admin Account Registration Window Toggle
document.getElementById("toggleRegBtn").addEventListener("click", () => {
    document.getElementById("adminManagementZone").classList.toggle("hidden");
});

// Technician History Table Toggle
document.getElementById("toggleTechHistoryBtn").addEventListener("click", () => {
    const historyZone = document.getElementById("techHistoryZone");
    const toggleBtn = document.getElementById("toggleTechHistoryBtn");
    
    historyZone.classList.toggle("hidden");
    if (historyZone.classList.contains("hidden")) {
        toggleBtn.innerText = "📊 View My Weekly Logged History";
    } else {
        toggleBtn.innerText = "✖️ Hide My Weekly Logged History";
    }
});

// ─── TRANSACTION LOGGERS ───
document.getElementById("adminServiceForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    await commitTransaction({
        tech_id: parseInt(document.getElementById("adminTechId").value),
        client_name: document.getElementById("adminClientName").value,
        service_name: document.getElementById("adminServiceName").value,
        total_charged: parseFloat(document.getElementById("adminTotalCharged").value)
    }, "adminServiceForm", refreshAdminDashboard);
});

document.getElementById("techServiceForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const techId = localStorage.getItem("techId");
    await commitTransaction({
        tech_id: parseInt(techId),
        client_name: document.getElementById("techClientName").value,
        service_name: document.getElementById("techServiceName").value,
        total_charged: parseFloat(document.getElementById("techTotalCharged").value)
    }, "techServiceForm", refreshTechDashboard);
});

async function commitTransaction(payload, formId, successCallback) {
    const token = localStorage.getItem("token");
    try {
        const response = await fetch(`${API_BASE_URL}/operations/transactions`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error("Log entry blocked.");
        
        document.getElementById(formId).reset();
        const techId = localStorage.getItem("techId");
        if (document.getElementById("lockedTechId")) {
            document.getElementById("lockedTechId").value = techId;
        }
        successCallback();
    } catch (err) {
        alert(err.message);
    }
}

// ─── ADMIN REGISTER NEW TECH ───
document.getElementById("techRegistrationForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const feedbackEl = document.getElementById("registrationFeedback");
    feedbackEl.classList.add("hidden");
    const token = localStorage.getItem("token");

    try {
        const params = new URLSearchParams({
            username: document.getElementById("newTechUsername").value,
            plain_pass: document.getElementById("newTechPassword").value,
            full_name: document.getElementById("newTechFullName").value
        });

        const response = await fetch(`${API_BASE_URL}/admin/techs?${params.toString()}`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (!response.ok) throw new Error("Account generation blocked.");
        const data = await response.json();

        feedbackEl.innerText = `Generated profile for ${data.name}! (ID: #${data.tech_id})`;
        feedbackEl.className = "text-xs text-emerald-600 font-medium block";
        document.getElementById("techRegistrationForm").reset();
        refreshAdminDashboard();
    } catch (err) {
        feedbackEl.innerText = err.message;
        feedbackEl.className = "text-xs text-red-500 font-medium block";
    }
});

// ─── DASHBOARD REFRESH METRICS ───
async function refreshAdminDashboard() {
    const token = localStorage.getItem("token");
    try {
        const response = await fetch(`${API_BASE_URL}/admin/dashboard`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!response.ok) return;
        const data = await response.json();

        document.getElementById("grossRevenue").innerText = `KSh ${data.gross_revenue.toLocaleString()}`;
        document.getElementById("techPayouts").innerText = `KSh ${data.total_payouts_to_techs.toLocaleString()}`;
        document.getElementById("shopProfit").innerText = `KSh ${data.net_shop_profit.toLocaleString()}`;

        const techBody = document.getElementById("techMatrixBody");
        if (techBody && data.technicians_breakdown) {
            techBody.innerHTML = "";
            data.technicians_breakdown.forEach(tech => {
                const row = document.createElement("tr");
                row.className = "divide-x divide-neutral-100 hover:bg-neutral-50/50 transition";
                row.innerHTML = `
                    <td class="py-2.5 px-4 font-bold text-neutral-400">#${tech.tech_id}</td>
                    <td class="py-2.5 px-4 font-sans font-medium text-neutral-900">${tech.name}</td>
                    <td class="py-2.5 px-4 text-center font-bold">${tech.services_logged}</td>
                    <td class="py-2.5 px-4 font-bold text-blue-600">KSh ${tech.commission_earned.toLocaleString()}</td>
                `;
                techBody.appendChild(row);
            });
        }
    } catch (err) {
        console.error(err);
    }
}

async function refreshTechDashboard() {
    const token = localStorage.getItem("token");
    const techId = parseInt(localStorage.getItem("techId"));
    try {
        const response = await fetch(`${API_BASE_URL}/admin/dashboard`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!response.ok) return;
        const data = await response.json();

        // 1. Render Commission Summary Card
        const myRecord = data.technicians_breakdown.find(t => t.tech_id == techId);
        document.getElementById("myPersonalCommission").innerText = myRecord ? `KSh ${myRecord.commission_earned.toLocaleString()}` : "KSh 0";

        // 2. Render Personal Weekly Activities List
        const historyBody = document.getElementById("workerHistoryBody");
        if (historyBody && data.recent_transactions) {
            historyBody.innerHTML = "";
            const myTransactions = data.recent_transactions.filter(tx => tx.tech_id === techId);
            document.getElementById("myCustomerCount").innerText = `${myTransactions.length} Done`;

            if (myTransactions.length === 0) {
                historyBody.innerHTML = `<tr><td colspan="3" class="py-4 text-center text-neutral-400 font-sans italic">No logs found for your profile index.</td></tr>`;
                return;
            }

            myTransactions.forEach(tx => {
                const row = document.createElement("tr");
                row.className = "divide-x divide-neutral-100 hover:bg-neutral-50/50 transition";
                row.innerHTML = `
                    <td class="py-2.5 px-4 font-medium text-neutral-900">${tx.client_name}</td>
                    <td class="py-2.5 px-4 text-neutral-500">${tx.service_name || tx.service_rendered || 'Nail Service'}</td>
                    <td class="py-2.5 px-4 font-bold font-mono text-emerald-600">KSh ${(tx.total_charged || tx.amount || 0).toLocaleString()}</td>
                `;
                historyBody.appendChild(row);
            });
        }
    } catch (err) {
        console.error(err);
    }
}