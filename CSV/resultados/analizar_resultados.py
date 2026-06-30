# -*- coding: utf-8 -*-
"""
analizar_resultados.py
======================
Analisis perceptual-acustico del cuestionario de Paisajes Sonoros (TFG URJC).

Metodologia:
  * Modelo circumplejo ISO 12913-2/3 calculado con la libreria **Soundscapy**
    (coordenadas ISOPleasant / ISOEventful a partir de los 8 atributos PAQ).
  * Calibracion acustica: se mide el nivel equivalente A-ponderado (LAeq)
    digital de cada WAV y se calibra contra los audios de referencia, cuyo
    nivel de presion sonora nominal es conocido (52, 56, 60, 64, 68 dB).
  * **Penalizacion de molestia (metodo de Hongisto / Oliva et al.)**: se
    ajusta la recta dosis-respuesta molestia(LAeq) de los audios de referencia
    y, para cada sonido experimental, la penalizacion k [dB] es la diferencia
    entre su LAeq real y el LAeq aparente de un audio de referencia que
    resultaria igual de molesto.
        k = LAeq_aparente(molestia) - LAeq_real
  * Estadistica: descriptivos, ANOVA de medidas repetidas no parametrico
    (Friedman) + comparaciones por pares (Wilcoxon, Bonferroni), correlaciones
    de Pearson, y relacion penalizacion vs. centroide espectral (Hongisto).

Genera todas las graficas PNG en CSV/resultados/ y un informe PDF completo.

Requiere:
    pip install pandas numpy matplotlib scipy soundscapy soundfile reportlab

Uso:
    python analizar_resultados.py
    python analizar_resultados.py CSV/resultados/paisajes_sonoros.csv \
        --audio-dir resources/audios --ref-dir resources/ref
"""

import sys
import argparse
import warnings
from io import StringIO
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import stats as scipy_stats
from scipy.signal import bilinear, lfilter

warnings.filterwarnings('ignore')

# ── Soundscapy (modelo circumplejo ISO 12913) ──────────────────────────────
try:
    from soundscapy import surveys as sspy_surveys
    from soundscapy import plotting as sspy_plotting
    SOUNDSCAPY_AVAILABLE = True
except Exception as _e:                                       # pragma: no cover
    SOUNDSCAPY_AVAILABLE = False
    print(f'[AVISO] Soundscapy no disponible ({_e}). Se omiten graficas ISO.')

# ── soundfile (lectura WAV multicanal) ─────────────────────────────────────
try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except Exception:                                            # pragma: no cover
    SOUNDFILE_AVAILABLE = False

# ── reportlab (informe PDF) ────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                    TableStyle, Image as RLImage, PageBreak)
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except Exception:                                            # pragma: no cover
    REPORTLAB_AVAILABLE = False

# ── Paleta de colores ──────────────────────────────────────────────────────
COLOR_ROAD   = '#e74c3c'
COLOR_VOICES = '#3498db'
COLOR_NATURE = '#2ecc71'
COLOR_LOW    = '#27ae60'
COLOR_EQUAL  = '#f39c12'
COLOR_HIGH   = '#c0392b'
COLOR_REF    = '#f39c12'
COLOR_EXP    = '#8e44ad'
COLORS_AFECT = ['#9b59b6', '#e67e22', '#1abc9c', '#95a5a6',
                '#34495e', '#e74c3c', '#3498db', '#7f8c8d']

RUIDO_LABEL = {'road': 'Tráfico', 'voices': 'Voces', 'nature': 'Naturaleza'}
RUIDO_COLOR = {'road': COLOR_ROAD, 'voices': COLOR_VOICES, 'nature': COLOR_NATURE}
RUIDOS      = ['road', 'voices', 'nature']
NIVEL_ORDER = ['low', 'equal', 'high']
NIVEL_LABEL = {'low': 'Low (+8 dB SNR)', 'equal': 'Equal (0 dB SNR)',
               'high': 'High (-8 dB SNR)'}
NIVEL_COLOR = {'low': COLOR_LOW, 'equal': COLOR_EQUAL, 'high': COLOR_HIGH}

# --- Niveles SPL del diseno experimental (calibrados en dBZ, sin ponderar) --
# El mensaje de evacuacion esta SIEMPRE a 60 dB; lo que varia es el nivel del
# ruido de fondo (52 / 60 / 68 dB). El nivel total (suma logaritmica) es:
#   10*log10(10^(60/10) + 10^(ruido/10))  ->  60.63 / 63.00 / 68.63 dBZ.
# Estos valores son dBZ (sin ponderar). El analisis de Hongisto trabaja en LAeq
# (dBA): cada nivel se convierte a dBA sumando la correccion A medida del WAV
# (ver aweight_offset). Las referencias (ruido grave) tienen una correccion de
# ~ -28 dB; los audios experimentales (banda ancha + voz) de ~ +1 dB.
NOISE_BY_NIVEL  = {'low': 52.0, 'equal': 60.0, 'high': 68.0}
LAEQ_BY_NIVEL   = {'low': 60.63, 'equal': 63.00, 'high': 68.63}  # dBZ total
MENSAJE_SPL = 60.0

# Mapeo PAQ (ISO 12913) -> columnas del cuestionario.
# Orden PAQ: 1 pleasant, 2 vibrant, 3 eventful, 4 chaotic,
#            5 annoying, 6 monotonous, 7 uneventful, 8 calm
PAQ_MAP = {
    'PAQ1': 'afectiva_agradable',     # pleasant
    'PAQ2': 'afectiva_estimulante',   # vibrant
    'PAQ3': 'afectiva_conactividad',  # eventful
    'PAQ4': 'afectiva_caotico',       # chaotic
    'PAQ5': 'afectiva_molesto',       # annoying
    'PAQ6': 'afectiva_monotono',      # monotonous
    'PAQ7': 'afectiva_sinactividad',  # uneventful
    'PAQ8': 'afectiva_calmado',       # calm
}

AFECTIVAS = ['afectiva_agradable', 'afectiva_caotico', 'afectiva_estimulante',
             'afectiva_sinactividad', 'afectiva_calmado', 'afectiva_molesto',
             'afectiva_conactividad', 'afectiva_monotono']
NOMBRES_AFECT = ['Agradable', 'Caótico', 'Estimulante', 'Sin actividad',
                 'Calmado', 'Molesto', 'Con actividad', 'Monótono']


# =============================================================================
# Utilidades acusticas
# =============================================================================
def a_weighting_coeffs(fs):
    """Coeficientes del filtro de ponderacion A (IEC 61672) por bilineal."""
    f1, f2, f3, f4 = 20.598997, 107.65265, 737.86223, 12194.217
    A1000 = 1.9997
    num = [(2 * np.pi * f4) ** 2 * (10 ** (A1000 / 20.0)), 0, 0, 0, 0]
    den = np.polymul([1, 4 * np.pi * f4, (2 * np.pi * f4) ** 2],
                     [1, 4 * np.pi * f1, (2 * np.pi * f1) ** 2])
    den = np.polymul(np.polymul(den, [1, 2 * np.pi * f3]), [1, 2 * np.pi * f2])
    return bilinear(num, den, fs)


def laeq_digital(path):
    """LAeq digital [dB rel. fondo de escala] de un WAV (media de canales)."""
    x, fs = sf.read(str(path))
    b, a = a_weighting_coeffs(fs)
    if x.ndim > 1:
        powers = []
        for ch in range(x.shape[1]):
            y = lfilter(b, a, x[:, ch])
            powers.append(np.mean(y ** 2))
        p = np.mean(powers)
    else:
        y = lfilter(b, a, x)
        p = np.mean(y ** 2)
    return 10.0 * np.log10(p + 1e-20)


def spectral_centroid(path):
    """Centroide espectral [Hz] (media de canales, ventana Hann)."""
    x, fs = sf.read(str(path))
    if x.ndim > 1:
        x = x.mean(axis=1)
    w = np.hanning(len(x))
    X = np.abs(np.fft.rfft(x * w)) ** 2
    f = np.fft.rfftfreq(len(x), 1.0 / fs)
    s = np.sum(X)
    return float(np.sum(f * X) / s) if s > 0 else np.nan


