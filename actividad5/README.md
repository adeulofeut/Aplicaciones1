# Predicción de nacimientos en Colombia por departamento para 2024

**Cuaderno en Google Colab:** https://colab.research.google.com/github/adeulofeut/Aplicaciones1/blob/main/actividad5/Nacimientos_Colombia_2024.ipynb
**Integrantes:** Juan Camilo Narváez Sánchez · Ronald Andrés García Díaz · Adrián Felipe Deulofeut Gil
Aplicaciones I (SMTART84, Grupo 2) · Maestría en Inteligencia Artificial · Universidad de La Salle · 2026-2

Modelo de Machine Learning que estima los nacimientos de 2024 en cada uno de los 32 departamentos y Bogotá D. C., entrenado con los microdatos de las Estadísticas Vitales (EEVV) del DANE de 2020 a 2023.

## Contenido

```
actividad5/
├── Nacimientos_Colombia_2024.ipynb   # Cuaderno: secciones A) a H) y anexo
├── Nacimientos_Colombia_2024.html    # El mismo cuaderno exportado, con resultados
└── datos/
    └── nac2020.zip … nac2023.zip     # CSV originales de nacimientos del DANE, sin modificar
```

## Resultado

| | |
|---|---|
| Modelo elegido | Regresión lineal en escala logarítmica (comparada con regresión lineal, Random Forest, Gradient Boosting y persistencia) |
| Validación (entrena 2021–2022, prueba 2023) | MAE 745 nacimientos por departamento · MAPE 7,1 % · R² 0,995 |
| Predicción nacional 2024 | **451.533** nacimientos (−11,2 % frente a 2023) |

## Cómo ejecutarlo

Abrir el enlace de Colab y usar **Entorno de ejecución → Ejecutar todas**. El cuaderno descarga los datos de la carpeta `datos/` de este repositorio, así que no hay que subir nada.

## Fuentes

DANE, Estadísticas Vitales – EEVV, catálogos de microdatos [2020](https://microdatos.dane.gov.co/index.php/catalog/732), [2021](https://microdatos.dane.gov.co/index.php/catalog/775), [2022](https://microdatos.dane.gov.co/index.php/catalog/807) y [2023](https://microdatos.dane.gov.co/index.php/catalog/876).
