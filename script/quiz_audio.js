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
    const info = document.getElementById('audio-info');
    const counter = document.getElementById('audio-counter');
    
    const audioData = parseAudioFilename(audioFiles[index]);
    
    source.src = `./resources/audios/${audioFiles[index]}`;
    audio.load();
    
    const nivelTexto = {
        'equal': 'Nivel igual',
        'low': 'Nivel bajo (-8 dB)',
        'high': 'Nivel alto (+8 dB)'
    };
    
    const ruidoTexto = {
        'road': 'Tráfico',
        'voices': 'Voces',
        'nature': 'Naturaleza'
    };
    
    title.textContent = `Mensaje de Evacuación ${audioData.mensaje.replace('mensaje', '')}`;
    info.textContent = `Ruido: ${ruidoTexto[audioData.ruido]} | ${nivelTexto[audioData.nivel]}`;
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

function completeQuiz() {
    quizCompleteTimestamp = new Date().toISOString();
    saveToCSV();
    
    document.getElementById('screen-audio').style.display = 'none';
    document.getElementById('screen-summary').style.display = 'flex';
}

function saveToCSV() {
    const headers = [
        'participante_id', 'timestamp_inicio', 'timestamp_respuesta', 'timestamp_fin',
        'edad', 'genero', 'estudios', 'audicion', 'castellano',
        'audio_index', 'audio_filename', 'mensaje', 'ruido', 'nivel',
        'molestia', 'fuentes',
        'afectiva_agradable', 'afectiva_caotico', 'afectiva_estimulante', 
        'afectiva_sinactividad', 'afectiva_calmado', 'afectiva_molesto',
        'afectiva_conactividad', 'afectiva_monotono'
    ];
    
    let existingData = [];
    let csvContent = '';
    let participantId = generateParticipantId();
    
    const csvFile = document.getElementById('csv-file-input');
    
    if (csvFile.files.length > 0) {
        const file = csvFile.files[0];
        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            const lines = content.split('\n');
            
            if (lines.length > 1) {
                csvContent = content;
                const lastParticipantId = findLastParticipantId(content);
                if (lastParticipantId) {
                    participantId = lastParticipantId + 1;
                }
            } else {
                csvContent = headers.join(',') + '\n';
            }
            
            appendNewResponses(csvContent, participantId);
        };
        reader.readAsText(file);
    } else {
        csvContent = headers.join(',') + '\n';
        appendNewResponses(csvContent, participantId);
    }
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