def aweight_offset(path):
    """Correccion de ponderacion A de un WAV: LAeq - LZeq [dB].

    Es la diferencia entre el nivel A-ponderado y el sin ponderar (Z) de la
    misma senal. Depende solo del ESPECTRO (no de la ganancia de reproduccion),
    por lo que se mide de forma fiable del archivo. Permite convertir niveles
    calibrados en dBZ a dBA (LAeq), como requiere el metodo de Hongisto.
    """
    x, fs = sf.read(str(path))
    b, a = a_weighting_coeffs(fs)
    if x.ndim > 1:
        pz = np.mean([np.mean(x[:, c] ** 2) for c in range(x.shape[1])])
        pa = np.mean([np.mean(lfilter(b, a, x[:, c]) ** 2) for c in range(x.shape[1])])
    else:
        pz = np.mean(x ** 2)
        pa = np.mean(lfilter(b, a, x) ** 2)
    return 10.0 * np.log10((pa + 1e-20) / (pz + 1e-20))


# =============================================================================
class Analyzer:
# =============================================================================

    def __init__(self, csv_path, audio_dir=None, ref_dir=None,
                 output_dir=None, weighting='dba', drop_ref=None):
        self.csv_path = Path(csv_path)
        self.audio_dir = Path(audio_dir) if audio_dir else None
        self.ref_dir = Path(ref_dir) if ref_dir else None
        self.output_dir = Path(output_dir) if output_dir else self.csv_path.parent
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Ponderacion del eje de niveles: 'dba' aplica la correccion A medida
        # de cada WAV (LAeq, metodo de Hongisto); 'dbz' deja los niveles de
        # calibracion sin ponderar (sin correccion).
        self.weighting = weighting.lower()
        self.unit = 'dBA' if self.weighting == 'dba' else 'dBZ'

        # Niveles de referencia descartados (problemas de escucha en el test).
        self.drop_ref = list(drop_ref) if drop_ref else []

        self.df = pd.read_csv(self.csv_path)
        self.df['molestia'] = pd.to_numeric(self.df['molestia'], errors='coerce')

        # Columnas de referencia ref_NN -> niveles dB (excluyendo descartados)
        self.ref_cols = sorted(
            [c for c in self.df.columns if c.startswith('ref_')
             and int(c.replace('ref_', '')) not in self.drop_ref],
            key=lambda c: int(c.replace('ref_', '')))
        self.ref_niveles = [int(c.replace('ref_', '')) for c in self.ref_cols]
        if self.drop_ref:
            print(f'[INFO] Referencias descartadas: '
                  f'{", ".join(str(d) for d in self.drop_ref)} dB. '
                  f'Se usan: {", ".join(str(n) for n in self.ref_niveles)} dB.')
        for col in self.ref_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        for col in AFECTIVAS:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        self.id_col = 'participante_id' if 'participante_id' in self.df.columns \
                      else 'timestamp_inicio'
        self.df_part = self.df.drop_duplicates(self.id_col).copy()

        # Coordenadas ISO (modelo circumplejo) con Soundscapy
        self._add_iso_coords()

        # Resultados que alimentan el PDF
        self.results = {}

    # ── helpers ────────────────────────────────────────────────────────────
    def _n_part(self):
        return self.df[self.id_col].nunique()

    def _save(self, fig, name):
        p = self.output_dir / name
        fig.savefig(p, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f'  Guardado: {p}')
        return p

    def _add_iso_coords(self):
        """Calcula ISOPleasant / ISOEventful con Soundscapy (ISO 12913)."""
        if not SOUNDSCAPY_AVAILABLE:
            self.df['ISOPleasant'] = np.nan
            self.df['ISOEventful'] = np.nan
            return
        tmp = self.df.copy()
        for paq, col in PAQ_MAP.items():
            tmp[paq] = self.df[col]
        out = sspy_surveys.add_iso_coords(tmp, val_range=(1, 5), overwrite=True)
        self.df['ISOPleasant'] = out['ISOPleasant'].values
        self.df['ISOEventful'] = out['ISOEventful'].values

    # =========================================================================
    # 1. CALIBRACION ACUSTICA + LAeq DE LOS AUDIOS EXPERIMENTALES
    # =========================================================================
    def calibrar_acustica(self):
        """Convierte los niveles de diseno (dBZ) a LAeq (dBA) y mide el centroide.

        Los niveles se calibraron en dBZ (sin ponderar). El metodo de Hongisto
        opera en LAeq (dBA), asi que cada nivel se convierte a dBA sumando la
        correccion de ponderacion A (LAeq-LZeq) medida directamente de cada
        senal (independiente de la ganancia de reproduccion):
          * referencias (ruido grave):     correccion ~ -28 dB
          * experimentales (banda ancha):  correccion ~ +1 dB
        El centroide espectral tambien se mide del WAV.
        """
        print('\n' + '=' * 64)
        if self.weighting == 'dba':
            print('NIVELES ACUSTICOS: CONVERSION dBZ -> LAeq (dBA) Y CENTROIDE')
        else:
            print('NIVELES ACUSTICOS: SIN CORRECCION (dBZ) Y CENTROIDE')
        print('=' * 64)
        self.laeq_exp = None
        self.calib = None
        self.ref_offset = 0.0
        self.ref_niveles_dba = list(self.ref_niveles)

        # 1) Correccion A de las referencias (solo en modo dBA)
        ref_offs = []
        if self.weighting == 'dba' and SOUNDFILE_AVAILABLE and self.ref_dir is not None:
            for nv in self.ref_niveles:
                f = self.ref_dir / f'ref_{nv}.wav'
                if f.exists():
                    try:
                        ref_offs.append(aweight_offset(f))
                    except Exception as e:
                        print(f'    [ref offset] ref_{nv}: {e}')
        if ref_offs:
            self.ref_offset = float(np.mean(ref_offs))
            self.ref_niveles_dba = [n + self.ref_offset for n in self.ref_niveles]
            print(f'  Correccion A referencias: {self.ref_offset:+.2f} dB '
                  f'(dBZ {self.ref_niveles[0]}-{self.ref_niveles[-1]} '
                  f'-> dBA {self.ref_niveles_dba[0]:.1f}-{self.ref_niveles_dba[-1]:.1f})')
        elif self.weighting == 'dbz':
            print(f'  Modo sin correccion: niveles de referencia en dBZ '
                  f'({self.ref_niveles[0]}-{self.ref_niveles[-1]}).')
        else:
            print('  [AVISO] No se pudieron medir las referencias; se asume dBZ=dBA.')

        # 2) Nivel y centroide de cada audio experimental
        exp_rows = []
        for fname in sorted(self.df['audio_filename'].dropna().unique()):
            parts = fname.replace('_hrtf.wav', '').split('_')
            if len(parts) < 3:
                continue
            mensaje, ruido, nivel = parts[0], parts[1], parts[2]
            laeq_dbz = LAEQ_BY_NIVEL.get(nivel, np.nan)
            centro = np.nan
            offset = np.nan
            if (SOUNDFILE_AVAILABLE and self.audio_dir is not None
                    and (self.audio_dir / fname).exists()):
                try:
                    centro = spectral_centroid(self.audio_dir / fname)
                    offset = aweight_offset(self.audio_dir / fname)
                except Exception as e:
                    print(f'    [audio] {fname}: {e}')
            # En modo dBZ no se aplica la correccion A al nivel experimental
            applied = (offset if (self.weighting == 'dba'
                                  and not np.isnan(offset)) else 0.0)
            laeq_final = laeq_dbz + applied
            exp_rows.append({
                'audio_filename': fname,
                'mensaje': mensaje, 'ruido': ruido, 'nivel': nivel,
                'noise_db': NOISE_BY_NIVEL.get(nivel, np.nan),
                'laeq_dbz': laeq_dbz, 'aweight_offset': offset,
                'laeq_db': laeq_final, 'centroide_hz': centro})
        if not exp_rows:
            print('  [SKIP] No hay audios en el CSV.')
            return
        self.laeq_exp = pd.DataFrame(exp_rows)

        if self.weighting == 'dba':
            print('\n  Mensaje fijo 60 dB + ruido 52/60/68 dB (suma log.) -> dBZ total;'
                  ' conversion a LAeq (dBA):')
            for nv in NIVEL_ORDER:
                sub = self.laeq_exp[self.laeq_exp['nivel'] == nv]
                print(f'    {nv:<6}: {LAEQ_BY_NIVEL[nv]:.2f} dBZ  ->  '
                      f'{sub["laeq_db"].mean():.2f} dBA  '
                      f'(corr A {sub["aweight_offset"].mean():+.2f})')
        else:
            print('\n  Niveles experimentales (dBZ, sin correccion):')
            for nv in NIVEL_ORDER:
                print(f'    {nv:<6}: {LAEQ_BY_NIVEL[nv]:.2f} dBZ')
        if self.laeq_exp['centroide_hz'].notna().any():
            print('\n  Centroide espectral medio por ruido [Hz]:')
            for ru in RUIDOS:
                c = self.laeq_exp[self.laeq_exp['ruido'] == ru]['centroide_hz'].mean()
                print(f'    {RUIDO_LABEL[ru]:<12}: {c:.0f} Hz')
        self.results['laeq_by_nivel'] = LAEQ_BY_NIVEL
        self.results['ref_offset'] = self.ref_offset
        self.results['exp_offset'] = self.laeq_exp['aweight_offset'].mean()

    # =========================================================================
    # 2. PENALIZACION DE MOLESTIA (metodo de Hongisto / Oliva)
    # =========================================================================
    def penalizacion_hongisto(self):
        print('\n' + '=' * 64)
        print('PENALIZACION DE MOLESTIA (metodo Hongisto / Oliva et al.)')
        print('=' * 64)
        self.penalty = None
        self.ref_reg = None
        if self.laeq_exp is None:
            print('  [SKIP] Se requiere calibracion acustica previa.')
            return

        # Recta de referencia dosis-respuesta: molestia = a + b * LAeq(dBA).
        # Los niveles de referencia se expresan en dBA (correccion A aplicada).
        niveles_ref = self.ref_niveles_dba
        ref_means = [self.df_part[c].mean() for c in self.ref_cols]
        b, a, r, p, se = scipy_stats.linregress(niveles_ref, ref_means)
        if abs(b) < 1e-6:
            print('  [SKIP] Pendiente de referencia ~0; penalizacion indefinida.')
            return
        self.ref_reg = {'a': a, 'b': b, 'r2': r ** 2, 'p': p,
                        'means': ref_means, 'niveles': niveles_ref}
        print(f'  Niveles referencia en {self.unit}: '
              f'{", ".join(f"{x:.1f}" for x in niveles_ref)}')
        print(f'  Recta de referencia: molestia = {a:.3f} + {b:.4f} * Nivel({self.unit})'
              f'   (R2={r**2:.3f}, p={p:.4g})')
        print(f'  -> LAeq_aparente(molestia) = (molestia - {a:.3f}) / {b:.4f}')

        # LAeq real por (ruido, nivel) y por audio
        laeq_by_cond = self.laeq_exp.groupby(['ruido', 'nivel'])['laeq_db'].mean()
        laeq_by_audio = self.laeq_exp.set_index('audio_filename')['laeq_db']

        # Penalizacion por participante para cada condicion ruido x nivel
        rows = []
        for ruido in RUIDOS:
            for nivel in NIVEL_ORDER:
                laeq_real = laeq_by_cond.get((ruido, nivel), np.nan)
                if np.isnan(laeq_real):
                    continue
                sub = self.df[(self.df['ruido'] == ruido) &
                              (self.df['nivel'] == nivel)]
                # molestia media por participante en esta condicion
                mp = sub.groupby(self.id_col)['molestia'].mean().dropna()
                apparent = (mp - a) / b
                pen = apparent - laeq_real
                n = len(pen)
                mean_pen = pen.mean()
                sd_pen = pen.std(ddof=1) if n > 1 else 0.0
                ci = (scipy_stats.t.ppf(0.975, n - 1) * sd_pen / np.sqrt(n)
                      if n > 1 else 0.0)
                rows.append({
                    'ruido': ruido, 'nivel': nivel,
                    'laeq_real': laeq_real,
                    'molestia_media': sub['molestia'].mean(),
                    'penalty_mean': mean_pen, 'penalty_sd': sd_pen,
                    'penalty_ci95': ci, 'n': n})
        self.penalty = pd.DataFrame(rows)

        # Penalizacion por audio individual (18)
        arows = []
        for fname, laeq_real in laeq_by_audio.items():
            sub = self.df[self.df['audio_filename'] == fname]
            mp = sub.groupby(self.id_col)['molestia'].mean().dropna()
            apparent = (mp - a) / b
            pen = apparent - laeq_real
            n = len(pen)
            arows.append({
                'audio_filename': fname,
                'ruido': sub['ruido'].iloc[0], 'nivel': sub['nivel'].iloc[0],
                'laeq_real': laeq_real,
                'centroide_hz': self.laeq_exp.set_index('audio_filename')
                                    .loc[fname, 'centroide_hz'],
                'molestia_media': sub['molestia'].mean(),
                'penalty_mean': pen.mean(),
                'penalty_sd': pen.std(ddof=1) if n > 1 else 0.0})
        self.penalty_audio = pd.DataFrame(arows)

        print('\n  Penalizacion media por condicion [dB]:')
        show = self.penalty.copy()
        show['cond'] = show['ruido'].map(RUIDO_LABEL) + ' / ' + show['nivel']
        print(show[['cond', 'laeq_real', 'molestia_media',
                    'penalty_mean', 'penalty_ci95']].round(2).to_string(index=False))

        # Penalizacion media por tipo de ruido (promedio de niveles)
        pen_ruido = self.penalty.groupby('ruido')['penalty_mean'].mean()
        print('\n  Penalizacion media por tipo de ruido [dB]:')
        for ru in RUIDOS:
            if ru in pen_ruido:
                print(f'    {RUIDO_LABEL[ru]:<12}: {pen_ruido[ru]:+.2f} dB')
        self.results['pen_ruido'] = pen_ruido

    # =========================================================================
    # 3. INFORMES DE TEXTO
    # =========================================================================
    def info_general(self):
        n = self._n_part()
        denom = n or 1
        print('=' * 64)
        print('INFORME GENERAL')
        print('=' * 64)
        print(f'Participantes:           {n}')
        print(f'Total respuestas:        {len(self.df)}')
        print(f'Respuestas/participante: {len(self.df)/denom:.1f}')
        print('\n--- Demografia ---')
        demo = {}
        for col, label in [('edad', 'Edad'), ('genero', 'Genero'),
                           ('estudios', 'Estudios'), ('audicion', 'Problemas audicion'),
                           ('castellano', 'Castellano L1')]:
            if col in self.df_part.columns:
                vc = self.df_part[col].value_counts()
                demo[label] = vc
                print(f'\n{label}:')
                print(vc.to_string())
        self.results['demografia'] = demo

    def estadisticas_molestia(self):
        print('\n' + '=' * 64)
        print('ESTADISTICAS DE MOLESTIA (0-10)')
        print('=' * 64)
        print('\n[Audios de referencia - media por nivel dB]')
        for col, nivel in zip(self.ref_cols, self.ref_niveles):
            vals = self.df_part[col].dropna()
            if len(vals):
                print(f'  {nivel} dB: media={vals.mean():.2f}  std={vals.std():.2f}'
                      f'  [{vals.min():.0f}-{vals.max():.0f}]')
        print('\n[Audios del experimento]')
        print(self.df['molestia'].describe().round(2).to_string())
        for label, col in [('ruido', 'ruido'), ('nivel', 'nivel'),
                           ('mensaje', 'mensaje')]:
            print(f'\n--- Molestia por {label} ---')
            print(self.df.groupby(col)['molestia']
                  .agg(['mean', 'std', 'min', 'max']).round(2).to_string())
        print('\n--- Molestia por ruido x nivel ---')
        tab = self.df.groupby(['ruido', 'nivel'])['molestia'].agg(['mean', 'std'])
        print(tab.round(2).to_string())
        self.results['molestia_cond'] = (
            self.df.groupby(['ruido', 'nivel'])['molestia'].mean()
            .unstack().reindex(index=RUIDOS, columns=NIVEL_ORDER))

    def estadisticas_inferenciales(self):
        """Friedman (medidas repetidas no parametrico) + Wilcoxon por pares."""
        print('\n' + '=' * 64)
        print('ESTADISTICA INFERENCIAL (molestia)')
        print('=' * 64)
        inf = {}

        def friedman_factor(factor, niveles):
            # matriz participante x nivel (molestia media)
            piv = (self.df.groupby([self.id_col, factor])['molestia'].mean()
                   .unstack().reindex(columns=niveles).dropna())
            if piv.shape[0] < 3 or piv.shape[1] < 3:
                return None
            chi2, pv = scipy_stats.friedmanchisquare(*[piv[c] for c in niveles])
            pairs = []
            for i in range(len(niveles)):
                for j in range(i + 1, len(niveles)):
                    w, pw = scipy_stats.wilcoxon(piv[niveles[i]], piv[niveles[j]])
                    pairs.append((niveles[i], niveles[j], pw,
                                  pw * 3))  # Bonferroni (3 comparaciones)
            return {'chi2': chi2, 'p': pv, 'n': piv.shape[0], 'pairs': pairs,
                    'medias': piv.mean()}

        for factor, niveles, lab in [('ruido', RUIDOS, 'TIPO DE RUIDO'),
                                     ('nivel', NIVEL_ORDER, 'NIVEL (SNR)')]:
            res = friedman_factor(factor, niveles)
            print(f'\n--- Efecto de {lab} (Friedman, medidas repetidas) ---')
            if res is None:
                print('  [N insuficiente]')
                continue
            sig = 'SIGNIFICATIVO' if res['p'] < 0.05 else 'no significativo'
            print(f'  chi2={res["chi2"]:.3f}, p={res["p"]:.4g}, '
                  f'N={res["n"]}  -> {sig}')
            print('  Comparaciones por pares (Wilcoxon, p Bonferroni):')
            for a_, b_, pw, pb in res['pairs']:
                mark = '*' if pb < 0.05 else ' '
                print(f'    {a_:>6} vs {b_:<6}: p={pw:.4g} (corr={min(pb,1):.4g}) {mark}')
            inf[factor] = res
        self.results['inferencial'] = inf

    def estadisticas_iso(self):
        print('\n' + '=' * 64)
        print('MODELO CIRCUMPLEJO ISO 12913 (Soundscapy)')
        print('=' * 64)
        if not SOUNDSCAPY_AVAILABLE:
            print('  [SKIP] Soundscapy no disponible.')
            return
        print('\nCoordenadas ISO medias por tipo de ruido:')
        g = self.df.groupby('ruido')[['ISOPleasant', 'ISOEventful']].agg(['mean', 'std'])
        print(g.round(3).to_string())
        print('\nCoordenadas ISO medias por nivel:')
        g2 = self.df.groupby('nivel')[['ISOPleasant', 'ISOEventful']].agg(['mean', 'std'])
        print(g2.round(3).to_string())
        self.results['iso_ruido'] = self.df.groupby('ruido')[
            ['ISOPleasant', 'ISOEventful']].mean().reindex(RUIDOS)
        self.results['iso_nivel'] = self.df.groupby('nivel')[
            ['ISOPleasant', 'ISOEventful']].mean().reindex(NIVEL_ORDER)

    def estadisticas_afectivas(self):
        print('\n' + '=' * 64)
        print('PERCEPCION AFECTIVA (8 atributos PAQ, escala 1-5)')
        print('=' * 64)
        for af, nom in zip(AFECTIVAS, NOMBRES_AFECT):
            s = self.df[af].describe()
            print(f'  {nom:<15}: media={s["mean"]:.2f}  std={s["std"]:.2f}')
        self.results['afect_global'] = self.df[AFECTIVAS].mean()

    def estadisticas_fuentes(self):
        print('\n' + '=' * 64)
        print('FUENTES SONORAS DETECTADAS')
        print('=' * 64)
        todas = []
        for f in self.df['fuentes']:
            if pd.notna(f):
                todas.extend([x.strip().strip('"') for x in str(f).split(';') if x.strip()])
        conteo = Counter(todas)
        n = len(self.df)
        fuentes = {}
        for fuente, count in conteo.most_common():
            print(f'  {fuente:<12}: {count:>4}  ({count/n*100:.1f}%)')
            fuentes[fuente] = count
        self.results['fuentes'] = fuentes

    def correlaciones(self):
        print('\n' + '=' * 64)
        print('CORRELACIONES CLAVE')
        print('=' * 64)
        corr = {}
        # molestia vs ISOPleasant (a nivel de respuesta)
        d = self.df[['molestia', 'ISOPleasant', 'ISOEventful']].dropna()
        if len(d) > 3:
            r, p = scipy_stats.pearsonr(d['molestia'], d['ISOPleasant'])
            print(f'  Molestia vs ISOPleasant: r={r:.3f}, p={p:.4g}')
            corr['molestia_isopleasant'] = (r, p)
            r2, p2 = scipy_stats.pearsonr(d['molestia'], d['ISOEventful'])
            print(f'  Molestia vs ISOEventful: r={r2:.3f}, p={p2:.4g}')
            corr['molestia_isoeventful'] = (r2, p2)
        # penalizacion vs centroide espectral (Hongisto)
        if getattr(self, 'penalty_audio', None) is not None:
            d2 = self.penalty_audio[['penalty_mean', 'centroide_hz']].dropna()
            if len(d2) > 3 and d2['centroide_hz'].nunique() > 1:
                r, p = scipy_stats.pearsonr(d2['centroide_hz'], d2['penalty_mean'])
                print(f'  Penalizacion vs centroide espectral: r={r:.3f}, p={p:.4g}')
                corr['penalty_centroide'] = (r, p)
            d3 = self.penalty_audio[['molestia_media', 'centroide_hz']].dropna()
            if len(d3) > 3 and d3['centroide_hz'].nunique() > 1:
                r, p = scipy_stats.pearsonr(d3['centroide_hz'], d3['molestia_media'])
                print(f'  Molestia vs centroide espectral:      r={r:.3f}, p={p:.4g}')
                corr['molestia_centroide'] = (r, p)
        self.results['correlaciones'] = corr

    # =========================================================================
    # 4. GRAFICAS
    # =========================================================================
    def _jointplot(self, d, hue_col, order, palette, title, fname):
        """Jointplot de Soundscapy: densidad circumpleja + KDE marginales."""
        dd = d.dropna(subset=['ISOPleasant', 'ISOEventful', hue_col]).copy()
        dd[hue_col] = pd.Categorical(dd[hue_col], categories=order, ordered=True)
        try:
            g = sspy_plotting.jointplot(
                dd, hue=hue_col, title=title, palette=palette,
                marginal_kind='kde', legend=True, incl_scatter=True,
                fill=True, alpha=0.55,
                scatter_kws={'s': 18, 'linewidth': 0, 'alpha': 0.5},
                diagonal_lines=False)
            g.savefig(self.output_dir / fname, dpi=150, bbox_inches='tight')
            plt.close(g.figure)
            print(f'  Guardado: {self.output_dir / fname}')
        except Exception as e:
            print(f'  [jointplot {fname}] {e}')

    def grafico_circumplejo(self):
        if not SOUNDSCAPY_AVAILABLE:
            return
        d = self.df.dropna(subset=['ISOPleasant', 'ISOEventful']).copy()
        d['Ruido'] = d['ruido'].map(RUIDO_LABEL)
        d['Nivel'] = d['nivel'].map({'low': 'Low', 'equal': 'Equal', 'high': 'High'})

        # Jointplot por tipo de ruido (densidad ISO + distribuciones marginales)
        self._jointplot(
            d, 'Ruido', [RUIDO_LABEL[r] for r in RUIDOS],
            [COLOR_ROAD, COLOR_VOICES, COLOR_NATURE],
            'Percepción del paisaje sonoro por tipo de ruido (ISO 12913)',
            'iso_jointplot_ruido.png')

        # Jointplot por nivel sonoro (estilo "perception as a function of level")
        self._jointplot(
            d, 'Nivel', ['Low', 'Equal', 'High'],
            [COLOR_LOW, COLOR_EQUAL, COLOR_HIGH],
            'Percepción del paisaje sonoro según el nivel',
            'iso_jointplot_nivel.png')

        # Medias por condicion sobre el plano ISO
        fig, ax = plt.subplots(figsize=(7.5, 7.5))
        ax.axhline(0, color='gray', lw=0.8); ax.axvline(0, color='gray', lw=0.8)
        ax.add_patch(plt.Circle((0, 0), 1, fill=False, color='gray', lw=0.8, ls='--'))
        for ruido in RUIDOS:
            for nivel in NIVEL_ORDER:
                sub = d[(d['ruido'] == ruido) & (d['nivel'] == nivel)]
                if sub.empty:
                    continue
                x, y = sub['ISOPleasant'].mean(), sub['ISOEventful'].mean()
                marker = {'low': 'v', 'equal': 'o', 'high': '^'}[nivel]
                ax.scatter(x, y, s=160, color=RUIDO_COLOR[ruido], marker=marker,
                           edgecolor='black', zorder=3)
        ax.set_xlim(-1, 1); ax.set_ylim(-1, 1)
        ax.set_xlabel('ISOPleasant  (agradable +)', fontsize=11)
        ax.set_ylabel('ISOEventful  (dinámico +)', fontsize=11)
        ax.set_title('Posición media por condición (ruido x nivel)\n'
                     'color = ruido | marcador: v=low o=equal ^=high', fontsize=11)
        from matplotlib.lines import Line2D
        leg = [Line2D([0], [0], marker='o', color='w', markerfacecolor=RUIDO_COLOR[r],
                      markersize=11, label=RUIDO_LABEL[r]) for r in RUIDOS]
        ax.legend(handles=leg, loc='lower left', fontsize=9)
        ax.set_aspect('equal')
        plt.tight_layout()
        self._save(fig, 'iso_medias_condicion.png')

    def grafico_molestia(self):
        ref_mean = np.mean(self.ref_reg['means']) if self.ref_reg else None
        fig, axes = plt.subplots(1, 3, figsize=(16, 5))
        specs = [
            ('ruido', RUIDOS, [RUIDO_LABEL[r] for r in RUIDOS],
             [RUIDO_COLOR[r] for r in RUIDOS], 'Molestia por tipo de ruido'),
            ('nivel', NIVEL_ORDER, [NIVEL_LABEL[n] for n in NIVEL_ORDER],
             [NIVEL_COLOR[n] for n in NIVEL_ORDER], 'Molestia por nivel (SNR)'),
        ]
        for ax, (col, order, labels, cols, title) in zip(axes, specs):
            d = self.df.groupby(col)['molestia'].mean().reindex(order)
            bars = ax.bar(labels, d.values, color=cols, edgecolor='white')
            if ref_mean is not None:
                ax.axhline(ref_mean, color=COLOR_REF, ls='--', lw=1.6,
                           label=f'Media ref: {ref_mean:.2f}')
                ax.legend(fontsize=8)
            ax.set_title(title); ax.set_ylabel('Molestia (0-10)')
            ax.set_ylim(0, 10.5); ax.grid(axis='y', alpha=0.3)
            ax.tick_params(axis='x', labelsize=8)
            for b, v in zip(bars, d.values):
                if not np.isnan(v):
                    ax.text(b.get_x() + b.get_width() / 2, v + 0.2, f'{v:.2f}',
                            ha='center', fontsize=9)
        # tercer panel: ruido x nivel
        ax = axes[2]
        piv = self.results['molestia_cond']
        x = np.arange(len(RUIDOS)); w = 0.25
        for i, nivel in enumerate(NIVEL_ORDER):
            ax.bar(x + (i - 1) * w, piv[nivel].values, w,
                   label=NIVEL_LABEL[nivel], color=NIVEL_COLOR[nivel],
                   edgecolor='white')
        ax.set_xticks(x); ax.set_xticklabels([RUIDO_LABEL[r] for r in RUIDOS])
        ax.set_title('Molestia: ruido x nivel'); ax.set_ylabel('Molestia (0-10)')
        ax.set_ylim(0, 10.5); ax.grid(axis='y', alpha=0.3); ax.legend(fontsize=7)
        fig.suptitle('Molestia media', fontsize=12)
        plt.tight_layout()
        self._save(fig, 'molestia_resumen.png')

    def grafico_curva_penalizacion(self):
        if self.ref_reg is None or self.penalty is None:
            return
        a, b = self.ref_reg['a'], self.ref_reg['b']
        niveles_ref = self.ref_reg['niveles']
        fig, ax = plt.subplots(figsize=(11, 7))
        # recta de referencia (eje en dBA)
        x_hi = max(max(niveles_ref), self.penalty['laeq_real'].max()) + 4
        xs = np.linspace(min(niveles_ref) - 2, x_hi, 100)
        ax.plot(xs, a + b * xs, color='#34495e', lw=2,
                label=f'Recta referencia: molestia={a:.2f}+{b:.3f}*LAeq (R2={self.ref_reg["r2"]:.2f})')
        ax.scatter(niveles_ref, self.ref_reg['means'], color='#34495e',
                   s=70, zorder=5, label=f'Audios referencia (media, {self.unit})')
        # puntos experimentales + flechas de penalizacion
        for _, row in self.penalty.iterrows():
            laeq_real = row['laeq_real']; mol = row['molestia_media']
            apparent = (mol - a) / b
            color = RUIDO_COLOR[row['ruido']]
            ax.scatter(laeq_real, mol, color=color, s=90,
                       marker={'low': 'v', 'equal': 'o', 'high': '^'}[row['nivel']],
                       edgecolor='black', zorder=6)
            ax.annotate('', xy=(apparent, mol), xytext=(laeq_real, mol),
                        arrowprops=dict(arrowstyle='->', color=color, alpha=0.6, lw=1.3))
        ax.set_xlabel(f'Nivel [{self.unit}]', fontsize=11)
        ax.set_ylabel('Molestia (0-10)', fontsize=11)
        ax.set_title('Derivación de la penalización (método Hongisto/Oliva)\n'
                     'Penalización k = nivel aparente - nivel real (flecha horizontal)',
                     fontsize=12)
        ax.set_ylim(0, 10.5); ax.grid(alpha=0.3)
        from matplotlib.lines import Line2D
        leg = ax.get_legend_handles_labels()[0]
        leg += [Line2D([0], [0], marker='o', color='w', markerfacecolor=RUIDO_COLOR[r],
                       markersize=10, label=RUIDO_LABEL[r]) for r in RUIDOS]
        # Significado de cada marcador (tipo de nivel/SNR)
        nivel_marker = {'low': 'v', 'equal': 'o', 'high': '^'}
        nivel_leg_label = {'low': 'Low (SNR +8 dB)', 'equal': 'Equal (SNR 0 dB)',
                           'high': 'High (SNR -8 dB)'}
        leg += [Line2D([0], [0], marker=nivel_marker[nv], color='w',
                       markerfacecolor='gray', markeredgecolor='black',
                       markersize=10, label=nivel_leg_label[nv]) for nv in NIVEL_ORDER]
        ax.legend(handles=leg, fontsize=8, loc='upper left')
        plt.tight_layout()
        self._save(fig, 'penalizacion_curva.png')

    def grafico_penalizacion_barras(self):
        if self.penalty is None:
            return
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        # por condicion ruido x nivel
        ax = axes[0]
        x = np.arange(len(RUIDOS)); w = 0.25
        for i, nivel in enumerate(NIVEL_ORDER):
            sub = self.penalty[self.penalty['nivel'] == nivel].set_index('ruido')
            vals = [sub.loc[r, 'penalty_mean'] if r in sub.index else np.nan for r in RUIDOS]
            ax.bar(x + (i - 1) * w, vals, w,
                   label=NIVEL_LABEL[nivel], color=NIVEL_COLOR[nivel], edgecolor='white')
        ax.axhline(0, color='black', lw=0.8)
        ax.set_xticks(x); ax.set_xticklabels([RUIDO_LABEL[r] for r in RUIDOS])
        ax.set_ylabel('Penalización k [dB]')
        ax.set_title('Penalización por condición')
        ax.grid(axis='y', alpha=0.3); ax.legend(fontsize=8)
        # por tipo de ruido (promedio de niveles)
        ax = axes[1]
        pr = self.penalty.groupby('ruido')['penalty_mean'].mean().reindex(RUIDOS)
        bars = ax.bar([RUIDO_LABEL[r] for r in RUIDOS], pr.values,
                      color=[RUIDO_COLOR[r] for r in RUIDOS], edgecolor='white')
        ax.axhline(0, color='black', lw=0.8)
        ax.set_ylabel('Penalización k [dB]')
        ax.set_title('Penalización media por tipo de ruido')
        ax.grid(axis='y', alpha=0.3)
        for b_, v in zip(bars, pr.values):
            if not np.isnan(v):
                ax.text(b_.get_x() + b_.get_width() / 2,
                        v + (0.2 if v >= 0 else -0.5), f'{v:+.1f}',
                        ha='center', fontsize=10)
        fig.suptitle('Penalización de molestia (método Hongisto)', fontsize=13)
        plt.tight_layout()
        self._save(fig, 'penalizacion_barras.png')

    def grafico_penalizacion_centroide(self):
        if getattr(self, 'penalty_audio', None) is None:
            return
        d = self.penalty_audio.dropna(subset=['penalty_mean', 'centroide_hz'])
        if len(d) < 3:
            return
        fig, ax = plt.subplots(figsize=(9, 6))
        for ruido in RUIDOS:
            sub = d[d['ruido'] == ruido]
            ax.scatter(sub['centroide_hz'], sub['penalty_mean'],
                       color=RUIDO_COLOR[ruido], s=80, edgecolor='black',
                       label=RUIDO_LABEL[ruido], zorder=3)
        if d['centroide_hz'].nunique() > 1:
            m, c, r, p, _ = scipy_stats.linregress(d['centroide_hz'], d['penalty_mean'])
            xs = np.linspace(d['centroide_hz'].min(), d['centroide_hz'].max(), 50)
            ax.plot(xs, m * xs + c, 'r--', lw=1.6,
                    label=f'r={r:.2f}, p={p:.3g}')
        ax.set_xlabel('Centroide espectral [Hz]'); ax.set_ylabel('Penalización k [dB]')
        ax.set_title('Penalización vs centroide espectral (cf. Hongisto et al. 2024)')
        ax.grid(alpha=0.3); ax.legend(fontsize=9)
        plt.tight_layout()
        self._save(fig, 'penalizacion_vs_centroide.png')

    def grafico_heatmap(self):
        fig, ax = plt.subplots(figsize=(8, 5))
        pivot = self.results['molestia_cond']
        im = ax.imshow(pivot.values, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=10)
        ax.set_xticks(range(3)); ax.set_xticklabels([NIVEL_LABEL[n] for n in NIVEL_ORDER])
        ax.set_yticks(range(3)); ax.set_yticklabels([RUIDO_LABEL[r] for r in RUIDOS])
        ax.set_title('Mapa de calor: molestia media (ruido x nivel)')
        plt.colorbar(im, ax=ax, label='Molestia (0-10)')
        for i in range(3):
            for j in range(3):
                v = pivot.values[i, j]
                if not np.isnan(v):
                    ax.text(j, i, f'{v:.2f}', ha='center', va='center',
                            color='black', fontsize=11, fontweight='bold')
        plt.tight_layout()
        self._save(fig, 'heatmap_molestia.png')

    def grafico_radar_afectivas(self):
        # Orden circumplejo ISO 12913 (sentido antihorario desde 0 grados a la
        # derecha): eje horizontal Agradable (dcha) <-> Molesto (izq), eje
        # vertical Con actividad (arriba) <-> Sin actividad (abajo), y las
        # combinaciones en las diagonales.
        circ_cols = ['afectiva_agradable', 'afectiva_estimulante',
                     'afectiva_conactividad', 'afectiva_caotico',
                     'afectiva_molesto', 'afectiva_monotono',
                     'afectiva_sinactividad', 'afectiva_calmado']
        labels = ['Agradable', 'Estimulante', 'Con actividad', 'Caótico',
                  'Molesto', 'Monótono', 'Sin actividad', 'Calmado']
        N = len(labels)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles += angles[:1]
        fig, axes = plt.subplots(1, 2, figsize=(14, 7), subplot_kw=dict(polar=True))
        # global
        ax = axes[0]
        vals = [self.df[af].mean() for af in circ_cols]; vals += vals[:1]
        ax.plot(angles, vals, color=COLOR_EXP, lw=2)
        ax.fill(angles, vals, color=COLOR_EXP, alpha=0.25)
        ax.plot(angles, [3] * N + [3], color='gray', lw=0.8, ls='--', alpha=0.6)
        ax.set_theta_offset(0); ax.set_theta_direction(1)
        ax.set_xticks(angles[:-1]); ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylim(1, 5); ax.set_title('Percepción afectiva - media global', pad=15)
        # por ruido
        ax2 = axes[1]
        for ruido in RUIDOS:
            sub = self.df[self.df['ruido'] == ruido]
            v = [sub[af].mean() for af in circ_cols]; v += v[:1]
            ax2.plot(angles, v, color=RUIDO_COLOR[ruido], lw=2, label=RUIDO_LABEL[ruido])
            ax2.fill(angles, v, color=RUIDO_COLOR[ruido], alpha=0.10)
        ax2.plot(angles, [3] * N + [3], color='gray', lw=0.8, ls='--', alpha=0.6)
        ax2.set_theta_offset(0); ax2.set_theta_direction(1)
        ax2.set_xticks(angles[:-1]); ax2.set_xticklabels(labels, fontsize=9)
        ax2.set_ylim(1, 5); ax2.set_title('Percepción afectiva - por ruido', pad=15)
        ax2.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)
        plt.tight_layout()
        self._save(fig, 'radar_afectivas.png')

    def grafico_afectivas(self):
        fig, ax = plt.subplots(figsize=(12, 5))
        medias = self.df[AFECTIVAS].mean()
        bars = ax.bar(NOMBRES_AFECT, medias.values, color=COLORS_AFECT, edgecolor='white')
        ax.axhline(3, color='red', ls='--', alpha=0.5, label='Neutral (3)')
        ax.set_title('Percepción afectiva media (escala 1-5)')
        ax.set_ylabel('Puntuación media'); ax.set_ylim(0, 5.3); ax.legend()
        ax.grid(axis='y', alpha=0.3)
        for b_, v in zip(bars, medias.values):
            ax.text(b_.get_x() + b_.get_width() / 2, v + 0.05, f'{v:.2f}',
                    ha='center', fontsize=8)
        plt.tight_layout()
        self._save(fig, 'afectivas_global.png')

    def grafico_fuentes(self):
        if 'fuentes' not in self.results or not self.results['fuentes']:
            return
        fig, ax = plt.subplots(figsize=(7, 5))
        items = sorted(self.results['fuentes'].items(), key=lambda x: -x[1])
        fuente_label = {'trafico': 'Tráfico', 'humano': 'Humano', 'natural': 'Natural'}
        labels = [fuente_label.get(k, k.capitalize()) for k, _ in items]
        vals = [v for _, v in items]
        n = len(self.df)
        bars = ax.bar(labels, vals, color=['#e74c3c', '#3498db', '#2ecc71'][:len(labels)],
                      edgecolor='white')
        ax.set_title('Frecuencia de fuentes sonoras detectadas')
        ax.set_ylabel('Nº de detecciones'); ax.grid(axis='y', alpha=0.3)
        for b_, v in zip(bars, vals):
            ax.text(b_.get_x() + b_.get_width() / 2, v + 1,
                    f'{v}\n({v/n*100:.0f}%)', ha='center', fontsize=9)
        plt.tight_layout()
        self._save(fig, 'fuentes_sonoras.png')

    # =========================================================================
    # 5. INFORME PDF
    # =========================================================================
    def generar_pdf(self):
        if not REPORTLAB_AVAILABLE:
            print('  [SKIP] reportlab no disponible; no se genera PDF.')
            return
        pdf_path = self.output_dir / 'informe_paisajes_sonoros.pdf'
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                                leftMargin=2 * cm, rightMargin=2 * cm,
                                topMargin=1.8 * cm, bottomMargin=1.8 * cm)
        ss = getSampleStyleSheet()
        h1 = ParagraphStyle('h1', parent=ss['Heading1'], fontSize=15,
                            textColor=colors.HexColor('#2c3e50'), spaceAfter=8)
        h2 = ParagraphStyle('h2', parent=ss['Heading2'], fontSize=12,
                            textColor=colors.HexColor('#34495e'), spaceBefore=10, spaceAfter=4)
        body = ParagraphStyle('body', parent=ss['BodyText'], fontSize=9.5,
                              alignment=TA_JUSTIFY, leading=13)
        title = ParagraphStyle('title', parent=ss['Title'], fontSize=20,
                               textColor=colors.HexColor('#2c3e50'))
        small = ParagraphStyle('small', parent=ss['BodyText'], fontSize=8,
                               textColor=colors.grey)
        el = []

        def img(name, width=16 * cm):
            p = self.output_dir / name
            if p.exists():
                im = RLImage(str(p))
                im._restrictSize(width, 22 * cm)
                el.append(im); el.append(Spacer(1, 6))

        def tbl(data, col_w=None):
            t = Table(data, colWidths=col_w, hAlign='LEFT')
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 8.5),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.white, colors.HexColor('#ecf0f1')]),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
            el.append(t); el.append(Spacer(1, 8))

        # ── Portada ──
        el.append(Spacer(1, 1.5 * cm))
        el.append(Paragraph('Analisis Perceptual-Acustico de Paisajes Sonoros', title))
        el.append(Spacer(1, 4))
        el.append(Paragraph('Molestia, modelo circumplejo ISO 12913 y penalizacion '
                            'de molestia segun el metodo de Hongisto / Oliva', h2))
        el.append(Spacer(1, 10))
        n = self._n_part()
        el.append(Paragraph(
            f'Trabajo de Fin de Grado - URJC. Informe generado automaticamente a '
            f'partir de <b>{n} participantes</b> y <b>{len(self.df)} respuestas</b> '
            f'sobre 18 audios binaurales (mensaje de evacuacion fijo a 60 dB + ruido '
            f'de fondo: trafico, voces o naturaleza a 52/60/68 dB; SNR -8/0/+8 dB), '
            f'mas {len(self.ref_cols)} audios de referencia calibrados '
            f'({", ".join(str(x) for x in self.ref_niveles)} dB SPL).', body))
        el.append(Spacer(1, 14))

        # ── 1. Metodologia ──
        el.append(Paragraph('1. Metodologia', h1))
        el.append(Paragraph(
            '<b>Modelo circumplejo (ISO 12913-2/3).</b> Los 8 atributos afectivos '
            '(agradable, estimulante, con actividad, caotico, molesto, monotono, '
            'sin actividad, calmado) se proyectan en el plano ISOPleasant-ISOEventful '
            'mediante la libreria <i>Soundscapy</i>, que aplica la transformacion '
            'trigonometrica normalizada del estandar (ISOPleasant y ISOEventful en '
            '[-1, 1]).', body))
        if self.weighting == 'dba':
            el.append(Paragraph(
                '<b>Niveles acusticos (LAeq).</b> El mensaje de evacuacion se presento '
                'siempre a 60 dB; lo que varia entre condiciones es el nivel del ruido '
                'de fondo (52, 60 y 68 dB para low, equal y high). El nivel total de cada '
                'audio es la suma logaritmica de ambos: 60,63 / 63,00 / 68,63 dB. Estos '
                'niveles se calibraron en <b>dBZ</b> (sin ponderar), pero el metodo de '
                'Hongisto opera en <b>LAeq (dBA)</b>; por ello cada nivel se convierte a '
                'dBA sumando la correccion de ponderacion A (LAeq-LZeq) medida '
                'directamente de cada senal. Esta correccion depende solo del espectro y '
                'es decisiva aqui: los audios de referencia son ruido de baja frecuencia '
                f'(correccion ≈ {self.results.get("ref_offset", 0):+.0f} dB, '
                f'por lo que {self.ref_niveles[0]}-{self.ref_niveles[-1]} dBZ equivalen a '
                f'{self.ref_niveles_dba[0]:.0f}-{self.ref_niveles_dba[-1]:.0f} dBA), '
                'mientras que los soundscapes experimentales son de banda ancha '
                f'(correccion ≈ {self.results.get("exp_offset", 0):+.0f} dB). El centroide '
                'espectral se mide tambien del WAV (forma del espectro, cf. Hongisto et al. '
                '2024).', body))
        else:
            el.append(Paragraph(
                '<b>Niveles acusticos (dBZ, SIN correccion de ponderacion).</b> El '
                'mensaje de evacuacion se presento siempre a 60 dB; lo que varia es el '
                'nivel del ruido de fondo (52, 60 y 68 dB para low, equal y high). El '
                'nivel total es la suma logaritmica: 60,63 / 63,00 / 68,63 dB. En esta '
                'version los niveles se usan tal cual fueron calibrados, en <b>dBZ</b> '
                '(sin ponderacion A). <b>Aviso:</b> las referencias son ruido de baja '
                'frecuencia, por lo que su nivel A-ponderado (LAeq) real es ~28 dB '
                'inferior; al no aplicar esa correccion, las penalizaciones resultan '
                'considerablemente mayores. Esta version se incluye solo para '
                'comparacion; la version en dBA (LAeq) es la consistente con el metodo '
                'de Hongisto.', body))
        el.append(Paragraph(
            '<b>Penalizacion de molestia (Hongisto / Oliva et al.).</b> Se ajusta la '
            'recta dosis-respuesta molestia=f(LAeq) de los audios de referencia. Para '
            'cada sonido experimental, la penalizacion <i>k</i> [dB] es la diferencia '
            'entre su LAeq real y el LAeq aparente de un audio de referencia igual de '
            'molesto: <b>k = (molestia - a)/b - LAeq_real</b>. Un valor positivo indica '
            'que el sonido es mas molesto de lo que su nivel fisico predeciria.', body))

        # ── 2. Muestra y demografia ──
        el.append(Paragraph('2. Muestra y demografia', h1))
        for label, vc in self.results.get('demografia', {}).items():
            data = [[label, 'N', '%']]
            tot = vc.sum()
            for k, v in vc.items():
                data.append([str(k), str(v), f'{v/tot*100:.0f}%'])
            tbl(data, col_w=[7 * cm, 2.5 * cm, 2.5 * cm])

        # ── 3. Molestia ──
        el.append(Paragraph('3. Molestia percibida', h1))
        ov = self.df['molestia'].describe()
        el.append(Paragraph(
            f'Molestia global del experimento: media = <b>{ov["mean"]:.2f}</b> '
            f'(DT {ov["std"]:.2f}; rango {ov["min"]:.0f}-{ov["max"]:.0f}).', body))
        # tabla molestia por condicion
        piv = self.results['molestia_cond']
        data = [['Ruido \\ Nivel'] + [NIVEL_LABEL[n] for n in NIVEL_ORDER]]
        for r in RUIDOS:
            data.append([RUIDO_LABEL[r]] + [f'{piv.loc[r, n]:.2f}' for n in NIVEL_ORDER])
        tbl(data)
        img('molestia_resumen.png')
        img('heatmap_molestia.png', width=11 * cm)

        # ── 4. Estadistica inferencial ──
        if self.results.get('inferencial'):
            el.append(Paragraph('4. Estadistica inferencial (Friedman + Wilcoxon)', h1))
            for factor, res in self.results['inferencial'].items():
                sig = 'significativo' if res['p'] < 0.05 else 'no significativo'
                el.append(Paragraph(
                    f'<b>Efecto de {factor}</b>: chi²({res["n"]}) = {res["chi2"]:.2f}, '
                    f'p = {res["p"]:.4g} ({sig}).', body))
                data = [['Comparacion', 'p (Wilcoxon)', 'p (Bonferroni)', 'Sig.']]
                for a_, b_, pw, pb in res['pairs']:
                    data.append([f'{a_} vs {b_}', f'{pw:.4g}', f'{min(pb,1):.4g}',
                                 'Sí' if pb < 0.05 else 'no'])
                tbl(data, col_w=[5 * cm, 3.5 * cm, 3.5 * cm, 2 * cm])

        # ── 5. Modelo circumplejo ISO ──
        if SOUNDSCAPY_AVAILABLE and 'iso_ruido' in self.results:
            el.append(PageBreak())
            el.append(Paragraph('5. Modelo circumplejo ISO 12913', h1))
            iso = self.results['iso_ruido']
            data = [['Ruido', 'ISOPleasant', 'ISOEventful']]
            for r in RUIDOS:
                data.append([RUIDO_LABEL[r], f'{iso.loc[r, "ISOPleasant"]:+.3f}',
                             f'{iso.loc[r, "ISOEventful"]:+.3f}'])
            tbl(data, col_w=[5 * cm, 4 * cm, 4 * cm])
            iso2 = self.results['iso_nivel']
            data = [['Nivel', 'ISOPleasant', 'ISOEventful']]
            for nv in NIVEL_ORDER:
                data.append([NIVEL_LABEL[nv], f'{iso2.loc[nv, "ISOPleasant"]:+.3f}',
                             f'{iso2.loc[nv, "ISOEventful"]:+.3f}'])
            tbl(data, col_w=[5 * cm, 4 * cm, 4 * cm])
            el.append(Paragraph(
                'Jointplots (densidad ISO con distribuciones marginales en los '
                'laterales) generados con Soundscapy:', body))
            img('iso_jointplot_ruido.png', width=13 * cm)
            img('iso_jointplot_nivel.png', width=13 * cm)
            img('iso_medias_condicion.png', width=11 * cm)

        # ── 6. Penalizacion de Hongisto ──
        if self.penalty is not None:
            el.append(PageBreak())
            el.append(Paragraph('6. Penalizacion de molestia (metodo Hongisto)', h1))
            rr = self.ref_reg
            el.append(Paragraph(
                f'Recta de referencia: molestia = {rr["a"]:.3f} + {rr["b"]:.4f}·LAeq '
                f'(R² = {rr["r2"]:.3f}, p = {rr["p"]:.4g}). La penalizacion se deriva '
                f'invirtiendo esta recta.', body))
            ref_max = max(rr['means']); exp_max = self.df['molestia'].max()
            if exp_max > ref_max:
                el.append(Paragraph(
                    f'<b>Nota metodologica:</b> los audios de referencia (ruido neutro, '
                    f'espectro -9 dB/octava) resultaron muy poco molestos '
                    f'(molestia media maxima ≈ {ref_max:.1f} a {max(rr["niveles"]):.0f} {self.unit}), '
                    f'mientras que los audios experimentales (con mensaje de evacuacion) '
                    f'alcanzan molestias de hasta {exp_max:.0f}. La referencia, por tanto, '
                    f'no cubre todo el rango experimental y la penalizacion implica cierta '
                    f'extrapolacion: sus valores absolutos en dB deben interpretarse como '
                    f'una cota del exceso (o defecto) de molestia de estos paisajes '
                    f'sonoros respecto a un ruido neutro de igual nivel, mas '
                    f'que como una cifra exacta. El orden relativo entre condiciones si '
                    f'es robusto.', body))
            data = [['Ruido', 'Nivel', f'Nivel real\n[{self.unit}]', 'Molestia\nmedia',
                     'Penalización\nk [dB]', 'IC 95%']]
            for _, row in self.penalty.iterrows():
                data.append([RUIDO_LABEL[row['ruido']], row['nivel'],
                             f'{row["laeq_real"]:.1f}', f'{row["molestia_media"]:.2f}',
                             f'{row["penalty_mean"]:+.2f}', f'±{row["penalty_ci95"]:.2f}'])
            tbl(data)
            pr = self.penalty.groupby('ruido')['penalty_mean'].mean().reindex(RUIDOS)
            data = [['Tipo de ruido', 'Penalización media k [dB]']]
            for r in RUIDOS:
                data.append([RUIDO_LABEL[r], f'{pr[r]:+.2f}'])
            tbl(data, col_w=[6 * cm, 6 * cm])
            img('penalizacion_curva.png')
            img('penalizacion_barras.png')
            img('penalizacion_vs_centroide.png', width=12 * cm)

        # ── 7. Percepcion afectiva ──
        el.append(PageBreak())
        el.append(Paragraph('7. Percepcion afectiva y fuentes sonoras', h1))
        afg = self.results['afect_global']
        data = [['Atributo', 'Media (1-5)']]
        for af, nom in zip(AFECTIVAS, NOMBRES_AFECT):
            data.append([nom, f'{afg[af]:.2f}'])
        tbl(data, col_w=[6 * cm, 4 * cm])
        img('radar_afectivas.png')
        img('afectivas_global.png')
        if self.results.get('fuentes'):
            tot = len(self.df)
            data = [['Fuente', 'Detecciones', '%']]
            for k, v in sorted(self.results['fuentes'].items(), key=lambda x: -x[1]):
                data.append([k, str(v), f'{v/tot*100:.1f}%'])
            tbl(data, col_w=[5 * cm, 4 * cm, 3 * cm])
            img('fuentes_sonoras.png', width=10 * cm)

        # ── 8. Correlaciones ──
        if self.results.get('correlaciones'):
            el.append(Paragraph('8. Correlaciones clave', h1))
            etq = {'molestia_isopleasant': 'Molestia vs ISOPleasant',
                   'molestia_isoeventful': 'Molestia vs ISOEventful',
                   'penalty_centroide': 'Penalización vs centroide espectral',
                   'molestia_centroide': 'Molestia vs centroide espectral'}
            data = [['Relacion', 'r (Pearson)', 'p', 'Sig.']]
            for k, (r, p) in self.results['correlaciones'].items():
                data.append([etq.get(k, k), f'{r:+.3f}', f'{p:.4g}',
                             'Sí' if p < 0.05 else 'no'])
            tbl(data, col_w=[7 * cm, 3 * cm, 3 * cm, 2 * cm])

        el.append(Spacer(1, 14))
        el.append(Paragraph(
            'Informe generado por analizar_resultados.py (Soundscapy + metodo de '
            'penalizacion de Hongisto/Oliva). Las cifras provienen directamente de '
            'los datos de los participantes.', small))

        doc.build(el)
        print(f'  Informe PDF: {pdf_path}')

    # =========================================================================
    # INFORME TXT
    # =========================================================================
    def guardar_txt(self):
        old = sys.stdout
        sys.stdout = buf = StringIO()
        self.info_general()
        self.estadisticas_molestia()
        self.estadisticas_inferenciales()
        self.estadisticas_iso()
        self.estadisticas_afectivas()
        self.estadisticas_fuentes()
        self.correlaciones()
        if self.penalty is not None:
            print('\n' + '=' * 64)
            print('TABLA DE PENALIZACION POR CONDICION')
            print('=' * 64)
            print(self.penalty.round(2).to_string(index=False))
        sys.stdout = old
        out = self.output_dir / 'informe.txt'
        out.write_text(buf.getvalue(), encoding='utf-8')
        print(f'  Informe TXT: {out}')

    # =========================================================================
    def run_all(self):
        # Acustica + penalizacion (antes que el resto, alimentan al informe)
        self.calibrar_acustica()
        self.penalizacion_hongisto()
        # Texto
        self.info_general()
        self.estadisticas_molestia()
        self.estadisticas_inferenciales()
        self.estadisticas_iso()
        self.estadisticas_afectivas()
        self.estadisticas_fuentes()
        self.correlaciones()
        # Graficas
        print('\n' + '=' * 64)
        print('GENERANDO GRAFICAS')
        print('=' * 64)
        self.grafico_molestia()
        self.grafico_heatmap()
        self.grafico_circumplejo()
        self.grafico_curva_penalizacion()
        self.grafico_penalizacion_barras()
        self.grafico_penalizacion_centroide()
        self.grafico_radar_afectivas()
        self.grafico_afectivas()
        self.grafico_fuentes()
        # Informes
        print('\n' + '=' * 64)
        print('GENERANDO INFORMES')
        print('=' * 64)
        self.guardar_txt()
        self.generar_pdf()
        print('\nAnalisis completado!')


