# SOFEM-CI Environment Variables
# Copier ce fichier vers .env et remplir les valeurs

# Django Settings
SECRET_KEY=votre-cle-secrete-tres-longue-et-aleatoire-ici
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database Configuration (SQLite par défaut)
# Pour MySQL, décommenter et remplir :
# DB_ENGINE=django.db.backends.mysql
# DB_NAME=sofemci_db
# DB_USER=root
# DB_PASSWORD=votre_mot_de_passe
# DB_HOST=localhost
# DB_PORT=3306

# Email Configuration (optionnel pour les alertes)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=votre_email@gmail.com
# EMAIL_HOST_PASSWORD=votre_mot_de_passe

# Production Settings (à configurer pour la production)
#