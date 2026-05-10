// static/blog_script.js

lucide.createIcons();

const setHtml = (id, content) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = marked.parse(content || '');
};

// Initialize content from window.blogData
if (window.blogData) {
    setHtml('summary-content', window.blogData.summary);
    setHtml('verdict-content', window.blogData.summary);
    setHtml('market-content', window.blogData.market || '');
    setHtml('sentiment-content', window.blogData.sentiment || '');
    setHtml('fundamentals-content', window.blogData.fundamentals || '');
    setHtml('risk-content', window.blogData.summary);
}

// Global Task Poller for Blog Pages
let activeTaskId = localStorage.getItem('active_task_id');
const taskIndicator = document.getElementById('active-task-indicator');
const notificationToast = document.getElementById('notification-toast');
const toastTicker = document.getElementById('toast-ticker');
const toastViewBtn = document.getElementById('toast-view-btn');

function showToast(ticker, blogId) {
    if (!toastTicker || !notificationToast || !toastViewBtn) return;
    toastTicker.innerText = ticker;
    toastViewBtn.onclick = () => window.location.href = '/blog/' + blogId;
    notificationToast.style.display = 'block';
    setTimeout(() => notificationToast.style.transform = 'translateX(0)', 100);
    setTimeout(hideToast, 10000);
}

function hideToast() {
    if (!notificationToast) return;
    notificationToast.style.transform = 'translateX(120%)';
    setTimeout(() => notificationToast.style.display = 'none', 500);
}

if (activeTaskId) {
    if (taskIndicator) taskIndicator.classList.remove('hidden');
    const interval = setInterval(async () => {
        try {
            const res = await fetch('/status/' + activeTaskId);
            if (!res.ok) throw new Error('Status check failed');
            const data = await res.json();
            if (data.status === 'completed') {
                clearInterval(interval);
                localStorage.removeItem('active_task_id');
                if (taskIndicator) taskIndicator.classList.add('hidden');
                showToast(localStorage.getItem('active_task_ticker'), data.result.blog_id);
            } else if (data.status === 'failed') {
                clearInterval(interval);
                localStorage.removeItem('active_task_id');
                if (taskIndicator) taskIndicator.classList.add('hidden');
            }
        } catch (e) {
            console.error('Polling error:', e);
        }
    }, 5000);
}
