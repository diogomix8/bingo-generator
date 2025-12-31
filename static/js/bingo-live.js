/**
 * BINGO LIVE - Cliente JavaScript
 * ================================
 * Maneja la interacción del simulador en vivo
 */

// Estado global
let jugadaId = null;
let sonidoHabilitado = true;

// Audio Context para generar sonidos programáticamente
let audioContext = null;

function initAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioContext;
}

function playBolillaSound() {
    if (!sonidoHabilitado) return;
    
    try {
        const ctx = initAudioContext();
        const oscillator = ctx.createOscillator();
        const gainNode = ctx.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(ctx.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15);
        
        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.15);
    } catch (e) {
        console.log('Audio not supported');
    }
}

function playBingoSound() {
    if (!sonidoHabilitado) return;
    
    try {
        const ctx = initAudioContext();
        
        // Secuencia de notas para fanfarria
        const notas = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
        
        notas.forEach((freq, index) => {
            const oscillator = ctx.createOscillator();
            const gainNode = ctx.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(ctx.destination);
            
            oscillator.frequency.value = freq;
            oscillator.type = 'square';
            
            const startTime = ctx.currentTime + (index * 0.15);
            gainNode.gain.setValueAtTime(0.2, startTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 0.3);
            
            oscillator.start(startTime);
            oscillator.stop(startTime + 0.3);
        });
    } catch (e) {
        console.log('Audio not supported');
    }
}

// =====================================================
// INICIALIZACIÓN
// =====================================================

document.addEventListener('DOMContentLoaded', function() {
    // Form de inicio
    document.getElementById('form-iniciar').addEventListener('submit', iniciarJugada);
    
    // Toggle de sonido
    document.getElementById('toggle-sonido').addEventListener('change', function() {
        sonidoHabilitado = this.checked;
    });
    
    // Botón deshacer
    document.getElementById('btn-deshacer').addEventListener('click', deshacerBolilla);
    
    // Botón reiniciar
    document.getElementById('btn-reiniciar').addEventListener('click', reiniciarJugada);
    
    // Clicks en bolillero
    document.querySelectorAll('.bolilla').forEach(btn => {
        btn.addEventListener('click', function() {
            const numero = parseInt(this.dataset.numero);
            cantarBolilla(numero);
        });
    });
});

// =====================================================
// FUNCIONES PRINCIPALES
// =====================================================

async function iniciarJugada(e) {
    e.preventDefault();
    
    const archivoCorel = document.getElementById('archivo-corel').value;
    if (!archivoCorel) {
        alert('Selecciona un archivo de bingos');
        return;
    }
    
    try {
        const response = await fetch('/api/bingo-live/iniciar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ archivo_corel: archivoCorel })
        });
        
        const data = await response.json();
        
        if (data.exito) {
            jugadaId = data.jugada_id;
            
            // Mostrar panel de juego
            document.getElementById('config-panel').classList.add('d-none');
            document.getElementById('game-panel').classList.remove('d-none');
            
            // Actualizar UI con estado inicial
            actualizarEstado(data.estado);
            
            // Resetear bolillero
            resetearBolillero();
        } else {
            alert('Error: ' + data.mensaje);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error al iniciar la jugada');
    }
}

