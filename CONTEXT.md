# CONTEXT.md — Proyecto Paisajes Sonoros (TFG URJC)

> Este archivo describe **todo el estado actual del proyecto** para que Claude pueda retomar el trabajo desde cualquier ubicación sin perder contexto. Actualizado: 2026-06-08.

---

## 1. Descripción general del proyecto

**Título:** Estudio de Percepción de Paisajes Sonoros  
**Tipo:** Trabajo de Fin de Grado — Universidad Rey Juan Carlos (URJC)  
**Naturaleza:** Aplicación web de cuestionario perceptual + análisis estadístico-acústico en Python  
**Stack:** HTML/CSS/JavaScript vanilla (sin frameworks) + Python 3.9 (pandas, matplotlib, scipy, scikit-maad)  
**Ruta local (Windows):** `K:\Universidad\TFG\paisajessonoros`

El proyecto recopila evaluaciones perceptuales de participantes sobre 18 audios binaurales de mensajes de evacuación mezclados con distintos tipos de ruido de fondo. Los participantes evalúan: nivel de molestia, fuentes sonoras detectadas y percepción afectiva (modelo circumplejo ISO 12913-2). Los datos se guardan en CSV y se analizan offline con Python.

---

## 2. Estructura de directorios completa

```
paisajessonoros/
├── index.html                        ← Página de inicio (landing)
├── audio_quiz.html                   ← Cuestionario principal (SPA multi-pantalla)
├── analizar_resultados.py            ← Script Python de análisis (870 líneas)
├── CONTEXT.md                        ← Este archivo
│
├── script/
│   ├── quiz_demographic.js           ← Lógica demográfica + navegación entre pantallas
│   ├── quiz_audio.js                 ← Lógica audios referencia + experimento + CSV
│   ├── filesystem.js                 ← File System Access API + IndexedDB
│   ├── audio_quiz.js                 ← Script legacy (sistema antiguo, no tocar)
│   ├── content.js                    ← Toggle show/hide genérico
│   ├── converter.js                  ← Conversor formato JSON antiguo→nuevo
│   ├── showAudioInstructions.js      ← Soporte instrucciones audio
│   ├── start_quiz.js                 ← Minimal (sin uso activo)
│   ├── results.js                    ← Vacío
│   ├── video_quiz.js                 ← Sistema antiguo cuestionario vídeo
│   └── resultados/                   ← Scripts del sistema antiguo de visualización
│       ├── index_readfile.js
│       ├── index_comparation.js
│       ├── comparation_cities.js
│       ├── Canvas/                   ← Gráficas canvas legacy
│       ├── functions/
│       └── getData/
│
├── styles/
│   ├── style.css                     ← Estilos globales
│   ├── style_quiz.css                ← Estilos del cuestionario (ACTIVO)
│   ├── style_nav.css                 ← Estilos barra navegación
│   ├── style_read.css                ← Legacy
│   ├── style_canvas.css              ← Legacy
│   ├── styles-form.css               ← Legacy
│   ├── results-style.css             ← Vacío
│   ├── background1.jpg               ← Fondo oscuro del cuestionario
│   └── images/                       ← Iconos, logos, flechas, etc.
│       └── logo_urjc.png, logo3.ico, up-arrow.png, down-arrow.png, ...
│
├── resources/
│   ├── audios/                       ← 27 WAV binaurales HRTF (experimento)
│   │   ├── mensaje1_road_equal_hrtf.wav
│   │   ├── mensaje1_road_low_hrtf.wav
│   │   ├── mensaje1_road_high_hrtf.wav
│   │   ├── mensaje1_voices_equal_hrtf.wav
│   │   ├── mensaje1_voices_low_hrtf.wav
│   │   ├── mensaje1_voices_high_hrtf.wav
│   │   ├── mensaje1_nature_equal_hrtf.wav
│   │   ├── mensaje1_nature_low_hrtf.wav
│   │   ├── mensaje1_nature_high_hrtf.wav
│   │   ├── mensaje2_road_equal_hrtf.wav
│   │   ├── mensaje2_road_low_hrtf.wav
│   │   ├── mensaje2_road_high_hrtf.wav
│   │   ├── mensaje2_voices_equal_hrtf.wav
│   │   ├── mensaje2_voices_low_hrtf.wav
│   │   ├── mensaje2_voices_high_hrtf.wav
│   │   ├── mensaje2_nature_equal_hrtf.wav
│   │   ├── mensaje2_nature_low_hrtf.wav
│   │   ├── mensaje2_nature_high_hrtf.wav
│   │   ├── mensaje3_road_equal_hrtf.wav   ← mensaje3 existe en disco pero NO
│   │   ├── mensaje3_road_low_hrtf.wav         está en el array audioFiles del JS
│   │   ├── mensaje3_road_high_hrtf.wav        (solo mensaje1 y mensaje2 se usan)
│   │   ├── mensaje3_voices_equal_hrtf.wav
│   │   ├── mensaje3_voices_low_hrtf.wav
│   │   ├── mensaje3_voices_high_hrtf.wav
│   │   ├── mensaje3_nature_equal_hrtf.wav
│   │   ├── mensaje3_nature_low_hrtf.wav
│   │   └── mensaje3_nature_high_hrtf.wav
│   │
│   ├── ref/                          ← 9 WAV de referencia para calibración
│   │   ├── ref_28.wav                   (niveles de presión sonora en dB SPL:
│   │   ├── ref_32.wav                    28, 32, 36, 40, 44, 48, 52, 56, 60)
│   │   ├── ref_36.wav                   Cada archivo pesa ~3.97 MB
│   │   ├── ref_40.wav
│   │   ├── ref_44.wav
│   │   ├── ref_48.wav
│   │   ├── ref_52.wav
│   │   ├── ref_56.wav
│   │   └── ref_60.wav
│   │
│   ├── examples/                     ← Audios soporte PAC (modelo circumplejo)
│   │   ├── Pleasant/Agradable.wav
│   │   ├── Uneventful/No_definido.wav
│   │   ├── Annoying/Molesto.wav
│   │   ├── Eventful/Eventful.wav
│   │   ├── Calm/Calma.wav
│   │   ├── Chaotic/Caótico.wav
│   │   ├── Monotonous/Monótono.wav
│   │   └── Vibrant/vibrante.wav
│   │
│   ├── img/
│   │   └── modelo_circumplejo.png    ← Diagrama del modelo circumplejo ISO 12913-2
│   │
│   └── templates/
│       ├── oldTemplate.json          ← Formato JSON sistema antiguo
│       └── newTemplate.json          ← Formato JSON sistema antiguo (nuevo)
│
├── CSV/
│   ├── paisajes_sonoros.csv          ← CSV principal de resultados (ACTIVO)
│   └── resultados/                   ← Gráficas y análisis generados por Python
│       ├── afectivas_global.png
│       ├── afectivas_por_ruido.png
│       ├── comparacion_referencia.png
│       ├── cronologia_resultados.png
│       ├── heatmap_molestia.png
│       ├── informe.txt
│       ├── maad_correlacion_molestia.png
│       ├── maad_espectrogramas.png
│       ├── maad_indices.csv
│       ├── maad_indices_por_nivel.png
│       ├── maad_indices_por_ruido.png
│       ├── molestia_resumen.png
│       └── radar_afectivas.png
│
└── [páginas legacy — no modificar]
    ├── video_quiz.html
    ├── resultados.html
    ├── comparation.html
    ├── comparation-cities.html
    ├── comparation-visual.html
    ├── read_file.html
    └── converter.html
```

