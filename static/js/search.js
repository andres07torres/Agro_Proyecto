/**
 * INTELLIGENT GLOBAL SEARCH
 * Handles predictive search and navigation for all modules.
 */

const searchModules = [
    {
        id: 'nav_dashboard',
        label_es: 'Explorador de Mapas',
        label_en: 'Map Explorer',
        keywords: ['mapa', 'visor', 'dashboard', 'explorer', 'map', 'geo', 'capas', 'layers'],
        icon: 'map',
        url: '/dashboard'
    },
    {
        id: 'sidebar_trends',
        label_es: 'Historial de Tendencias',
        label_en: 'Trends History',
        keywords: ['tendencias', 'analisis', 'graficos', 'trends', 'analysis', 'charts', 'historico', 'stats'],
        icon: 'trending_up',
        url: '/tendencias'
    },
    {
        id: 'sidebar_upload',
        label_es: 'Carga de Datos',
        label_en: 'Data Upload',
        keywords: ['carga', 'datos', 'subir', 'netcdf', 'upload', 'files', 'importar', 'import'],
        icon: 'cloud_upload',
        url: '/carga-datos'
    },
    {
        id: 'sidebar_config',
        label_es: 'Configuración de Perfil',
        label_en: 'Profile Settings',
        keywords: ['configuracion', 'perfil', 'ajustes', 'settings', 'profile', 'config', 'seguridad', 'security', 'password'],
        icon: 'settings',
        url: '/configuracion'
    },
    {
        id: 'nav_inicio',
        label_es: 'Página de Inicio',
        label_en: 'Home Page',
        keywords: ['inicio', 'home', 'principal', 'welcom', 'bienvenida'],
        icon: 'home',
        url: '/'
    }
];

let activeIndex = -1;

function initGlobalSearch() {
    const searchInput = document.getElementById('globalSearch');
    const suggestionsContainer = document.getElementById('searchSuggestions');
    
    if (!searchInput || !suggestionsContainer) return;

    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase().trim();
        if (!term) {
            hideSuggestions();
            return;
        }
        
        const filtered = searchModules.filter(m => 
            m.label_es.toLowerCase().includes(term) || 
            m.label_en.toLowerCase().includes(term) || 
            m.keywords.some(k => k.includes(term))
        );
        
        renderSuggestions(filtered);
    });

    searchInput.addEventListener('keydown', (e) => {
        const items = suggestionsContainer.querySelectorAll('.search-item');
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            activeIndex = (activeIndex + 1) % items.length;
            updateActiveItem(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            activeIndex = (activeIndex - 1 + items.length) % items.length;
            updateActiveItem(items);
        } else if (e.key === 'Enter') {
            if (activeIndex >= 0 && items[activeIndex]) {
                items[activeIndex].click();
            } else if (items.length > 0) {
                // Si no hay nada seleccionado pero hay resultados, ir al primero
                items[0].click();
            }
        } else if (e.key === 'Escape') {
            hideSuggestions();
            searchInput.blur();
        }
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
            hideSuggestions();
        }
    });

    // Show suggestions when focusing if there's text
    searchInput.addEventListener('focus', (e) => {
        if (e.target.value.trim()) {
            const term = e.target.value.toLowerCase().trim();
            const filtered = searchModules.filter(m => 
                m.label_es.toLowerCase().includes(term) || 
                m.label_en.toLowerCase().includes(term) || 
                m.keywords.some(k => k.includes(term))
            );
            renderSuggestions(filtered);
        }
    });
}

function renderSuggestions(modules) {
    const container = document.getElementById('searchSuggestions');
    const lang = document.documentElement.lang || 'es';
    
    if (modules.length === 0) {
        container.innerHTML = `<div class="p-4 text-xs text-secondary/50 italic text-center">${lang === 'es' ? 'No se encontraron resultados' : 'No results found'}</div>`;
    } else {
        container.innerHTML = modules.map((m, index) => `
            <a href="${m.url}" class="search-item flex items-center gap-3 p-3 hover:bg-primary/5 dark:hover:bg-white/5 transition-colors group">
                <div class="w-8 h-8 rounded-lg bg-surface-container dark:bg-white/5 flex items-center justify-center text-secondary dark:text-primary-fixed group-hover:bg-primary group-hover:text-white transition-all shadow-sm">
                    <span class="material-symbols-outlined text-sm" style="font-variation-settings: 'FILL' 1;">${m.icon}</span>
                </div>
                <div class="flex-1">
                    <p class="text-xs font-bold text-on-surface dark:text-white">${lang === 'es' ? m.label_es : m.label_en}</p>
                    <p class="text-[9px] text-secondary/60 dark:text-secondary/40 uppercase tracking-widest font-black">${m.url}</p>
                </div>
                <span class="material-symbols-outlined text-xs text-outline opacity-0 group-hover:opacity-100 transition-opacity">arrow_forward</span>
            </a>
        `).join('');
    }
    
    container.classList.remove('hidden');
    // Animate presence
    container.style.opacity = '0';
    container.style.transform = 'translateY(-10px)';
    requestAnimationFrame(() => {
        container.style.transition = 'all 0.2s ease-out';
        container.style.opacity = '1';
        container.style.transform = 'translateY(0)';
    });

    activeIndex = -1;
}

function updateActiveItem(items) {
    items.forEach((item, idx) => {
        if (idx === activeIndex) {
            item.classList.add('bg-primary/10', 'dark:bg-white/10', 'border-l-4', 'border-primary');
            item.scrollIntoView({ block: 'nearest' });
        } else {
            item.classList.remove('bg-primary/10', 'dark:bg-white/10', 'border-l-4', 'border-primary');
        }
    });
}

function hideSuggestions() {
    const container = document.getElementById('searchSuggestions');
    if (container && !container.classList.contains('hidden')) {
        container.style.opacity = '0';
        container.style.transform = 'translateY(-10px)';
        setTimeout(() => container.classList.add('hidden'), 200);
    }
    activeIndex = -1;
}

document.addEventListener('DOMContentLoaded', initGlobalSearch);
