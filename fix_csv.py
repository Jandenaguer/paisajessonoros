import csv

csv_path = r'K:\Universidad\TFG\paisajessonoros\CSV\paisajes_sonoros.csv'

headers = [
    'participante_id','timestamp_inicio','timestamp_respuesta','timestamp_fin',
    'edad','genero','estudios','audicion','castellano',
    'audio_index','audio_filename','mensaje','ruido','nivel',
    'molestia','molestia_ref_before','fuentes',
    'afectiva_agradable','afectiva_caotico','afectiva_estimulante',
    'afectiva_sinactividad','afectiva_calmado','afectiva_molesto',
    'afectiva_conactividad','afectiva_monotono'
]

def q(v):
    return f'"{v}"'

data = [
    [1,'2026-05-06T16:30:55.651Z','2026-05-06T16:31:15.387Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',1,'mensaje1_road_equal_hrtf.wav','mensaje1','road','equal',7,'',q('trafico'),4,3,4,4,4,4,4,4],
    [2,'2026-05-06T16:30:55.651Z','2026-05-06T16:31:25.060Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',2,'mensaje1_road_low_hrtf.wav','mensaje1','road','low',5,'',q('trafico'),3,3,3,3,3,3,3,3],
    [3,'2026-05-06T16:30:55.651Z','2026-05-06T16:31:59.944Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',3,'mensaje1_road_high_hrtf.wav','mensaje1','road','high',8,'',q('humano'),2,2,2,2,2,2,2,2],
    [4,'2026-05-06T16:30:55.651Z','2026-05-06T16:32:08.059Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',4,'mensaje1_voices_equal_hrtf.wav','mensaje1','voices','equal',7,'',q('trafico;natural'),2,2,2,2,2,2,2,2],
    [5,'2026-05-06T16:30:55.651Z','2026-05-06T16:32:18.261Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',5,'mensaje1_voices_low_hrtf.wav','mensaje1','voices','low',5,'',q('humano'),3,3,3,3,3,3,3,3],
    [6,'2026-05-06T16:30:55.651Z','2026-05-06T16:32:27.552Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',6,'mensaje1_voices_high_hrtf.wav','mensaje1','voices','high',4,'',q('trafico'),4,4,4,4,4,4,4,4],
    [7,'2026-05-06T16:30:55.651Z','2026-05-06T16:32:39.661Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',7,'mensaje1_nature_equal_hrtf.wav','mensaje1','nature','equal',6,'',q('natural'),1,2,3,4,5,4,3,2],
    [8,'2026-05-06T16:30:55.651Z','2026-05-06T16:32:46.624Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',8,'mensaje1_nature_low_hrtf.wav','mensaje1','nature','low',5,'',q('trafico'),2,2,2,2,2,2,2,2],
    [9,'2026-05-06T16:30:55.651Z','2026-05-06T16:32:53.439Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',9,'mensaje1_nature_high_hrtf.wav','mensaje1','nature','high',8,'',q('trafico'),4,4,4,4,3,3,3,2],
    [10,'2026-05-06T16:30:55.651Z','2026-05-06T16:33:03.978Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',10,'mensaje2_road_equal_hrtf.wav','mensaje2','road','equal',5,'',q('trafico'),3,3,2,2,2,3,2,1],
    [11,'2026-05-06T16:30:55.651Z','2026-05-06T16:33:12.324Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',11,'mensaje2_road_low_hrtf.wav','mensaje2','road','low',6,'',q('trafico'),5,5,5,4,4,4,5,5],
    [12,'2026-05-06T16:30:55.651Z','2026-05-06T16:33:22.801Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',12,'mensaje2_road_high_hrtf.wav','mensaje2','road','high',4,'',q('trafico'),2,3,3,4,4,5,5,5],
    [13,'2026-05-06T16:30:55.651Z','2026-05-06T16:33:30.561Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',13,'mensaje2_voices_equal_hrtf.wav','mensaje2','voices','equal',7,'',q('humano'),4,3,4,3,4,3,4,5],
    [14,'2026-05-06T16:30:55.651Z','2026-05-06T16:33:40.727Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',14,'mensaje2_voices_low_hrtf.wav','mensaje2','voices','low',7,'',q('trafico'),5,5,5,5,5,5,5,5],
    [15,'2026-05-06T16:30:55.651Z','2026-05-06T16:33:49.584Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',15,'mensaje2_voices_high_hrtf.wav','mensaje2','voices','high',6,'',q('humano'),3,4,3,4,3,4,3,2],
    [16,'2026-05-06T16:30:55.651Z','2026-05-06T16:33:58.108Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',16,'mensaje2_nature_equal_hrtf.wav','mensaje2','nature','equal',6,'',q('trafico'),1,2,2,2,3,3,3,2],
    [17,'2026-05-06T16:30:55.651Z','2026-05-06T16:34:08.666Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',17,'mensaje2_nature_low_hrtf.wav','mensaje2','nature','low',5,'',q('trafico'),2,2,2,2,2,2,2,2],
    [18,'2026-05-06T16:30:55.651Z','2026-05-06T16:34:16.422Z','2026-05-06T16:34:16.422Z','18-25','Masculino','Bachillerato','No','Si',18,'mensaje2_nature_high_hrtf.wav','mensaje2','nature','high',7,'',q('natural'),3,3,3,3,3,3,3,3],
    [19,'2026-05-06T16:34:56.203Z','2026-05-06T16:35:21.453Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',1,'mensaje1_road_equal_hrtf.wav','mensaje1','road','equal',7,'',q('trafico'),1,1,1,2,2,2,2,3],
    [20,'2026-05-06T16:34:56.203Z','2026-05-06T16:35:29.658Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',2,'mensaje1_road_low_hrtf.wav','mensaje1','road','low',7,'',q('natural'),4,4,4,4,4,4,4,4],
    [21,'2026-05-06T16:34:56.203Z','2026-05-06T16:40:01.825Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',3,'mensaje1_road_high_hrtf.wav','mensaje1','road','high',5,'',q('trafico'),4,4,4,4,4,4,4,4],
    [22,'2026-05-06T16:34:56.203Z','2026-05-06T16:40:11.245Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',4,'mensaje1_voices_equal_hrtf.wav','mensaje1','voices','equal',6,'',q('trafico'),3,3,3,2,3,4,3,2],
    [23,'2026-05-06T16:34:56.203Z','2026-05-06T16:40:21.780Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',5,'mensaje1_voices_low_hrtf.wav','mensaje1','voices','low',6,'',q('natural'),3,2,3,2,3,2,3,2],
    [24,'2026-05-06T16:34:56.203Z','2026-05-06T16:40:36.052Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',6,'mensaje1_voices_high_hrtf.wav','mensaje1','voices','high',9,'',q('natural'),2,2,2,2,2,2,2,5],
    [25,'2026-05-06T16:34:56.203Z','2026-05-06T16:40:45.789Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',7,'mensaje1_nature_equal_hrtf.wav','mensaje1','nature','equal',6,'',q('humano'),3,3,3,3,3,3,3,3],
    [26,'2026-05-06T16:34:56.203Z','2026-05-06T16:40:56.132Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',8,'mensaje1_nature_low_hrtf.wav','mensaje1','nature','low',5,'',q('trafico'),3,3,3,2,3,4,3,2],
    [27,'2026-05-06T16:34:56.203Z','2026-05-06T16:41:05.985Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',9,'mensaje1_nature_high_hrtf.wav','mensaje1','nature','high',8,'',q('humano'),3,3,3,3,2,3,2,2],
    [28,'2026-05-06T16:34:56.203Z','2026-05-06T16:41:13.061Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',10,'mensaje2_road_equal_hrtf.wav','mensaje2','road','equal',7,'',q('natural'),2,2,2,2,2,2,2,2],
    [29,'2026-05-06T16:34:56.203Z','2026-05-06T16:41:20.333Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',11,'mensaje2_road_low_hrtf.wav','mensaje2','road','low',5,'',q('humano'),5,5,5,5,5,5,4,3],
    [30,'2026-05-06T16:34:56.203Z','2026-05-06T16:41:26.335Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',12,'mensaje2_road_high_hrtf.wav','mensaje2','road','high',5,'',q('trafico'),3,3,3,3,3,3,3,2],
    [31,'2026-05-06T16:34:56.203Z','2026-05-06T16:41:34.075Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',13,'mensaje2_voices_equal_hrtf.wav','mensaje2','voices','equal',5,'',q('trafico'),3,3,3,3,3,3,3,3],
    [32,'2026-05-06T16:34:56.203Z','2026-05-06T16:41:41.851Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',14,'mensaje2_voices_low_hrtf.wav','mensaje2','voices','low',7,'',q('humano'),3,3,2,3,4,3,2,2],
    [33,'2026-05-06T16:34:56.203Z','2026-05-06T16:41:50.144Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',15,'mensaje2_voices_high_hrtf.wav','mensaje2','voices','high',8,'',q('trafico'),3,2,2,2,2,2,3,3],
    [34,'2026-05-06T16:34:56.203Z','2026-05-06T16:42:00.256Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',16,'mensaje2_nature_equal_hrtf.wav','mensaje2','nature','equal',10,'',q('humano'),1,2,2,2,2,3,3,3],
    [35,'2026-05-06T16:34:56.203Z','2026-05-06T16:42:07.222Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',17,'mensaje2_nature_low_hrtf.wav','mensaje2','nature','low',7,'',q('natural'),5,4,5,4,5,4,5,4],
    [36,'2026-05-06T16:34:56.203Z','2026-05-06T16:42:16.854Z','2026-05-06T16:42:16.854Z','35-45','Femenino','Formacion_Profesional','No','Si',18,'mensaje2_nature_high_hrtf.wav','mensaje2','nature','high',7,'',q('humano'),4,4,4,4,4,4,4,3],
]

with open(csv_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    for row in data:
        writer.writerow(row)

print(f'CSV written: {csv_path}')
print(f'Header cols: {len(headers)}')

# Verify
with open(csv_path, 'r') as f:
    lines = f.readlines()
print(f'Total lines: {len(lines)}')
print(f'Header: {lines[0].strip()[:120]}...')
print(f'First data line cols: {len(lines[1].split(","))}')
