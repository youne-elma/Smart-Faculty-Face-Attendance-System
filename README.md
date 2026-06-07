# Conception et implementation d'un systeme embarque intelligent de gestion de presence par reconnaissance faciale securise pour une Smart Faculty

Projet de fin d'etudes visant a automatiser la gestion des presences a la faculte a l'aide d'un systeme embarque autonome. Le systeme identifie les etudiants en temps reel, enregistre automatiquement leur presence, protege les donnees biometriques et fonctionne localement sans dependance cloud.

## Contexte

La gestion des presences en faculte est souvent manuelle, lente et sujette aux erreurs. Ce projet s'inscrit dans une demarche de Smart Faculty: utiliser l'IA embarquee pour rendre le controle de presence plus rapide, plus fiable et mieux securise.

Le prototype cible repose sur une ESP32-CAM pour la capture video et une Raspberry Pi pour le traitement IA, l'administration locale et l'export des listes de presence ou d'absence.

## Objectif general

Developper un prototype fonctionnel de gestion de presence base sur la reconnaissance faciale embarquee, optimise pour les contraintes materielles et energetiques d'une Raspberry Pi.

Le systeme doit permettre a un professeur ou administrateur de se connecter a une interface web locale, d'importer une fiche d'absence, de lancer une session de reconnaissance, puis d'exporter automatiquement le resultat sous forme de fichier Excel.

## Objectifs techniques

- Identifier les etudiants en temps reel.
- Enregistrer automatiquement la presence.
- Fonctionner en mode Edge AI, sans connexion cloud.
- Garantir la confidentialite des donnees biometriques.
- Deployer le traitement IA sur Raspberry Pi.
- Mettre en place un mecanisme de chiffrement des donnees sensibles.
- Concevoir une base de donnees locale securisee.
- Evaluer les performances: precision, latence, consommation et stabilite.
- Developper une interface web locale d'administration.
- Exporter les listes de presence et d'absence.

## Architecture cible

```text
ESP32-CAM
  - Capture video en temps reel
  - Diffusion du flux sur le reseau Wi-Fi local
  - Adresse par defaut: http://192.168.1.30/

Raspberry Pi
  - Recuperation du flux ESP32-CAM
  - Detection des visages
  - Reconnaissance/comparaison des etudiants
  - Enregistrement local des presences
  - Chiffrement des donnees biometriques
  - Base de donnees locale securisee
  - Export Excel des listes
  - Serveur backend de l'interface web locale

Interface web locale
  - Connexion professeur/admin
  - Import de la fiche d'absence
  - Lancement et suivi d'une session
  - Visualisation des etudiants identifies
  - Export du resultat final
```

## Demarche fonctionnelle

1. Le professeur ouvre l'interface web locale.
2. Il se connecte avec un compte admin/professeur.
3. Il importe la fiche d'absence du cours ou de l'examen.
4. Il lance une session de reconnaissance.
5. Les etudiants passent un par un devant l'ESP32-CAM.
6. La Raspberry Pi lit le flux video depuis `http://192.168.1.30/`.
7. Le systeme detecte le visage.
8. Le systeme reconnait ou compare l'etudiant avec la base locale.
9. La presence est enregistree automatiquement.
10. Le professeur exporte la liste finale au format Excel.

## Choix techniques principaux

### Detection faciale

La version active utilise MediaPipe Face Detection pour detecter les visages dans le flux ESP32-CAM. Haar Cascade reste conserve dans le projet pour les comparaisons futures.

Algorithmes prevus pour comparaison:

- MediaPipe Face Detection
- Haar Cascade
- MTCNN
- YOLOFace

### Reconnaissance faciale

La premiere version utilise FaceNet pour calculer les embeddings faciaux et comparer chaque visage avec les etudiants enregistres.

Algorithmes prevus pour comparaison:

- FaceNet
- MobileFaceNet
- DeepFace

## Securite et confidentialite

Le cahier des charges impose la protection des donnees biometriques. Les images, embeddings et informations d'etudiants ne doivent pas etre envoyes vers le cloud.

Principes retenus:

- Traitement local sur Raspberry Pi.
- Acces a l'interface protege par login et mot de passe.
- Stockage local des donnees sensibles.
- Chiffrement des embeddings ou fichiers sensibles.
- Mots de passe admin haches, jamais stockes en clair.
- Configuration par variables d'environnement.