---

## 3. Flujo del cuestionario (audio_quiz.html)

La aplicación es una **SPA de pantalla única** que alterna visibilidad de `div.wrapper` mediante `display: none/flex`. El orden es estrictamente lineal:

```
screen-instructions
      ↓  startCircumplex()
screen-circumplex
      ↓  proceedFromCircumplex()
screen-demographics
      ↓  validateDemographics()
screen-ref-molestia      ← 9 audios de referencia (ref_28…ref_60), uno por uno
      ↓  nextRefAudio() × 9 → al último llama initializeQuiz()
screen-audio             ← 18 audios del experimento, iterados
      ↓  submitAudioResponse() × 18 → al último llama completeQuiz()
screen-summary
```

### Pantalla 1: screen-instructions
- Instrucciones de uso
- Consentimiento informado
- Bloque opcional "Configurar carpeta CSV" → `setupCsvDirectory()` (filesystem.js)
- Botón "Continuar" → `startCircumplex()`

### Pantalla 2: screen-circumplex
- Explicación del Modelo Circumplejo (ISO 12913-2)
- Imagen: `resources/img/modelo_circumplejo.png`
- Descripción de los dos ejes: Agradable↔Molesto (valence), Dinámico↔Estático (activation)
- Botón "Continuar" → `proceedFromCircumplex()`

