// ── Audios de referencia (evaluación de molestia previa) ──────────────────────
const refAudioFiles = [
    'ref_52.wav', 'ref_56.wav', 'ref_60.wav', 'ref_64.wav', 'ref_68.wav'
];
let currentRefIndex = 0;
const refResponses = [];   // [{file, value}, …]  — 5 entradas al finalizar

// Carga el audio de referencia indicado por currentRefIndex
function loadRefAudio(index) {
    const src    = document.getElementById('audio_ref_molestia_source');
    const player = document.getElementById('audio_ref_molestia');
    const counter = document.getElementById('ref-counter');
    const bar     = document.getElementById('ref-progress-bar');
    const pct     = document.getElementById('ref-progress-pct');
    const btn     = document.getElementById('button_next');

    src.src = `./resources/ref/${refAudioFiles[index]}`;
    player.load();

    const n = refAudioFiles.length;
    const progress = Math.round(((index + 1) / n) * 100);
    if (counter) counter.textContent = index + 1;
    if (bar)     bar.style.width = progress + '%';
    if (pct)     pct.textContent = progress + '%';

    // Último audio → cambiar texto del botón
    if (btn) btn.textContent = (index === n - 1) ? 'Comenzar Cuestionario' : 'Siguiente';

    // Limpiar selección anterior
    document.getElementsByName('molestia_ref_current')
            .forEach(r => r.checked = false);
}

// Avanzar al siguiente audio de referencia (o pasar al cuestionario)
window.nextRefAudio = function () {
    const selected = document.querySelector('input[name="molestia_ref_current"]:checked');
    if (!selected) {
        alert('Por favor, indique el nivel de molestia antes de continuar.');
        return;
    }

    refResponses.push({
        file:  refAudioFiles[currentRefIndex],
        value: selected.value
    });

    currentRefIndex++;

    if (currentRefIndex < refAudioFiles.length) {
        loadRefAudio(currentRefIndex);
    } else {
        // Guardar en window para usarlo al construir el CSV
        window._refResponses = refResponses;

        document.getElementById('screen-ref-molestia').style.display = 'none';
        document.getElementById('screen-audio').style.display = 'flex';
        initializeQuiz();
    }
};

// ── Audios del experimento ────────────────────────────────────────────────────
const audioFiles = [
    'mensaje1_road_equal_hrtf.wav', 'mensaje1_road_low_hrtf.wav', 'mensaje1_road_high_hrtf.wav',
    'mensaje1_voices_equal_hrtf.wav', 'mensaje1_voices_low_hrtf.wav', 'mensaje1_voices_high_hrtf.wav',
    'mensaje1_nature_equal_hrtf.wav', 'mensaje1_nature_low_hrtf.wav', 'mensaje1_nature_high_hrtf.wav',
    'mensaje2_road_equal_hrtf.wav', 'mensaje2_road_low_hrtf.wav', 'mensaje2_road_high_hrtf.wav',
    'mensaje2_voices_equal_hrtf.wav', 'mensaje2_voices_low_hrtf.wav', 'mensaje2_voices_high_hrtf.wav',
    'mensaje2_nature_equal_hrtf.wav', 'mensaje2_nature_low_hrtf.wav', 'mensaje2_nature_high_hrtf.wav'
];

let currentAudioIndex = 0;
let allResponses = [];
let quizCompleteTimestamp = '';
// Persisted CSV content if user imports an existing file to append to
window._loadedCsvContent = null;

// En modo escritorio (Electron) los resultados se envían por correo, así que
// el bloque opcional de "Configurar carpeta CSV" no tiene utilidad: se oculta.
window.addEventListener('DOMContentLoaded', () => {
  if (window.electronAPI) {
    const blk = document.getElementById('data-save-block');
    if (blk) blk.style.display = 'none';
  }
});

function initializeQuiz() {
    currentAudioIndex = 0;
    allResponses = [];
    loadAudio(currentAudioIndex);
}