Exemple cible:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changer-ce-mot-de-passe
SECRET_KEY=changer-cette-cle
ESP32_CAM_URL=http://192.168.1.30/
```

Pour la version finale, `ADMIN_PASSWORD` devra etre transforme en mot de passe hache ou remplace par une commande de creation d'utilisateur admin.

## Base de donnees locale

La base de donnees doit rester locale sur la Raspberry Pi. Elle servira a stocker:

- Les etudiants.
- Les groupes/classes.
- Les sessions de cours ou d'examen.
- Les presences.
- Les chemins ou references vers donnees faciales.
- Les embeddings chiffres ou proteges.

Le choix recommande pour le prototype est SQLite, car il est simple, local, leger et adapte a une Raspberry Pi. Une evolution vers PostgreSQL reste possible si le projet devient multi-postes.

Tables SQLite prevues:

- `students`: informations des etudiants.
- `student_photos`: references vers les photos des etudiants.
- `attendance_sessions`: cours, examens ou sessions de presence.
- `attendance_records`: statut de presence par etudiant et par session.
- `admin_users`: comptes administrateurs/professeurs avec mot de passe hache.

Relation importante:

- Un `admin_user` peut creer plusieurs `attendance_sessions`.
- Une `attendance_session` peut etre rattachee a un `admin_user` via `admin_user_id`.

## Comparaison des algorithmes

Le projet est organise pour permettre l'ajout progressif de plusieurs detecteurs et modeles de reconnaissance. L'objectif est de comparer:

- Precision de detection.
- Precision de reconnaissance.
- Latence par image.
- Temps total d'identification.
- Consommation CPU/RAM.
- Consommation energetique si mesure disponible.
- Stabilite sur Raspberry Pi.
- Facilite d'integration.

Les resultats pourront etre stockes dans `backend/data/benchmarks/` et exportes sous forme de fichiers Excel ou CSV.

## Structure du projet

```text
PFE_Project_v2.0/
  backend/
    app/
      api/                 # Routes API pour l'interface web
      auth/                # Login admin/professeur
      config/              # Configuration camera, chemins, seuils
      core/                # Demarrage backend et logique globale
      database/            # Connexion SQLite et migrations
      models/              # Schemas et objets metier
      security/            # Hachage, chiffrement, protection donnees
      services/
        attendance/        # Import/export fiches d'absence
        camera/            # Recuperation du flux ESP32-CAM
        comparison/        # Benchmarks entre algorithmes
        detection/         # Haar Cascade, MTCNN, YOLOFace
        metrics/           # Precision, latence, ressources
        recognition/       # FaceNet, MobileFaceNet, DeepFace
      utils/               # Fonctions communes
    data/
      benchmarks/          # Resultats des tests et comparaisons
      db/                  # Base SQLite locale
      imports/             # Fiches d'absence importees
      exports/             # Fichiers Excel generes
      known_faces/         # Images ou embeddings des etudiants connus
      models/              # Poids/modeles telecharges
  frontend/
    src/
      assets/              # Images, icons, fichiers statiques
      components/          # Composants reutilisables
      pages/               # Pages login, dashboard, session
      services/            # Appels API backend
      styles/              # Styles CSS
  docs/                    # Documentation technique et rapport
  scripts/                 # Scripts d'installation et preparation
  tests/                   # Tests automatises
```

## Donnees attendues

### Base des etudiants connus

La version finale devra recuperer les photos depuis la base de donnees locale securisee. Pour le developpement et les tests, un provider local temporaire lit les photos placees dans `backend/data/known_faces/`.

Chaque etudiant doit avoir des images de reference ou un embedding deja calcule. Exemple d'organisation locale possible:

```text
backend/data/known_faces/
  CNE001_Nom_Prenom/
    image_1.jpg
    image_2.jpg
  CNE002_Nom_Prenom/
    image_1.jpg
