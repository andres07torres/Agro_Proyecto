/**
 * AGRO VISOR - TRENDS LOGIC
 * Manages full historical analysis, data filtering, and synchronized charting.
 */

let datosTendencias = null;
let chartBarra = null;
let chartLinea = null;

const isDark = () => document.documentElement.classList.contains('dark');
const getPrimaryColor = () => isDark() ? '#7cda9a' : '#004423';
const getTextColor = () => isDark() ? '#c0c9bb' : '#717a6d';

async function cargarDatosReales() {
    const filename = localStorage.getItem('active_netcdf_file');
    const lat = localStorage.getItem('active_lat');
    const lon = localStorage.getItem('active_lon');
    
    if (!filename) {
        document.getElementById('emptyState').classList.remove('hidden');
        document.getElementById('trendsContent').classList.add('hidden');
        return;
    }

    document.getElementById('trendsContent').classList.remove('hidden');
    document.getElementById('emptyState').classList.add('hidden');
    
    const lang = document.documentElement.lang || 'es';
    document.getElementById('nombreArchivoActivo').innerText = translations[lang]['btn_loading'] || "Procesando...";

    let url = `/api/get_trends/${filename}?t=${Date.now()}`;
    if (lat && lon) {
        url += `&lat=${lat}&lon=${lon}`;
    }

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error("File not found");
        
        datosTendencias = await response.json();
        if (!datosTendencias.exito) throw new Error(datosTendencias.error || "Analysis failed");

        // Update location and filename display
        document.getElementById('ubicacionAnalisis').innerText = datosTendencias.ubicacion === "Resumen Regional" 
            ? (translations[lang]['stat_reg_summary'] || "Resumen Regional")
            : datosTendencias.ubicacion;
            
        document.getElementById('nombreArchivoActivo').innerText = `${translations[lang]['file_label'] || "Archivo:"} ${filename}`;

        actualizarTarjetas(datosTendencias);
        poblarSelectorAnios(datosTendencias.anual_labels);
        actualizarFiltroTendencia();
        
        const btnClear = document.getElementById('btnClearTrends');
        if (btnClear) btnClear.classList.remove('hidden');
    } catch (err) {
        console.error("Error cargando tendencias:", err);
        const btnClear = document.getElementById('btnClearTrends');
        if (btnClear) btnClear.classList.add('hidden');
        localStorage.removeItem('active_netcdf_file');
        document.getElementById('emptyState').classList.remove('hidden');
        document.getElementById('trendsContent').classList.add('hidden');
    }
}

function limpiarTendencias() {
    const lang = document.documentElement.lang || 'es';
    if (typeof Swal === 'undefined') {
        if (confirm("¿Limpiar datos?")) {
            localStorage.removeItem('active_netcdf_file');
            localStorage.removeItem('active_lat');
            localStorage.removeItem('active_lon');
            window.location.reload();
        }
        return;
    }

    Swal.fire({
        title: translations[lang]['swal_clear_title'] || "Limpiar Análisis",
        text: translations[lang]['swal_clear_text'] || "¿Deseas borrar el archivo actual de la sesión?",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#ba1a1a",
        cancelButtonColor: "#3085d6",
        confirmButtonText: translations[lang]['btn_confirm'] || "Confirmar",
        cancelButtonText: translations[lang]['btn_cancel'] || "Cancelar",
        background: isDark() ? '#191c1d' : '#fff',
        color: isDark() ? '#fff' : '#000'
    }).then((result) => {
        if (result.isConfirmed) {
            localStorage.removeItem('active_netcdf_file');
            localStorage.removeItem('active_lat');
            localStorage.removeItem('active_lon');
            window.location.reload();
        }
    });
}

function poblarSelectorAnios(anios) {
    const lang = document.documentElement.lang || 'es';
    const select = document.getElementById('filtroAnioTendencias');
    if (!select) return;
    const currentTitle = translations[lang]['opt_all'] || "Histórico Completo";
    select.innerHTML = `<option value="todos" data-i18n="opt_all">${currentTitle}</option>`;
    anios.forEach(anio => {
        const opt = document.createElement('option');
        opt.value = opt.innerText = anio;
        select.appendChild(opt);
    });
    const container = document.getElementById('filterContainer');
    if (container) container.classList.remove('hidden');
}

