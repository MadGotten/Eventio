[![Eventio CI](https://github.com/MadGotten/Eventio/actions/workflows/django.yml/badge.svg)](https://github.com/MadGotten/Eventio/actions/workflows/django.yml)

# Eventio
Eventio is a web application designed for managing events, allowing users to create, view, and register for events. The platform supports adding a review, ticket purchasing and user account management.

## Features
- **User Authentication**: Users can register, log in, and manage their accounts.
- **Event Management**: Create, update and delete events with different statuses (approved, pending).
- **Review System**: Users can submit reviews to events they've been.
- **Ticketing System**: Users can buy tickets for paid events and register for free events.
- **Event Search**: Search for events based on title and description.
- **User Dashboard**: View created events, registered events, and purchased tickets.

## Tech Stack
- Django
- Django Allauth
- PostgreSQL
- HTMX
- Hyperscript
- AlpineJS
- TailwindCSS
- Pillow
- Stripe

## Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/eventio.git
cd eventio
```
2. Create a virtual environment:
```bash
python -m venv .venv
source venv/bin/activate
```
3. Install the required packages:
```bash
pip install -r development.txt
```
4. Install Node modules dependencies for development
```bash
npm install
```
5. Set up the database:
- Create a PostgreSQL database and user.
- Update the database settings in core/settings/base.py.
6. Run migrations:
```bash
python manage.py migrate
```
7. Create a superuser (optional):
```bash
python manage.py createsuperuser
```
8. Run the development server:
```bash
python manage.py runserver
```
9. Run watch or minify changes in tailwindcss file:
```bash
npm run watch | npm run build
```
Open your browser and go to http://127.0.0.1:8000/.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
