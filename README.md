# Andrés Task Manager

Gestor personal de **tareas** y **notas**, con interfaz gráfica en modo oscuro,
hecho en Python con Tkinter. Sin dependencias externas.

## Características

- Gestión de tareas: título, descripción, prioridad, categoría y fecha límite.
- Marcado de tareas como completadas / pendientes y detección automática de
  tareas vencidas.
- Buscador y filtros por estado y prioridad en la lista de tareas.
- Notas con título, categoría y contenido libre.
- Buscador de notas.
- Ordenación de las tablas haciendo clic en cualquier columna.
- Panel de inicio con resumen (pendientes, completadas, vencidas, notas).
- Diálogos redimensionables que se ajustan automáticamente al contenido.
- Persistencia local en un archivo JSON (`~/AndresTaskManager/datos.json`).
- Guardado automático en cada cambio + guardado manual (`Ctrl+S`).

## Requisitos

- Python 3.8 o superior.
- Tkinter (incluido por defecto en la mayoría de instalaciones de Python).

No hace falta instalar ninguna librería externa.

## Uso

```bash
python app.py
```

## Estructura de datos

Los datos se guardan en:

```
~/AndresTaskManager/datos.json
```

con la siguiente forma:

```json
{
  "tasks": [
    {
      "id": "uuid",
      "title": "Título",
      "description": "Descripción",
      "priority": "Alta | Media | Baja",
      "category": "Categoría",
      "due_date": "AAAA-MM-DD",
      "completed": false,
      "created_at": "AAAA-MM-DD HH:MM",
      "completed_at": null
    }
  ],
  "notes": [
    {
      "id": "uuid",
      "title": "Título",
      "category": "Categoría",
      "content": "Contenido",
      "created_at": "AAAA-MM-DD HH:MM",
      "updated_at": "AAAA-MM-DD HH:MM"
    }
  ]
}
```

## Licencia

Uso personal / libre modificación.