async function cantarBolilla(numero) {
    if (!jugadaId) return;
    
    const botonBolilla = document.querySelector(`.bolilla[data-numero="${numero}"]`);
    if (botonBolilla.classList.contains('cantada')) return;
    
    try {
        const response = await fetch(`/api/bingo-live/cantar/${numero}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jugada_id: jugadaId })
        });
        
        const data = await response.json();
        
        if (data.exito) {
            // Reproducir sonido
            playBolillaSound();
            
            // Marcar bolilla como cantada
            marcarBolillaCantada(numero);
            
            // Actualizar historial
            actualizarHistorial(data.bolilla, data.total_cantadas);
            
            // Actualizar ranking
            actualizarRanking(data.ranking_top20);
            
            // Actualizar contadores
            document.getElementById('contador-bolillas').textContent = data.total_cantadas;
            
            // Habilitar botón deshacer
            document.getElementById('btn-deshacer').disabled = false;
            
            // Verificar si hay ganador
            if (data.hay_ganador) {
                mostrarBingo(data.ganadores, data.total_cantadas);
            }
        } else {
            alert(data.mensaje);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function deshacerBolilla() {
    if (!jugadaId) return;
    
    try {
        const response = await fetch('/api/bingo-live/deshacer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jugada_id: jugadaId })
        });
        
        const data = await response.json();
        
        if (data.exito) {
            // Desmarcar bolilla
            desmarcarBolilla(data.bolilla_deshecha);
            
            // Actualizar UI
            actualizarEstadoCompleto();
        } else {
            alert(data.mensaje);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function reiniciarJugada() {
    if (!jugadaId) {
        // Si no hay jugada, volver al panel de configuración
        document.getElementById('config-panel').classList.remove('d-none');
        document.getElementById('game-panel').classList.add('d-none');
        return;
    }
    
    if (!confirm('¿Reiniciar la jugada actual?')) return;
    
    try {
        const response = await fetch('/api/bingo-live/reiniciar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jugada_id: jugadaId })
        });
        
        const data = await response.json();
        
        if (data.exito) {
            // Cerrar modal de bingo si está abierto
            const modalBingo = bootstrap.Modal.getInstance(document.getElementById('modal-bingo'));
            if (modalBingo) modalBingo.hide();
            
            // Resetear UI
            resetearBolillero();
            actualizarEstado(data.estado);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// =====================================================
// FUNCIONES DE UI
// =====================================================

function actualizarEstado(estado) {
    document.getElementById('total-cartones').textContent = estado.total_cartones;
    document.getElementById('contador-bolillas').textContent = estado.total_cantadas;
    
    // Actualizar mejor aciertos
    if (estado.ranking_top20 && estado.ranking_top20.length > 0) {
        document.getElementById('mejor-aciertos').textContent = estado.ranking_top20[0].aciertos;
    }
    
    // Actualizar ranking
    actualizarRanking(estado.ranking_top20);
    
    // Marcar bolillas ya cantadas
    estado.bolillas_cantadas.forEach(num => marcarBolillaCantada(num, false));
    
    // Actualizar historial
    const historialContainer = document.getElementById('ultimas-bolillas');
    if (estado.bolillas_cantadas.length > 0) {
        historialContainer.innerHTML = estado.bolillas_cantadas
            .slice(-10)
            .reverse()
            .map(num => `<div class="bolilla-historial">${num}</div>`)
            .join('');
    } else {
        historialContainer.innerHTML = '<span class="text-muted">Ninguna bolilla cantada aún</span>';
    }
    
    // Estado botón deshacer
    document.getElementById('btn-deshacer').disabled = estado.bolillas_cantadas.length === 0;
}

async function actualizarEstadoCompleto() {
    if (!jugadaId) return;
    
    try {
        const response = await fetch(`/api/bingo-live/estado?jugada_id=${jugadaId}`);
        const data = await response.json();
        
        if (data.exito) {
            // Resetear bolillero
            document.querySelectorAll('.bolilla').forEach(btn => {
                btn.classList.remove('cantada', 'ultima-cantada');
            });
            
            // Actualizar estado
            actualizarEstado(data.estado);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function marcarBolillaCantada(numero, animacion = true) {
    const boton = document.querySelector(`.bolilla[data-numero="${numero}"]`);
    if (!boton) return;
    
    // Quitar clase de última de cualquier otra
    document.querySelectorAll('.bolilla.ultima-cantada').forEach(btn => {
        btn.classList.remove('ultima-cantada');
    });
    
    boton.classList.add('cantada');
    if (animacion) {
        boton.classList.add('ultima-cantada');
    }
}

function desmarcarBolilla(numero) {
    const boton = document.querySelector(`.bolilla[data-numero="${numero}"]`);
    if (boton) {
        boton.classList.remove('cantada', 'ultima-cantada');
    }
}

function resetearBolillero() {
    document.querySelectorAll('.bolilla').forEach(btn => {
        btn.classList.remove('cantada', 'ultima-cantada');
    });
    
    document.getElementById('ultimas-bolillas').innerHTML = 
        '<span class="text-muted">Ninguna bolilla cantada aún</span>';
    
    document.getElementById('contador-bolillas').textContent = '0';
    document.getElementById('mejor-aciertos').textContent = '0';
    document.getElementById('btn-deshacer').disabled = true;
    document.getElementById('badge-ganador').classList.add('d-none');
}

function actualizarHistorial(bolilla, total) {
    const container = document.getElementById('ultimas-bolillas');
    
    // Limpiar si es la primera bolilla
    if (total === 1) {
        container.innerHTML = '';
    }
    
    // Agregar nueva bolilla al inicio
    const nuevaBolilla = document.createElement('div');
    nuevaBolilla.className = 'bolilla-historial';
    nuevaBolilla.textContent = bolilla;
    container.insertBefore(nuevaBolilla, container.firstChild);
    
    // Limitar a 10 bolillas visibles
    while (container.children.length > 10) {
        container.removeChild(container.lastChild);
    }
}

function actualizarRanking(ranking) {
    const container = document.getElementById('ranking-container');
    
    if (!ranking || ranking.length === 0) {
        container.innerHTML = '<div class="col-12 text-center text-muted"><p>Sin datos aún</p></div>';
        return;
    }
    
    // Actualizar mejor aciertos
    document.getElementById('mejor-aciertos').textContent = ranking[0].aciertos;
    
    // Generar HTML del ranking
    container.innerHTML = ranking.map((item, index) => {
        const porcentaje = (item.aciertos / 10) * 100;
        const colorBarra = item.es_ganador ? 'bg-success' : 
                          item.aciertos >= 8 ? 'bg-warning' : 'bg-primary';
        
        return `
            <div class="col-md-6 col-lg-4">
                <div class="ranking-item ${item.es_ganador ? 'ganador' : ''}" 
                     onclick="verDetalleCarton('${item.bingo_id}')">
                    <div class="d-flex align-items-center gap-2 mb-2">
                        <div class="ranking-position">${index + 1}</div>
                        <div class="flex-grow-1">
                            <strong>Bingo #${item.bingo_id}</strong>
                            <span class="badge bg-secondary ms-1">${item.carton_tipo}</span>
                        </div>
                        <span class="badge ${item.es_ganador ? 'bg-warning text-dark' : 'bg-info'}">
                            ${item.aciertos}/10
                        </span>
                    </div>
                    <div class="progress progress-aciertos">
                        <div class="progress-bar ${colorBarra}" style="width: ${porcentaje}%"></div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function verDetalleCarton(bingoId) {
    if (!jugadaId) return;
    
    try {
        const response = await fetch(`/api/bingo-live/detalle/${bingoId}?jugada_id=${jugadaId}`);
        const data = await response.json();
        
        if (data.exito) {
            document.getElementById('modal-bingo-id').textContent = `#${bingoId}`;
            
            const container = document.getElementById('modal-cartones');
            container.innerHTML = data.cartones.map(carton => `
                <div class="col-md-4">
                    <div class="carton-detalle">
                        <h6 class="text-center">
                            Cartón ${carton.carton_tipo}
                            <span class="badge ${carton.es_ganador ? 'bg-success' : 'bg-secondary'} ms-2">
                                ${carton.cantidad_aciertos}/10
                            </span>
                        </h6>
                        <div class="d-flex flex-wrap justify-content-center">
                            ${carton.numeros.map(num => `
                                <div class="numero-carton ${carton.aciertos.includes(num) ? 'acertado' : ''}">
                                    ${num}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `).join('');
            
            const modal = new bootstrap.Modal(document.getElementById('modal-detalle'));
            modal.show();
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function mostrarBingo(ganadores, totalBolillas) {
    // Reproducir sonido de celebración
    playBingoSound();
    
    // Mostrar badge de ganador en ranking
    document.getElementById('badge-ganador').classList.remove('d-none');
    
    // Llenar info de ganadores
    const ganadoresInfo = document.getElementById('ganadores-info');
    ganadoresInfo.innerHTML = ganadores.map(g => `
        <div class="ganador-badge">
            <i class="bi bi-trophy-fill me-2"></i>
            Bingo #${g.bingo_id} - Cartón ${g.carton_tipo}
        </div>
    `).join('');
    
    document.getElementById('bolillas-finales').textContent = totalBolillas;
    
    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById('modal-bingo'));
    modal.show();
}

// Función global para reiniciar desde el modal
window.reiniciarJugada = reiniciarJugada;
