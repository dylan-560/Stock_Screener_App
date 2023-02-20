# Generated by Django 4.1.5 on 2023-01-17 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DailyScreenResults',
            fields=[
                ('screen_result', models.JSONField()),
            ],
            options={
                'db_table': 'daily_screen_results',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='FinalScreenResults',
            fields=[
                ('symbol', models.CharField(max_length=6)),
                ('datetime', models.DateTimeField()),
                ('prev_close', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('max_pct_gain', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('market_cap', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('shares_float', models.DecimalField(blank=True, decimal_places=3, max_digits=9, null=True)),
                ('short_perc_float', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('shares_short', models.DecimalField(blank=True, decimal_places=3, max_digits=9, null=True)),
                ('shares_outstanding', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('sector', models.CharField(blank=True, max_length=45, null=True)),
                ('industry', models.CharField(blank=True, max_length=45, null=True)),
                ('ext_market_activity', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('high_to_close', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('dollar_volume', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
            ],
            options={
                'db_table': 'final_screen_results',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='FinalScreenResultsDummy',
            fields=[
                ('symbol', models.CharField(max_length=6)),
                ('datetime', models.DateTimeField()),
                ('prev_close', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('max_pct_gain', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('market_cap', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('shares_float', models.DecimalField(blank=True, decimal_places=3, max_digits=9, null=True)),
                ('short_perc_float', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('shares_short', models.DecimalField(blank=True, decimal_places=3, max_digits=9, null=True)),
                ('shares_outstanding', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('sector', models.CharField(blank=True, max_length=45, null=True)),
                ('industry', models.CharField(blank=True, max_length=45, null=True)),
                ('ext_market_activity', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('high_to_close', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('dollar_volume', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
            ],
            options={
                'db_table': 'final_screen_results_dummy',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Ohlcv',
            fields=[
                ('ticker', models.CharField(max_length=6)),
                ('datetime', models.DateTimeField(blank=True, null=True)),
                ('open', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('high', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('low', models.CharField(blank=True, max_length=45, null=True)),
                ('close', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('volume', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'ohlcv',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='OhlcvDummy',
            fields=[
                ('ticker', models.CharField(max_length=6)),
                ('datetime', models.DateTimeField(blank=True, null=True)),
                ('open', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('high', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('low', models.CharField(blank=True, max_length=45, null=True)),
                ('close', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('volume', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'ohlcv_dummy',
                'managed': False,
            },
        ),
    ]
