
# Optimización de la Conversión CNF a dDNNF: Técnicas de Vivificación y Backbone

## Descripción

Este repositorio contiene el código y los resultados del proyecto sobre **optimización de la conversión de CNF a dDNNF** mediante técnicas de **vivificación y backbone**. Estas técnicas están diseñadas para mejorar el rendimiento en la transformación de fórmulas lógicas, proporcionando CNFs más eficientes para su uso en sistemas complejos y configurables.

## Estructura del Proyecto

```bash
TFM_Project/
|
|–– data/
|   |–– 2023SAT_Competition_MCtrack1/    # Ejemplos de la competencia SAT 2023
|   |–– CNF_EXAMPLES/                    # Ejemplos en formato CNF
|   |–– ComplexConfigurableModels/       # Modelos de sistemas configurables
|   \–– SAT_RESULTS/                     # Resultados de ejecuciones
|
|–– scripts/
|   └── SAT.py                           # Script principal para la obtención de resultados
|
|–– programs/
|   |–– c2d/                             # Compilador para DNNF
|   |–– COMSPS+/                         # Solver SAT paralelo
|   |–– d4/                              # Compilador eficiente para dDNNF
|   |–– dDNNFreasoner/                   # Herramienta de consultas booleanas dDNNF
|   |–– Glucose+/                        # Solver SAT basado en CDCL
|   |–– Maple+/                          # Solver SAT con técnicas de aprendizaje
|   |–– MapleLRB+/                       # Solver SAT con restarts adaptativos
|   |–– pmc/                             # Compilador para conteo de modelos
|   \–– backbone/                        # Herramienta para el backbone en SAT
|
|–– requirements.txt                     # Lista de dependencias para instalar
└── README.md                            # Este archivo
```

## Instalación

### Requisitos

Antes de ejecutar el proyecto, asegúrate de instalar los requisitos indicados en requirements.txt.
Estos requisitos incluyen:

- Dependencias para compilar los SAT solvers
- Dependencias para ejecutar la solución en Python3
- Soporte para arquitecturas de 32 bits para c2d
- Dependecias de d4

### Instrucciones

1. Clona el repositorio:

   ```bash
   git clone https://github.com/victoref/cnf2ddnnfTechniques.git
   ```

2. Navega al directorio del proyecto:

   ```bash
   cd cnf2ddnnfTechniques/scripts
   ```

3. Ejecuta el preprocesamiento de una fórmula CNF de ejemplo con vivificación y backbone:

   ```bash
   python3 SAT.py --solver pmc --example CNF_EXAMPLES/busybox_fernandez22.dimacs --vivification --backbone
   ```

## Uso

Este proyecto permite ejecutar transformaciones de CNF a dDNNF utilizando las técnicas de **vivificación** y **backbone** de forma individual o combinada. Puedes ejecutar las siguientes combinaciones de comandos para obtener diferentes resultados:

```bash
# Usar vivificación y backbone con un ejemplo CNF
python3 SAT.py --solver maple --example CNF_EXAMPLES/mc2023_track1_008.cnf --vivification --backbone
```

Las opciones del script son las siguientes:

- `--solver` o `-s`: Especifica el solver SAT (e.g., `pmc`, `glucose+`, `maple`).
- `--example` o `-e`: Especifica el archivo CNF a utilizar.
- `--backbone` o `-b`: Aplica la técnica de backbone.
- `--vivification` o `-v`: Aplica la técnica de vivificación.

En caso de disponer de parallel, el script puede ser ejecutado de la siguiente manera:

```bash
nohup parallel --jobs 1 python3 SAT.py -s {1} -e {2} -v -b ::: pmc maple mapleLRB glucose+ comsps ::: mc2023_track1_008.cnf 2.6.32-2var_oh20.dimacs &
```

## Resultados


El script genera los siguientes cuatro ficheros clave:

1. **Fichero `.log`**: Contiene una línea en formato CSV con los valores de todas las métricas extraídas.
Su nombre es "<nombreSATSolver>_<PID>_<Ejemplo>_<Fecha(YYY-MMDD_hhmmss).log"

