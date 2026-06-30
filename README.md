# Paisajes Sonoros — Test de escucha (TFG)

Aplicación **web** y de **escritorio** del test de escucha de *Paisajes Sonoros*,
desarrollada para el Trabajo de Fin de Grado de **Mario Hiniesto Íñigo**
(Universidad Rey Juan Carlos, URJC — 2026).

La herramienta presenta a cada participante una serie de audios (mensajes de
megafonía PA/VA mezclados con distintos ruidos de fondo) y recoge sus
valoraciones de molestia, identificación de fuentes sonoras (PSS) y percepción
afectiva según el modelo circumplejo de la ISO 12913 (atributos **PAQ**). Los
resultados se exportan en formato CSV para su análisis posterior.


## Cómo ejecutar

### Versión web

Requiere un servidor local (los navegadores bloquean la carga de audio desde
`file://`):

```bash
python -m http.server 8080
# y abrir http://localhost:8080/audio_quiz.html
```

### Versión de escritorio (Electron)

```bash
npm install
npm start
```

## Estructura del proyecto

```
audio_quiz.html        Cuestionario principal (SPA)
script/                Lógica del cuestionario (quiz_demographic.js, quiz_audio.js, filesystem.js)
styles/                Hojas de estilo
resources/             Audios (experimento, referencia y ejemplos) e imágenes
electron/              Punto de entrada de la app de escritorio
CSV/                   Resultados y análisis
```

## Origen

Este repositorio es un *fork* del proyecto de evaluación perceptual de paisajes
sonoros de **Manuel Salcedo** (TFG previo en la misma facultad). A partir de su
código, realicé las modificaciones y ampliaciones necesarias para este trabajo.

## Autoría

**Mario Hiniesto Íñigo** — Trabajo de Fin de Grado, URJC, 2026.
