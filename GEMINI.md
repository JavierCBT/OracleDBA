# Reglas del proyecto OracleDBA

## Actualización automática de GitHub
Tras completar y verificar cualquier cambio en el código, estilos, datos o configuración del repositorio:
1. Revisa `git status` y añade al staging (`git add`) **únicamente** los archivos modificados o nuevos propios de la tarea (nunca incluyas `.venv/` ni archivos temporales).
2. Crea un commit con un mensaje claro en formato Conventional Commits (por ejemplo, `feat(ui): ...` o `fix(...): ...`).
3. Ejecuta `git push` al remoto `origin` en la rama activa (`main`) e informa del hash del commit en la respuesta final.