### Pantalla 3: screen-demographics
- Pregunta 1: Edad (select: 18-25, 25-35, 35-45, 45-55, 55-65, 65+)
- Pregunta 2: Género (radio: Masculino/Femenino/Otro)
- Pregunta 3: Nivel de estudios (select: Sin estudios → Doctorado)
- Pregunta 4: Problemas de audición (radio: Sí/No)
- Pregunta 5: Castellano lengua materna (radio: Sí/No)
- Botón "Siguiente" → `validateDemographics()`

### Pantalla 4: screen-ref-molestia
Mini-cuestionario de 9 pasos **sin cambiar de pantalla**:
- Barra de progreso animada ("Audio X de 9 — XX%")
- Reproductor `<audio id="audio_ref_molestia">` que carga `resources/ref/ref_NN.wav`
- Pregunta: "¿Cuánto le molesta o perturba este audio?" (radio 0–10, name=`molestia_ref_current`)
- Botón "Siguiente" (en el último: "Comenzar Cuestionario") → `nextRefAudio()`
- Al completar los 9: guarda `window._refResponses = [{file, value}, …]`, muestra screen-audio

### Pantalla 5: screen-audio (18 iteraciones)
Por cada audio (el mismo HTML se reutiliza, se actualizan dinámicamente los valores):

**Cabecera:** "Audio X de 18" + reproductor `<audio id="main-audio">` + info del ruido/nivel

**SECCIÓN 1 — MOLESTIA** (borde azul `#3498db`):
- Pregunta 6: "¿Cuánto le molesta o perturba este sonido?" (radio 0–10, name=`molestia`)

**SECCIÓN 2 — PERCEPCIÓN AFECTIVA PAC** (borde verde `#2ecc71`):
- 4 audios de soporte (Agradable, Estático, Molesto, Dinámico) como referencia perceptual
- Pregunta 8: Fuentes sonoras detectadas (checkboxes: `trafico`, `humano`, `natural`)
- Pregunta 9: 8 items Likert 1–5 (Agradable, Caótico, Estimulante, Sin actividad, Calmado, Molesto, Con actividad, Monótono)

Botón "Siguiente Audio" → `submitAudioResponse()`

### Pantalla 6: screen-summary
- Mensaje de agradecimiento
- Estado del guardado (`#csv-save-status`): verde si FS API, naranja si descarga
- Botón "Descargar CSV manualmente" → `downloadCsvBlob(window._loadedCsvContent)`

---

## 4. Código fuente completo — script/quiz_demographic.js

```javascript
const demographicData = {
    edad: '', genero: '', estudios: '', audicion: '', castellano: '',
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

function startDemographics() {  // legacy, mantener por compatibilidad
    document.getElementById('screen-instructions').style.display = 'none';
    document.getElementById('screen-demographics').style.display = 'flex';
    demographicData.timestamp_inicio = new Date().toISOString();
}

function validateDemographics() {
    demographicData.edad = document.getElementById('edad').value;
    // ... leer radios de genero, audicion, castellano ...
    // validar todos los campos requeridos
    document.getElementById('screen-demographics').style.display = 'none';
    document.getElementById('screen-ref-molestia').style.display = 'flex';
    // Inicializar secuencia de 9 audios de referencia:
    currentRefIndex = 0;
    refResponses.length = 0;
    window._refResponses = null;
    loadRefAudio(0);
}
```

---

## 5. Código fuente completo — script/quiz_audio.js

### Variables globales
```javascript
// Referencia (9 audios)
const refAudioFiles = ['ref_28.wav','ref_32.wav','ref_36.wav','ref_40.wav',
                       'ref_44.wav','ref_48.wav','ref_52.wav','ref_56.wav','ref_60.wav'];
let currentRefIndex = 0;
const refResponses = [];   // [{file, value}, …]

// Experimento (18 audios)
const audioFiles = [
    'mensaje1_road_equal_hrtf.wav', 'mensaje1_road_low_hrtf.wav', 'mensaje1_road_high_hrtf.wav',
    'mensaje1_voices_equal_hrtf.wav','mensaje1_voices_low_hrtf.wav','mensaje1_voices_high_hrtf.wav',
    'mensaje1_nature_equal_hrtf.wav','mensaje1_nature_low_hrtf.wav','mensaje1_nature_high_hrtf.wav',
    'mensaje2_road_equal_hrtf.wav', 'mensaje2_road_low_hrtf.wav', 'mensaje2_road_high_hrtf.wav',
    'mensaje2_voices_equal_hrtf.wav','mensaje2_voices_low_hrtf.wav','mensaje2_voices_high_hrtf.wav',
    'mensaje2_nature_equal_hrtf.wav','mensaje2_nature_low_hrtf.wav','mensaje2_nature_high_hrtf.wav'
];
let currentAudioIndex = 0;
let allResponses = [];
let quizCompleteTimestamp = '';
window._loadedCsvContent = null;
```

