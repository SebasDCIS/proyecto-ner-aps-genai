# Datos

Esta carpeta **no se versiona**. Los corpus se descargan con:

```bash
python src/datos/descargar.py
```

| Corpus | Uso en el proyecto | Licencia |
|---|---|---|
| Chilean Waiting List Corpus (CWLC) | Entrenamiento y examen (test) con texto real de APS chilena | CC BY-NC-SA 4.0 |
| DisTEMIST | Texto clínico "limpio" de España con enfermedades anotadas (contraste) | ver `configs/datos.yaml` |
| GES classification dataset (opcional) | Segunda tarea, de clasificación | CC BY 4.0 |

Reglas:
- No agregar datos institucionales ni de pacientes identificables.
- Los ejemplos usados en prompts (few-shot) salen **solo** del split de entrenamiento.
- El split de test se usa una sola vez por experimento para reportar.