function toggleReference(type) {
    const div = document.getElementById(`support_${type}`);
    const arrow = document.getElementById(`arrow_${type}`);
    
    if (div.style.display === 'none') {
        div.style.display = 'block';
        arrow.src = './styles/images/up-arrow.png';
    } else {
        div.style.display = 'none';
        arrow.src = './styles/images/down-arrow.png';
    }
}

function parseAudioFilename(filename) {
    const parts = filename.replace('_hrtf.wav', '').split('_');
    return {
        mensaje: parts[0],
        ruido: parts[1],
        nivel: parts[2]
    };
}

function loadAudio(index) {
    const audio = document.getElementById('main-audio');
    const source = document.getElementById('audio-source');
    const title = document.getElementById('audio-title');
    const counter = document.getElementById('audio-counter');

    const audioData = parseAudioFilename(audioFiles[index]);

    source.src = `./resources/audios/${audioFiles[index]}`;
    audio.load();

    title.textContent = `Mensaje de Evacuación ${audioData.mensaje.replace('mensaje', '')}`;
    counter.textContent = index + 1;
    
    resetAudioQuestions();
}

function resetAudioQuestions() {
    document.getElementsByName('molestia').forEach(radio => radio.checked = false);
    
    document.getElementsByName('fuentes').forEach(checkbox => checkbox.checked = false);
    
    document.querySelectorAll('input[name^="afectiva_"]').forEach(radio => radio.checked = false);
}

function submitAudioResponse() {
    const molestiaSelected = document.querySelector('input[name="molestia"]:checked');
    
    if (!molestiaSelected) {
        alert('Por favor, indique el nivel de molestia (pregunta 6).');
        return;
    }
    
    const fuentesSelected = [];
    document.querySelectorAll('input[name="fuentes"]:checked').forEach(cb => {
        fuentesSelected.push(cb.value);
    });
    
    if (fuentesSelected.length === 0) {
        alert('Por favor, indique al menos una fuente sonora detectada (pregunta 8).');
        return;
    }
    
    const afectivas = {};
    const afectivaKeys = ['agradable', 'caotico', 'estimulante', 'sinactividad', 'calmado', 'molesto', 'conactividad', 'monotono'];
    let allAfectivasOK = true;
    
    for (let key of afectivaKeys) {
        const selected = document.querySelector(`input[name="afectiva_${key}"]:checked`);
        if (!selected) {
            allAfectivasOK = false;
            break;
        }
        afectivas[key] = selected.value;
    }
    
    if (!allAfectivasOK) {
        alert('Por favor, complete todas las preguntas de percepción afectiva (pregunta 9).');
        return;
    }
    
    const audioData = parseAudioFilename(audioFiles[currentAudioIndex]);
    
    const response = {
        timestamp_respuesta: new Date().toISOString(),
        audio_index: currentAudioIndex + 1,
        audio_filename: audioFiles[currentAudioIndex],
        mensaje: audioData.mensaje,
        ruido: audioData.ruido,
        nivel: audioData.nivel,
        molestia: molestiaSelected.value,
        fuentes: fuentesSelected.join(';'),
        afectiva_agradable: afectivas.agradable,
        afectiva_caotico: afectivas.caotico,
        afectiva_estimulante: afectivas.estimulante,
        afectiva_sinactividad: afectivas.sinactividad,
        afectiva_calmado: afectivas.calmado,
        afectiva_molesto: afectivas.molesto,
        afectiva_conactividad: afectivas.conactividad,
        afectiva_monotono: afectivas.monotono
    };
    
    allResponses.push(response);
    
    currentAudioIndex++;
    
    if (currentAudioIndex < audioFiles.length) {
        loadAudio(currentAudioIndex);
    } else {
        completeQuiz();
    }
}

