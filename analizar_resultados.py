import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from pathlib import Path
from scipy import stats as scipy_stats


class Analyzer:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        self.output_dir = Path(csv_path).parent / 'resultados'
        self.output_dir.mkdir(exist_ok=True)

        # Columnas afectivas
        self.afectivas = [
            'afectiva_agradable', 'afectiva_caotico', 'afectiva_estimulante',
            'afectiva_sinactividad', 'afectiva_calmado', 'afectiva_molesto',
            'afectiva_conactividad', 'afectiva_monotono'
        ]
        self.nombres_afectivas = [
            'Agradable', 'Caotico', 'Estimulante', 'Sin actividad',
            'Calmado', 'Molesto', 'Con actividad', 'Monotono'
        ]

        # DataFrame por participante (una fila por participante, con molestia_ref_before)
        if 'participante_id' in self.df.columns:
            self.df_part = self.df.drop_duplicates('participante_id').copy()
        else:
            self.df_part = self.df.drop_duplicates('timestamp_inicio').copy()

        # Asegurar tipos numericos
        self.df['molestia'] = pd.to_numeric(self.df['molestia'], errors='coerce')
        if 'molestia_ref_before' in self.df.columns:
            self.df['molestia_ref_before'] = pd.to_numeric(
                self.df['molestia_ref_before'], errors='coerce'
            )
            self.df_part['molestia_ref_before'] = pd.to_numeric(
                self.df_part['molestia_ref_before'], errors='coerce'
            )
        for col in self.afectivas:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

    # ------------------------------------------------------------------
    def _num_participantes(self):
        if 'participante_id' in self.df.columns:
            return self.df['participante_id'].nunique()
        return self.df['timestamp_inicio'].nunique()

    # ==================================================================
    # INFO GENERAL
    # ==================================================================
    def info_general(self):
        n = self._num_participantes()
        denom = n if n else 1
        print('=' * 60)
        print('INFORME GENERAL')
        print('=' * 60)
        print(f'Participantes:          {n}')
        print(f'Total de respuestas:    {len(self.df)}')
        print(f'Respuestas/participante:{len(self.df) / denom:.1f}')

        if 'molestia_ref_before' in self.df.columns:
            ref = self.df_part['molestia_ref_before'].dropna()
            if len(ref):
                print(f'\nMolestia audio referencia (media por participante): '
                      f'{ref.mean():.2f}  (std={ref.std():.2f}, '
                      f'min={ref.min():.0f}, max={ref.max():.0f})')

        print('\n--- Distribucion demografica ---')
        print('\nEdad:')
        print(self.df_part['edad'].value_counts().to_string())
        print('\nGenero:')
        print(self.df_part['genero'].value_counts().to_string())
        print('\nNivel de estudios:')
        print(self.df_part['estudios'].value_counts().to_string())

    # ==================================================================
    # MOLESTIA
    # ==================================================================
    def estadisticas_molestia(self):
        print()
        print('=' * 60)
        print('ESTADISTICAS DE MOLESTIA (0-10)')
        print('=' * 60)

        # --- Referencia ---
        if 'molestia_ref_before' in self.df.columns:
            ref = self.df_part['molestia_ref_before'].dropna()
            if len(ref):
                print('\n[Audio de referencia] (una puntuacion por participante)')
                print(ref.describe().round(2).to_string())

        # --- Audios del experimento ---
        print('\n[Audios del experimento] (18 respuestas por participante)')
        print(self.df['molestia'].describe().round(2).to_string())

        print('\n--- Por tipo de ruido ---')
        print(self.df.groupby('ruido')['molestia']
              .agg(['mean', 'std', 'min', 'max']).round(2).to_string())

        print('\n--- Por mensaje ---')
        print(self.df.groupby('mensaje')['molestia']
              .agg(['mean', 'std', 'min', 'max']).round(2).to_string())

        print('\n--- Por nivel ---')
        print(self.df.groupby('nivel')['molestia']
              .agg(['mean', 'std', 'min', 'max']).round(2).to_string())

        print('\n--- Por combinacion ruido x nivel ---')
        print(self.df.groupby(['ruido', 'nivel'])['molestia']
              .agg(['mean', 'std']).round(2).to_string())

        return self.df.groupby(['ruido', 'nivel'])['molestia'].mean().unstack()

    # ==================================================================
    # COMPARACION CON AUDIO DE REFERENCIA
    # ==================================================================
    def comparacion_referencia(self):
        if 'molestia_ref_before' not in self.df.columns:
            print('\n[AVISO] No existe columna molestia_ref_before en el CSV.')
            return

        ref_vals = self.df_part['molestia_ref_before'].dropna()
        if len(ref_vals) == 0:
            print('\n[AVISO] No hay datos de molestia_ref_before.')
            return

        print()
        print('=' * 60)
        print('COMPARACION CON AUDIO DE REFERENCIA')
        print('=' * 60)

        media_ref = ref_vals.mean()
        media_exp = self.df['molestia'].mean()
        print(f'\nMolestia media audio referencia : {media_ref:.2f}')
        print(f'Molestia media audios experimento: {media_exp:.2f}')
        print(f'Diferencia (exp - ref)           : {media_exp - media_ref:+.2f}')

        # Media de molestia por participante en los audios del experimento
        if 'participante_id' in self.df.columns:
            media_por_part = self.df.groupby('participante_id')['molestia'].mean()
        else:
            media_por_part = self.df.groupby('timestamp_inicio')['molestia'].mean()
        media_por_part.name = 'molestia_media_exp'

        # Unir con referencia
        df_comp = self.df_part.set_index(
            'participante_id' if 'participante_id' in self.df_part.columns else 'timestamp_inicio'
        )[['molestia_ref_before']].join(media_por_part)
        df_comp = df_comp.dropna()

        if len(df_comp) >= 3:
            # Correlacion de Pearson (solo si hay variabilidad en la referencia)
            if df_comp['molestia_ref_before'].nunique() > 1:
                r, p = scipy_stats.pearsonr(
                    df_comp['molestia_ref_before'], df_comp['molestia_media_exp']
                )
                print(f'\nCorrelacion Pearson (ref vs media experimento): r={r:.3f}, p={p:.4f}')
                if p < 0.05:
                    print('  -> Correlacion estadisticamente significativa (p<0.05)')
                else:
                    print('  -> Correlacion NO significativa con los datos actuales')
            else:
                print('\n[AVISO] Todos los participantes asignaron el mismo valor de '
                      'referencia; no es posible calcular correlacion de Pearson.')

            # T-test pareado: referencia vs media del experimento por participante
            t, p_t = scipy_stats.ttest_rel(
                df_comp['molestia_ref_before'], df_comp['molestia_media_exp']
            )
            print(f'\nT-test pareado (ref vs media experimento): t={t:.3f}, p={p_t:.4f}')
            if p_t < 0.05:
                print('  -> Diferencia estadisticamente significativa (p<0.05)')
            else:
                print('  -> Sin diferencia significativa con los datos actuales')
        else:
            print('\n[AVISO] Se necesitan al menos 3 participantes con datos completos '
                  'para calcular correlaciones.')

        # Por tipo de ruido: comparar molestia media vs referencia
        print('\n--- Molestia media por ruido vs. referencia ---')
        print(f'  Referencia: {media_ref:.2f}')
        for ruido, grupo in self.df.groupby('ruido'):
            m = grupo['molestia'].mean()
            print(f'  {ruido:<10}: {m:.2f}  (dif={m - media_ref:+.2f})')

        # Por nivel
        print('\n--- Molestia media por nivel vs. referencia ---')
        for nivel in ['low', 'equal', 'high']:
            grupo = self.df[self.df['nivel'] == nivel]
            if len(grupo):
                m = grupo['molestia'].mean()
                print(f'  {nivel:<8}: {m:.2f}  (dif={m - media_ref:+.2f})')

        return df_comp

    # ==================================================================
    # FUENTES SONORAS
    # ==================================================================
    def estadisticas_fuentes(self):
        print()
        print('=' * 60)
        print('ESTADISTICAS DE FUENTES SONORAS')
        print('=' * 60)
        from collections import Counter
        todas = []
        for f in self.df['fuentes']:
            if pd.notna(f):
                todas.extend([x.strip().strip('"') for x in str(f).split(';')])
        conteo = Counter(todas)
        n = len(self.df)
        print()
        for fuente, count in conteo.most_common():
            print(f'  {fuente:<12}: {count:>4}  ({count/n*100:.1f}%)')
        return conteo

    # ==================================================================
    # PERCEPCION AFECTIVA
    # ==================================================================
    def estadisticas_afectivas(self):
        print()
        print('=' * 60)
        print('ESTADISTICAS DE PERCEPCION AFECTIVA (1-5)')
        print('=' * 60)
        for af, nom in zip(self.afectivas, self.nombres_afectivas):
            s = self.df[af].describe()
            print(f'  {nom:<15}: media={s["mean"]:.2f}  std={s["std"]:.2f}  '
                  f'[{s["min"]:.0f}-{s["max"]:.0f}]')

        print('\n--- Por tipo de ruido ---')
        print(self.df.groupby('ruido')[self.afectivas].mean().round(2).to_string())
        return self.df.groupby('ruido')[self.afectivas].mean().round(2)

    # ==================================================================
    # GRAFICOS
    # ==================================================================
    def generar_graficos(self):
        print()
        print('=' * 60)
        print('GENERANDO GRAFICOS')
        print('=' * 60)
        self._grafico_resumen_molestia()
        self._grafico_referencia()
        self._grafico_heatmap()
        self._grafico_afectivas()
        plt.close('all')

    # ------------------------------------------------------------------
    def _grafico_resumen_molestia(self):
        fig, axes = plt.subplots(1, 3, figsize=(16, 5))

        # 1) Por ruido
        ax = axes[0]
        d = self.df.groupby('ruido')['molestia'].mean().sort_values(ascending=False)
        colores = ['#e74c3c', '#3498db', '#2ecc71']
        bars = ax.bar(d.index, d.values, color=colores[:len(d)])
        ax.set_title('Molestia media por ruido')
        ax.set_ylabel('Molestia (0-10)')
        ax.set_ylim(0, 10)
        for b, v in zip(bars, d.values):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.15,
                    f'{v:.2f}', ha='center', fontsize=9)
        # Linea de referencia si existe
        if 'molestia_ref_before' in self.df.columns:
            ref_mean = self.df_part['molestia_ref_before'].dropna().mean()
            if not np.isnan(ref_mean):
                ax.axhline(ref_mean, color='orange', linestyle='--', linewidth=1.5,
                           label=f'Ref: {ref_mean:.2f}')
                ax.legend(fontsize=8)

        # 2) Por nivel
        ax = axes[1]
        orden = ['low', 'equal', 'high']
        etiquetas = ['Low\n(-8 dB)', 'Equal\n(0 dB)', 'High\n(+8 dB)']
        d2 = self.df.groupby('nivel')['molestia'].mean().reindex(orden)
        bars2 = ax.bar(etiquetas, d2.values, color=['#27ae60', '#f39c12', '#c0392b'])
        ax.set_title('Molestia media por nivel')
        ax.set_ylabel('Molestia (0-10)')
        ax.set_ylim(0, 10)
        for b, v in zip(bars2, d2.values):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.15,
                    f'{v:.2f}', ha='center', fontsize=9)
        if 'molestia_ref_before' in self.df.columns:
            ref_mean = self.df_part['molestia_ref_before'].dropna().mean()
            if not np.isnan(ref_mean):
                ax.axhline(ref_mean, color='orange', linestyle='--', linewidth=1.5,
                           label=f'Ref: {ref_mean:.2f}')
                ax.legend(fontsize=8)

        # 3) Por mensaje
        ax = axes[2]
        d3 = self.df.groupby('mensaje')['molestia'].mean().sort_values(ascending=False)
        bars3 = ax.bar(d3.index, d3.values, color=['#8e44ad', '#16a085'])
        ax.set_title('Molestia media por mensaje')
        ax.set_ylabel('Molestia (0-10)')
        ax.set_ylim(0, 10)
        for b, v in zip(bars3, d3.values):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.15,
                    f'{v:.2f}', ha='center', fontsize=9)
        if 'molestia_ref_before' in self.df.columns:
            ref_mean = self.df_part['molestia_ref_before'].dropna().mean()
            if not np.isnan(ref_mean):
                ax.axhline(ref_mean, color='orange', linestyle='--', linewidth=1.5,
                           label=f'Ref: {ref_mean:.2f}')
                ax.legend(fontsize=8)

        plt.suptitle('Molestia media (linea naranja = audio referencia)', fontsize=12)
        plt.tight_layout()
        path = self.output_dir / 'molestia_resumen.png'
        plt.savefig(path, dpi=150)
        print(f'  Guardado: {path}')

    # ------------------------------------------------------------------
    def _grafico_referencia(self):
        if 'molestia_ref_before' not in self.df.columns:
            return
        ref_vals = self.df_part['molestia_ref_before'].dropna()
        if len(ref_vals) == 0:
            return

        has_multi = len(ref_vals) >= 2

        if has_multi:
            fig, axes = plt.subplots(1, 3, figsize=(16, 5))
        else:
            fig, axes = plt.subplots(1, 2, figsize=(11, 5))

        # --- Panel 1: Referencia vs media experimento por ruido ---
        ax = axes[0]
        ruidos = ['road', 'voices', 'nature']
        etiquetas_ruido = ['Trafico', 'Voces', 'Naturaleza']
        medias_exp = [
            self.df[self.df['ruido'] == r]['molestia'].mean() for r in ruidos
        ]
        ref_mean = ref_vals.mean()
        x = np.arange(len(ruidos))
        w = 0.35
        bars_exp = ax.bar(x, medias_exp, w, label='Experimento', color='#3498db')
        ax.axhline(ref_mean, color='orange', linestyle='--', linewidth=2,
                   label=f'Referencia ({ref_mean:.2f})')
        ax.set_xticks(x)
        ax.set_xticklabels(etiquetas_ruido)
        ax.set_title('Molestia por ruido vs. referencia')
        ax.set_ylabel('Molestia (0-10)')
        ax.set_ylim(0, 10)
        ax.legend(fontsize=8)
        for b, v in zip(bars_exp, medias_exp):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.15,
                    f'{v:.2f}', ha='center', fontsize=9)

        # --- Panel 2: Referencia vs media experimento por nivel ---
        ax = axes[1]
        niveles = ['low', 'equal', 'high']
        etiquetas_nivel = ['Low\n(-8dB)', 'Equal', 'High\n(+8dB)']
        medias_nivel = [
            self.df[self.df['nivel'] == n]['molestia'].mean() for n in niveles
        ]
        bars_niv = ax.bar(np.arange(3), medias_nivel, color='#2ecc71')
        ax.axhline(ref_mean, color='orange', linestyle='--', linewidth=2,
                   label=f'Referencia ({ref_mean:.2f})')
        ax.set_xticks(np.arange(3))
        ax.set_xticklabels(etiquetas_nivel)
        ax.set_title('Molestia por nivel vs. referencia')
        ax.set_ylabel('Molestia (0-10)')
        ax.set_ylim(0, 10)
        ax.legend(fontsize=8)
        for b, v in zip(bars_niv, medias_nivel):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.15,
                    f'{v:.2f}', ha='center', fontsize=9)

        # --- Panel 3: Scatter referencia individual vs media experimento ---
        if has_multi:
            ax = axes[2]
            if 'participante_id' in self.df.columns:
                media_por_part = self.df.groupby('participante_id')['molestia'].mean()
                df_comp = self.df_part.set_index('participante_id')[
                    ['molestia_ref_before']
                ].join(media_por_part)
            else:
                media_por_part = self.df.groupby('timestamp_inicio')['molestia'].mean()
                df_comp = self.df_part.set_index('timestamp_inicio')[
                    ['molestia_ref_before']
                ].join(media_por_part)
            df_comp = df_comp.dropna()

            ax.scatter(df_comp['molestia_ref_before'], df_comp['molestia'],
                       color='#8e44ad', s=80, zorder=3)
            # Linea diagonal de identidad
            lim_max = 10
            ax.plot([0, lim_max], [0, lim_max], 'k--', linewidth=1,
                    alpha=0.4, label='y = x')
            # Regresion lineal si hay suficientes puntos
            if len(df_comp) >= 3 and df_comp['molestia_ref_before'].nunique() > 1:
                m, b, r, p, _ = scipy_stats.linregress(
                    df_comp['molestia_ref_before'], df_comp['molestia']
                )
                xs = np.linspace(df_comp['molestia_ref_before'].min(),
                                 df_comp['molestia_ref_before'].max(), 50)
                ax.plot(xs, m*xs + b, color='red', linewidth=1.5,
                        label=f'Regresion (r={r:.2f}, p={p:.3f})')
            ax.set_xlabel('Molestia referencia (por participante)')
            ax.set_ylabel('Molestia media experimento (por participante)')
            ax.set_title('Correlacion: referencia vs experimento')
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 10)
            ax.legend(fontsize=8)

        plt.suptitle('Comparacion molestia: audio de referencia vs. experimento',
                     fontsize=12)
        plt.tight_layout()
        path = self.output_dir / 'comparacion_referencia.png'
        plt.savefig(path, dpi=150)
        print(f'  Guardado: {path}')

    # ------------------------------------------------------------------
    def _grafico_heatmap(self):
        fig, ax = plt.subplots(figsize=(8, 5))
        pivot = self.df.groupby(['ruido', 'nivel'])['molestia'].mean().unstack()
        pivot = pivot.reindex(index=['road', 'voices', 'nature'],
                              columns=['low', 'equal', 'high'])
        im = ax.imshow(pivot.values, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=10)
        ax.set_xticks(range(3))
        ax.set_xticklabels(['Low (-8dB)', 'Equal (0dB)', 'High (+8dB)'])
        ax.set_yticks(range(3))
        ax.set_yticklabels(['Trafico', 'Voces', 'Naturaleza'])
        ax.set_title('Mapa de calor: Molestia media por combinacion ruido x nivel')
        plt.colorbar(im, ax=ax, label='Molestia (0-10)')
        for i in range(3):
            for j in range(3):
                v = pivot.values[i, j]
                if not np.isnan(v):
                    ax.text(j, i, f'{v:.2f}', ha='center', va='center',
                            color='black', fontsize=11, fontweight='bold')
        plt.tight_layout()
        path = self.output_dir / 'heatmap_molestia.png'
        plt.savefig(path, dpi=150)
        print(f'  Guardado: {path}')

    # ------------------------------------------------------------------
    def _grafico_afectivas(self):
        # Figura 1: barras medias globales
        fig, ax = plt.subplots(figsize=(12, 5))
        medias = self.df[self.afectivas].mean()
        colors = ['#9b59b6', '#e67e22', '#1abc9c', '#95a5a6',
                  '#34495e', '#e74c3c', '#3498db', '#7f8c8d']
        bars = ax.bar(self.nombres_afectivas, medias.values, color=colors)
        ax.axhline(3, color='red', linestyle='--', alpha=0.5, label='Neutral (3)')
        ax.set_title('Percepcion afectiva media (escala 1-5)')
        ax.set_ylabel('Puntuacion media')
        ax.set_ylim(0, 5)
        ax.legend()
        for b, v in zip(bars, medias.values):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.05,
                    f'{v:.2f}', ha='center', fontsize=8)
        plt.tight_layout()
        path = self.output_dir / 'afectivas_global.png'
        plt.savefig(path, dpi=150)
        print(f'  Guardado: {path}')

        # Figura 2: por tipo de ruido (2x4 subplots)
        fig, axes = plt.subplots(2, 4, figsize=(18, 8))
        for idx, (af, nom) in enumerate(zip(self.afectivas, self.nombres_afectivas)):
            r, c = idx // 4, idx % 4
            ax = axes[r, c]
            d = self.df.groupby('ruido')[af].mean().reindex(['road', 'voices', 'nature'])
            etq = ['Trafico', 'Voces', 'Naturaleza']
            bars = ax.bar(etq, d.values, color=['#e74c3c', '#3498db', '#2ecc71'])
            ax.axhline(3, color='red', linestyle='--', alpha=0.4, linewidth=0.8)
            ax.set_title(nom, fontsize=10)
            ax.set_ylabel('Media (1-5)', fontsize=8)
            ax.set_ylim(0, 5)
            ax.tick_params(axis='x', labelsize=8)
            for b, v in zip(bars, d.values):
                if not np.isnan(v):
                    ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.05,
                            f'{v:.2f}', ha='center', fontsize=7)
        plt.suptitle('Percepcion afectiva por tipo de ruido', fontsize=12)
        plt.tight_layout()
        path = self.output_dir / 'afectivas_por_ruido.png'
        plt.savefig(path, dpi=150)
        print(f'  Guardado: {path}')

    # ==================================================================
    # GUARDAR INFORME TXT
    # ==================================================================
    def guardar_resultados(self):
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = buf = StringIO()
        self.info_general()
        self.estadisticas_molestia()
        self.comparacion_referencia()
        self.estadisticas_fuentes()
        self.estadisticas_afectivas()
        sys.stdout = old_stdout
        output_file = self.output_dir / 'informe.txt'
        output_file.write_text(buf.getvalue(), encoding='utf-8')
        print(f'  Informe guardado: {output_file}')

    # ==================================================================
    # RUN ALL
    # ==================================================================
    def run_all(self):
        self.info_general()
        self.estadisticas_molestia()
        self.comparacion_referencia()
        self.estadisticas_fuentes()
        self.estadisticas_afectivas()
        self.generar_graficos()
        self.guardar_resultados()
        print()
        print('Analisis completado!')


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Uso: python analizar_resultados.py <ruta_al_csv>')
        print('Ejemplo: python analizar_resultados.py CSV/paisajes_sonoros.csv')
        sys.exit(1)
    analyzer = Analyzer(sys.argv[1])
    analyzer.run_all()
