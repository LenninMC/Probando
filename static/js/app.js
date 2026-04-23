// Elementos del DOM
const estadoMotor = document.getElementById('estado-motor');
const pulsosValor = document.getElementById('pulsos-valor');
const vueltasValor = document.getElementById('vueltas-valor');
const rpmValor = document.getElementById('rpm-valor');
const rpmBar = document.getElementById('rpm-bar');
const ultimaActualizacion = document.getElementById('ultima-actualizacion');

// Configuración del motor
const VELOCIDAD_MAX = 180;  // PWM máximo
const RPM_MAX = 3000;       // RPM máxima esperada (ajustar según tu motor)

// Configuración de la gráfica
const ctx = document.getElementById('mainChart').getContext('2d');
let chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: 'RPM',
                data: [],
                borderColor: '#00ff9d',
                backgroundColor: 'rgba(0, 255, 157, 0.1)',
                borderWidth: 2,
                pointRadius: 3,
                pointHoverRadius: 5,
                tension: 0.3,
                fill: true
            },
            {
                label: 'Pulsos',
                data: [],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                pointRadius: 3,
                pointHoverRadius: 5,
                tension: 0.3,
                fill: true,
                yAxisID: 'y1'
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            tooltip: { 
                mode: 'index', 
                intersect: false
            }
        },
        scales: {
            y: {
                position: 'left',
                title: { display: true, text: 'RPM', color: '#8d9db0' },
                grid: { color: 'rgba(255,255,255,0.1)' },
                ticks: { color: '#8d9db0' },
                min: 0,
                max: RPM_MAX
            },
            y1: {
                position: 'right',
                title: { display: true, text: 'Pulsos', color: '#8d9db0' },
                grid: { display: false },
                ticks: { color: '#8d9db0' }
            },
            x: {
                grid: { display: false },
                ticks: { color: '#8d9db0', maxRotation: 45, minRotation: 45 }
            }
        }
    }
});

function updateChart(rpm, pulsos) {
    const ahora = new Date().toLocaleTimeString();
    
    chart.data.labels.push(ahora);
    chart.data.datasets[0].data.push(rpm);
    chart.data.datasets[1].data.push(pulsos);
    
    // Mantener últimos 30 puntos
    if (chart.data.labels.length > 30) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
        chart.data.datasets[1].data.shift();
    }
    
    chart.update();
}

function actualizarUI(estado) {
    if (!estado) return;
    
    // Actualizar estado del motor
    let estadoTexto = "";
    let estadoColor = "";
    
    switch(estado.estado) {
        case "ADELANTE":
            estadoTexto = "▶ ADELANTE";
            estadoColor = "#00ff9d";
            break;
        case "ATRAS":
            estadoTexto = "◀ ATRÁS";
            estadoColor = "#ff6b6b";
            break;
        case "PARADO":
            estadoTexto = "⏹ PARADO";
            estadoColor = "#ffaa00";
            break;
        default:
            estadoTexto = "---";
            estadoColor = "#5f6b7a";
    }
    
    estadoMotor.textContent = estadoTexto;
    estadoMotor.style.color = estadoColor;
    
    // Actualizar valores
    pulsosValor.textContent = estado.pulsos || 0;
    vueltasValor.textContent = estado.vueltas ? estado.vueltas.toFixed(4) : "0.0000";
    rpmValor.textContent = estado.rpm ? estado.rpm.toFixed(2) : "0.00";
    
    // Actualizar barra de RPM
    const porcentajeRPM = Math.min((estado.rpm || 0) / RPM_MAX * 100, 100);
    rpmBar.style.width = `${porcentajeRPM}%`;
    
    // Actualizar gráfica
    updateChart(estado.rpm || 0, estado.pulsos || 0);
}

async function fetchEstado() {
    try {
        const r = await fetch("/api/estado");
        const j = await r.json();
        
        if (j.ok) {
            actualizarUI(j);
            
            // Actualizar timestamp
            const ahora = new Date();
            ultimaActualizacion.textContent = `${ahora.toLocaleDateString()} ${ahora.toLocaleTimeString()}`;
            
            console.log(`Estado: ${j.estado}, RPM: ${j.rpm}, Pulsos: ${j.pulsos}`);
        } else {
            console.error('Error en datos:', j.error);
        }
    } catch (error) {
        console.error('Error de conexión:', error);
    }
}

async function enviarComando(cmd) {
    try {
        const r = await fetch("/api/comando", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ comando: cmd })
        });
        const j = await r.json();
        
        if (j.ok) {
            console.log(`Comando ${cmd} enviado correctamente`);
            // Esperar un momento y actualizar estado
            setTimeout(fetchEstado, 100);
        } else {
            console.error('Error al enviar comando:', j.error);
        }
    } catch (error) {
        console.error('Error de conexión:', error);
    }
}

// Iniciar polling cada 500ms
setInterval(fetchEstado, 500);
fetchEstado();