# =============================================================================
if __name__ == '__main__':
    here = Path(__file__).resolve().parent

    # CSV por defecto: junto al script, o en la estructura de la app
    csv_local = here / 'paisajes_sonoros.csv'
    csv_app = here / 'CSV' / 'resultados' / 'paisajes_sonoros.csv'
    csv_default = csv_local if csv_local.exists() else csv_app

    parser = argparse.ArgumentParser(description='Analisis Paisajes Sonoros')
    parser.add_argument('csv_path', nargs='?', default=str(csv_default),
                        help='Ruta al CSV unificado')
    parser.add_argument('--audio-dir', default=str(here / 'resources' / 'audios'),
                        help='Carpeta con los WAV del experimento')
    parser.add_argument('--ref-dir', default=str(here / 'resources' / 'ref'),
                        help='Carpeta con los WAV de referencia')
    parser.add_argument('--weighting', choices=['dba', 'dbz'], default='dba',
                        help='dba: aplica correccion A (LAeq, Hongisto); '
                             'dbz: sin correccion de ponderacion')
    parser.add_argument('--output-dir', default=None,
                        help='Carpeta de salida (por defecto: '
                             'con_correccion_dBA / sin_correccion_dBA junto al script)')
    parser.add_argument('--drop-ref', default='52,56',
                        help='Niveles de referencia a descartar (dB, separados por '
                             'coma). Por defecto 52,56 (problemas de escucha).')
    args = parser.parse_args()

    out = args.output_dir
    if out is None:
        out = str(here / ('con_correccion_dBA' if args.weighting == 'dba'
                          else 'sin_correccion_dBA'))
    drop_ref = [int(x) for x in args.drop_ref.split(',') if x.strip()]

    analyzer = Analyzer(args.csv_path, audio_dir=args.audio_dir, ref_dir=args.ref_dir,
                        output_dir=out, weighting=args.weighting, drop_ref=drop_ref)
    analyzer.run_all()