function actualizarFiltroTendencia() {
    if (!datosTendencias) return;
    const anioSel = document.getElementById('filtroAnioTendencias').value;
    const lang = document.documentElement.lang || 'es';
    
    const monthMap = {
        'Ene': 'm_1', 'Feb': 'm_2', 'Mar': 'm_3', 'Abr': 'm_4', 'May': 'm_5', 'Jun': 'm_6',
        'Jul': 'm_7', 'Ago': 'm_8', 'Sep': 'm_9', 'Oct': 'm_10', 'Nov': 'm_11', 'Dic': 'm_12'
    };
    const labels = datosTendencias.ciclo_labels.map(l => translations[lang][monthMap[l]] || l);
    const values = anioSel === 'todos' ? datosTendencias.ciclo_values : (datosTendencias.anual_dist[anioSel] || labels.map(() => 0));
    
    const titleText = anioSel === 'todos' 
        ? (translations[lang]['chart_hydrology_hist'] || "Ciclo Hidrológico Mensual Histórico")
        : `${translations[lang]['chart_dist_month'] || "Distribución Mensual"} ${anioSel}`;
        
    const titleEl = document.getElementById('tituloBarra');
    if (titleEl) titleEl.innerText = titleText;
    
    renderBarra(labels, values);
    renderLinea(datosTendencias.anual_labels, datosTendencias.anual_values); 
}

function actualizarTarjetas(data) {
    const lang = document.documentElement.lang || 'es';
    document.getElementById('cardAnomalia').innerText = `${data.anomalia > 0 ? '+' : ''}${data.anomalia} mm`;
    document.getElementById('cardMaxVal').innerText = `${data.max_precip} mm`;
    document.getElementById('cardMaxFecha').innerText = data.max_fecha;
    document.getElementById('cardPromedio').innerText = `${data.promedio_total} mm`;
    
    let stabilityText = data.estabilidad || "-";
    if (data.estabilidad === "Baja") stabilityText = translations[lang]['stat_low'] || "Baja";
    else if (data.estabilidad === "Media") stabilityText = translations[lang]['stat_med'] || "Media";
    else if (data.estabilidad === "Alta") stabilityText = translations[lang]['stat_high'] || "Alta";
    
    document.getElementById('cardEstabilidad').innerText = stabilityText;
    document.getElementById('agroRecomendacion').innerText = data.recomendacion || "-";
}

function renderBarra(labels, values) {
    const canvas = document.getElementById('graficoBarrasMensual');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (chartBarra) chartBarra.destroy();

    const primaryColor = getPrimaryColor();
    const textColor = getTextColor();

    chartBarra = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Precipitación (mm)',
                data: values,
                backgroundColor: primaryColor,
                borderRadius: 8, 
                hoverBackgroundColor: isDark() ? '#97f7b5' : '#005f32'
            }]
        },
        options: { 
            responsive: true, maintainAspectRatio: false, 
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: isDark() ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)' }, ticks: { font: { size: 10 }, color: textColor } },
                x: { grid: { display: false }, ticks: { font: { size: 10 }, color: textColor } }
            }
        }
    });
}

function renderLinea(labels, values) {
    const canvas = document.getElementById('cicloEstacionalLinea');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (chartLinea) chartLinea.destroy();

    const primaryColor = getPrimaryColor();
    const textColor = getTextColor();

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, isDark() ? 'rgba(124, 218, 154, 0.2)' : 'rgba(0, 68, 35, 0.2)');
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

    chartLinea = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Anual (mm)',
                data: values,
                borderColor: primaryColor,
                backgroundColor: gradient,
                fill: true,
                tension: 0.4,
                borderWidth: 3,
                pointRadius: 4,
                pointBackgroundColor: isDark() ? '#191c1d' : '#ffffff',
                pointBorderColor: primaryColor,
                pointBorderWidth: 2
            }]
        },
        options: { 
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: isDark() ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)' }, ticks: { color: textColor } },
                x: { ticks: { font: { size: 9 }, color: textColor, maxRotation: 45 } }
            }
        }
    });
}

// Global UI Listeners
window.addEventListener('languageChanged', (e) => {
    if (datosTendencias) {
        actualizarTarjetas(datosTendencias);
        actualizarFiltroTendencia();
    }
});

// Initialize on load
document.addEventListener('DOMContentLoaded', cargarDatosReales);
