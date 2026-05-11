const demographicData = {
    edad: '',
    genero: '',
    estudios: '',
    audicion: '',
    castellano: '',
    timestamp_inicio: ''
};

function startCircumplex() {
    document.getElementById('screen-instructions').style.display = 'none';
    document.getElementById('screen-circumplex').style.display = 'flex';
}

function proceedFromCircumplex() {
    document.getElementById('screen-circumplex').style.display = 'none';
    document.getElementById('screen-demographics').style.display = 'flex';
    demographicData.timestamp_inicio = new Date().toISOString();
}

function startDemographics() {
    document.getElementById('screen-instructions').style.display = 'none';
    document.getElementById('screen-demographics').style.display = 'flex';
    demographicData.timestamp_inicio = new Date().toISOString();
}

function validateDemographics() {
    demographicData.edad = document.getElementById('edad').value;
    
    const generoRadios = document.getElementsByName('genero');
    for (let radio of generoRadios) {
        if (radio.checked) {
            demographicData.genero = radio.value;
            break;
        }
    }
    
    demographicData.estudios = document.getElementById('estudios').value;
    
    const audicionRadios = document.getElementsByName('audicion');
    for (let radio of audicionRadios) {
        if (radio.checked) {
            demographicData.audicion = radio.value;
            break;
        }
    }
    
    const castellanoRadios = document.getElementsByName('castellano');
    for (let radio of castellanoRadios) {
        if (radio.checked) {
            demographicData.castellano = radio.value;
            break;
        }
    }
    
    if (!demographicData.edad || !demographicData.genero || !demographicData.estudios || 
        !demographicData.audicion || !demographicData.castellano) {
        alert('Por favor, complete todas las preguntas.');
        return;
    }
    
    document.getElementById('screen-demographics').style.display = 'none';
    document.getElementById('screen-ref-molestia').style.display = 'flex';

    // Inicializar la secuencia de 9 audios de referencia
    currentRefIndex = 0;
    refResponses.length = 0;
    window._refResponses = null;
    loadRefAudio(0);
}