# Initial affiliate product catalogue.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('shop', '0001_initial')]

    operations = [
        migrations.CreateModel(
            name='AffiliateProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=140)),
                ('slug', models.SlugField(blank=True, max_length=160, unique=True)),
                ('category', models.CharField(choices=[('equipment', 'Gym equipment'), ('accessories', 'Accessories'), ('apparel', 'Fitness apparel'), ('recovery', 'Recovery'), ('nutrition', 'Nutrition'), ('other', 'Other')], default='equipment', max_length=20)),
                ('description', models.TextField(max_length=1200)),
                ('seller_name', models.CharField(max_length=100)),
                ('seller_url', models.URLField(max_length=500, help_text='HTTPS product page on the seller website.')),
                ('affiliate_url', models.URLField(blank=True, max_length=500, help_text='Optional tracked link supplied by an affiliate programme. Leave blank to use seller URL.')),
                ('image_url', models.URLField(blank=True, max_length=500)),
                ('price_label', models.CharField(blank=True, max_length=60, help_text='Optional display price, including currency; keep it updated.')),
                ('is_active', models.BooleanField(default=False, help_text='Enable only after verifying the product, seller link and image rights.')),
                ('featured', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-featured', 'category', 'title']},
        ),
    ]
