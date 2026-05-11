"""
analizar_resultados.py
Análisis completo del cuestionario de Paisajes Sonoros.

Requiere:
    pip install pandas matplotlib numpy scipy scikit-maad

Uso:
    python analizar_resultados.py CSV/paisajes_sonoros.csv
    python analizar_resultados.py CSV/paisajes_sonoros.csv --audio-dir resources/audios
"""

import sys
import argparse
import warnings
from io import StringIO
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch
from scipy import stats as scipy_stats

warnings.filterwarnings('ignore')

# ── scikit-maad ────────────────────────────────────────────────────────────────
try:
    from maad import sound, features as maad_features
    MAAD_AVAILABLE = True
except ImportError:
    MAAD_AVAILABLE = False
    print('[AVISO] scikit-maad no encontrado. Las graficas acusticas se omitiran.')

# ── Paleta de colores consistente ─────────────────────────────────────────────
COLOR_ROAD    = '#e74c3c'
COLOR_VOICES  = '#3498db'
COLOR_NATURE  = '#2ecc71'
COLOR_LOW     = '#27ae60'
COLOR_EQUAL   = '#f39c12'
COLOR_HIGH    = '#c0392b'
COLOR_REF     = '#f39c12'
COLOR_EXP     = '#8e44ad'
COLORS_AFECT  = ['#9b59b6','#e67e22','#1abc9c','#95a5a6',
                 '#34495e','#e74c3c','#3498db','#7f8c8d']

RUIDO_LABEL   = {'road': 'Trafico', 'voices': 'Voces', 'nature': 'Naturaleza'}
NIVEL_ORDER   = ['low', 'equal', 'high']
NIVEL_LABEL   = ['Low (-8dB)', 'Equal (0dB)', 'High (+8dB)']


