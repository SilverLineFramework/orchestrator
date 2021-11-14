**Dependencies**: python 3, pip3, virtualenv (and requirements.txt; check if path in Makefile is correct)

**Setup:**
- Create db: ```make migrate```
- Start the virtualenv - ```source env/bin/activate```
- Create admin user: ```python manage.py createsuperuser --email admin@example.com --username admin```

**Execute:**
- ```make run```

**UIs:**

- Admin: `http://localhost:8000/admin/`
- Vizualize: `http://localhost:8000/static/index.html`
