import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locais', '0001_initial'),
        ('solicitacoes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitacao',
            name='local_devolucao',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='solicitacoes_devolucao',
                to='locais.local',
            ),
        ),
    ]
