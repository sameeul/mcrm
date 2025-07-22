#!/usr/bin/env python3
"""
Enhanced Database Initialization Script
Creates all tables and populates with sample data including Pathao integration
"""

import os
import sys
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import (
    db, User, Customer, Product, ProductType, SizeGroup, SizeGroupMapping, 
    Order, OrderItem, PathaoCity, PathaoZone, PathaoToken, PathaoStore
)

def init_database():
    """Initialize database with tables and sample data"""
    app = create_app()
    
    with app.app_context():
        print("🗄️  Dropping existing tables...")
        db.drop_all()
        
        print("🏗️  Creating new tables...")
        db.create_all()
        
        print("👤 Creating users...")
        create_users()
        
        # print("🏷️  Creating product types...")
        # create_product_types()
        
        # print("📏 Creating size groups...")
        # create_size_groups()
        
        # print("📦 Creating products...")
        # create_products()
        
        # print("👥 Creating customers...")
        # create_customers()
        
        print("🌍 Creating sample Pathao location data...")
        create_sample_pathao_data()
        
        # print("📋 Creating sample orders...")
        # create_orders()
        
        print("✅ Database initialization completed successfully!")
        print("\n🔑 Login credentials:")
        print("   Admin: admin / admin123")
        print("   User:  user / user123")

def create_users():
    """Create sample users"""
    # Admin user
    admin = User(
        username='admin',
        email='admin@example.com',
        role='admin'
    )
    admin.set_password('admin123')
    admin.last_login = datetime.utcnow()
    db.session.add(admin)
    
    # Regular user
    user = User(
        username='user',
        email='user@example.com',
        role='user'
    )
    user.set_password('user123')
    user.last_login = datetime.utcnow() - timedelta(hours=2)
    db.session.add(user)
    
    # Additional users
    for i in range(3, 6):
        test_user = User(
            username=f'user{i}',
            email=f'user{i}@example.com',
            role='user'
        )
        test_user.set_password('password123')
        db.session.add(test_user)
    
    db.session.commit()

def create_product_types():
    """Create product types"""
    product_types = [
        {'name': 'T-Shirt', 'description': 'Casual cotton t-shirts'},
        {'name': 'Polo Shirt', 'description': 'Collared polo shirts'},
        {'name': 'Hoodie', 'description': 'Hooded sweatshirts'},
        {'name': 'Jeans', 'description': 'Denim jeans'},
        {'name': 'Shorts', 'description': 'Casual shorts'},
        {'name': 'Dress', 'description': 'Women\'s dresses'},
        {'name': 'Jacket', 'description': 'Outerwear jackets'},
        {'name': 'Sneakers', 'description': 'Casual sneakers'},
    ]
    
    for pt_data in product_types:
        product_type = ProductType(**pt_data)
        db.session.add(product_type)
    
    db.session.commit()

def create_size_groups():
    """Create size groups with mappings"""
    size_groups_data = [
        # Clothing sizes
        {'product_type': 'T-Shirt', 'name': 'Standard', 'sizes': ['XS', 'S', 'M', 'L', 'XL', 'XXL']},
        {'product_type': 'Polo Shirt', 'name': 'Standard', 'sizes': ['S', 'M', 'L', 'XL', 'XXL']},
        {'product_type': 'Hoodie', 'name': 'Standard', 'sizes': ['S', 'M', 'L', 'XL', 'XXL']},
        {'product_type': 'Jeans', 'name': 'Waist Size', 'sizes': ['28', '30', '32', '34', '36', '38', '40']},
        {'product_type': 'Shorts', 'name': 'Standard', 'sizes': ['S', 'M', 'L', 'XL']},
        {'product_type': 'Dress', 'name': 'Standard', 'sizes': ['XS', 'S', 'M', 'L', 'XL']},
        {'product_type': 'Jacket', 'name': 'Standard', 'sizes': ['S', 'M', 'L', 'XL', 'XXL']},
        # Shoe sizes
        {'product_type': 'Sneakers', 'name': 'US Men', 'sizes': ['7', '8', '9', '10', '11', '12']},
        {'product_type': 'Sneakers', 'name': 'US Women', 'sizes': ['5', '6', '7', '8', '9', '10']},
    ]
    
    for sg_data in size_groups_data:
        # Find product type
        product_type = ProductType.query.filter_by(name=sg_data['product_type']).first()
        if product_type:
            size_group = SizeGroup(
                name=sg_data['name'],
                product_type_id=product_type.id,
                description=f"{sg_data['name']} sizes for {sg_data['product_type']}"
            )
            db.session.add(size_group)
            db.session.flush()  # Get ID
            
            # Add size mappings
            for size in sg_data['sizes']:
                mapping = SizeGroupMapping(size_group_id=size_group.id, size=size)
                db.session.add(mapping)
    
    db.session.commit()