### Funciones clave
- `loadRefAudio(index)` — Carga `resources/ref/refAudioFiles[index]`, actualiza barra de progreso y contador, cambia texto del botón en el último
- `window.nextRefAudio()` — Valida selección, push a `refResponses`, avanza o lanza `initializeQuiz()`
- `parseAudioFilename(filename)` — Extrae `{mensaje, ruido, nivel}` de `mensaje1_road_equal_hrtf.wav`
- `loadAudio(index)` — Carga el audio del experimento, actualiza título/info/contador, llama `resetAudioQuestions()`
- `resetAudioQuestions()` — Limpia todos los radios de molestia, fuentes y afectivas
- `submitAudioResponse()` — Valida molestia + fuentes + 8 afectivas, push a `allResponses`, avanza o llama `completeQuiz()`
- `completeQuiz()` — Guarda timestamp, llama `saveToCSV()`, muestra screen-summary con estado
- `saveToCSV()` — Construye CSV con cabeceras dinámicas (incluyendo ref_28…ref_60), intenta FS API, fallback a `downloadCsvBlob()`
- `downloadCsvBlob(content)` — Crea Blob y descarga como `paisajes_sonoros_TIMESTAMP.csv`
- `appendNewResponses(existingCsv, participantId)` — Función legacy de descarga directa (no se usa en el flujo principal)

### Estructura de una fila CSV
```
participante_id | timestamp_inicio | timestamp_respuesta | timestamp_fin |
edad | genero | estudios | audicion | castellano |
audio_index | audio_filename | mensaje | ruido | nivel |
molestia |
ref_28 | ref_32 | ref_36 | ref_40 | ref_44 | ref_48 | ref_52 | ref_56 | ref_60 |
fuentes |
afectiva_agradable | afectiva_caotico | afectiva_estimulante | afectiva_sinactividad |
afectiva_calmado | afectiva_molesto | afectiva_conactividad | afectiva_monotono
```

**Notas importantes sobre el CSV:**
- Por cada participante se generan **18 filas** (una por audio del experimento)
- Los valores `ref_*` se repiten idénticos en las 18 filas del mismo participante (son datos del participante, no del audio)
- `fuentes` se almacena entre comillas: `"trafico;natural"` (separado por `;`)
- `participante_id` es un entero autoincrementado leyendo la última fila del CSV existente

---

## 6. Código fuente completo — script/filesystem.js

Sistema de persistencia con **File System Access API** + **IndexedDB**:

- `openDb()` — Abre IndexedDB `paisajes_csv_fs`, store `handles`
- `putHandle(key, value)` / `getHandle(key)` — CRUD sobre el store
- `window.setupCsvDirectory()` — Llama `showDirectoryPicker()`, guarda handle en IndexedDB y `window._dirHandle`
- `loadConfiguredDirectory()` — Al cargar la página, restaura `window._dirHandle` desde IndexedDB
- `readCsvFromDir()` — Lee `paisajes_sonoros.csv` del directorio configurado
- `writeCsvToDir(content)` — Escribe/sobreescribe `paisajes_sonoros.csv` en el directorio configurado

---

## 7. Estructura HTML de audio_quiz.html (resumen por pantalla)

