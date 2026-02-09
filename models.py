from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' or 'user'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True)
    
    def __repr__(self):
        return f'<Customer {self.name}>'

class PathaoCity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, unique=True, nullable=False)  # Pathao city_id
    city_name = db.Column(db.String(100), nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    zones = db.relationship('PathaoZone', backref='city', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PathaoCity {self.city_name}>'

class PathaoZone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, unique=True, nullable=False)  # Pathao zone_id
    zone_name = db.Column(db.String(100), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('pathao_city.city_id'), nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PathaoZone {self.zone_name}>'


class PathaoToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_expired(self):
        """Check if token is expired"""
        return datetime.now(UTC) >= self.expires_at
    
    def __repr__(self):
        return f'<PathaoToken expires_at={self.expires_at}>'

class ProductType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='product_type', lazy=True)
    size_groups = db.relationship('SizeGroup', backref='product_type', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ProductType {self.name}>'

class SizeGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    product_type_id = db.Column(db.Integer, db.ForeignKey('product_type.id'), nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='size_group', lazy=True)
    size_mappings = db.relationship('SizeGroupMapping', backref='size_group', lazy=True, cascade='all, delete-orphan')
    
    # Unique constraint: same name can exist for different product types
    __table_args__ = (db.UniqueConstraint('name', 'product_type_id', name='_name_product_type_uc'),)
    
    def get_sizes(self):
        """Get all sizes assigned to this size group"""
        return [mapping.size for mapping in self.size_mappings]
    
    def has_size(self, size):
        """Check if a specific size is assigned to this group"""
        return any(mapping.size == size for mapping in self.size_mappings)
    
    def add_size(self, size):
        """Add a size to this group"""
        if not self.has_size(size):
            mapping = SizeGroupMapping(size_group_id=self.id, size=size)
            db.session.add(mapping)
            return True
        return False
    
    def remove_size(self, size):
        """Remove a size from this group"""
        mapping = SizeGroupMapping.query.filter_by(size_group_id=self.id, size=size).first()
        if mapping:
            db.session.delete(mapping)
            return True
        return False
    
    def __repr__(self):
        return f'<SizeGroup {self.name} ({self.product_type.name})>'

class SizeGroupMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    size_group_id = db.Column(db.Integer, db.ForeignKey('size_group.id'), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint: each size can only belong to one group per product type
    __table_args__ = (db.UniqueConstraint('size_group_id', 'size', name='_size_group_size_uc'),)
    
    def __repr__(self):
        return f'<SizeGroupMapping {self.size} -> {self.size_group.name}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Specific product name/style
    product_type_id = db.Column(db.Integer, db.ForeignKey('product_type.id'), nullable=False)
    product_code = db.Column(db.String(5), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    size_group_id = db.Column(db.Integer, db.ForeignKey('size_group.id'))
    quantity = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    
    # Unique constraint for product_type+name+size combination
    __table_args__ = (db.UniqueConstraint('product_type_id', 'name', 'size', name='_product_unique_uc'),)
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.quantity > 0
    
    @property
    def is_low_stock(self):
        """Check if product has low stock (less than 10)"""
        return self.quantity < 10
    
    @property
    def stock_quantity(self):
        """Backward compatibility property"""
        return self.quantity
    
    @stock_quantity.setter
    def stock_quantity(self, value):
        """Backward compatibility setter"""
        self.quantity = value
    
    def reduce_stock(self, quantity):
        """Reduce stock quantity"""
        if self.quantity >= quantity:
            self.quantity -= quantity
            return True
        return False
    
    def get_compatible_products(self):
        """Get products with compatible sizes from the same size group"""
        if not self.size_group_id:
            return []
        return Product.query.filter(
            Product.product_type_id == self.product_type_id,
            Product.name == self.name,
            Product.size_group_id == self.size_group_id,
            Product.id != self.id
        ).all()
    
    def get_total_available_quantity(self):
        """Get total quantity available including compatible sizes"""
        total = self.quantity
        for compatible in self.get_compatible_products():
            total += compatible.quantity
        return total
    
    def can_fulfill_order(self, requested_quantity):
        """Check if order can be fulfilled using this product and compatible sizes"""
        return self.get_total_available_quantity() >= requested_quantity
    
    def fulfill_order(self, requested_quantity):
        """Fulfill order by reducing stock from this product and compatible sizes"""
        if not self.can_fulfill_order(requested_quantity):
            return False
        
        remaining = requested_quantity
        
        # First, use stock from the exact product
        if self.quantity > 0:
            used = min(self.quantity, remaining)
            self.quantity -= used
            remaining -= used
        
        # Then use stock from compatible sizes
        if remaining > 0:
            for compatible in self.get_compatible_products():
                if remaining <= 0:
                    break
                if compatible.quantity > 0:
                    used = min(compatible.quantity, remaining)
                    compatible.quantity -= used
                    remaining -= used
        
        self.updated_at = datetime.now(UTC)
        return remaining == 0
    
    def auto_assign_size_group(self):
        """Automatically assign size group based on product type and size"""
        if not self.product_type_id or not self.size:
            return False
        
        # Find size group that contains this size for this product type
        mapping = SizeGroupMapping.query.join(SizeGroup).filter(
            SizeGroup.product_type_id == self.product_type_id,
            SizeGroupMapping.size == self.size
        ).first()
        
        if mapping:
            self.size_group_id = mapping.size_group_id
            return True
        return False
    
    def get_display_name(self):
        """Get formatted display name for the product"""
        return f"{self.product_type.name} - {self.name}"
    
    def __repr__(self):
        return f'<Product {self.name} ({self.product_type.name}) - {self.product_code} - {self.size}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    
    # Pathao Location Information
    city_id = db.Column(db.Integer, nullable=True)  # Pathao city_id
    city_name = db.Column(db.String(100), nullable=True)
    zone_id = db.Column(db.Integer, nullable=True)  # Pathao zone_id  
    zone_name = db.Column(db.String(100), nullable=True)
    shipping_requested = db.Column(db.Boolean, default=False)  # Whether shipping is requested
    
    # Order Financial Details
    delivery_charge = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    discount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, processing, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    @property
    def item_count(self):
        """Get total number of items in order"""
        return sum(item.quantity for item in self.order_items)
    
    @property
    def delivery_location(self):
        """Get formatted delivery location"""
        parts = []
        if self.zone_name:
            parts.append(self.zone_name)
        if self.city_name:
            parts.append(self.city_name)
        return ', '.join(parts) if parts else 'Location not specified'
    
    @property
    def products_subtotal(self):
        """Get subtotal of all products (before delivery charges and discount)"""
        return sum(item.quantity * item.unit_price for item in self.order_items)
    
    @property
    def final_total(self):
        """Get final total including delivery charges and discount"""
        return int(self.products_subtotal) + int(self.delivery_charge) - int(self.discount)
    
    def calculate_total(self):
        """Calculate total amount including delivery charges and discount"""
        self.total_amount = self.final_total
        return self.total_amount
    
    def __repr__(self):
        return f'<Order {self.id}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    tracking_code = db.Column(db.String(12), nullable=True)  # Will be populated after insert
    
    @property
    def subtotal(self):
        """Calculate subtotal for this item"""
        return self.quantity * self.unit_price
    
    def generate_tracking_code(self):
        """Generate tracking code: product_code + size(max 4 chars) + padded ID"""
        if not self.product or not self.id:
            return None
        
        # Get product code (max 5 chars as per Product model)
        product_code = self.product.product_code or ""
        
        # Get size, truncate to max 4 chars
        size = (self.product.size or "")[:4]
        
        # Calculate remaining space for ID padding
        used_chars = len(product_code) + len(size)
        id_padding = 12 - used_chars
        
        # Ensure we have at least 1 character for ID
        if id_padding < 1:
            # If product_code + size is too long, truncate size further
            max_size_chars = 12 - len(product_code) - 1  # Reserve 1 char for ID minimum
            size = size[:max(0, max_size_chars)]
            id_padding = 12 - len(product_code) - len(size)
        
        # Format ID with zero padding
        padded_id = str(self.id).zfill(id_padding)
        
        # If ID is too long even with no padding, truncate from left
        if len(padded_id) > id_padding:
            padded_id = padded_id[-id_padding:]
        
        return f"{product_code}{size}{padded_id}"
    
    def update_tracking_code(self):
        """Update the tracking code field"""
        self.tracking_code = self.generate_tracking_code()
        return self.tracking_code
    
    def __repr__(self):
        return f'<OrderItem {self.id} - {self.tracking_code or "No tracking code"}>'

# Login attempt tracking for security
class LoginAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 compatible
    username = db.Column(db.String(80))
    success = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LoginAttempt {self.ip_address} - {self.success}>'

class PathaoStore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(100), nullable=False)
    store_address = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Store {self.store_name}>'

class PathaoDelivery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    consignment_id = db.Column(db.String(50), unique=True, nullable=False)  # Pathao's tracking ID
    merchant_order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    order_status = db.Column(db.String(50), nullable=False)  # Pending, Pickup_Requested, etc.
    delivery_fee = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = db.relationship('Order', backref='pathao_delivery', lazy=True)
    
    @property
    def is_delivered(self):
        """Check if delivery is completed"""
        return self.order_status.lower() in ['delivered', 'completed']
    
    @property
    def is_pending(self):
        """Check if delivery is still pending"""
        return self.order_status.lower() == 'pending'
    
    @property
    def is_in_transit(self):
        """Check if delivery is in transit"""
        transit_statuses = ['pickup_requested', 'picked_up', 'in_transit', 'out_for_delivery']
        return self.order_status.lower().replace(' ', '_') in transit_statuses
    
    def update_status(self, new_status, new_delivery_fee=None):
        """Update delivery status and optionally delivery fee"""
        self.order_status = new_status
        if new_delivery_fee is not None:
            self.delivery_fee = new_delivery_fee
        self.updated_at = datetime.now(UTC)
    
    def __repr__(self):
        return f'<PathaoDelivery {self.consignment_id} - {self.order_status}>'