def create_products():
    """Create sample products"""
    products_data = [
        # T-Shirts
        {'type': 'T-Shirt', 'name': 'Classic Cotton Tee', 'colors': ['Red', 'Blue', 'Black', 'White'], 'sizes': ['S', 'M', 'L', 'XL'], 'price': 15.99},
        {'type': 'T-Shirt', 'name': 'Vintage Logo Tee', 'colors': ['Navy', 'Gray'], 'sizes': ['M', 'L', 'XL'], 'price': 18.99},
        {'type': 'T-Shirt', 'name': 'Premium Organic Tee', 'colors': ['White', 'Black'], 'sizes': ['S', 'M', 'L'], 'price': 24.99},
        
        # Polo Shirts
        {'type': 'Polo Shirt', 'name': 'Classic Polo', 'colors': ['Navy', 'White', 'Red'], 'sizes': ['M', 'L', 'XL'], 'price': 29.99},
        {'type': 'Polo Shirt', 'name': 'Performance Polo', 'colors': ['Blue', 'Gray'], 'sizes': ['S', 'M', 'L'], 'price': 34.99},
        
        # Hoodies
        {'type': 'Hoodie', 'name': 'Comfort Hoodie', 'colors': ['Gray', 'Black', 'Navy'], 'sizes': ['M', 'L', 'XL'], 'price': 45.99},
        {'type': 'Hoodie', 'name': 'Zip-Up Hoodie', 'colors': ['Black', 'Blue'], 'sizes': ['L', 'XL'], 'price': 52.99},
        
        # Jeans
        {'type': 'Jeans', 'name': 'Slim Fit Jeans', 'colors': ['Blue', 'Black'], 'sizes': ['30', '32', '34', '36'], 'price': 59.99},
        {'type': 'Jeans', 'name': 'Regular Fit Jeans', 'colors': ['Blue'], 'sizes': ['32', '34', '36', '38'], 'price': 54.99},
        
        # Shorts
        {'type': 'Shorts', 'name': 'Casual Shorts', 'colors': ['Navy', 'Gray', 'Brown'], 'sizes': ['M', 'L', 'XL'], 'price': 24.99},
        
        # Dresses
        {'type': 'Dress', 'name': 'Summer Dress', 'colors': ['Red', 'Blue', 'Pink'], 'sizes': ['S', 'M', 'L'], 'price': 39.99},
        {'type': 'Dress', 'name': 'Casual Dress', 'colors': ['Black', 'Navy'], 'sizes': ['M', 'L'], 'price': 44.99},
        
        # Jackets
        {'type': 'Jacket', 'name': 'Denim Jacket', 'colors': ['Blue', 'Black'], 'sizes': ['M', 'L', 'XL'], 'price': 69.99},
        
        # Sneakers
        {'type': 'Sneakers', 'name': 'Classic Sneakers', 'colors': ['White', 'Black'], 'sizes': ['8', '9', '10', '11'], 'price': 79.99},
        {'type': 'Sneakers', 'name': 'Running Shoes', 'colors': ['Blue', 'Gray'], 'sizes': ['9', '10', '11'], 'price': 89.99},
    ]
    
    for product_data in products_data:
        product_type = ProductType.query.filter_by(name=product_data['type']).first()
        if product_type:
            for color in product_data['colors']:
                for size in product_data['sizes']:
                    # Generate random stock quantity
                    import random
                    quantity = random.randint(5, 50)
                    
                    product = Product(
                        name=product_data['name'],
                        product_type_id=product_type.id,
                        color=color,
                        size=size,
                        quantity=quantity,
                        price=product_data['price']
                    )
                    
                    # Auto-assign size group
                    product.auto_assign_size_group()
                    
                    db.session.add(product)
    
    db.session.commit()

