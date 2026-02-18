from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, IntegerField, DecimalField, HiddenField
from wtforms.validators import DataRequired, Email, Length, NumberRange, ValidationError, EqualTo, Regexp
from models import User, Product, ProductType, SizeGroup, Customer

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])

class CreateUserForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address'),
        Length(max=120, message='Email must be less than 120 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[
        ('user', 'User'),
        ('admin', 'Admin')
    ], validators=[DataRequired()])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please choose a different one.')

class ProductTypeForm(FlaskForm):
    name = StringField('Product Type Name', validators=[
        DataRequired(message='Product type name is required'),
        Length(min=1, max=50, message='Name must be between 1 and 50 characters')
    ])
    description = TextAreaField('Description', validators=[
        Length(max=200, message='Description must be less than 200 characters')
    ])
    
    def __init__(self, *args, **kwargs):
        self.product_type_id = kwargs.pop('product_type_id', None)
        super(ProductTypeForm, self).__init__(*args, **kwargs)
    
    def validate_name(self, field):
        query = ProductType.query.filter_by(name=field.data)
        if self.product_type_id:
            query = query.filter(ProductType.id != self.product_type_id)
        if query.first():
            raise ValidationError('Product type with this name already exists.')

class SizeGroupForm(FlaskForm):
    name = StringField('Size Group Name', validators=[
        DataRequired(message='Size group name is required'),
        Length(min=1, max=50, message='Name must be between 1 and 50 characters')
    ])
    product_type_id = SelectField('Product Type', coerce=int, validators=[
        DataRequired(message='Please select a product type')
    ])
    description = TextAreaField('Description', validators=[
        Length(max=200, message='Description must be less than 200 characters')
    ])
    sizes = StringField('Sizes (comma-separated)', validators=[
        DataRequired(message='Please specify at least one size')
    ])
    
    def __init__(self, *args, **kwargs):
        self.size_group_id = kwargs.pop('size_group_id', None)
        super(SizeGroupForm, self).__init__(*args, **kwargs)
        # Populate product type choices
        self.product_type_id.choices = [
            (pt.id, pt.name) for pt in ProductType.query.all()
        ]
        if not self.product_type_id.choices:
            self.product_type_id.choices = [(0, 'No product types available')]
    
    def validate_name(self, field):
        if self.product_type_id.data:
            query = SizeGroup.query.filter_by(
                name=field.data,
                product_type_id=self.product_type_id.data
            )
            if self.size_group_id:
                query = query.filter(SizeGroup.id != self.size_group_id)
            if query.first():
                raise ValidationError('Size group with this name already exists for this product type.')
    
    def validate_sizes(self, field):
        if field.data:
            sizes = [s.strip() for s in field.data.split(',') if s.strip()]
            if not sizes:
                raise ValidationError('Please specify at least one size.')
            
            # Check for duplicate sizes within the same product type
            if self.product_type_id.data:
                from models import SizeGroupMapping
                existing_mappings = SizeGroupMapping.query.join(SizeGroup).filter(
                    SizeGroup.product_type_id == self.product_type_id.data,
                    SizeGroupMapping.size.in_(sizes)
                )
                if self.size_group_id:
                    existing_mappings = existing_mappings.filter(SizeGroup.id != self.size_group_id)
                
                conflicts = existing_mappings.all()
                if conflicts:
                    conflict_sizes = [m.size for m in conflicts]
                    raise ValidationError(f'These sizes are already assigned to other groups: {", ".join(conflict_sizes)}')