async function completeQuiz() {
    quizCompleteTimestamp = new Date().toISOString();

    document.getElementById('screen-audio').style.display = 'none';
    document.getElementById('screen-summary').style.display = 'flex';
    const statusEl = document.getElementById('csv-save-status');

    // Modo escritorio (Electron): enviar los resultados por correo
    if (window.electronAPI && typeof window.electronAPI.sendResults === 'function') {
        const csv = buildStandaloneCsv();
        window._loadedCsvContent = csv;
        const ts = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `paisajes_sonoros_${ts}.csv`;

        if (statusEl) {
            statusEl.textContent = 'Enviando respuestas por correo...';
            statusEl.style.color = '#f39c12';
        }
        try {
            const res = await window.electronAPI.sendResults(csv, filename);
            if (!res || !res.ok) throw new Error(res && res.error ? res.error : 'desconocido');
            if (statusEl) {
                statusEl.textContent = 'Respuestas enviadas por correo correctamente.';
                statusEl.style.color = '#2ecc71';
            }
        } catch (e) {
            if (statusEl) {
                statusEl.textContent = 'No se pudo enviar el correo (' + e.message +
                    '). Pulse "Descargar CSV manualmente" para no perder los datos.';
                statusEl.style.color = '#e74c3c';
            }
        }
        return;
    }

    // Modo web: comportamiento existente (carpeta FS API o descarga)
    const savedToDir = await saveToCSV();
    if (statusEl) {
        if (savedToDir) {
            statusEl.textContent = 'Datos guardados en el archivo CSV de la carpeta configurada.';
            statusEl.style.color = '#2ecc71';
        } else {
            statusEl.textContent = 'Se ha descargado el archivo CSV con sus respuestas.';
            statusEl.style.color = '#f39c12';
        }
    }
}

// Nueva función: Proceder al cuestionario despues de la molestia de referencia
window.proceedToAudioQuiz = function() {
    const refSelected = document.querySelector('input[name="molestia_ref_before"]:checked');
    if (!refSelected) {
        alert('Por favor, indique la molestia del audio de referencia (pregunta 6.a).');
        return;
    }
    // Guardar respuesta de referencia para usarla en cada fila de este participante
    window._molestiaRefBefore = refSelected.value;
    
    document.getElementById('screen-ref-molestia').style.display = 'none';
    document.getElementById('screen-audio').style.display = 'flex';
    initializeQuiz();
}

function initializeQuiz() {
    currentAudioIndex = 0;
    allResponses = [];
    // Reiniciar también la respuesta de referencia para este participante
    loadAudio(currentAudioIndex);
}

// ── Construcción del CSV ──────────────────────────────────────────────────────
// Cabecera (columnas ref_* dinámicas a partir de refAudioFiles)
function csvHeaders() {
  // El nombre de archivo ya empieza por "ref_", solo se quita la extensión
  const refHeaders = refAudioFiles.map(f => f.replace('.wav', ''));
  return [
    'participante_id','timestamp_inicio','timestamp_respuesta','timestamp_fin',
    'edad','genero','estudios','audicion','castellano',
    'audio_index','audio_filename','mensaje','ruido','nivel',
    'molestia',
    ...refHeaders,
    'fuentes',
    'afectiva_agradable','afectiva_caotico','afectiva_estimulante',
    'afectiva_sinactividad','afectiva_calmado','afectiva_molesto',
    'afectiva_conactividad','afectiva_monotono'
  ];
}

// Filas de este participante, numerando participante_id desde startId
function csvRows(startId) {
  const refVals = refAudioFiles.map((f, i) =>
    (window._refResponses && window._refResponses[i])
      ? window._refResponses[i].value
      : ''
  );
  let id = startId;
  let rows = '';
  for (let response of allResponses) {
    const row = [
      id++,
      demographicData.timestamp_inicio,
      response.timestamp_respuesta,
      quizCompleteTimestamp,
      demographicData.edad,
      demographicData.genero,
      demographicData.estudios,
      demographicData.audicion,
      demographicData.castellano,
      response.audio_index,
      response.audio_filename,
      response.mensaje,
      response.ruido,
      response.nivel,
      response.molestia,
      ...refVals,
      `"${response.fuentes}"`,
      response.afectiva_agradable,
      response.afectiva_caotico,
      response.afectiva_estimulante,
      response.afectiva_sinactividad,
      response.afectiva_calmado,
      response.afectiva_molesto,
      response.afectiva_conactividad,
      response.afectiva_monotono
    ];
    rows += row.join(',') + '\n';
  }
  return rows;
}

