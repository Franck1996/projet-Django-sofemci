# sofemci/management/commands/init_data.py
"""
Commande Django pour initialiser les données de base
Usage: python manage.py init_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from sofemci.models import Equipe, ZoneExtrusion, Machine
from datetime import time

User = get_user_model()


class Command(BaseCommand):
    help = 'Initialise les données de base pour SOFEM-CI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprime les données existantes avant de créer',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('Suppression des données existantes...'))
            Equipe.objects.all().delete()
            ZoneExtrusion.objects.all().delete()
            Machine.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Création des données de base...'))

        # Créer les équipes
        self.stdout.write('Création des équipes...')
        equipes_data = [
            {'nom': 'A', 'heure_debut': time(6, 0), 'heure_fin': time(14, 0)},
            {'nom': 'B', 'heure_debut': time(14, 0), 'heure_fin': time(22, 0)},
            {'nom': 'C', 'heure_debut': time(22, 0), 'heure_fin': time(6, 0)},
        ]
        
        for data in equipes_data:
            equipe, created = Equipe.objects.get_or_create(
                nom=data['nom'],
                defaults={
                    'heure_debut': data['heure_debut'],
                    'heure_fin': data['heure_fin'],
                    'description': f"Équipe {data['nom']}"
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Équipe {equipe.nom} créée'))
            else:
                self.stdout.write(f'  - Équipe {equipe.nom} existe déjà')

        # Créer les zones d'extrusion
        self.stdout.write('Création des zones d\'extrusion...')
        for i in range(1, 6):
            zone, created = ZoneExtrusion.objects.get_or_create(
                numero=i,
                defaults={
                    'nom': f'Zone {i}',
                    'nombre_machines_max': 4,
                    'active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Zone {i} créée'))
            else:
                self.stdout.write(f'  - Zone {i} existe déjà')

        # Créer des machines d'exemple
        self.stdout.write('Création des machines...')
        machines_data = [
            # Extrusion
            {'numero': 'EXT-Z1-M1', 'type_machine': 'extrudeuse', 'section': 'extrusion', 'zone': 1},
            {'numero': 'EXT-Z1-M2', 'type_machine': 'extrudeuse', 'section': 'extrusion', 'zone': 1},
            {'numero': 'EXT-Z2-M1', 'type_machine': 'extrudeuse', 'section': 'extrusion', 'zone': 2},
            # Imprimerie
            {'numero': 'IMP-01', 'type_machine': 'imprimante', 'section': 'imprimerie'},
            {'numero': 'IMP-02', 'type_machine': 'imprimante', 'section': 'imprimerie'},
            # Soudure
            {'numero': 'SOU-01', 'type_machine': 'soudeuse', 'section': 'soudure'},
            {'numero': 'SOU-02', 'type_machine': 'soudeuse', 'section': 'soudure'},
            # Recyclage
            {'numero': 'REC-M1', 'type_machine': 'moulinex', 'section': 'recyclage'},
            {'numero': 'REC-M2', 'type_machine': 'moulinex', 'section': 'recyclage'},
        ]

        for data in machines_data:
            zone_obj = None
            if 'zone' in data:
                zone_obj = ZoneExtrusion.objects.get(numero=data['zone'])
            
            machine, created = Machine.objects.get_or_create(
                numero=data['numero'],
                section=data['section'],
                defaults={
                    'type_machine': data['type_machine'],
                    'zone_extrusion': zone_obj,
                    'etat': 'actif'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Machine {machine.numero} créée'))
            else:
                self.stdout.write(f'  - Machine {machine.numero} existe déjà')

        # Créer un utilisateur admin de test si n'existe pas
        self.stdout.write('Vérification compte administrateur...')
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@sofemci.com',
                password='admin123',
                first_name='Administrateur',
                last_name='Système',
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS('  ✓ Compte admin créé (admin/admin123)'))
        else:
            self.stdout.write('  - Compte admin existe déjà')

        # Créer des utilisateurs de test
        self.stdout.write('Création des utilisateurs de test...')
        users_data = [
            {
                'username': 'chef_ext1',
                'password': 'test123',
                'first_name': 'Jean',
                'last_name': 'KOUASSI',
                'role': 'chef_extrusion',
                'email': 'jean.kouassi@sofemci.com'
            },
            {
                'username': 'chef_imp1',
                'password': 'test123',
                'first_name': 'Marie',
                'last_name': 'YAO',
                'role': 'chef_imprimerie',
                'email': 'marie.yao@sofemci.com'
            },
            {
                'username': 'superviseur1',
                'password': 'test123',
                'first_name': 'Kofi',
                'last_name': 'BAMBA',
                'role': 'superviseur',
                'email': 'kofi.bamba@sofemci.com'
            },
        ]

        for user_data in users_data:
            if not User.objects.filter(username=user_data['username']).exists():
                User.objects.create_user(**user_data)
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ Utilisateur {user_data['username']} créé ({user_data['role']})"
                ))
            else:
                self.stdout.write(f"  - Utilisateur {user_data['username']} existe déjà")

        self.stdout.write(self.style.SUCCESS('\n✅ Initialisation terminée avec succès!'))
        self.stdout.write(self.style.WARNING('\nComptes de test créés:'))
        self.stdout.write('  - admin / admin123 (Administrateur)')
        self.stdout.write('  - chef_ext1 / test123 (Chef Extrusion)')
        self.stdout.write('  - chef_imp1 / test123 (Chef Imprimerie)')
        self.stdout.write('  - superviseur1 / test123 (Superviseur)')