class ProductForm(FlaskForm):
    name = StringField('Product Name/Style', validators=[
        DataRequired(message='Product name is required'),
        Length(min=1, max=100, message='Product name must be between 1 and 100 characters')
    ])
    product_type_id = SelectField('Product Type', coerce=int, validators=[
        DataRequired(message='Please select a product type')
    ])
    product_code = StringField('Product Code', validators=[
        DataRequired(message='Product code is required'),
        Length(min=1, max=5, message='Product code must be 1-5 characters'),
        Regexp(r'^[A-Za-z0-9]+$', message='Product code can only contain letters and numbers')
    ])
    size = StringField('Size', validators=[
        DataRequired(message='Size is required'),
        Length(min=1, max=20, message='Size must be between 1 and 20 characters')
    ])
    size_group_id = SelectField('Size Group (Optional)', coerce=int, validators=[])
    quantity = IntegerField('Quantity', validators=[
        DataRequired(message='Quantity is required'),
        NumberRange(min=0, message='Quantity cannot be negative')
    ])
    price = DecimalField('Price', validators=[
        DataRequired(message='Price is required'),
        NumberRange(min=0.01, message='Price must be greater than 0')
    ], places=2)
    
    def __init__(self, *args, **kwargs):
        self.product_id = kwargs.pop('product_id', None)
        super(ProductForm, self).__init__(*args, **kwargs)
        
        # Populate product type choices
        self.product_type_id.choices = [
            (pt.id, pt.name) for pt in ProductType.query.all()
        ]
        if not self.product_type_id.choices:
            self.product_type_id.choices = [(0, 'No product types available')]
        
        # Populate size group choices (will be filtered by JavaScript based on product type)
        self.size_group_id.choices = [(0, 'Auto-assign based on size')] + [
            (sg.id, f"{sg.name} ({', '.join(sg.get_sizes())})")
            for sg in SizeGroup.query.all()
        ]
    
    def validate_product_code(self, product_code):
        # Check for duplicate product code
        pass
    
    def validate_product_combination(self):
        # Check for duplicate product combination
        if self.product_type_id.data and self.name.data and self.size.data:
            query = Product.query.filter_by(
                product_type_id=self.product_type_id.data,
                name=self.name.data,
                size=self.size.data
            )
            if self.product_id:
                query = query.filter(Product.id != self.product_id)
            if query.first():
                raise ValidationError('Product with this type, name, and size combination already exists.')
    
    # Backward compatibility
    @property
    def stock_quantity(self):
        return self.quantity

class OrderItemForm(FlaskForm):
    product_id = SelectField('Product', coerce=int, validators=[
        DataRequired(message='Please select a product')
    ])
    quantity = IntegerField('Quantity', validators=[
        DataRequired(message='Quantity is required'),
        NumberRange(min=1, message='Quantity must be at least 1')
    ])
    
    def __init__(self, *args, **kwargs):
        super(OrderItemForm, self).__init__(*args, **kwargs)
        # Populate product choices with in-stock products only
        self.product_id.choices = [
            (p.id, f"{p.get_display_name()} - {p.product_code} - {p.size} - ${p.price} (Stock: {p.quantity})")
            for p in Product.query.filter(Product.quantity > 0).all()
        ]
        if not self.product_id.choices:
            self.product_id.choices = [(0, 'No products in stock')]
    
    def validate_quantity(self, quantity):
        if self.product_id.data:
            product = Product.query.get(self.product_id.data)
            if product and quantity.data > product.get_total_available_quantity():
                available = product.get_total_available_quantity()
                raise ValidationError(f'Only {available} items available (including compatible sizes)')