# ==============================================================================
class Analyzer:
# ==============================================================================

    def __init__(self, csv_path, audio_dir=None):
        self.csv_path  = Path(csv_path)
        self.audio_dir = Path(audio_dir) if audio_dir else None
        self.output_dir = self.csv_path.parent / 'resultados'
        self.output_dir.mkdir(exist_ok=True)

        self.df = pd.read_csv(self.csv_path)

        # Tipos numéricos
        self.df['molestia'] = pd.to_numeric(self.df['molestia'], errors='coerce')

        # Columnas de referencia: ref_28, ref_32, … ref_60
        self.ref_cols = sorted([c for c in self.df.columns if c.startswith('ref_')])
        self.ref_niveles = [int(c.replace('ref_', '')) for c in self.ref_cols]
        for col in self.ref_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        self.afectivas = [
            'afectiva_agradable', 'afectiva_caotico', 'afectiva_estimulante',
            'afectiva_sinactividad', 'afectiva_calmado', 'afectiva_molesto',
            'afectiva_conactividad', 'afectiva_monotono'
        ]
        self.nombres_afectivas = [
            'Agradable', 'Caotico', 'Estimulante', 'Sin actividad',
            'Calmado', 'Molesto', 'Con actividad', 'Monotono'
        ]
        for col in self.afectivas:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        # DataFrame de un registro por participante
        id_col = 'participante_id' if 'participante_id' in self.df.columns \
                 else 'timestamp_inicio'
        self.id_col    = id_col
        self.df_part   = self.df.drop_duplicates(id_col).copy()

    # ── helpers ───────────────────────────────────────────────────────────────
    def _n_part(self):
        return self.df[self.id_col].nunique()

    def _save(self, fig, name):
        p = self.output_dir / name
        fig.savefig(p, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f'  Guardado: {p}')

    # ==========================================================================
    # 1. INFO GENERAL (texto)
    # ==========================================================================
    def info_general(self):
        n = self._n_part()
        denom = n or 1
        print('=' * 60)
        print('INFORME GENERAL')
        print('=' * 60)
        print(f'Participantes:           {n}')
        print(f'Total respuestas:        {len(self.df)}')
        print(f'Respuestas/participante: {len(self.df)/denom:.1f}')

        if self.ref_cols:
            print(f'\nAudios referencia evaluados: {len(self.ref_cols)} '
                  f'({", ".join(self.ref_cols)})')
            medias_ref = self.df_part[self.ref_cols].mean()
            print(f'  Media global ref: {medias_ref.mean():.2f}')

        print('\n--- Demografia ---')
        for col, label in [('edad','Edad'), ('genero','Genero'),
                           ('estudios','Estudios')]:
            if col in self.df_part.columns:
                print(f'\n{label}:')
                print(self.df_part[col].value_counts().to_string())

    # ==========================================================================
    # 2. ESTADÍSTICAS MOLESTIA (texto)
    # ==========================================================================
    def estadisticas_molestia(self):
        print('\n' + '=' * 60)
        print('ESTADISTICAS DE MOLESTIA (0-10)')
        print('=' * 60)

        if self.ref_cols:
            print('\n[Audios referencia — media por nivel dB]')
            for col, nivel in zip(self.ref_cols, self.ref_niveles):
                vals = self.df_part[col].dropna()
                if len(vals):
                    print(f'  {nivel} dB: media={vals.mean():.2f}  '
                          f'std={vals.std():.2f}  [{vals.min():.0f}–{vals.max():.0f}]')

        print('\n[Audios experimento]')
        print(self.df['molestia'].describe().round(2).to_string())

        for label, col in [('ruido','ruido'), ('mensaje','mensaje'),
                           ('nivel','nivel')]:
            print(f'\n--- Por {label} ---')
            print(self.df.groupby(col)['molestia']
                  .agg(['mean','std','min','max']).round(2).to_string())

        print('\n--- Ruido x Nivel ---')
        print(self.df.groupby(['ruido','nivel'])['molestia']
              .agg(['mean','std']).round(2).to_string())

    # ==========================================================================
    # 3. COMPARACIÓN CON REFERENCIA (texto)
    # ==========================================================================
    def comparacion_referencia(self):
        if not self.ref_cols:
            return

        print('\n' + '=' * 60)
        print('COMPARACION CON AUDIOS DE REFERENCIA')
        print('=' * 60)

        # Media global de referencia (todos los niveles, todos los participantes)
        ref_global = self.df_part[self.ref_cols].mean(axis=1).mean()
        media_exp  = self.df['molestia'].mean()
        print(f'\nMolestia media referencia (global): {ref_global:.2f}')
        print(f'Molestia media experimento        : {media_exp:.2f}')
        print(f'Diferencia (exp - ref)            : {media_exp - ref_global:+.2f}')

        # Evolución de la molestia a lo largo de los 9 niveles
        print('\n--- Curva de molestia de referencia por nivel (dB SPL) ---')
        for col, nivel in zip(self.ref_cols, self.ref_niveles):
            vals = self.df_part[col].dropna()
            if len(vals):
                print(f'  {nivel:>3} dB: {vals.mean():.2f}')

        # Correlación entre molestia de referencia media (por participante)
        # y molestia media en el experimento
        media_pp  = self.df.groupby(self.id_col)['molestia'].mean()
        media_ref_pp = self.df_part.set_index(self.id_col)[self.ref_cols]\
                           .mean(axis=1).rename('ref_media')
        df_c = media_ref_pp.to_frame().join(media_pp).dropna()
        df_c.columns = ['ref', 'exp']

        if len(df_c) >= 3:
            if df_c['ref'].nunique() > 1:
                r, p = scipy_stats.pearsonr(df_c['ref'], df_c['exp'])
                print(f'\nCorrelacion Pearson (ref vs exp por participante): '
                      f'r={r:.3f}, p={p:.4f}')
                print('  -> Significativa (p<0.05)' if p < 0.05
                      else '  -> No significativa')
            t, pt = scipy_stats.ttest_rel(df_c['ref'], df_c['exp'])
            print(f'T-test pareado: t={t:.3f}, p={pt:.4f}')
            print('  -> Diferencia significativa (p<0.05)' if pt < 0.05
                  else '  -> Sin diferencia significativa')
        else:
            print('\n[AVISO] Se necesitan >=3 participantes para test estadisticos.')

        print('\n--- Molestia experimento vs referencia global por ruido ---')
        for ruido in ['road', 'voices', 'nature']:
            m = self.df[self.df['ruido'] == ruido]['molestia'].mean()
            print(f'  {RUIDO_LABEL[ruido]:<12}: {m:.2f}  (dif={m-ref_global:+.2f})')

        print('\n--- Molestia experimento vs referencia global por nivel ---')
        for nivel in NIVEL_ORDER:
            m = self.df[self.df['nivel'] == nivel]['molestia'].mean()
            print(f'  {nivel:<8}: {m:.2f}  (dif={m-ref_global:+.2f})')

    # ==========================================================================
    # 4. FUENTES SONORAS (texto)
    # ==========================================================================
    def estadisticas_fuentes(self):
        print('\n' + '=' * 60)
        print('ESTADISTICAS DE FUENTES SONORAS')
        print('=' * 60)
        todas = []
        for f in self.df['fuentes']:
            if pd.notna(f):
                todas.extend([x.strip().strip('"') for x in str(f).split(';')])
        conteo = Counter(todas)
        n = len(self.df)
        for fuente, count in conteo.most_common():
            print(f'  {fuente:<12}: {count:>4}  ({count/n*100:.1f}%)')

    # ==========================================================================
    # 5. AFECTIVAS (texto)
    # ==========================================================================
    def estadisticas_afectivas(self):
        print('\n' + '=' * 60)
        print('ESTADISTICAS DE PERCEPCION AFECTIVA (1-5)')
        print('=' * 60)
        for af, nom in zip(self.afectivas, self.nombres_afectivas):
            s = self.df[af].describe()
            print(f'  {nom:<15}: media={s["mean"]:.2f}  '
                  f'std={s["std"]:.2f}  [{s["min"]:.0f}–{s["max"]:.0f}]')
        print('\n--- Por ruido ---')
        print(self.df.groupby('ruido')[self.afectivas].mean().round(2).to_string())

    # ==========================================================================
    # 6. GRÁFICA CRONOLOGÍA DE RESULTADOS
    # ==========================================================================
    def grafico_cronologia(self):
        """Timeline de respuestas: molestia en el tiempo para cada participante."""
        if 'timestamp_respuesta' not in self.df.columns:
            print('  [SKIP] No hay columna timestamp_respuesta.')
            return

        df = self.df.copy()
        df['ts'] = pd.to_datetime(df['timestamp_respuesta'], errors='coerce')
        df = df.dropna(subset=['ts'])
        if df.empty:
            return

        participants = df[self.id_col].unique()
        n_p = len(participants)
        colors_p = plt.cm.tab10(np.linspace(0, 1, min(n_p, 10)))

        fig, axes = plt.subplots(2, 1, figsize=(14, 9),
                                 gridspec_kw={'height_ratios': [2, 1]})

        # ── Panel superior: molestia por timestamp ──────────────────────────
        ax = axes[0]
        for i, pid in enumerate(participants):
            sub = df[df[self.id_col] == pid].sort_values('ts')
            col = colors_p[i % 10]
            ax.plot(sub['ts'], sub['molestia'].astype(float),
                    marker='o', markersize=4, linewidth=1.2,
                    color=col, alpha=0.8,
                    label=f'P{i+1}')
            # Punto de referencia si existe
            if 'molestia_ref_before' in sub.columns:
                ref_val = sub['molestia_ref_before'].dropna()
                if len(ref_val):
                    ax.axhline(float(ref_val.iloc[0]), color=col,
                               linestyle=':', linewidth=0.8, alpha=0.5)

        ax.set_ylabel('Molestia (0–10)', fontsize=10)
        ax.set_ylim(-0.5, 10.5)
        ax.set_title('Cronología de respuestas de molestia por participante\n'
                     '(línea punteada = valor audio referencia)', fontsize=11)
        ax.grid(axis='y', alpha=0.3)
        if n_p <= 10:
            ax.legend(loc='upper right', fontsize=8, ncol=2)

        # Colorear fondo por tipo de ruido
        ruido_col = {'road': COLOR_ROAD, 'voices': COLOR_VOICES,
                     'nature': COLOR_NATURE}
        df_sorted = df.sort_values('ts')
        prev_ts = None
        for _, row in df_sorted.iterrows():
            if prev_ts is not None:
                ax.axvspan(prev_ts, row['ts'],
                           color=ruido_col.get(row['ruido'], '#aaaaaa'),
                           alpha=0.07)
            prev_ts = row['ts']

        # ── Panel inferior: histograma acumulado de respuestas en el tiempo ─
        ax2 = axes[1]
        # Número de respuestas por intervalo de tiempo (ventana 30s)
        df_sorted2 = df.sort_values('ts').copy()
        df_sorted2['t_min'] = (df_sorted2['ts'] - df_sorted2['ts'].min())\
                               .dt.total_seconds() / 60
        ax2.bar(df_sorted2['t_min'], [1]*len(df_sorted2),
                width=0.2, color='#8e44ad', alpha=0.6)
        ax2.set_xlabel('Tiempo transcurrido desde el inicio (min)', fontsize=10)
        ax2.set_ylabel('Resp.', fontsize=9)
        ax2.set_title('Distribución temporal de respuestas', fontsize=10)
        ax2.grid(axis='y', alpha=0.3)

        # Leyenda colores de ruido
        from matplotlib.patches import Patch
        legend_ruido = [Patch(facecolor=c, alpha=0.4, label=RUIDO_LABEL[k])
                        for k, c in ruido_col.items()]
        axes[0].legend(handles=legend_ruido + (
            [plt.Line2D([0],[0], color='gray', marker='o', linewidth=1,
                        label=f'P{i+1}') for i in range(min(n_p,5))]
        ), loc='upper right', fontsize=8, ncol=3)

        plt.tight_layout()
        self._save(fig, 'cronologia_resultados.png')

    # ==========================================================================
    # 7. GRÁFICA RADAR — 8 dimensiones afectivas
    # ==========================================================================
    def grafico_radar_afectivas(self):
        """Radar chart de las 8 dimensiones afectivas, desglosado por ruido."""
        labels = self.nombres_afectivas
        N = len(labels)
        angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
        angles += angles[:1]  # cerrar el polígono

        grupos = {
            'road':   (COLOR_ROAD,    'Trafico'),
            'voices': (COLOR_VOICES,  'Voces'),
            'nature': (COLOR_NATURE,  'Naturaleza'),
        }

        fig, axes = plt.subplots(1, 2, figsize=(14, 7),
                                 subplot_kw=dict(polar=True))

        # ── Panel izquierdo: media global ─────────────────────────────────
        ax = axes[0]
        media_global = [self.df[af].mean() for af in self.afectivas]
        media_global += media_global[:1]
        ax.plot(angles, media_global, color=COLOR_EXP, linewidth=2)
        ax.fill(angles, media_global, color=COLOR_EXP, alpha=0.25)
        # Línea neutra (valor 3)
        neutral = [3]*N + [3]
        ax.plot(angles, neutral, color='gray', linewidth=0.8,
                linestyle='--', alpha=0.6)

        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylim(1, 5)
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_yticklabels(['1','2','3','4','5'], fontsize=7, color='gray')
        ax.set_title('Percepción afectiva\nMedia global', fontsize=11, pad=15)

        # ── Panel derecho: por tipo de ruido ──────────────────────────────
        ax2 = axes[1]
        for ruido, (color, label) in grupos.items():
            sub = self.df[self.df['ruido'] == ruido]
            if sub.empty:
                continue
            valores = [sub[af].mean() for af in self.afectivas]
            valores += valores[:1]
            ax2.plot(angles, valores, color=color, linewidth=2, label=label)
            ax2.fill(angles, valores, color=color, alpha=0.12)

        ax2.plot(angles, neutral, color='gray', linewidth=0.8,
                 linestyle='--', alpha=0.6, label='Neutral (3)')
        ax2.set_theta_offset(np.pi / 2)
        ax2.set_theta_direction(-1)
        ax2.set_xticks(angles[:-1])
        ax2.set_xticklabels(labels, fontsize=9)
        ax2.set_ylim(1, 5)
        ax2.set_yticks([1, 2, 3, 4, 5])
        ax2.set_yticklabels(['1','2','3','4','5'], fontsize=7, color='gray')
        ax2.set_title('Percepción afectiva\npor tipo de ruido', fontsize=11, pad=15)
        ax2.legend(loc='upper right', bbox_to_anchor=(1.35, 1.1), fontsize=9)

        fig.suptitle('Radar de evaluación afectiva (escala 1–5  |  línea gris = neutral)',
                     fontsize=12, y=1.02)
        plt.tight_layout()
        self._save(fig, 'radar_afectivas.png')

    # ==========================================================================
    # 8. GRÁFICAS MOLESTIA + REFERENCIA
    # ==========================================================================
    def grafico_molestia(self):
        has_ref  = bool(self.ref_cols)
        ref_mean = self.df_part[self.ref_cols].mean(axis=1).mean() \
                   if has_ref else None

        fig, axes = plt.subplots(1, 3, figsize=(16, 5))

        for ax, (groupby, etiquetas, title, colors) in zip(axes, [
            ('ruido',   [RUIDO_LABEL[r] for r in ['road','voices','nature']],
             'Molestia por ruido',   [COLOR_ROAD, COLOR_VOICES, COLOR_NATURE]),
            ('nivel',   NIVEL_LABEL, 'Molestia por nivel',
             [COLOR_LOW, COLOR_EQUAL, COLOR_HIGH]),
            ('mensaje', None, 'Molestia por mensaje',
             ['#8e44ad','#16a085']),
        ]):
            if groupby == 'nivel':
                d = self.df.groupby('nivel')['molestia'].mean().reindex(NIVEL_ORDER)
            else:
                d = self.df.groupby(groupby)['molestia'].mean().sort_values(ascending=False)
            labels = etiquetas if etiquetas else list(d.index)
            bars = ax.bar(labels, d.values,
                          color=colors[:len(d)], edgecolor='white', linewidth=0.5)
            if ref_mean is not None:
                ax.axhline(ref_mean, color=COLOR_REF, linestyle='--',
                           linewidth=1.8, label=f'Ref: {ref_mean:.2f}')
                ax.legend(fontsize=8)
            ax.set_title(title, fontsize=11)
            ax.set_ylabel('Molestia (0–10)')
            ax.set_ylim(0, 10.5)
            ax.grid(axis='y', alpha=0.3)
            for b, v in zip(bars, d.values):
                if not np.isnan(v):
                    ax.text(b.get_x() + b.get_width()/2,
                            b.get_height() + 0.15, f'{v:.2f}',
                            ha='center', fontsize=9)

        fig.suptitle('Molestia media  (línea naranja = audio de referencia)',
                     fontsize=12)
        plt.tight_layout()
        self._save(fig, 'molestia_resumen.png')

    def grafico_comparacion_referencia(self):
        if not self.ref_cols:
            return

        ref_global = self.df_part[self.ref_cols].mean(axis=1).mean()

        fig = plt.figure(figsize=(18, 10))
        gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

        # ── Panel 1 (fila 0, col 0-1): curva de molestia de referencia ───
        ax_curva = fig.add_subplot(gs[0, :2])
        medias_nivel = [self.df_part[c].dropna().mean() for c in self.ref_cols]
        stds_nivel   = [self.df_part[c].dropna().std()  for c in self.ref_cols]
        niveles      = self.ref_niveles

        ax_curva.plot(niveles, medias_nivel, marker='o', color='#3498db',
                      linewidth=2, markersize=7, label='Media participantes')
        ax_curva.fill_between(
            niveles,
            [m - s for m, s in zip(medias_nivel, stds_nivel)],
            [m + s for m, s in zip(medias_nivel, stds_nivel)],
            alpha=0.18, color='#3498db', label='±1 std'
        )
        ax_curva.axhline(ref_global, color=COLOR_REF, linestyle='--',
                         linewidth=1.5, label=f'Media global ref: {ref_global:.2f}')
        ax_curva.set_xlabel('Nivel de presion sonora (dB SPL)', fontsize=10)
        ax_curva.set_ylabel('Molestia (0-10)', fontsize=10)
        ax_curva.set_title('Curva de molestia de referencia por nivel', fontsize=11)
        ax_curva.set_xticks(niveles)
        ax_curva.set_ylim(0, 10.5)
        ax_curva.grid(alpha=0.3)
        ax_curva.legend(fontsize=9)

        # ── Panel 2 (fila 0, col 2): por participante (heatmap) ──────────
        ax_heat = fig.add_subplot(gs[0, 2])
        mat = self.df_part[self.ref_cols].values.astype(float)
        if mat.shape[0] > 0:
            im = ax_heat.imshow(mat, aspect='auto', cmap='RdYlGn_r',
                                vmin=0, vmax=10,
                                extent=[niveles[0]-2, niveles[-1]+2, 0, mat.shape[0]])
            ax_heat.set_xlabel('Nivel (dB SPL)', fontsize=9)
            ax_heat.set_ylabel('Participante', fontsize=9)
            ax_heat.set_title('Molestia ref. por participante\n(verde=baja, rojo=alta)',
                               fontsize=10)
            ax_heat.set_xticks(niveles)
            ax_heat.tick_params(axis='x', labelsize=8)
            plt.colorbar(im, ax=ax_heat, label='Molestia')

        # ── Panel 3 (fila 1, col 0): ruido vs referencia ─────────────────
        ax_ruido = fig.add_subplot(gs[1, 0])
        ruidos = ['road', 'voices', 'nature']
        etqs   = [RUIDO_LABEL[r] for r in ruidos]
        medias = [self.df[self.df['ruido']==r]['molestia'].mean() for r in ruidos]
        bars = ax_ruido.bar(etqs, medias,
                            color=[COLOR_ROAD, COLOR_VOICES, COLOR_NATURE],
                            edgecolor='white')
        ax_ruido.axhline(ref_global, color=COLOR_REF, linestyle='--',
                         linewidth=1.8, label=f'Ref global: {ref_global:.2f}')
        ax_ruido.set_ylim(0, 10.5)
        ax_ruido.set_title('Experimento por ruido\nvs. referencia global', fontsize=10)
        ax_ruido.set_ylabel('Molestia (0-10)')
        ax_ruido.legend(fontsize=8)
        ax_ruido.grid(axis='y', alpha=0.3)
        for b, v in zip(bars, medias):
            if not np.isnan(v):
                ax_ruido.text(b.get_x()+b.get_width()/2, v+0.15,
                              f'{v:.2f}', ha='center', fontsize=9)

        # ── Panel 4 (fila 1, col 1): nivel vs referencia ─────────────────
        ax_nivel = fig.add_subplot(gs[1, 1])
        medias_n = [self.df[self.df['nivel']==n]['molestia'].mean()
                    for n in NIVEL_ORDER]
        bars2 = ax_nivel.bar(NIVEL_LABEL, medias_n,
                             color=[COLOR_LOW, COLOR_EQUAL, COLOR_HIGH],
                             edgecolor='white')
        ax_nivel.axhline(ref_global, color=COLOR_REF, linestyle='--',
                         linewidth=1.8, label=f'Ref global: {ref_global:.2f}')
        ax_nivel.set_ylim(0, 10.5)
        ax_nivel.set_title('Experimento por nivel\nvs. referencia global', fontsize=10)
        ax_nivel.set_ylabel('Molestia (0-10)')
        ax_nivel.legend(fontsize=8)
        ax_nivel.grid(axis='y', alpha=0.3)
        for b, v in zip(bars2, medias_n):
            if not np.isnan(v):
                ax_nivel.text(b.get_x()+b.get_width()/2, v+0.15,
                              f'{v:.2f}', ha='center', fontsize=9)

        # ── Panel 5 (fila 1, col 2): scatter ref media vs exp media ──────
        ax_scatter = fig.add_subplot(gs[1, 2])
        media_pp     = self.df.groupby(self.id_col)['molestia'].mean()
        media_ref_pp = self.df_part.set_index(self.id_col)[self.ref_cols]\
                           .mean(axis=1)
        df_c = media_ref_pp.to_frame('ref').join(media_pp).dropna()
        df_c.columns = ['ref', 'exp']
        ax_scatter.scatter(df_c['ref'], df_c['exp'],
                           color=COLOR_EXP, s=80, zorder=3)
        ax_scatter.plot([0,10],[0,10],'k--', linewidth=1, alpha=0.4, label='y=x')
        if len(df_c) >= 3 and df_c['ref'].nunique() > 1:
            m, b, r, p, _ = scipy_stats.linregress(df_c['ref'], df_c['exp'])
            xs = np.linspace(df_c['ref'].min(), df_c['ref'].max(), 50)
            ax_scatter.plot(xs, m*xs+b, color='red', linewidth=1.5,
                            label=f'r={r:.2f}, p={p:.3f}')
        ax_scatter.set_xlim(0, 10)
        ax_scatter.set_ylim(0, 10)
        ax_scatter.set_xlabel('Molestia ref. media (por participante)')
        ax_scatter.set_ylabel('Molestia media experimento')
        ax_scatter.set_title('Correlacion ref. vs experimento\n(por participante)',
                              fontsize=10)
        ax_scatter.legend(fontsize=8)
        ax_scatter.grid(alpha=0.3)

        fig.suptitle('Comparacion: audios de referencia vs. experimento', fontsize=13)
        self._save(fig, 'comparacion_referencia.png')

    def grafico_heatmap(self):
        fig, ax = plt.subplots(figsize=(8, 5))
        pivot = self.df.groupby(['ruido','nivel'])['molestia'].mean().unstack()
        pivot = pivot.reindex(index=['road','voices','nature'],
                              columns=NIVEL_ORDER)
        im = ax.imshow(pivot.values, cmap='RdYlGn_r', aspect='auto',
                       vmin=0, vmax=10)
        ax.set_xticks(range(3))
        ax.set_xticklabels(NIVEL_LABEL)
        ax.set_yticks(range(3))
        ax.set_yticklabels([RUIDO_LABEL[r] for r in ['road','voices','nature']])
        ax.set_title('Mapa de calor: Molestia media (ruido × nivel)')
        plt.colorbar(im, ax=ax, label='Molestia (0–10)')
        for i in range(3):
            for j in range(3):
                v = pivot.values[i, j]
                if not np.isnan(v):
                    ax.text(j, i, f'{v:.2f}', ha='center', va='center',
                            color='black', fontsize=11, fontweight='bold')
        plt.tight_layout()
        self._save(fig, 'heatmap_molestia.png')

    # ==========================================================================
    # 9. GRÁFICAS AFECTIVAS (barras)
    # ==========================================================================
    def grafico_afectivas(self):
        # Global
        fig, ax = plt.subplots(figsize=(12, 5))
        medias = self.df[self.afectivas].mean()
        bars = ax.bar(self.nombres_afectivas, medias.values,
                      color=COLORS_AFECT, edgecolor='white')
        ax.axhline(3, color='red', linestyle='--', alpha=0.5, label='Neutral (3)')
        ax.set_title('Percepción afectiva media (escala 1–5)')
        ax.set_ylabel('Puntuación media')
        ax.set_ylim(0, 5.3)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        for b, v in zip(bars, medias.values):
            ax.text(b.get_x() + b.get_width()/2, v + 0.05,
                    f'{v:.2f}', ha='center', fontsize=8)
        plt.tight_layout()
        self._save(fig, 'afectivas_global.png')

        # Por ruido
        fig, axes = plt.subplots(2, 4, figsize=(18, 8))
        for idx, (af, nom) in enumerate(zip(self.afectivas, self.nombres_afectivas)):
            r, c = idx // 4, idx % 4
            ax = axes[r, c]
            d = self.df.groupby('ruido')[af].mean()\
                    .reindex(['road','voices','nature'])
            bars = ax.bar([RUIDO_LABEL[x] for x in ['road','voices','nature']],
                          d.values,
                          color=[COLOR_ROAD, COLOR_VOICES, COLOR_NATURE],
                          edgecolor='white')
            ax.axhline(3, color='red', linestyle='--', alpha=0.4, linewidth=0.8)
            ax.set_title(nom, fontsize=10)
            ax.set_ylabel('Media (1–5)', fontsize=8)
            ax.set_ylim(0, 5.3)
            ax.grid(axis='y', alpha=0.3)
            ax.tick_params(axis='x', labelsize=8)
            for b, v in zip(bars, d.values):
                if not np.isnan(v):
                    ax.text(b.get_x() + b.get_width()/2, v + 0.05,
                            f'{v:.2f}', ha='center', fontsize=7)
        fig.suptitle('Percepción afectiva por tipo de ruido', fontsize=12)
        plt.tight_layout()
        self._save(fig, 'afectivas_por_ruido.png')

    # ==========================================================================
    # 10. ANÁLISIS ACÚSTICO CON scikit-maad
    # ==========================================================================
    def grafico_acustico_maad(self):
        if not MAAD_AVAILABLE:
            print('  [SKIP] scikit-maad no disponible.')
            return
        if self.audio_dir is None or not self.audio_dir.exists():
            print('  [SKIP] Directorio de audios no especificado o no encontrado.')
            print('         Usa --audio-dir resources/audios')
            return

        audio_files = sorted(self.audio_dir.glob('*.wav'))
        if not audio_files:
            print(f'  [SKIP] No se encontraron .wav en {self.audio_dir}')
            return

        print(f'  Computando indices acusticos para {len(audio_files)} archivos...')
        records = []
        for fpath in audio_files:
            name = fpath.stem  # e.g. mensaje1_road_equal_hrtf
            parts = name.replace('_hrtf','').split('_')
            if len(parts) < 3:
                continue
            mensaje, ruido, nivel = parts[0], parts[1], parts[2]
            try:
                s, fs = sound.load(str(fpath), channel='left', detrend=True,
                                   verbose=False)
                # Índices temporales
                df_t = maad_features.all_temporal_alpha_indices(
                    s, fs, verbose=False)
                # Espectrograma e índices espectrales
                Sxx, tn, fn, ext = sound.spectrogram(
                    s, fs, nperseg=1024, noverlap=512,
                    verbose=False, display=False)
                df_s, _ = maad_features.all_spectral_alpha_indices(
                    Sxx, tn, fn, verbose=False, display=False)

                row = {'archivo': fpath.name,
                       'mensaje': mensaje,
                       'ruido':   ruido,
                       'nivel':   nivel}
                row.update(df_t.iloc[0].to_dict())
                row.update(df_s.iloc[0].to_dict())
                records.append(row)
            except Exception as e:
                print(f'    [ERROR] {fpath.name}: {e}')

        if not records:
            print('  [SKIP] No se pudo procesar ningún audio.')
            return

        df_maad = pd.DataFrame(records)

        # ── Figura 1: índices acústicos clave por tipo de ruido ───────────
        indices_plot = ['LEQt', 'Ht', 'ACI', 'NDSI', 'BI', 'ADI', 'SNRt', 'Hf']
        indices_plot = [c for c in indices_plot if c in df_maad.columns]

        fig, axes = plt.subplots(2, 4, figsize=(18, 8))
        axes = axes.flatten()
        for i, idx_name in enumerate(indices_plot):
            ax = axes[i]
            d = df_maad.groupby('ruido')[idx_name].mean()\
                    .reindex(['road','voices','nature'])
            ax.bar([RUIDO_LABEL[x] for x in ['road','voices','nature']],
                   d.values,
                   color=[COLOR_ROAD, COLOR_VOICES, COLOR_NATURE],
                   edgecolor='white')
            ax.set_title(idx_name, fontsize=11)
            ax.set_ylabel('Valor medio', fontsize=8)
            ax.grid(axis='y', alpha=0.3)
            ax.tick_params(axis='x', labelsize=8)
        # Ocultar paneles sobrantes
        for j in range(len(indices_plot), len(axes)):
            axes[j].set_visible(False)

        fig.suptitle('Índices acústicos (scikit-maad) por tipo de ruido', fontsize=13)
        plt.tight_layout()
        self._save(fig, 'maad_indices_por_ruido.png')

        # ── Figura 2: índices por nivel ───────────────────────────────────
        fig, axes = plt.subplots(2, 4, figsize=(18, 8))
        axes = axes.flatten()
        for i, idx_name in enumerate(indices_plot):
            ax = axes[i]
            d = df_maad.groupby('nivel')[idx_name].mean().reindex(NIVEL_ORDER)
            ax.bar(NIVEL_LABEL, d.values,
                   color=[COLOR_LOW, COLOR_EQUAL, COLOR_HIGH],
                   edgecolor='white')
            ax.set_title(idx_name, fontsize=11)
            ax.set_ylabel('Valor medio', fontsize=8)
            ax.grid(axis='y', alpha=0.3)
            ax.tick_params(axis='x', labelsize=9)
        for j in range(len(indices_plot), len(axes)):
            axes[j].set_visible(False)

        fig.suptitle('Índices acústicos (scikit-maad) por nivel de señal', fontsize=13)
        plt.tight_layout()
        self._save(fig, 'maad_indices_por_nivel.png')

        # ── Figura 3: espectrograma + waveform de un audio representativo ─
        rep_files = {
            'road':   self.audio_dir / 'mensaje1_road_equal_hrtf.wav',
            'voices': self.audio_dir / 'mensaje1_voices_equal_hrtf.wav',
            'nature': self.audio_dir / 'mensaje1_nature_equal_hrtf.wav',
        }
        rep_files = {k: v for k, v in rep_files.items() if v.exists()}
        if rep_files:
            fig, axes = plt.subplots(2, len(rep_files),
                                     figsize=(6*len(rep_files), 7))
            if len(rep_files) == 1:
                axes = axes.reshape(2, 1)

            for col, (ruido, fpath) in enumerate(rep_files.items()):
                try:
                    s, fs = sound.load(str(fpath), channel='left',
                                       detrend=True, verbose=False)
                    t = np.arange(len(s)) / fs
                    # Waveform
                    ax_w = axes[0, col]
                    ax_w.plot(t, s, color=([COLOR_ROAD, COLOR_VOICES,
                               COLOR_NATURE][list(rep_files).index(ruido)]),
                              linewidth=0.5, alpha=0.8)
                    ax_w.set_title(f'Waveform — {RUIDO_LABEL[ruido]}', fontsize=10)
                    ax_w.set_xlabel('Tiempo (s)')
                    ax_w.set_ylabel('Amplitud')
                    ax_w.grid(alpha=0.3)

                    # Espectrograma
                    ax_s = axes[1, col]
                    Sxx, tn, fn, ext = sound.spectrogram(
                        s, fs, nperseg=1024, noverlap=512,
                        verbose=False, display=False)
                    Sxx_db = 10 * np.log10(Sxx + 1e-12)
                    im = ax_s.imshow(Sxx_db, aspect='auto', origin='lower',
                                     extent=ext, cmap='viridis')
                    ax_s.set_title(f'Espectrograma — {RUIDO_LABEL[ruido]}',
                                   fontsize=10)
                    ax_s.set_xlabel('Tiempo (s)')
                    ax_s.set_ylabel('Frecuencia (Hz)')
                    plt.colorbar(im, ax=ax_s, label='dB')
                except Exception as e:
                    axes[0, col].set_title(f'Error: {e}')

            fig.suptitle('Waveforms y espectrogramas (mensaje1, nivel equal)',
                         fontsize=12)
            plt.tight_layout()
            self._save(fig, 'maad_espectrogramas.png')

        # ── Figura 4: correlación índices acústicos vs molestia media ─────
        if len(df_maad) >= 3 and 'audio_filename' in self.df.columns:
            df_mol = self.df.groupby('audio_filename')['molestia'].mean()\
                         .reset_index()
            df_mol.columns = ['audio_filename', 'molestia_media']
            df_maad['audio_filename'] = df_maad['archivo']
            df_merge = df_maad.merge(df_mol, on='audio_filename', how='inner')

            if len(df_merge) >= 3:
                correlaciones = {}
                for idx_name in indices_plot:
                    if idx_name in df_merge.columns:
                        x = df_merge[idx_name].dropna()
                        y = df_merge.loc[x.index, 'molestia_media'].dropna()
                        common = x.index.intersection(y.index)
                        if len(common) >= 3 and x[common].nunique() > 1:
                            r, p = scipy_stats.pearsonr(x[common], y[common])
                            correlaciones[idx_name] = (r, p)

                if correlaciones:
                    fig, ax = plt.subplots(figsize=(10, 5))
                    names = list(correlaciones.keys())
                    rs = [correlaciones[n][0] for n in names]
                    ps = [correlaciones[n][1] for n in names]
                    colors_bar = ['#e74c3c' if p < 0.05 else '#95a5a6'
                                  for p in ps]
                    bars = ax.bar(names, rs, color=colors_bar, edgecolor='white')
                    ax.axhline(0, color='black', linewidth=0.8)
                    ax.set_title('Correlación (r de Pearson) entre índices acústicos '
                                 'y molestia media\n(rojo = p<0.05)', fontsize=11)
                    ax.set_ylabel('r de Pearson')
                    ax.set_ylim(-1, 1)
                    ax.grid(axis='y', alpha=0.3)
                    for b, r_val in zip(bars, rs):
                        ax.text(b.get_x() + b.get_width()/2,
                                r_val + (0.03 if r_val >= 0 else -0.06),
                                f'{r_val:.2f}', ha='center', fontsize=8)
                    plt.tight_layout()
                    self._save(fig, 'maad_correlacion_molestia.png')

        # Guardar CSV con índices
        csv_out = self.output_dir / 'maad_indices.csv'
        df_maad.to_csv(csv_out, index=False)
        print(f'  CSV índices maad: {csv_out}')

    # ==========================================================================
    # GUARDAR INFORME TXT
    # ==========================================================================
    def guardar_resultados(self):
        old_stdout = sys.stdout
        sys.stdout = buf = StringIO()
        self.info_general()
        self.estadisticas_molestia()
        self.comparacion_referencia()
        self.estadisticas_fuentes()
        self.estadisticas_afectivas()
        sys.stdout = old_stdout
        out = self.output_dir / 'informe.txt'
        out.write_text(buf.getvalue(), encoding='utf-8')
        print(f'  Informe guardado: {out}')

    # ==========================================================================
    # RUN ALL
    # ==========================================================================
    def run_all(self):
        # Texto
        self.info_general()
        self.estadisticas_molestia()
        self.comparacion_referencia()
        self.estadisticas_fuentes()
        self.estadisticas_afectivas()

        # Gráficas
        print('\n' + '=' * 60)
        print('GENERANDO GRAFICAS')
        print('=' * 60)
        self.grafico_cronologia()
        self.grafico_radar_afectivas()
        self.grafico_molestia()
        self.grafico_comparacion_referencia()
        self.grafico_heatmap()
        self.grafico_afectivas()
        self.grafico_acustico_maad()

        # Informe
        self.guardar_resultados()
        print('\nAnalisis completado!')


# ==============================================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Análisis de resultados — Paisajes Sonoros')
    parser.add_argument('csv_path',
                        help='Ruta al CSV (ej: CSV/paisajes_sonoros.csv)')
    parser.add_argument('--audio-dir', default=None,
                        help='Carpeta con los .wav (ej: resources/audios)')
    args = parser.parse_args()

    analyzer = Analyzer(args.csv_path, audio_dir=args.audio_dir)
    analyzer.run_all()
