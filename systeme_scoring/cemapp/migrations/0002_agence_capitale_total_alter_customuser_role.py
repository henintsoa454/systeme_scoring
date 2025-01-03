# Generated by Django 5.1.3 on 2024-12-30 08:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cemapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='agence',
            name='capitale_total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(choices=[('admin', 'Admin'), ('directeur_agence', "Directeur de l' Agence"), ('analyste_demande', 'Analyste des Demandes'), ('gestionnaire', 'Gestionnaire des Demandes'), ('service_client', 'Service Client'), ('agent_inspection', "Agent d' Inspection")], default='service_client', max_length=25),
        ),
    ]
