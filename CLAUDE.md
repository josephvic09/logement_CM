# Règles de travail — Projet LogementCM (Django / Python)

## Contexte (ne pas relire pour le redécouvrir)
- Stack : Django, templates Django + Bootstrap 5 + Lucide icons + Chart.js, SQLite/PostgreSQL.
- Apps : accounts, logements, chat, notifs, paiements, api. Templates dans templates/<app>/.
- Base de style de référence : templates/accounts/dashboard_admin.html (classes .adm-*).
- Ignorer totalement : env/, staticfiles/, media/, .git/, *.sql, __pycache__/.

## Économie de tokens (obligatoire)
1. Ne lis JAMAIS un fichier entier si tu peux cibler : utilise Grep/Glob d'abord, puis Read avec offset/limit sur les lignes utiles.
2. Ne relis pas un fichier déjà lu dans la session, sauf s'il a été modifié depuis.
3. Pour modifier : utilise Edit (remplacement ciblé), jamais de réécriture complète d'un fichier existant sauf demande explicite.
4. Pas d'exploration du projet « pour comprendre » : lis uniquement ce que la tâche exige.
5. Pas de sous-agents, pas de plan détaillé, pas de liste de tâches pour une tâche simple.
6. Réponses courtes : pas de résumé de ce que tu vas faire, pas de récapitulatif des étapes, pas de réexplication du code écrit. À la fin : 2 à 4 lignes maximum (fichiers touchés + point d'attention éventuel).
7. Ne colle pas de code dans la réponse s'il est déjà écrit dans un fichier.
8. Une seule commande de vérification à la fin (ex. `python manage.py check`), pas de tests répétés.
9. Si une info manque, pose UNE question courte au lieu d'explorer au hasard.

## Qualité du code (obligatoire)
- Python : PEP 8, noms explicites en français cohérents avec le projet, fonctions courtes, pas de code mort ni de commentaires inutiles.
- Django ORM : select_related / prefetch_related sur les relations affichées, pas de requête dans une boucle, agrégats en base (Count, Sum) plutôt qu'en Python, .only()/.values() quand c'est suffisant.
- Vues : vérifier les permissions (login_required, rôle), get_object_or_404, POST + CSRF pour toute action qui modifie.
- Templates : réutiliser les classes CSS existantes, pas de style dupliqué, pas de logique métier dans le template.
- Sécurité : jamais de secret en dur (utiliser .env), échapper les données dans le JS (json_script / escapejs).
- Ne change que ce qui est demandé ; ne renomme ni ne déplace rien sans le dire.
- Avant de terminer : vérifier que les noms d'URL, variables de contexte et champs de modèle utilisés existent réellement.