def create_customers():
    """Create sample customers"""
    customers_data = [
        {'name': 'John Doe', 'phone': '+8801712345678', 'address': 'House 123, Road 5, Dhanmondi, Dhaka'},
        {'name': 'Jane Smith', 'phone': '+8801812345679', 'address': 'Flat 4B, Building 7, Gulshan 2, Dhaka'},
        {'name': 'Ahmed Rahman', 'phone': '+8801912345680', 'address': 'House 45, Block C, Bashundhara R/A, Dhaka'},
        {'name': 'Fatima Khan', 'phone': '+8801612345681', 'address': 'Apartment 3A, Road 12, Uttara, Dhaka'},
        {'name': 'Michael Johnson', 'phone': '+8801512345682', 'address': 'House 78, Sector 7, Uttara, Dhaka'},
        {'name': 'Sarah Wilson', 'phone': '+8801412345683', 'address': 'Flat 2C, Green Road, Dhanmondi, Dhaka'},
        {'name': 'David Brown', 'phone': '+8801312345684', 'address': 'House 234, Road 15, Banani, Dhaka'},
        {'name': 'Lisa Davis', 'phone': '+8801212345685', 'address': 'Apartment 5D, Gulshan Avenue, Gulshan 1, Dhaka'},
    ]
    
    for customer_data in customers_data:
        customer = Customer(**customer_data)
        db.session.add(customer)
    
    db.session.commit()

def create_sample_pathao_data():
    """Create sample Pathao location data for testing"""
    # Sample cities
    cities_data = [
        {'city_id': 1, 'city_name': 'Dhaka'},
        {'city_id': 2, 'city_name': 'Chittagong'},
        {'city_id': 3, 'city_name': 'Sylhet'},
    ]
    
    for city_data in cities_data:
        city = PathaoCity(**city_data)
        db.session.add(city)
    
    # Sample zones for Dhaka
    zones_data = [
        {'zone_id': 1, 'zone_name': 'Dhanmondi', 'city_id': 1},
        {'zone_id': 2, 'zone_name': 'Gulshan', 'city_id': 1},
        {'zone_id': 3, 'zone_name': 'Uttara', 'city_id': 1},
        {'zone_id': 4, 'zone_name': 'Banani', 'city_id': 1},
        {'zone_id': 5, 'zone_name': 'Mirpur', 'city_id': 1},
    ]
    
    for zone_data in zones_data:
        zone = PathaoZone(**zone_data)
        db.session.add(zone)
    
    db.session.commit()

def create_orders():
    """Create sample orders"""
    import random
    
    users = User.query.all()
    customers = Customer.query.all()
    products = Product.query.filter(Product.quantity > 0).all()

    
    if not users or not customers or not products or not areas:
        print("⚠️  Skipping order creation - missing required data")
        return
    
    statuses = ['pending', 'processing', 'completed', 'cancelled']
    
    for i in range(15):  # Create 15 sample orders
        user = random.choice(users)
        customer = random.choice(customers)
        area = random.choice(areas)
        
        # Get zone and city info
        zone = PathaoZone.query.get(area.zone_id)
        city = PathaoCity.query.get(zone.city_id)
        
        order = Order(
            user_id=user.id,
            customer_id=customer.id,
            city_id=city.city_id,
            city_name=city.city_name,
            zone_id=zone.zone_id,
            zone_name=zone.zone_name,
            area_id=area.area_id,
            area_name=area.area_name,
            status=random.choice(statuses),
            total_amount=0,
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
        )
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Add 1-3 items per order
        num_items = random.randint(1, 3)
        total_amount = 0
        
        for _ in range(num_items):
            product = random.choice(products)
            max_quantity = min(product.quantity, 5)  # Max 5 items per order item
            quantity = random.randint(1, max_quantity)
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price
            )
            db.session.add(order_item)
            
            # Update product stock
            product.quantity -= quantity
            total_amount += float(product.price) * quantity
        
        order.total_amount = total_amount
        order.updated_at = order.created_at + timedelta(hours=random.randint(1, 48))
    
    db.session.commit()

if __name__ == '__main__':
    init_database()
