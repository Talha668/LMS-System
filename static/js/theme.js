// static/js/theme.js

class ThemeManager {
    constructor() {
        this.theme = localStorage.getItem('theme') || 'light';
        this.init();
    }
    
    init() {
        // Apply theme on load
        this.applyTheme(this.theme);
        
        // Create theme toggle button
        this.createToggleButton();
        
        // Listen for system theme changes
        this.watchSystemTheme();
    }
    
    applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
            document.body.classList.add('dark-mode');
        } else {
            document.documentElement.removeAttribute('data-theme');
            document.body.classList.remove('dark-mode');
        }
        
        localStorage.setItem('theme', theme);
        this.theme = theme;
        this.updateToggleIcon();
    }
    
    toggle() {
        const newTheme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
    }
    
    createToggleButton() {
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'theme-toggle btn btn-outline-light';
        toggleBtn.setAttribute('aria-label', 'Toggle theme');
        toggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
        toggleBtn.onclick = () => this.toggle();
        
        // Add to navbar
        const navbar = document.querySelector('.navbar-nav');
        if (navbar) {
            const li = document.createElement('li');
            li.className = 'nav-item';
            li.appendChild(toggleBtn);
            navbar.appendChild(li);
        }
        
        this.toggleBtn = toggleBtn;
        this.updateToggleIcon();
    }
    
    updateToggleIcon() {
        if (!this.toggleBtn) return;
        const icon = this.toggleBtn.querySelector('i');
        if (this.theme === 'dark') {
            icon.className = 'fas fa-sun';
            this.toggleBtn.title = 'Switch to light mode';
        } else {
            icon.className = 'fas fa-moon';
            this.toggleBtn.title = 'Switch to dark mode';
        }
    }
    
    watchSystemTheme() {
        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!localStorage.getItem('theme')) {
                    this.applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }
}

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});