SATsolver;Example;Vivification;Backbone;#vars OGCNF;#clau OGCNF;OGCNF worlds;Vivify-Time;Backbone-Time;#vars VIVCNF;#clau PRECNF;PRECNF worlds;Same worlds;OGCNF2dDNNF Time;PRECNF2dDNNF Time;OGdDNNF worlds;PREdDNNF worlds;

   ```plaintext
   pmc;mc2023_track1_008.cnf;1;2;6856;27626;171798691840;0,192401;0,180000;6856;11750;171798691840;TRUE;66,792;20,693;171798691840;171798691840;TRUE;
   ```

2. **CNF preprocesada**: Archivo con el resultado de aplicar las técnicas de preprocesamiento en formato DIMACS.
Su nombre es "prepro_<nombreSATSolver>_<PID>_<Ejemplo>"

   ```plaintext
   p cnf 6856 11750
   c Problem Statistics
   c Number of variables: 6856
   c Number of clauses: 26533
   c Parse time (sec.) : 0.00
   c
   -1 0
   <...>
   153 -465 0
   -464 153 0
   c restarts : 21
   c decisions : 17287 (0.00 % random)
   c CPU time (sec.): 0.192401
   ```

3. **dDNNF original**: Contiene el resultado de transformar la CNF original.
Su nombre es "<PID>_<Ejemplo>.nnf"


   ```plaintext
   nnf 11381 104485 6856
   L 61
   L 62
   ...
   A 2 11376 11377
   A 325 3317 3318 3319 3320 3321 3322 3323 3324 3325 3326 3327 3328 3329
   3344 3345 3346 3347 3348 3349 3350 3351 3352 3353 3354 3355 3356 3357
   <...>
   5426 5450 5451 5513 5514 5557 5558 5620 5621 5664 5665 5689 5690 5714
   A 2 11378 11379
   ```


4. **dDNNF resultante**: Resultado de transformar la CNF preprocesada a dDNNF.
Su nombre es "prepro_<nombreSATSolver>_<PID>_<Ejemplo>.nnf"

   ```plaintext
   nnf 11286 59629 6856
   L 61
   L 62
   ...
   A 4003 3317 3318 3319 3320 3321 3322 3323 3324 3325 3326 3327 3328 3329
   3330 3331 3332 3333 3334 3335 3336 3337 3338 3339 3340 3341 3342 3343
   <...>
   7128 7129 7130 7131 7132 7133 7134 7135 7136 7137 7138 7139 7140 7142
   7144 7146 7149 7150 7
   A 2 11283 11284
   ```

Estos resultados y métricas permiten medir y comparar las técnicas entre sí, la diferencia entre aplicarlas o no y si tiene importancia el orden de aplicación.
Todo esto se puede agrupar en tablas y gráficas que permiten su visualización de forma más cómoda y extraer gran cantidad de información de las mismas.
Algunos ejemplos son los tiempos que tardan las diferentes técnicas en transformar CNF a dDNNF, o la tendencia a aumentar en tiempo según el número de variables.

<p align="center">
<img src="data/readmeFigures/Figure_1.png" alt="Tabla de resultados" width="700">
<img src="data/readmeFigures/Figure_2.png" alt="Tabla de resultados" width="700">
</p>

## Amenazas a la Validez

1. **Representatividad de los ejemplos**: Los ejemplos utilizados están limitados a ciertas configuraciones y podrían no representar todos los casos posibles de CNF.
2. **Rendimiento del hardware**: Los tiempos de ejecución dependen en gran medida del hardware utilizado. Las pruebas en diferentes configuraciones podrían arrojar resultados distintos.
3. **Orden de las técnicas**: El orden de aplicación de las técnicas de preprocesamiento puede influir en los resultados finales, lo cual es un área a explorar más profundamente.

## Conclusiones

La aplicación de las técnicas propuestas ha sido un éxito, cumpliendo con la premisa inicial de optimización y verificación en la transformación de CNF a dDNNF.
A partir de las métricas obtenidas, se pueden derivar conclusiones interesantes sobre la eficiencia de las técnicas combinadas y el impacto del orden en que se aplican.
Este análisis proporciona una base sólida para futuras investigaciones y optimizaciones en la resolución de problemas complejos.

## Licencia

Este proyecto está licenciado bajo los términos de la Licencia MIT. Ver [LICENSE](./LICENSE) para más detalles.

## Contacto

Para cualquier pregunta o contribución, puedes contactarme a través de [victorefr97@gmail.com](mailto:victorefr97@gmail.com).