class CreateOrderForm(FlaskForm):
    # Customer Information
    customer_name = StringField('Customer Name', validators=[
        DataRequired(message='Customer name is required'),
        Length(min=2, max=100, message='Customer name must be between 2 and 100 characters')
    ])
    customer_phone = StringField('Contact Number', validators=[
        DataRequired(message='Contact number is required'),
        Length(min=10, max=20, message='Contact number must be between 10 and 20 characters'),
        Regexp(r'^[\d\+\-\(\)\s]+$', message='Contact number can only contain digits, +, -, (, ), and spaces')
    ])
    customer_address = TextAreaField('Address', validators=[
        DataRequired(message='Address is required'),
        Length(min=10, max=500, message='Address must be between 10 and 500 characters')
    ])
    
    # Location Selection (Pathao Integration)
    city_id = SelectField('City', coerce=int, validators=[
        DataRequired(message='Please select a city')
    ])
    zone_id = SelectField('Zone', coerce=int, validators=[
        DataRequired(message='Please select a zone')
    ])
    
    # Products will be handled via JavaScript and submitted as JSON
    products_data = HiddenField('Products Data')
    
    # Order Financial Details
    delivery_charge = IntegerField('Delivery Charges', validators=[
        NumberRange(min=0, message='Delivery charges cannot be negative')
    ], default=0)
    discount = IntegerField('Discount', validators=[
        NumberRange(min=0, message='Discount cannot be negative')
    ], default=0)
    
    def __init__(self, *args, **kwargs):
        super(CreateOrderForm, self).__init__(*args, **kwargs)
        
        # Load all location data from database for validation
        from models import PathaoCity, PathaoZone
        
        self.city_id.choices = [(0, 'Select City')] + [
            (city.city_id, city.city_name) for city in PathaoCity.query.all()
        ]
        self.zone_id.choices = [(0, 'Select Zone')] + [
            (zone.zone_id, zone.zone_name) for zone in PathaoZone.query.all()
        ]
    
    def validate_products_data(self, products_data):
        """Validate the products data submitted via JavaScript"""
        import json
        
        if not products_data.data:
            raise ValidationError('Please select at least one product')
        
        try:
            products = json.loads(products_data.data)
        except (json.JSONDecodeError, TypeError):
            raise ValidationError('Invalid products data format')
        
        if not products or not isinstance(products, list):
            raise ValidationError('Please select at least one product')
        
        # Validate each product
        for i, product_data in enumerate(products):
            if not isinstance(product_data, dict):
                raise ValidationError(f'Invalid product data format for item {i+1}')
            
            if 'product_id' not in product_data or 'quantity' not in product_data:
                raise ValidationError(f'Missing product ID or quantity for item {i+1}')
            
            try:
                product_id = int(product_data['product_id'])
                quantity = int(product_data['quantity'])
            except (ValueError, TypeError):
                raise ValidationError(f'Invalid product ID or quantity for item {i+1}')
            
            if quantity < 1:
                raise ValidationError(f'Quantity must be at least 1 for item {i+1}')
            
            # Check if product exists and is in stock
            product = Product.query.get(product_id)
            if not product:
                raise ValidationError(f'Product not found for item {i+1}')
            
            if not product.can_fulfill_order(quantity):
                available = product.get_total_available_quantity()
                raise ValidationError(f'Only {available} items available for {product.get_display_name()} (including compatible sizes)')
    
    def validate_customer_phone(self, phone):
        # Remove all non-digit characters for validation
        digits_only = ''.join(filter(str.isdigit, phone.data))
        if len(digits_only) < 10:
            raise ValidationError('Contact number must contain at least 10 digits')
    
    def get_products_data(self):
        """Parse and return the products data"""
        import json
        try:
            return json.loads(self.products_data.data) if self.products_data.data else []
        except (json.JSONDecodeError, TypeError):
            return []

class UpdateOrderStatusForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], validators=[DataRequired()])
    order_id = HiddenField(validators=[DataRequired()])

class ReportFilterForm(FlaskForm):
    start_date = StringField('Start Date', validators=[
        DataRequired(message='Start date is required')
    ])
    end_date = StringField('End Date', validators=[
        DataRequired(message='End date is required')
    ])
    
    def validate_start_date(self, start_date):
        try:
            from datetime import datetime
            datetime.strptime(start_date.data, '%Y-%m-%d')
        except ValueError:
            raise ValidationError('Invalid date format. Use YYYY-MM-DD')
    
    def validate_end_date(self, end_date):
        try:
            from datetime import datetime
            end_dt = datetime.strptime(end_date.data, '%Y-%m-%d')
            start_dt = datetime.strptime(self.start_date.data, '%Y-%m-%d')
            if end_dt < start_dt:
                raise ValidationError('End date must be after start date')
        except ValueError:
            raise ValidationError('Invalid date format. Use YYYY-MM-DD')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required')
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password'),
        EqualTo('new_password', message='Passwords must match')
    ])
