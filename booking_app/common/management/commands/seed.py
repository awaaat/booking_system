import uuid
from django.utils import timezone
from django.contrib.gis.geos import Point
from datetime import timedelta, datetime
import random
from users.models.appuser import CustomUser
from listings.models.listing import Listing
from listings.models.property_images import PropertyImage
from bookings.models.booking import Booking
from reviews.models.review import Review
from payments.models.payment import Payment
from messaging.models.conversation import Conversation
from messaging.models.message import Message
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

class Command(BaseCommand):
    help = 'Clears existing data and seeds the database with realistic test data for a booking platform'

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            self.stdout.write("Clearing existing data...")
            Message.objects.all().delete()
            Conversation.objects.all().delete()
            Payment.objects.all().delete()
            Review.objects.all().delete()
            Booking.objects.all().delete()
            PropertyImage.objects.all().delete()
            Listing.objects.all().delete()
            CustomUser.objects.all().delete()

            self.stdout.write("Seeding users...")
            users = self.create_users()
            guests = [u for u in users if u.user_role == 'guest']
            hosts = [u for u in users if u.user_role == 'host']

            self.stdout.write("Seeding listings...")
            listings = self.create_listings(hosts)

            self.stdout.write("Seeding property images...")
            self.create_property_images(listings)

            self.stdout.write("Seeding bookings...")
            bookings = self.create_bookings(guests, listings)

            self.stdout.write("Seeding reviews...")
            self.create_reviews(guests, listings, bookings)

            self.stdout.write("Seeding payments...")
            self.create_payments(guests, bookings)

            self.stdout.write("Seeding conversations and messages...")
            self.create_conversations_and_messages(guests, hosts, listings)

        self.stdout.write(self.style.SUCCESS("Database cleared and seeded successfully!"))

    def create_users(self):
        users = []
        first_names = ['Alejandro', 'Priya', 'Liam', 'Fatima', 'Ethan', 'Sofia', 'Noah', 'Aisha', 'Mateo', 'Isabella',
                       'Lucas', 'Amara', 'Daniel', 'Chloe', 'Gabriel', 'Zara', 'James', 'Nia', 'Oliver', 'Layla',
                       'Amir', 'Maya', 'Elias', 'Anika', 'Samuel', 'Leila', 'Isaac', 'Zoe', 'Jacob', 'Aria']
        last_names = ['Patel', 'Nguyen', 'Rodriguez', 'Khan', 'Silva', 'Chen', 'Martinez', 'Ali', 'Santos', 'Wong',
                      'Garcia', 'Das', 'Lopez', 'Kim', 'Torres', 'Singh', 'Cruz', 'Li', 'Reyes', 'Gupta']
        domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'protonmail.com']
        used_usernames = set()

        for i in range(5):
            first = random.choice(first_names)
            last = random.choice(last_names)
            base_username = f"{first.lower()}.{last.lower()}"
            username = f"{base_username}{i+1:03d}"
            while username in used_usernames:
                username = f"{base_username}{uuid.uuid4().hex[:4]}"
            used_usernames.add(username)
            user = CustomUser.objects.create_user(
                user_id=uuid.uuid4(),
                username=username,
                email=f"{username}@{random.choice(domains)}",
                password='testPass123',
                first_name=first,
                last_name=last,
                phone_number=f"+{random.choice(['1', '44', '33', '81', '61'])}{random.randint(100000000, 999999999)}",
                user_role='admin',
                is_staff=True,
                is_email_verified=True,
                created_at=timezone.now() - timedelta(days=random.randint(100, 365))
            )
            users.append(user)

        for i in range(25):
            first = random.choice(first_names)
            last = random.choice(last_names)
            base_username = f"{first.lower()}.{last.lower()}"
            username = f"{base_username}{i+1:03d}"
            while username in used_usernames:
                username = f"{base_username}{uuid.uuid4().hex[:4]}"
            used_usernames.add(username)
            user = CustomUser.objects.create_user(
                user_id=uuid.uuid4(),
                username=username,
                email=f"{username}@{random.choice(domains)}",
                password='testPass123',
                first_name=first,
                last_name=last,
                phone_number=f"+{random.choice(['1', '44', '33', '81', '61'])}{random.randint(100000000, 999999999)}",
                user_role='host',
                bio=f"Experienced host offering unique stays in {random.choice(['New York', 'Paris', 'Tokyo', 'Sydney', 'Rome'])}. Love sharing local culture and tips! {random.randint(50, 200)} chars.",
                is_email_verified=True,
                created_at=timezone.now() - timedelta(days=random.randint(100, 365))
            )
            users.append(user)

        for i in range(120):
            first = random.choice(first_names)
            last = random.choice(last_names)
            base_username = f"{first.lower()}.{last.lower()}"
            username = f"{base_username}{i+1:03d}"
            while username in used_usernames:
                username = f"{base_username}{uuid.uuid4().hex[:4]}"
            used_usernames.add(username)
            user = CustomUser.objects.create_user(
                user_id=uuid.uuid4(),
                username=username,
                email=f"{username}@{random.choice(domains)}",
                password='testPass123',
                first_name=first,
                last_name=last,
                phone_number=f"+{random.choice(['1', '44', '33', '81', '61'])}{random.randint(100000000, 999999999)}",
                user_role='guest',
                bio=f"Passionate traveler exploring {random.choice(['Europe', 'Asia', 'North America', 'Australia'])}. Seeking unique stays and local experiences. {random.randint(50, 200)} chars.",
                is_email_verified=random.choice([True, False]),
                created_at=timezone.now() - timedelta(days=random.randint(30, 365))
            )
            users.append(user)

        return users

    def create_listings(self, hosts):
        listings = []
        cities = ['New York', 'Paris', 'Tokyo', 'London', 'Sydney', 'Rome', 'Barcelona', 'Amsterdam', 'Dubai', 'Miami']
        streets = ['Fifth Avenue', 'Champs-Élysées', 'Shibuya Street', 'Oxford Street', 'George Street', 
                   'Via del Corso', 'Rambla Catalunya', 'Damrak', 'Sheikh Zayed Road', 'Ocean Drive']
        property_types = [choice[0] for choice in Listing.PROPERTY_TYPES]
        cancellation_policies = [choice[0] for choice in Listing.CANCELLATION_POLICIES]
        adjectives = ['Cozy', 'Luxury', 'Modern', 'Charming', 'Elegant', 'Spacious']

        for host in hosts:  # Ensure every host has exactly 2 listings
            for i in range(2):
                city = random.choice(cities)
                listing = Listing.objects.create(
                    property_id=uuid.uuid4(),
                    host=host,
                    name=f"{random.choice(adjectives)} {random.choice(['Apartment', 'Villa', 'Hotel', 'Homestay'])} in {city}",
                    description=f"Experience a {random.choice(adjectives).lower()} stay in the heart of {city}. Enjoy modern amenities, {random.choice(['stunning views', 'local charm', 'easy access to landmarks'])}.",
                    location=Point(float(random.uniform(-180, 180)), float(random.uniform(-90, 90))),
                    address=f"{random.randint(100, 999)} {random.choice(streets)}",
                    city=city,
                    country={'New York': 'United States', 'Paris': 'France', 'Tokyo': 'Japan', 'London': 'United Kingdom',
                             'Sydney': 'Australia', 'Rome': 'Italy', 'Barcelona': 'Spain', 'Amsterdam': 'Netherlands',
                             'Dubai': 'UAE', 'Miami': 'United States'}[city],
                    distance_from_center=random.uniform(0.5, 15.0),
                    price_per_night=random.randint(50, 500),
                    capacity=random.randint(1, 10),
                    bedrooms=random.randint(1, 5),
                    bathrooms=random.randint(1, 4),
                    property_type=random.choice(property_types),
                    sustainability_certified=random.choice([True, False]),
                    is_beachfront=random.choice([True, False]),
                    is_entire_place=random.choice([True, False]),
                    pets_allowed=random.choice([True, False]),
                    adults_only=random.choice([True, False]),
                    cancellation_policy=random.choice(cancellation_policies),
                    amenities={
                        'wifi': random.choice([True, False]),
                        'pool': random.choice([True, False]),
                        'air_conditioning': random.choice([True, False]),
                        'parking': random.choice([True, False]),
                        'kitchen': random.choice([True, False])
                    },
                    room_facilities={
                        'sea_view': random.choice([True, False]),
                        'private_bathroom': random.choice([True, False]),
                        'balcony': random.choice([True, False])
                    },
                    accessibility_features={
                        'wheelchair_accessible': random.choice([True, False]),
                        'elevator': random.choice([True, False]),
                        'grab_rails': random.choice([True, False])
                    },
                    activities={
                        'diving': random.choice([True, False]),
                        'hiking': random.choice([True, False]),
                        'city_tours': random.choice([True, False])
                    },
                    landmarks={
                        f"{random.choice(['Museum', 'Park', 'Monument', 'Beach'])} {i+1}": random.uniform(0.5, 10.0)
                    },
                    availability={
                        '2025-08-01': True, '2025-08-02': True, '2025-08-03': True,
                        '2025-08-04': random.choice([True, False]), '2025-08-05': random.choice([True, False])
                    }
                )
                listings.append(listing)
        return listings

    def create_property_images(self, listings):
        for listing in listings:
            num_images = random.randint(2, 5)
            for i in range(num_images):
                PropertyImage.objects.create(
                    id=uuid.uuid4(),
                    listing=listing,
                    image='property_images/default.jpg',
                    alt_text=f"{listing.name} - {random.choice(['Living Room', 'Bedroom', 'Exterior', 'Bathroom', 'Balcony', 'Kitchen'])} View"
                )
        return

    def is_date_range_available(self, listing, start_date, end_date):
        """Check if a date range is available for a listing."""
        # Check listing.availability dictionary
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            if date_str in listing.availability and not listing.availability[date_str]:
                return False
            current_date += timedelta(days=1)

        # Check for overlapping bookings
        overlapping_bookings = Booking.objects.filter(
            listing=listing,
            booking_status__in=['PENDING', 'COMPLETED'],
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        return not overlapping_bookings.exists()

    def create_bookings(self, guests, listings):
        bookings = []
        # Ensure all but 4 guests have at least one booking
        guests_with_bookings = random.sample(guests, len(guests) - 4)
        for guest in guests_with_bookings:
            num_bookings = random.randint(1, 3)  # 1-3 bookings per guest
            for _ in range(num_bookings):
                listing = random.choice(listings)
                is_completed = random.random() < 0.8  # 80% chance of completed
                attempts = 0
                max_attempts = 10
                booking_created = False

                while attempts < max_attempts and not booking_created:
                    start_date = (timezone.now() - timedelta(days=random.randint(1, 180)) if is_completed 
                                  else timezone.now() + timedelta(days=random.randint(1, 30)))
                    end_date = start_date + timedelta(days=random.randint(1, 7))
                    if self.is_date_range_available(listing, start_date, end_date):
                        try:
                            booking = Booking.objects.create(
                                booking_id=uuid.uuid4(),
                                listing=listing,
                                user=guest,
                                guests=random.randint(1, listing.capacity),
                                start_date=start_date,
                                end_date=end_date,
                                booking_status='COMPLETED' if is_completed else 'PENDING',
                                payment_status='PAID' if is_completed else 'PENDING',
                                total_amount=random.randint(100, 1500),
                                tax_amount=random.randint(10, 150),
                                service_fee=random.randint(5, 75),
                                cancellation_deadline=start_date - timedelta(days=7) if is_completed else None,
                                is_instant_book=random.choice([True, False]),
                                special_requests=random.choice(["Early check-in", "Late check-out", "Extra towels", "Crib needed", None])
                            )
                            bookings.append(booking)
                            booking_created = True
                            # Update listing availability
                            current_date = start_date
                            while current_date <= end_date:
                                date_str = current_date.strftime('%Y-%m-%d')
                                if date_str in listing.availability:
                                    listing.availability[date_str] = False
                                current_date += timedelta(days=1)
                            listing.save()
                        except Exception:
                            attempts += 1
                    else:
                        attempts += 1

        # Ensure exactly 100 bookings (80 completed, 20 pending)
        completed_count = sum(1 for b in bookings if b.booking_status == 'COMPLETED')
        pending_count = len(bookings) - completed_count
        while completed_count < 80 or pending_count < 20:
            guest = random.choice(guests_with_bookings)
            listing = random.choice(listings)
            is_completed = completed_count < 80 and (pending_count >= 20 or random.random() < 0.8)
            attempts = 0
            max_attempts = 10
            booking_created = False

            while attempts < max_attempts and not booking_created:
                start_date = (timezone.now() - timedelta(days=random.randint(1, 180)) if is_completed 
                              else timezone.now() + timedelta(days=random.randint(1, 30)))
                end_date = start_date + timedelta(days=random.randint(1, 7))
                if self.is_date_range_available(listing, start_date, end_date):
                    try:
                        booking = Booking.objects.create(
                            booking_id=uuid.uuid4(),
                            listing=listing,
                            user=guest,
                            guests=random.randint(1, listing.capacity),
                            start_date=start_date,
                            end_date=end_date,
                            booking_status='COMPLETED' if is_completed else 'PENDING',
                            payment_status='PAID' if is_completed else 'PENDING',
                            total_amount=random.randint(100, 1500),
                            tax_amount=random.randint(10, 150),
                            service_fee=random.randint(5, 75),
                            cancellation_deadline=start_date - timedelta(days=7) if is_completed else None,
                            is_instant_book=random.choice([True, False]),
                            special_requests=random.choice(["Early check-in", "Late check-out", "Extra towels", "Crib needed", None])
                        )
                        bookings.append(booking)
                        booking_created = True
                        # Update listing availability
                        current_date = start_date
                        while current_date <= end_date:
                            date_str = current_date.strftime('%Y-%m-%d')
                            if date_str in listing.availability:
                                listing.availability[date_str] = False
                            current_date += timedelta(days=1)
                        listing.save()
                        completed_count += 1 if is_completed else 0
                        pending_count += 1 if not is_completed else 0
                    except Exception:
                        attempts += 1
                else:
                    attempts += 1

            if len(bookings) > 100:
                bookings.pop(random.randrange(len(bookings)))
                completed_count = sum(1 for b in bookings if b.booking_status == 'COMPLETED')
                pending_count = len(bookings) - completed_count

        return bookings

    def create_reviews(self, guests, listings, bookings):
        reviews = []
        completed_bookings = [b for b in bookings if b.booking_status == 'COMPLETED']
        for booking in random.sample(completed_bookings, min(80, len(completed_bookings))):
            review = Review.objects.create(
                review_id=uuid.uuid4(),
                booking=booking,
                user=booking.user,
                listing=booking.listing,
                review_date=booking.end_date + timedelta(days=random.randint(1, 10)),
                review_rating=float(random.randint(6, 10)),
                cleanliness_rating=float(random.randint(6, 10)),
                location_rating=float(random.randint(6, 10)),
                comfort_rating=float(random.randint(6, 10)),
                facilities_rating=float(random.randint(6, 10)),
                staff_rating=float(random.randint(6, 10)),
                value_for_money_rating=float(random.randint(6, 10)),
                comment=f"{'Amazing' if random.randint(6, 10) > 7 else 'Pleasant'} experience at {booking.listing.name}! {'Loved the location and amenities.' if random.randint(6, 10) > 7 else 'Comfortable and convenient.'}",
                is_approved=True,
                is_public=True
            )
            reviews.append(review)
            booking.listing.update_review_stats()
        return reviews

    def create_payments(self, guests, bookings):
        payments = []
        payment_methods = [choice[0] for choice in Payment.payment_method.field.choices]
        for booking in bookings:
            payment = Payment.objects.create(
                payment_id=uuid.uuid4(),
                booking=booking,
                user=booking.user,
                amount=booking.total_amount,
                tax_amount=booking.tax_amount,
                service_fee=booking.service_fee,
                payment_date=booking.created_at,
                payment_method=random.choice(payment_methods),
                payment_status=booking.payment_status,
                transaction_id=f"TXN-{uuid.uuid4().hex[:10]}",
                refund_amount=0,
                currency='USD'
            )
            payments.append(payment)
        return payments

    def create_conversations_and_messages(self, guests, hosts, listings):
        message_templates = [
            {
                'guest': [
                    "Hi, I'm interested in your {listing_name}. Is it available for {dates}?",
                    "Can you tell me more about the amenities at {listing_name}?",
                    "Is {listing_name} suitable for {guests} people? Any pet policies?",
                    "Looking for {nights} nights in {city}. Can you confirm availability for {listing_name}?",
                    "Does {listing_name} have parking or nearby public transport?"
                ],
                'host': [
                    "Thanks for your interest in {listing_name}! It's available for those dates. Any specific needs?",
                    "{listing_name} includes {amenities}. Let me know if you need more details!",
                    "{listing_name} can accommodate {capacity} guests. {pet_policy}. Anything else I can help with?",
                    "I’ve checked the calendar for {listing_name}, and it’s available for {nights} nights. Shall I reserve it?",
                    "{listing_name} has {parking}. Public transport is {transport}. Any other questions?"
                ]
            }
        ]

        for i in range(50):
            guest = random.choice(guests)
            listing = random.choice(listings)
            host = listing.host
            conversation = Conversation.objects.create(
                conversation_id=uuid.uuid4(),
                listing=listing,
                guest=guest,
                host=host,
                created_at=timezone.now() - timedelta(days=random.randint(1, 90))
            )
            num_messages = random.randint(5, 10)
            for j in range(num_messages):
                sender = guest if j % 2 == 0 else host
                receiver = host if j % 2 == 0 else guest
                template = random.choice(message_templates[0]['guest' if sender == guest else 'host'])
                message_content = template.format(
                    listing_name=listing.name,
                    dates=f"{(timezone.now() + timedelta(days=random.randint(7, 30))).strftime('%B %d')}",
                    guests=random.randint(1, listing.capacity),
                    nights=random.randint(1, 7),
                    city=listing.city,
                    amenities=', '.join([k for k, v in listing.amenities.items() if v]),
                    capacity=listing.capacity,
                    pet_policy='Pets allowed' if listing.pets_allowed else 'No pets allowed',
                    parking='parking' if listing.amenities.get('parking', False) else 'no parking',
                    transport='nearby' if random.choice([True, False]) else 'a short drive away'
                )
                Message.objects.create(
                    message_id=uuid.uuid4(),
                    conversation=conversation,
                    sender=sender,
                    receiver=receiver,
                    message_content=message_content,
                    timestamp=conversation.created_at + timedelta(hours=j),
                    read=random.choice([True, False])
                )