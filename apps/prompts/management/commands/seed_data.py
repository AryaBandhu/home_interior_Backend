from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.prompts.models import RoomType, RoomSize, DesignStyle, ColorTheme
from apps.subscriptions.models import SubscriptionPlan

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with initial data'

    def handle(self, *args, **options):
        self.seed_room_types()
        self.seed_room_sizes()
        self.seed_design_styles()
        self.seed_color_themes()
        self.seed_subscription_plans()
        self.seed_test_user()
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))

    def seed_room_types(self):
        types = [
            ('Living Room', 'living-room'),
            ('Bedroom', 'bedroom'),
            ('Kitchen', 'kitchen'),
            ('Bathroom', 'bathroom'),
            ('Dining Room', 'dining-room'),
            ('Home Office', 'home-office'),
            ('Kids Room', 'kids-room'),
            ('Balcony', 'balcony'),
        ]
        for name, slug in types:
            RoomType.objects.get_or_create(slug=slug, defaults={'name': name})
        self.stdout.write(f'  Created {len(types)} room types')

    def seed_room_sizes(self):
        sizes = [
            ('Small', 'small'),
            ('Medium', 'medium'),
            ('Large', 'large'),
            ('Extra Large', 'extra-large'),
        ]
        for name, slug in sizes:
            RoomSize.objects.get_or_create(slug=slug, defaults={'name': name})
        self.stdout.write(f'  Created {len(sizes)} room sizes')

    def seed_design_styles(self):
        styles = [
            ('Modern', 'modern'),
            ('Minimalist', 'minimalist'),
            ('Scandinavian', 'scandinavian'),
            ('Industrial', 'industrial'),
            ('Bohemian', 'bohemian'),
            ('Traditional', 'traditional'),
            ('Contemporary', 'contemporary'),
            ('Mid-Century Modern', 'mid-century-modern'),
            ('Japanese', 'japanese'),
            ('Rustic', 'rustic'),
        ]
        for name, slug in styles:
            DesignStyle.objects.get_or_create(slug=slug, defaults={'name': name})
        self.stdout.write(f'  Created {len(styles)} design styles')

    def seed_color_themes(self):
        themes = [
            ('Neutral', 'neutral'),
            ('Warm', 'warm'),
            ('Cool', 'cool'),
            ('Earth Tones', 'earth-tones'),
            ('Monochrome', 'monochrome'),
            ('Pastel', 'pastel'),
            ('Bold & Vibrant', 'bold-vibrant'),
            ('Dark & Moody', 'dark-moody'),
        ]
        for name, slug in themes:
            ColorTheme.objects.get_or_create(slug=slug, defaults={'name': name})
        self.stdout.write(f'  Created {len(themes)} color themes')

    def seed_subscription_plans(self):
        plans = [
            {
                'name': 'Free',
                'price': 0,
                'duration_days': 365,
                'description': '20 free credits to get started',
            },
            {
                'name': 'Basic',
                'price': 499,
                'duration_days': 30,
                'description': '100 generations per month, standard quality',
            },
            {
                'name': 'Pro',
                'price': 999,
                'duration_days': 30,
                'description': 'Unlimited generations, HD quality, priority support',
            },
            {
                'name': 'Annual Pro',
                'price': 9999,
                'duration_days': 365,
                'description': 'Everything in Pro, billed annually (save 17%)',
            },
        ]
        for plan_data in plans:
            SubscriptionPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
        self.stdout.write(f'  Created {len(plans)} subscription plans')

    def seed_test_user(self):
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'User',
                'credits': 20,
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write('  Created test user: test@example.com / testpass123')
        else:
            self.stdout.write('  Test user already exists')
