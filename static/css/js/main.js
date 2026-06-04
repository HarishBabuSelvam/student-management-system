// Sidebar toggle
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const main = document.getElementById('mainContent');
    if (window.innerWidth <= 768) {
        sidebar.classList.toggle('open');
    } else {
        const collapsed = sidebar.style.width === '0px';
        sidebar.style.width = collapsed ? '240px' : '0px';
        main.style.marginLeft = collapsed ? '240px' : '0px';
    }
}

// Dark mode toggle
function toggleTheme() {
    const html = document.documentElement;
    const icon = document.getElementById('themeIcon');
    const isDark = html.getAttribute('data-theme') === 'dark';
    html.setAttribute('data-theme', isDark ? 'light' : 'dark');
    icon.className = isDark ? 'fas fa-moon' : 'fas fa-sun';
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
}

// Restore saved theme on page load
(function () {
    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    const icon = document.getElementById('themeIcon');
    if (icon) icon.className = saved === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
})();

// Auto dismiss alerts after 4 seconds
setTimeout(() => {
    document.querySelectorAll('.alert').forEach(a => {
        const alert = bootstrap.Alert.getOrCreateInstance(a);
        if (alert) alert.close();
    });
}, 4000);