```html
<!-- Scripts cargados (defer) -->
<script src="script/quiz_demographic.js">
<script src="script/filesystem.js">
<script src="script/quiz_audio.js">

<!-- NAV: solo link a index.html + logo URJC -->

<!-- PANTALLA 1: instrucciones -->
<div class="wrapper" id="screen-instructions" style="display: flex;">
  <!-- instrucciones, consentimiento, botón CSV opcional, botón "Continuar" → startCircumplex() -->

<!-- PANTALLA 2: modelo circumplejo -->
<div class="wrapper" id="screen-circumplex" style="display: none;">
  <!-- imagen modelo_circumplejo.png, descripción ejes, botón → proceedFromCircumplex() -->

<!-- PANTALLA 3: demografía -->
<div class="wrapper" id="screen-demographics" style="display: none;">
  <!-- 5 preguntas (edad, género, estudios, audición, castellano), botón → validateDemographics() -->

<!-- PANTALLA 4: evaluación audios referencia (9 pasos sin cambiar pantalla) -->
<div class="wrapper" id="screen-ref-molestia" style="display: none;">
  <!-- barra de progreso, <audio id="audio_ref_molestia">, radio 0-10, botón → nextRefAudio() -->

<!-- PANTALLA 5: 18 audios del experimento -->
<div class="wrapper" id="screen-audio" style="display: none;">
  <!-- contador "Audio X de 18", <audio id="main-audio"> -->
  <!-- SECCIÓN 1 (azul): molestia 0-10 -->
  <!-- SECCIÓN 2 (verde): 4 audios soporte PAC + fuentes checkboxes + 8 Likert -->
  <!-- botón "Siguiente Audio" → submitAudioResponse() -->

<!-- PANTALLA 6: resumen final -->
<div class="wrapper" id="screen-summary" style="display: none;">
  <!-- mensaje gracias, estado CSV, botón descarga manual -->
```

---

## 8. CSS relevante — styles/style_quiz.css (cambios clave)

```css
/* Centrado de instrucciones y respuestas */
div[id^="wrapper_instructions"], div[id^="wrapper_replys"] {
    text-align: center;
    margin: 0 auto;
}

/* Tablas centradas dentro de .wrapper */
.wrapper table { margin: 0 auto; }
.wrapper table td, .wrapper table th { text-align: center; }

/* Botón principal de navegación */
button[id^="button_next"] {
    background-color: transparent;
    color: #ffffff;
    font-size: x-large;
    border: #ffffff 1px solid;
    border-radius: 5%;
    padding: 2%;
    /* hover: animación neon (text-shadow blanco parpadeante) */
}

/* Fondo oscuro con imagen */
body {
    background: rgba(0,0,0,0.8) url('background1.jpg');
    background-blend-mode: darken;
    color: #ffffff;
    font-family: 'Gill Sans', Calibri, 'Trebuchet MS', sans-serif;
}
```

---

## 9. CSV — Estructura actual y datos

**Archivo:** `CSV/paisajes_sonoros.csv`

**Cabecera completa (33 columnas):**
```
participante_id, timestamp_inicio, timestamp_respuesta, timestamp_fin,
edad, genero, estudios, audicion, castellano,
audio_index, audio_filename, mensaje, ruido, nivel,
molestia,
ref_28, ref_32, ref_36, ref_40, ref_44, ref_48, ref_52, ref_56, ref_60,
fuentes,
afectiva_agradable, afectiva_caotico, afectiva_estimulante, afectiva_sinactividad,
afectiva_calmado, afectiva_molesto, afectiva_conactividad, afectiva_monotono
```

**Estado actual de datos:**
- 1 participante completado (18 filas), participante_id secuencial (el único tiene id 1-18 porque el contador por fila subía, no debería; los futuros participantes arrancarán desde el último id+1)
- Las columnas `ref_*` están vacías en los datos históricos (ese participante completó el cuestionario antes de implementarse esa sección)
- La columna `molestia_ref_before` (columna legacy) fue renombrada/eliminada y reemplazada por las 9 columnas `ref_*`

---

## 10. analizar_resultados.py — Arquitectura completa

**Uso:**
```bash
python analizar_resultados.py CSV/paisajes_sonoros.csv
python analizar_resultados.py CSV/paisajes_sonoros.csv --audio-dir resources/audios
```

**Dependencias:** `pandas`, `matplotlib`, `numpy`, `scipy`, `scikit-maad` (v1.5.2)

### Clase Analyzer — métodos

#### `__init__(csv_path, audio_dir=None)`
- Lee CSV, convierte columnas a numérico
- Detecta automáticamente columnas `ref_*` (→ `self.ref_cols`, `self.ref_niveles`)
- Crea `self.df_part` (una fila por participante, por `drop_duplicates('participante_id')`)
- `self.afectivas`: lista de 8 columnas afectivas
- `self.nombres_afectivas`: nombres legibles de las 8 dimensiones
- Outputs a `CSV/resultados/`