// CSV autónomo (cabecera + filas del participante) — usado en modo Electron/correo
function buildStandaloneCsv() {
  return csvHeaders().join(',') + '\n' + csvRows(1).trimEnd();
}

// Modo web: guardar en carpeta configurada (FS API) o descargar como fallback
async function saveToCSV() {
  const headers = csvHeaders();

  // Intentar leer CSV existente desde la carpeta configurada (FS API)
  let base = '';
  try {
    base = await readCsvFromDir();
  } catch (e) { base = ''; }

  // Si no hay contenido previo, empezar con la cabecera
  if (!base || base.trim() === '') base = headers.join(',') + '\n';

  // Calcular el siguiente participante_id a partir de la última fila
  let nextId = 1;
  const lines = base.trim().split('\n');
  if (lines.length > 1) {
    const last = lines[lines.length - 1];
    const firstCell = last.split(',')[0];
    const lastId = Number(firstCell);
    if (!isNaN(lastId)) nextId = lastId + 1;
  }

  const finalContent = base.trimEnd() + '\n' + csvRows(nextId).trimEnd();
  window._loadedCsvContent = finalContent;

  // Intentar guardar en la carpeta configurada (FS API)
  if (window._dirHandle) {
    const saved = await writeCsvToDir(finalContent);
    if (saved) {
      console.log('CSV guardado en carpeta configurada.');
      return true;
    }
    console.warn('writeCsvToDir falló, descargando como fallback.');
  }

  // Fallback: descarga directa como archivo
  downloadCsvBlob(finalContent);
  return false;
}

function downloadCsvBlob(content) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  link.href = URL.createObjectURL(blob);
  link.download = `paisajes_sonoros_${timestamp}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
}

function generateParticipantId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

function findLastParticipantId(content) {
    const lines = content.trim().split('\n');
    if (lines.length < 2) return null;
    const lastLine = lines[lines.length - 1];
    const firstCell = lastLine.split(',')[0];
    const num = parseInt(firstCell);
    return isNaN(num) ? null : num;
}

function appendNewResponses(existingCsv, participantId) {
    const refVals = refAudioFiles.map((f, i) =>
        (window._refResponses && window._refResponses[i])
            ? window._refResponses[i].value
            : ''
    );

    let newRows = '';
    for (let response of allResponses) {
        const row = [
            participantId,
            demographicData.timestamp_inicio,
            response.timestamp_respuesta,
            quizCompleteTimestamp,
            demographicData.edad,
            demographicData.genero,
            demographicData.estudios,
            demographicData.audicion,
            demographicData.castellano,
            response.audio_index,
            response.audio_filename,
            response.mensaje,
            response.ruido,
            response.nivel,
            response.molestia,
            ...refVals,
            `"${response.fuentes}"`,
            response.afectiva_agradable,
            response.afectiva_caotico,
            response.afectiva_estimulante,
            response.afectiva_sinactividad,
            response.afectiva_calmado,
            response.afectiva_molesto,
            response.afectiva_conactividad,
            response.afectiva_monotono
        ];
        newRows += row.join(',') + '\n';
    }
    
    const finalCsv = existingCsv.trim() + '\n' + newRows.trim();
    
    const blob = new Blob([finalCsv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    link.href = URL.createObjectURL(blob);
    link.download = `paisajes_sonoros_completo_${timestamp}.csv`;
    link.click();
    
    localStorage.setItem('lastQuizTimestamp', quizCompleteTimestamp);
    localStorage.setItem('lastQuizData', JSON.stringify({
        demographic: demographicData,
        responses: allResponses,
        completeTimestamp: quizCompleteTimestamp,
        participantId: participantId
    }));
}
