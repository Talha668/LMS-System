import requests
import json
import hmac
import hashlib
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from .models import Course, Payment, Enrollment, User
from .notifications import EmailService










class LemonSqueezyPaymentService:
    """Service for handling payment with lemon squeezy"""
    def __init__(self):
        self.api_key = settings.LEMON_SQUEEZY_API_KEY
        self.store_id = settings.LEMON_SQUEEZY_STORE_ID
        self.api_url = settings.LEMON_SQUEEZY_API_URL
        self.headers = {
            'Accept': 'application/vnd.api+json',
            'Content-type': 'application/vnd.api+json',
            'Authorization': f'Bearer {self.api_key}'
        }

    def create_checkout(self, request, course):
        """Create a lemon squeezy checkout for a course"""    
        if course.price == 0:
            return None
        
        # Create a product in lemon squeezy if not exists
        product_id = self.get_or_create_product(course)

        # Create a checkout
        checkout_data = {
            'data': {
                'type': 'checkouts',
                'attributes': {
                    'checkout_data': {
                        'custom': {
                            'course_id': course.id,
                            'user_id': request.user.id,
                            'user_email': request.user.email,
                            'user_name': request.user.get_full_name()
                        }
                    },
                    'product_options': {
                        'name': course.title,
                        'description': course.description[:500],
                        'redirect_url': request.build_absolute_url(
                            reverse('payment_success', args=[course.id])
                        ),
                        'cancel_url': request.build_absolute_url(
                            reverse('payment_cancel', args=[course.id])
                        ),
                    }
                },
                'relationships': {
                    'store': {
                        'data': {
                            'type': 'stores',
                            'id': self.store_id
                        }
                    },
                    'variant': {
                        'data': {
                            'type': 'variants',
                            'id': product_id
                        }
                    }
                }
            }
        }

        try:
            response = request.post(
                f'{self.api_url}/checkouts',
                headers=self.headers,
                json=checkout_data
            )

            if response.status_code == 201:
                checkout_url = response.json()['data']['attributes']['url']

                # Create payment record
                Payment.objects.create(
                    user=request.user,
                    course=course,
                    amount=course.price,
                    payment_id=response.josn()['data']['id'],
                    status='pending'
                )
                
                return checkout_url
            else:
                raise Exception(f"Lemon squeezy error: {response.text}")
            
        except Exception as e:
            raise Exception(f"Payment creation failed: {str(e)}")


    def get_or_create_product(self, course):
        """Get or create a product in lemon squeezy"""
        # Check if product exists
        try:
            # Search or existing product
            response = requests.get(
                f'{self.api_url}/products',
                headers=self.headers,
                params={'filter[store_id]': self.store_id}
            )

            if response.status_code == 200:
                products = requests.json()['data']
                for product in products:
                    if product['attributes']['name'] == course.title:
                        # Return existing variant
                        variants_reponse = requests.get(
                            f'{self.api_url}/variants',
                            headers=self.headers,
                            params={'filter[product_id]': product['id']}
                        )
                        if variants_reponse.status_code == 200:
                            variants = variants_reponse.json()['data']
                            if variants:
                                return variants[0]['id']
        except:
            pass

        # Create new product
        product_data = {
            'data': {
                'type': 'products',
                'attributes': {
                    'name': course.title,
                    'description': course.description,
                    'status': 'published'
                },
                'realtionships': {
                    'store': {
                        'data': {
                            'type': 'stores',
                            'id': self.store_id
                        }
                    }
                }
            }
        }                    

        response = requests.post(
            f'{self.api_url}/products',
            headers=self.headers,
            json=product_data
        )

        if response.status_code == 201:
            product_id = response.json()['data']['id']

            # Create variant
            variant_data = {
                'data': {
                    'type': 'variants',
                    'attributes': {
                        'name': 'Standard',
                        'price': course.price * 100,      # Lemon squeezy uses cents
                        'status': 'published',
                        'is_subscription': False
                    },
                    'relationships': {
                        'product': {
                            'data': {
                                'type': 'products',
                                'id': product_id
                            }
                        }
                    }
                }
            }

            variants_reponse = requests.post(
                f'{self.api_url}/variants',
                headers=self.headers,
                json=variant_data
            )

            if variants_reponse.status_code == 201:
                return variants_reponse.josn()['data']['id']
            
        raise Exception("Failed to create product in lemon squeezy")   


    def handle_webhooks(self, request):
        """Handle lemon squeezy webhook events"""
        # Verify webhook signature
        signature = request.headers.get('X-Signature')
        if not signature:
            return False, 'Missing signature'

        # Varify signature 
        secret = settings.LEMON_SQUEEZY_WEBHOOK_SECRET
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            request.body,
            hashlib.sha256
        ).hexdigext()  

        if not hmac.compare_digest(signature, expected_signature):
            return False, 'Invalid signature'
        
        # Parse webhook data
        try:
            data = json.loads(request.body)
            event_name = data.get('meta', {}).get('event_name')

            if event_name == 'order_created':
                return self.handle_order_created(data)
            elif event_name == 'order_paid':
                return self.handle_order_paid(data)
            elif event_name == 'order_refunded':
                return self.handle_order_refunded(data)
            else:
                return True, f'Unhandled event: {event_name}'
        
        except Exception as e:
            return False, str(e)


    def handle_order_created(self, data):
        """Handle order created event"""
        order_data = data.get('data', {})
        attributes = order_data.get('attributes', {})
        custom_data = attributes.get('custom', {})
        
        course_id = custom_data.get('course_id')
        user_id = custom_data.get('user_id')

        if course_id and user_id:
            try:
                course = Course.objects.get(id=course_id)
                user = User.objects.get(id=user_id)

                # Update payment status
                Payment.objects.filter(
                    user=user,
                    course=course,
                    status='pending'
                ).update(
                    status='processing',
                    payment_id=order_data.get('id')
                )

                return True, 'Order processed'
            except:
                return False, 'Invalid course or user'
            
        return False, 'Missing custom data'


    def handle_order_paid(self, data):
        """Handle order paid event"""    
        order_data = data.get('data', {})
        attributes = order_data.get('attributes', {})
        custom_data = attributes.get('custom', {})

        course_id = custom_data.get('course')
        user_id = custom_data.get('user')

        if course_id and user_id:
            try:
                course = Course.objects.filter(id=course_id)
                user = User.objects.filter(id-user_id)

                # Update payment status
                payment = Payment.objects.filter(
                    user=user,
                    course=course
                ).first()

                if payment:
                    payment.status = 'completed'
                    payment.paid_at = timezone.now()
                    payment.save()

                    # Enroll user in course
                    enrollment, created = Enrollment.objects.get_or_create(
                        student=user,
                        course=course
                    )

                    if created:
                        # Send enrollment confirmation
                        try:
                            EmailService.send_course_enrollment_email(user, course)
                        except:
                            pass

                return True, 'Payment processed'
            except:
                return False, 'Invalid course or user'

        return False, 'Missing custom data'


    def handle_order_refunded(self, data):
        """Handel order refunded event"""           
        order_data = data.get('data', {})
        attributes = order_data.get('attributes', {})
        custom_data = attributes.get('custom', {})

        course_id = custom_data.get('course')
        user_id = custom_data.get('user')

        if course_id and user_id:
            try:
                course = Course.objects.filter(id=course_id)
                user = User.objects.filter(id=user_id)

                # Upate payment status
                Payment.objects.filter(
                    user=user,
                    course=course,
                ).update(
                    status='refunded'
                )

                # Unenroll user
                Enrollment.objects.filter(
                    student=user,
                    course=course
                ).delete()

                return True, 'Refund processed'
            except:
                return False, 'Invalid course or user'

        return False, 'Missing custom data'    