#### Métodos de texto (stdout + informe.txt)
| Método | Qué imprime |
|--------|-------------|
| `info_general()` | N participantes, totales, demografía, resumen ref_cols si existen |
| `estadisticas_molestia()` | Describe ref por nivel dB + experimento, por ruido/mensaje/nivel/combinación |
| `comparacion_referencia()` | Curva dB ref, Pearson r, t-test pareado, dif por ruido/nivel |
| `estadisticas_fuentes()` | Frecuencia trafico/humano/natural |
| `estadisticas_afectivas()` | Media/std de las 8 dimensiones + por ruido |

#### Métodos gráficos → `CSV/resultados/`
| Método | Archivo generado | Descripción |
|--------|-----------------|-------------|
| `grafico_cronologia()` | `cronologia_resultados.png` | Timeline molestia por participante vs tiempo, fondo coloreado por ruido, histograma de respuestas |
| `grafico_radar_afectivas()` | `radar_afectivas.png` | Radar polar 8 dimensiones: panel global + panel por ruido |
| `grafico_molestia()` | `molestia_resumen.png` | 3 barras: por ruido / por nivel / por mensaje, con línea referencia |
| `grafico_comparacion_referencia()` | `comparacion_referencia.png` | 5 paneles: curva ref con ±std, heatmap por participante, ruido vs ref, nivel vs ref, scatter correlación |
| `grafico_heatmap()` | `heatmap_molestia.png` | Mapa de calor molestia media ruido×nivel |
| `grafico_afectivas()` | `afectivas_global.png` + `afectivas_por_ruido.png` | Barras globales + subplots 2×4 por ruido |
| `grafico_acustico_maad()` | `maad_indices_por_ruido.png`, `maad_indices_por_nivel.png`, `maad_espectrogramas.png`, `maad_correlacion_molestia.png`, `maad_indices.csv` | Análisis acústico con scikit-maad sobre los 27 archivos WAV |

#### Paleta de colores (constantes globales)
```python
COLOR_ROAD    = '#e74c3c'   # rojo
COLOR_VOICES  = '#3498db'   # azul
COLOR_NATURE  = '#2ecc71'   # verde
COLOR_LOW     = '#27ae60'   # verde oscuro
COLOR_EQUAL   = '#f39c12'   # naranja
COLOR_HIGH    = '#c0392b'   # rojo oscuro
COLOR_REF     = '#f39c12'   # naranja (línea de referencia)
COLOR_EXP     = '#8e44ad'   # morado
COLORS_AFECT  = [9 colores distintos para cada dimensión]
RUIDO_LABEL   = {'road':'Trafico', 'voices':'Voces', 'nature':'Naturaleza'}
NIVEL_ORDER   = ['low','equal','high']
NIVEL_LABEL   = ['Low (-8dB)','Equal (0dB)','High (+8dB)']
```

#### Análisis acústico con scikit-maad
Para cada uno de los 27 archivos WAV en `resources/audios/`:
1. `maad.sound.load()` → señal temporal
2. `maad.features.all_temporal_alpha_indices()` → 16 índices temporales (ZCR, MEANt, VARt, SKEWt, KURTt, LEQt, BGNt, SNRt, MED, Ht, ACTtFraction, ACTtCount, ACTtMean, EVNtFraction, EVNtMean, EVNtCount)
3. `maad.sound.spectrogram()` (nperseg=1024, noverlap=512) → espectrograma
4. `maad.features.all_spectral_alpha_indices()` → 43 índices espectrales (MEANf, VARf, ACI, NDSI, BI, ADI, AEI, Hf, etc.)
5. Índices seleccionados para gráficas: `['LEQt','Ht','ACI','NDSI','BI','ADI','SNRt','Hf']`
6. Correlación Pearson de cada índice vs molestia media por audio (rojo = p<0.05)

---

## 11. Diseño del experimento — Audios

### Parámetros del experimento
| Variable | Valores | Descripción |
|----------|---------|-------------|
| `mensaje` | mensaje1, mensaje2 | Mensaje de evacuación (voz) |
| `ruido` | road, voices, nature | Tipo de ruido de fondo |
| `nivel` | low, equal, high | Nivel relativo SNR: -8dB, 0dB, +8dB |

**Total:** 2 × 3 × 3 = 18 audios (mensaje3 existe en disco pero no se usa)

