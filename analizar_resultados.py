import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

class Analyzer:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        self.output_dir = Path(csv_path).parent / 'resultados'
        self.output_dir.mkdir(exist_ok=True)
        
    def info_general(self):
        print("=" * 60)
        print("INFORME GENERAL")
        print("=" * 60)
        print(f"Número de participantes: {self.df['participante_id'].nunique()}")
        print(f"Número total de respuestas: {len(self.df)}")
        print(f"Respuestas por participante: {len(self.df) / self.df['participante_id'].nunique():.1f}")
        
        print("\n--- Distribución demográfica ---")
        print("\nEdad:")
        print(self.df['edad'].value_counts())
        print("\nGénero:")
        print(self.df['genero'].value_counts())
        print("\nNivel de estudios:")
        print(self.df['estudios'].value_counts())
        
    def estadisticas_molestia(self):
        print("\n" + "=" * 60)
        print("ESTADÍSTICAS DE MOLESTIA (0-10)")
        print("=" * 60)
        
        stats = self.df['molestia'].astype(int).describe()
        print(stats)
        
        print("\n--- Por tipo de ruido ---")
        ruido_stats = self.df.groupby('ruido')['molestia'].agg(['mean', 'std', 'min', 'max'])
        print(ruido_stats)
        
        print("\n--- Por mensaje ---")
        mensaje_stats = self.df.groupby('mensaje')['molestia'].agg(['mean', 'std', 'min', 'max'])
        print(mensaje_stats)
        
        print("\n--- Por nivel ---")
        nivel_stats = self.df.groupby('nivel')['molestia'].agg(['mean', 'std', 'min', 'max'])
        print(nivel_stats)
        
        print("\n--- Por combinación ruido x nivel ---")
        combinacion = self.df.groupby(['ruido', 'nivel'])['molestia'].agg(['mean', 'std']).round(2)
        print(combinacion)
        
        return self.df.groupby(['ruido', 'nivel'])['molestia'].mean().unstack()
        
    def estadisticas_fuentes(self):
        print("\n" + "=" * 60)
        print("ESTADÍSTICAS DE FUENTES SONORAS")
        print("=" * 60)
        
        todas_fuentes = []
        for f in self.df['fuentes']:
            if pd.notna(f):
                fuentes = [x.strip() for x in str(f).split(';')]
                todas_fuentes.extend(fuentes)
        
        from collections import Counter
        conteo = Counter(todas_fuentes)
        print("\nFrecuencia de detección de fuentes:")
        for fuente, count in conteo.most_common():
            pct = count / len(self.df) * 100
            print(f"  {fuente}: {count} ({pct:.1f}%)")
            
        return conteo
        
    def estadisticas_afectivas(self):
        print("\n" + "=" * 60)
        print("ESTADÍSTICAS DE PERCEPCIÓN AFECTIVA (1-5)")
        print("=" * 60)
        
        afectivas = ['afectiva_agradable', 'afectiva_caotico', 'afectiva_estimulante', 
                     'afectiva_sinactividad', 'afectiva_calmado', 'afectiva_molesto',
                     'afectiva_conactividad', 'afectiva_monotono']
        
        for af in afectivas:
            nombre = af.replace('afectiva_', '').capitalize()
            stats = self.df[af].astype(int).describe()
            print(f"\n{nombre}:")
            print(f"  Media: {stats['mean']:.2f}")
            print(f"  Std: {stats['std']:.2f}")
            print(f"  Mín: {stats['min']:.0f}, Máx: {stats['max']:.0f}")
            
        print("\n--- Por tipo de ruido ---")
        afectivas_ruido = self.df.groupby('ruido')[afectivas].mean().round(2)
        print(afectivas_ruido)
        
        return afectivas_ruido
        
    def generar_graficos(self):
        print("\n" + "=" * 60)
        print("GENERANDO GRÁFICOS")
        print("=" * 60)
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        ax1 = axes[0, 0]
        molestia_ruido = self.df.groupby('ruido')['molestia'].mean().sort_values(ascending=False)
        bars1 = ax1.bar(molestia_ruido.index, molestia_ruido.values, color=['#e74c3c', '#3498db', '#2ecc71'])
        ax1.set_title('Molestia media por tipo de ruido')
        ax1.set_ylabel('Molestia (0-10)')
        ax1.set_ylim(0, 10)
        for bar, val in zip(bars1, molestia_ruido.values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, f'{val:.2f}', ha='center')
            
        ax2 = axes[0, 1]
        molestia_nivel = self.df.groupby('nivel')['molestia'].mean()
        orden_nivel = ['low', 'equal', 'high']
        molestia_nivel = molestia_nivel.reindex(orden_nivel)
        bars2 = ax2.bar(molestia_nivel.index, molestia_nivel.values, color=['#27ae60', '#f39c12', '#c0392b'])
        ax2.set_title('Molestia media por nivel')
        ax2.set_ylabel('Molestia (0-10)')
        ax2.set_ylim(0, 10)
        for bar, val in zip(bars2, molestia_nivel.values):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, f'{val:.2f}', ha='center')
            
        ax3 = axes[1, 0]
        molestia_combinacion = self.df.groupby(['ruido', 'nivel'])['molestia'].mean().unstack()
        molestia_combinacion = molestia_combinacion.reindex(columns=['low', 'equal', 'high'])
        molestia_combinacion.plot(kind='bar', ax=ax3, colormap='viridis')
        ax3.set_title('Molestia: Ruido x Nivel')
        ax3.set_ylabel('Molestia (0-10)')
        ax3.set_ylim(0, 10)
        ax3.legend(title='Nivel')
        ax3.set_xticklabels(ax3.get_xticklabels(), rotation=0)
        
        ax4 = axes[1, 1]
        afectivas = ['afectiva_agradable', 'afectiva_caotico', 'afectiva_estimulante', 
                     'afectiva_sinactividad', 'afectiva_calmado', 'afectiva_molesto',
                     'afectiva_conactividad', 'afectiva_monotono']
        nombres = ['Agradable', 'Caótico', 'Estimulante', 'Sin act.', 'Calmado', 'Molesto', 'Con act.', 'Monótono']
        media_afectivas = self.df[afectivas].mean()
        bars4 = ax4.bar(nombres, media_afectivas.values, color=['#9b59b6', '#e67e22', '#1abc9c', '#95a5a6', '#34495e', '#e74c3c', '#3498db', '#7f8c8d'])
        ax4.set_title('Percepción afectiva media')
        ax4.set_ylabel('Puntuación (1-5)')
        ax4.set_ylim(0, 5)
        ax4.axhline(y=3, color='red', linestyle='--', alpha=0.5, label='Neutral')
        for bar, val in zip(bars4, media_afectivas.values):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, f'{val:.2f}', ha='center')
            
        plt.tight_layout()
        plt.savefig(self.output_dir / 'resumen_general.png', dpi=150)
        print(f"Guardado: {self.output_dir / 'resumen_general.png'}")
        
        fig2, ax = plt.subplots(figsize=(10, 6))
        molestia_heatmap = self.df.groupby(['ruido', 'nivel'])['molestia'].mean().unstack()
        molestia_heatmap = molestia_heatmap.reindex(index=['road', 'voices', 'nature'], columns=['low', 'equal', 'high'])
        im = ax.imshow(molestia_heatmap.values, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=10)
        ax.set_xticks(range(3))
        ax.set_xticklabels(['Low (-8dB)', 'Equal', 'High (+8dB)'])
        ax.set_yticks(range(3))
        ax.set_yticklabels(['Tráfico', 'Voces', 'Naturaleza'])
        ax.set_title('Mapa de calor: Molestia media por combinación')
        plt.colorbar(im, ax=ax, label='Molestia')
        for i in range(3):
            for j in range(3):
                text = ax.text(j, i, f'{molestia_heatmap.values[i, j]:.1f}',
                               ha="center", va="center", color="black", fontsize=12)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'heatmap_molestia.png', dpi=150)
        print(f"Guardado: {self.output_dir / 'heatmap_molestia.png'}")
        
        fig3, axes3 = plt.subplots(2, 4, figsize=(16, 8))
        afectivas = ['afectiva_agradable', 'afectiva_caotico', 'afectiva_estimulante', 
                     'afectiva_sinactividad', 'afectiva_calmado', 'afectiva_molesto',
                     'afectiva_conactividad', 'afectiva_monotono']
        nombres = ['Agradable', 'Caótico', 'Estimulante', 'Sin act.', 'Calmado', 'Molesto', 'Con act.', 'Monótono']
        for idx, (af, nom) in enumerate(zip(afectivas, nombres)):
            row = idx // 4
            col = idx % 4
            media_ruido = self.df.groupby('ruido')[af].mean()
            axes3[row, col].bar(media_ruido.index, media_ruido.values, color=['#e74c3c', '#3498db', '#2ecc71'])
            axes3[row, col].set_title(f'{nom}')
            axes3[row, col].set_ylabel('Media (1-5)')
            axes3[row, col].set_ylim(0, 5)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'afectivas_por_ruido.png', dpi=150)
        print(f"Guardado: {self.output_dir / 'afectivas_por_ruido.png'}")
        
        plt.close('all')
        
    def guardar_resultados(self):
        output_file = self.output_dir / 'informe.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            import sys
            from io import StringIO
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            self.info_general()
            self.estadisticas_molestia()
            self.estadisticas_fuentes()
            self.estadisticas_afectivas()
            
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            f.write(output)
            print(f"Informe guardado: {output_file}")
            
    def run_all(self):
        self.info_general()
        self.estadisticas_molestia()
        self.estadisticas_fuentes()
        self.estadisticas_afectivas()
        self.generar_graficos()
        self.guardar_resultados()
        print("\nAnálisis completado!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python analizar_resultados.py <ruta_al_csv>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    analyzer = Analyzer(csv_path)
    analyzer.run_all()