```

En version finale, les embeddings devront etre proteges ou chiffres avant stockage.

### Fiche d'absence importee

La fiche importee par le professeur doit contenir au minimum:

- Identifiant etudiant: CNE, CIN ou code apogee selon le choix final.
- Nom.
- Prenom.
- Groupe ou filiere.
- Statut de presence ou absence.

## Installation prevue sur Raspberry Pi

1. Installer Python 3.
2. Creer un environnement virtuel.
3. Installer les dependances backend.
4. Configurer l'adresse de l'ESP32-CAM.
5. Configurer le compte admin.
6. Initialiser la base de donnees locale.
7. Lancer le backend.
8. Lancer l'interface web locale.

Commandes backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Pour activer la reconnaissance FaceNet, installer aussi les dependances IA:

```bash
pip install -r requirements-facenet.txt
```

Note: FaceNet est charge uniquement quand la route de reconnaissance est appelee. Le backend peut donc demarrer sans `facenet-pytorch`, mais `GET /api/v1/recognition/identify` retournera une erreur tant que ces dependances ne sont pas installees.

Sur Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Pour activer la reconnaissance FaceNet sur Windows:

```powershell
pip install -r requirements-facenet.txt
```

MediaPipe Face Detection utilise le modele local:

```text
backend/data/models/blaze_face_short_range.tflite
```

Si ce fichier manque, telecharger le modele officiel BlazeFace short range:

```powershell
Invoke-WebRequest https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite -OutFile backend/data/models/blaze_face_short_range.tflite
```

Routes disponibles dans la premiere version backend:

- `GET /api/v1/health`: verification du backend.
- `POST /api/v1/auth/login`: connexion admin/professeur et generation JWT.
- `GET /api/v1/auth/me`: verification du token admin courant.
- `GET /api/v1/camera/status`: verification de disponibilite de l'ESP32-CAM.
- `GET /api/v1/database/status`: statut de la base SQLite locale.
- `POST /api/v1/database/initialize`: creation des tables SQLite.
- `GET /api/v1/camera/snapshot`: recuperation d'une image depuis l'ESP32-CAM. Si `/capture` n'est pas disponible, le backend extrait une image JPEG depuis le stream MJPEG.
- `GET /api/v1/camera/frame-info`: recuperation et decodage OpenCV d'une frame.
- `GET /api/v1/detection/faces`: detection des visages avec MediaPipe Face Detection.
- `GET /api/v1/detection/preview`: image JPEG annotee avec rectangles de detection.
- `GET /api/v1/recognition/identify`: reconnaissance FaceNet sur la frame camera courante.
- `GET /api/v1/students/known`: liste des etudiants connus et des photos de reference disponibles.

Tests rapides:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/database/status
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/v1/database/initialize
python scripts/create_admin.py
Invoke-RestMethod http://127.0.0.1:8000/api/v1/camera/status
Invoke-RestMethod http://127.0.0.1:8000/api/v1/camera/frame-info
Invoke-RestMethod http://127.0.0.1:8000/api/v1/detection/faces
Invoke-RestMethod http://127.0.0.1:8000/api/v1/recognition/identify
Invoke-RestMethod http://127.0.0.1:8000/api/v1/students/known
Invoke-WebRequest http://127.0.0.1:8000/api/v1/camera/snapshot -OutFile snapshot.jpg
Invoke-WebRequest http://127.0.0.1:8000/api/v1/detection/preview -OutFile detection-preview.jpg
```

Test login admin:

```powershell
$body = @{ username = "admin"; password = "change-this-password" } | ConvertTo-Json
$token = (Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/v1/auth/login -ContentType "application/json" -Body $body).access_token
Invoke-RestMethod http://127.0.0.1:8000/api/v1/auth/me -Headers @{ Authorization = "Bearer $token" }
```

## Configuration camera

Adresse ESP32-CAM par defaut:

```text
http://192.168.1.30/
```

Cette adresse doit rester configurable pour permettre un changement de reseau ou d'adresse IP.

## Livrables du projet

- Code Python pour Raspberry Pi.
- Interface web locale professeur/admin.
- Module de detection Haar Cascade.
- Module de reconnaissance FaceNet.
- Import de fiches d'absence.
- Export Excel des presences et absences.
- Base de donnees locale securisee.
- Mecanisme de protection des donnees biometriques.
- Structure extensible pour MTCNN, YOLOFace, MobileFaceNet et DeepFace.
- Documentation technique.
- Comparaison des algorithmes avec mesures de performance.

## Prochaines etapes de developpement

1. Initialiser le backend Python.
2. Ajouter la configuration globale et les variables d'environnement.
3. Ajouter le module camera pour lire le flux ESP32-CAM.
4. Ajouter la detection Haar Cascade.
5. Ajouter la reconnaissance FaceNet.
6. Ajouter la base SQLite locale.
7. Ajouter le chiffrement ou la protection des embeddings.
8. Ajouter l'import/export Excel.
9. Ajouter l'authentification admin.
10. Construire l'interface web locale.
11. Ajouter les modules de comparaison MTCNN, YOLOFace, MobileFaceNet et DeepFace.
12. Mesurer precision, latence, consommation et stabilite sur Raspberry Pi.