### Audios de referencia para calibración
9 tonos/ruidos con distintos niveles de presión sonora (dB SPL): 28, 32, 36, 40, 44, 48, 52, 56, 60 dB  
→ Permiten estimar la curva individual de sensibilidad a la molestia de cada participante

### Audios soporte PAC (modelo circumplejo, solo para referencia perceptual)
- `resources/examples/Pleasant/Agradable.wav` → ejemplo "Agradable"
- `resources/examples/Uneventful/No_definido.wav` → ejemplo "Estático"
- `resources/examples/Annoying/Molesto.wav` → ejemplo "Molesto"
- `resources/examples/Eventful/Eventful.wav` → ejemplo "Dinámico"

---

## 12. Modelo Circumplejo (ISO 12913-2)

El modelo describe la percepción afectiva de sonidos ambientales en un espacio 2D:

```
         DINÁMICO / EVENTFUL
              ↑
Molesto ←────┼────→ Agradable
              ↓
        ESTÁTICO / UNEVENTFUL
```

**8 dimensiones Likert (1–5)** que se mapean a este espacio:
- Eje X (valence): Agradable (+) ↔ Molesto (-)
- Eje Y (activation): Dinámico/Con actividad (+) ↔ Estático/Sin actividad (-)
- Dimensiones adicionales: Caótico, Estimulante, Calmado, Monótono

En las gráficas del script Python se visualizan como **radar chart** (8 ejes) y como **scatter 2D**.

---

## 13. Sistema de guardado CSV

### Flujo principal (nuevo sistema, filesystem.js)
1. **Opcional al inicio:** El usuario puede pulsar "Configurar carpeta CSV" → `setupCsvDirectory()` → `showDirectoryPicker()` → handle guardado en IndexedDB
2. Al cargar la página: `loadConfiguredDirectory()` restaura el handle si ya fue configurado
3. Al finalizar el cuestionario: `saveToCSV()`:
   - Intenta leer el CSV existente con `readCsvFromDir()`
   - Si no hay CSV previo, inicia con cabecera completa
   - Calcula `nextId` leyendo la última fila
   - Construye las 18 nuevas filas con todos los datos del participante
   - Intenta escribir con `writeCsvToDir()` → si falla o no hay handle, hace `downloadCsvBlob()`
4. En screen-summary: muestra estado (verde = guardado en carpeta, naranja = descargado) y botón de descarga manual

### Compatibilidad de cabeceras CSV
⚠️ Si el CSV existente tiene cabeceras distintas (ej: versión anterior con `molestia_ref_before`), el nuevo código escribirá su propia cabecera en CSVs nuevos pero NO reformateará CSVs antiguos. La migración se hizo manualmente con Python.

---

## 14. Sistema legacy (no modificar)

Los siguientes archivos son el **sistema antiguo** basado en JSON y EmailJS. Están en producción pero no se están desarrollando activamente:

- `video_quiz.html` + `script/video_quiz.js` — Cuestionario con vídeos YouTube de Menorca (Ciutadella + Maó), envía datos por email
- `resultados.html`, `comparation.html`, `comparation-cities.html`, `comparation-visual.html` — Visualización con Chart.js, leen datos JSON de GitHub
- `script/resultados/` — 14 scripts de Canvas/Chart.js para las visualizaciones legacy

**No tocar estos archivos.** El desarrollo activo es solo en `audio_quiz.html`, `script/quiz_*.js`, `script/filesystem.js`, `styles/style_quiz.css` y `analizar_resultados.py`.

---

## 15. Historial de cambios importantes (cronología)

1. **Flujo de pantallas reestructurado:** instructions → circumplejo (nueva pantalla) → demographics → ref → 18 audios → summary
2. **Sección PAC separada correctamente:** solo aparece en screen-audio (18 audios), no en otras pantallas
3. **CSV con fallback de descarga:** saveToCSV() siempre guarda aunque no haya FS API configurado
4. **9 audios de referencia:** screen-ref-molestia reemplazado por mini-cuestionario de 9 pasos con barra de progreso, evaluando ref_28…ref_60 dB
5. **Columnas CSV:** `molestia_ref_before` → reemplazado por `ref_28, ref_32, ref_36, ref_40, ref_44, ref_48, ref_52, ref_56, ref_60`
6. **analizar_resultados.py reescrito:** detección automática de columnas ref_*, métodos separados por tipo de análisis, gráficas con scikit-maad, radar chart 8 dimensiones afectivas, gráfica de cronología
7. **Centrado de textos:** `div[id^="wrapper_instructions"]` cambió de `text-align: left` a `text-align: center`
8. **HTML limpio:** eliminados todos los bloques HTML duplicados que causaban el PAC en "todas las páginas"

