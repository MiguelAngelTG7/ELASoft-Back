# Backend - Escuela de Liderazgo Alianza (ELA)

Este proyecto es el backend de la Escuela de Liderazgo Alianza, desarrollado en Django y desplegado en Render.

## Requisitos
- Python 3.10+
- pip
- PostgreSQL (para desarrollo local)

## Instalación local
1. Clona el repositorio y entra a la carpeta `backend`.
2. Crea y activa un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```
3. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Configura las variables de entorno necesarias (puedes usar `.env`).
5. Realiza migraciones:
   ```bash
   python manage.py migrate
   ```
6. Crea un superusuario:
   ```bash
   python manage.py createsuperuser
   ```
7. Inicia el servidor:
   ```bash
   python manage.py runserver
   ```

## Despliegue en Render
- El backend está desplegado en: https://elasoft-back.onrender.com
- Usa PostgreSQL como base de datos.
- Configura las variables de entorno en Render (`SECRET_KEY`, `DEBUG`, `DATABASE_URL`, etc).
- `ALLOWED_HOSTS` debe incluir el dominio de Render.

## Endpoints principales
- `/api/login/` — Login JWT
- `/api/refresh/` — Refresh de token
- `/api/usuario/` — Usuario actual autenticado
- `/api/director/clases/` — Clases del director
- `/api/director/periodos/` — Lista de periodos académicos
- `/api/director/profesores/?periodo_id=<id>` — Lista de profesores (titulares y asistentes) por periodo académico

## Notas
- Si el backend está dormido, la primera petición puede demorar unos segundos.
- El frontend debe apuntar a la URL de este backend en producción.
- Para actualizar cambios en producción: haz commit y push a GitHub, Render desplegará automáticamente y aplicará migraciones si está configurado.

---

# English
This is the Django backend for the ELA project. See instructions above for local development and deployment.