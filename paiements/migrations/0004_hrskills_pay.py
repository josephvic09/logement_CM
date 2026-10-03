from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0003_campay_paiement_reel'),
    ]

    operations = [
        migrations.RenameField(
            model_name='paiement',
            old_name='campay_reference',
            new_name='reference_externe',
        ),
        migrations.RemoveField(
            model_name='paiement',
            name='ussd_code',
        ),
    ]
