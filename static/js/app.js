// Estado global de la aplicación
let isMonitoring = false;
let autoRefreshInterval;

// Inicializar cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    loadSites();
    checkMonitoringStatus();
    
    // Configurar auto-refresh cada 30 segundos cuando no se esté monitoreando
    autoRefreshInterval = setInterval(() => {
        if (!isMonitoring) {
            loadSites();
        }
    }, 30000);
    
    // Manejar Enter en el input de URL
    document.getElementById('urlInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            addSite();
        }
    });
});

// Mostrar notificación
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 4000);
}

// Cargar todos los sitios
async function loadSites() {
    try {
        const response = await fetch('/api/sites');
        const data = await response.json();
        
        renderSites(data.sites);
        updateSiteCount(data.sites.length);
    } catch (error) {
        console.error('Error cargando sitios:', error);
        showNotification('Error al cargar los sitios', 'error');
    }
}

// Renderizar lista de sitios
function renderSites(sites) {
    const container = document.getElementById('sitesContainer');
    
    if (sites.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No hay sitios monitoreados</p>
                <p class="empty-hint">Agrega un sitio web usando el campo de arriba</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = sites.map(site => `
        <div class="site-card" data-url="${site.url}">
            <div class="site-header">
                <div class="site-info">
                    <span class="status-dot ${getStatusClass(site.last_status)}"></span>
                    <span class="site-url">${site.url}</span>
                </div>
                <button onclick="removeSite('${site.url}')" class="btn-remove" title="Eliminar sitio">×</button>
            </div>
            
            <div class="site-details">
                <div class="detail-item">
                    <span class="label">Estado:</span>
                    <span class="value status-${site.last_status || 'unknown'}">
                        ${getStatusText(site.last_status)}
                    </span>
                </div>
                
                ${site.response_time ? `
                <div class="detail-item">
                    <span class="label">Tiempo de respuesta:</span>
                    <span class="value">${site.response_time.toFixed(3)}s</span>
                </div>
                ` : ''}
                
                <div class="detail-item">
                    <span class="label">Última verificación:</span>
                    <span class="value">${formatTimestamp(site.last_checked)}</span>
                </div>
                
                ${site.last_error ? `
                <div class="detail-item error">
                    <span class="label">Error:</span>
                    <span class="value">${site.last_error}</span>
                </div>
                ` : ''}
            </div>
        </div>
    `).join('');
}

// Obtener clase CSS para el estado
function getStatusClass(status) {
    switch (status) {
        case 'online': return 'online';
        case 'offline': return 'offline';
        default: return 'unknown';
    }
}

// Obtener texto para el estado
function getStatusText(status) {
    switch (status) {
        case 'online': return 'En línea';
        case 'offline': return 'Fuera de línea';
        default: return 'Desconocido';
    }
}

// Formatear timestamp
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Nunca';
    
    try {
        const date = new Date(timestamp);
        return date.toLocaleString('es-ES', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    } catch (error) {
        return timestamp;
    }
}

// Actualizar contador de sitios
function updateSiteCount(count) {
    document.getElementById('siteCount').textContent = `${count} sitios`;
}

// Agregar sitio
async function addSite() {
    const urlInput = document.getElementById('urlInput');
    const url = urlInput.value.trim();
    
    if (!url) {
        showNotification('Por favor ingresa una URL', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/sites', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            urlInput.value = '';
            showNotification(`Sitio agregado: ${data.url}`, 'success');
            loadSites();
        } else {
            showNotification(data.error || 'Error al agregar sitio', 'error');
        }
    } catch (error) {
        console.error('Error agregando sitio:', error);
        showNotification('Error al agregar sitio', 'error');
    }
}

// Eliminar sitio
async function removeSite(url) {
    if (!confirm(`¿Estás seguro de que quieres eliminar ${url}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/sites/${encodeURIComponent(url)}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Sitio eliminado exitosamente', 'success');
            loadSites();
        } else {
            showNotification(data.error || 'Error al eliminar sitio', 'error');
        }
    } catch (error) {
        console.error('Error eliminando sitio:', error);
        showNotification('Error al eliminar sitio', 'error');
    }
}

// Verificar todos los sitios una vez
async function checkAllSites() {
    const button = event.target;
    const originalText = button.textContent;
    
    button.textContent = 'Verificando...';
    button.disabled = true;
    
    try {
        const response = await fetch('/api/check', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Verificación completada', 'success');
            loadSites();
        } else {
            showNotification(data.error || 'Error en la verificación', 'error');
        }
    } catch (error) {
        console.error('Error verificando sitios:', error);
        showNotification('Error al verificar sitios', 'error');
    } finally {
        button.textContent = originalText;
        button.disabled = false;
    }
}

// Alternar monitoreo continuo
async function toggleMonitoring() {
    if (isMonitoring) {
        await stopMonitoring();
    } else {
        await startMonitoring();
    }
}

// Iniciar monitoreo
async function startMonitoring() {
    const interval = parseInt(document.getElementById('intervalInput').value) || 60;
    const timeout = parseInt(document.getElementById('timeoutInput').value) || 10;
    
    try {
        const response = await fetch('/api/monitor/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ interval, timeout })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            isMonitoring = true;
            updateMonitoringUI();
            showNotification(`Monitor iniciado (cada ${interval}s)`, 'success');
            
            // Cargar sitios cada 5 segundos durante el monitoreo
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = setInterval(loadSites, 5000);
        } else {
            showNotification(data.error || 'Error al iniciar monitor', 'error');
        }
    } catch (error) {
        console.error('Error iniciando monitor:', error);
        showNotification('Error al iniciar monitor', 'error');
    }
}

// Detener monitoreo
async function stopMonitoring() {
    try {
        const response = await fetch('/api/monitor/stop', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            isMonitoring = false;
            updateMonitoringUI();
            showNotification('Monitor detenido', 'info');
            
            // Volver al auto-refresh normal
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = setInterval(loadSites, 30000);
        } else {
            showNotification(data.error || 'Error al detener monitor', 'error');
        }
    } catch (error) {
        console.error('Error deteniendo monitor:', error);
        showNotification('Error al detener monitor', 'error');
    }
}

// Verificar estado del monitoreo
async function checkMonitoringStatus() {
    try {
        const response = await fetch('/api/monitor/status');
        const data = await response.json();
        
        isMonitoring = data.running;
        updateMonitoringUI();
    } catch (error) {
        console.error('Error verificando estado del monitor:', error);
    }
}

// Actualizar UI del monitoreo
function updateMonitoringUI() {
    const button = document.getElementById('monitorBtn');
    const indicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    
    if (isMonitoring) {
        button.textContent = 'Detener Monitor';
        button.className = 'btn btn-secondary';
        indicator.className = 'status-indicator running';
        statusText.textContent = 'Ejecutándose';
    } else {
        button.textContent = 'Iniciar Monitor';
        button.className = 'btn btn-secondary';
        indicator.className = 'status-indicator';
        statusText.textContent = 'Detenido';
    }
}