---

## 16. Decisiones de diseño y notas para futuros cambios

### Por qué 18 filas por participante en CSV
Cada audio genera una fila independiente para facilitar el análisis por grupos (ruido, nivel, mensaje) con pandas `groupby`. Los datos demográficos y de referencia se repiten en cada fila.

### Por qué los ref_* se repiten en las 18 filas
Mismo motivo: facilita el análisis por audio sin necesidad de joins. Al analizar, se usa `drop_duplicates('participante_id')` para obtener una fila por participante cuando se trabaja con los datos de referencia.

### Por qué nextId se incrementa por fila
Actualmente `nextId++` dentro del bucle de 18 filas hace que un participante ocupe 18 IDs consecutivos. Esto es un comportamiento existente que no se ha cambiado para no romper compatibilidad con datos existentes. Si se quisiera un ID por participante habría que calcularlo fuera del bucle.

### Limitación del análisis scikit-maad
Requiere `--audio-dir resources/audios` para funcionar. Sin este argumento, esa sección se salta silenciosamente.

### Orden de los 18 audios en el cuestionario
Los audios se presentan en el orden exacto del array `audioFiles` (no aleatorizados). Si se quisiese aleatorizar, habría que hacer `audioFiles.sort(() => Math.random() - 0.5)` en `initializeQuiz()`.

---

## 17. Comandos útiles

```bash
# Ejecutar análisis completo (solo estadísticas)
python analizar_resultados.py CSV/paisajes_sonoros.csv

# Ejecutar análisis completo con gráficas acústicas maad
python analizar_resultados.py CSV/paisajes_sonoros.csv --audio-dir resources/audios

# Verificar sintaxis Python
python -m py_compile analizar_resultados.py

# Abrir el cuestionario localmente (requiere servidor por restricciones de audio)
# Opción 1: VS Code Live Server
# Opción 2:
python -m http.server 8080
# → abrir http://localhost:8080/audio_quiz.html

# Ver estructura de archivos generados
dir CSV\resultados
```

---

## 18. Dependencias Python

```
pandas>=1.3
matplotlib>=3.4
numpy>=1.21
scipy>=1.7
scikit-maad==1.5.2   # versión confirmada instalada
```

Instalación:
```bash
pip install pandas matplotlib numpy scipy scikit-maad
```

---

## 19. Archivos que NO deben modificarse sin contexto adicional

| Archivo | Motivo |
|---------|--------|
| `script/audio_quiz.js` | Script legacy del sistema antiguo, no confundir con `quiz_audio.js` |
| `script/resultados/` | Todo el sistema de visualización legacy con JSON de GitHub |
| `video_quiz.html` | Sistema con EmailJS activo en producción |
| `resultados.html` y comparaciones | Frontend legacy que consume GitHub raw JSON |
| `resources/templates/*.json` | Formato de datos del sistema antiguo |

---

## 20. Estado actual del proyecto

**Implementado y funcionando:**
- ✅ Flujo completo de 6 pantallas en audio_quiz.html
- ✅ 9 audios de referencia con barra de progreso
- ✅ 18 audios del experimento con molestia + fuentes + 8 PAC
- ✅ Guardado CSV vía FS API con fallback a descarga
- ✅ CSV con 33 columnas incluyendo ref_28…ref_60
- ✅ analizar_resultados.py con estadísticas, gráficas, radar, cronología y maad
- ✅ Todos los textos centrados en la interfaz
- ✅ HTML sin duplicados

**Pendiente / posibles mejoras:**
- ⚠️ El `nextId` se incrementa por fila (18 IDs por participante), no por participante
- ⚠️ Los audios no están aleatorizados
- ⚠️ La función `proceedToAudioQuiz()` en quiz_audio.js es código legacy que ya no se usa (el flujo usa `nextRefAudio`) — puede eliminarse sin problema
- ⚠️ `appendNewResponses()` también es código legacy (ya no se llama desde ningún sitio)
- ℹ️ mensaje3_*.wav existen en disco pero no se usan en el cuestionario
