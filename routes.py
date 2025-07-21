from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from models import db, User, Product, ProductType, SizeGroup, SizeGroupMapping, Order, OrderItem, Customer, PathaoDelivery, Store
from forms import ProductForm, ProductTypeForm, SizeGroupForm, OrderItemForm, UpdateOrderStatusForm, ReportFilterForm, CreateOrderForm
from pathao_service import PathaoService
from auth import admin_required

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    # Get dashboard statistics
    stats = {}
    
    if current_user.is_admin():
        # Admin sees all statistics
        stats['total_products'] = Product.query.count()
        stats['low_stock_products'] = Product.query.filter(Product.quantity < 10).count()
        stats['total_orders'] = Order.query.count()
        stats['pending_orders'] = Order.query.filter_by(status='pending').count()
        stats['total_users'] = User.query.filter_by(is_active=True).count()
        
        # Recent orders
        recent_orders = Order.query.order_by(desc(Order.created_at)).limit(5).all()
        
        # Low stock products
        low_stock_products = Product.query.filter(Product.quantity < 10).limit(5).all()
    else:
        # Regular users see their own statistics
        stats['my_orders'] = Order.query.filter_by(user_id=current_user.id).count()
        stats['pending_orders'] = Order.query.filter_by(user_id=current_user.id, status='pending').count()
        stats['completed_orders'] = Order.query.filter_by(user_id=current_user.id, status='completed').count()
        
        # User's recent orders
        recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(desc(Order.created_at)).limit(5).all()
        low_stock_products = []
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_orders=recent_orders,
                         low_stock_products=low_stock_products)

@main.route('/inventory')
@login_required
def inventory():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Product.query
    if search:
        query = query.filter(Product.name.contains(search))
    
    products = query.order_by(Product.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('inventory.html', products=products, search=search)

@main.route('/add_product', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        # Validate product combination
        form.validate_product_combination()
        
        product = Product(
            name=form.name.data,
            product_type_id=form.product_type_id.data,
            product_code=form.product_code.data,
            size=form.size.data,
            quantity=form.quantity.data,
            price=form.price.data,
            size_group_id=form.size_group_id.data if form.size_group_id.data != 0 else None
        )
        
        # Auto-assign size group if not manually selected
        if not product.size_group_id:
            product.auto_assign_size_group()
        
        try:
            db.session.add(product)
            db.session.commit()
            flash(f'Product "{product.get_display_name()}" added successfully!', 'success')
            return redirect(url_for('main.inventory'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding product. Please try again.', 'error')
    
    return render_template('add_product.html', form=form)

@main.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product, product_id=product_id)
    
    if form.validate_on_submit():
        # Validate product combination
        form.validate_product_combination()
        
        product.name = form.name.data
        product.product_type_id = form.product_type_id.data
        product.product_code = form.product_code.data
        product.size = form.size.data
        product.quantity = form.quantity.data
        product.price = form.price.data
        product.size_group_id = form.size_group_id.data if form.size_group_id.data != 0 else None
        product.updated_at = datetime.utcnow()
        
        # Auto-assign size group if not manually selected
        if not product.size_group_id:
            product.auto_assign_size_group()
        
        try:
            db.session.commit()
            flash(f'Product "{product.get_display_name()}" updated successfully!', 'success')
            return redirect(url_for('main.inventory'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating product. Please try again.', 'error')
    
    return render_template('edit_product.html', form=form, product=product)

@main.route('/delete_product/<int:product_id>')
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if product has associated orders
    if product.order_items:
        flash('Cannot delete product with existing orders', 'error')
        return redirect(url_for('main.inventory'))
    
    try:
        db.session.delete(product)
        db.session.commit()
        flash(f'Product "{product.name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting product. Please try again.', 'error')
    
    return redirect(url_for('main.inventory'))

@main.route('/orders')
@login_required
def orders():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '', type=str)
    
    if current_user.is_admin():
        query = Order.query
    else:
        query = Order.query.filter_by(user_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    orders = query.order_by(desc(Order.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Create form for CSRF token generation
    update_status_form = UpdateOrderStatusForm()
    
    return render_template('orders.html', 
                         orders=orders, 
                         status_filter=status_filter,
                         update_status_form=update_status_form)

@main.route('/create_order', methods=['GET', 'POST'])
@login_required
def create_order():
    form = CreateOrderForm()
    
    if form.validate_on_submit():
        products_data = form.get_products_data()
        
        if not products_data:
            flash('Please select at least one product', 'error')
            return redirect(url_for('main.create_order'))
        
        try:
            # Create or get customer
            customer = Customer(
                name=form.customer_name.data,
                phone=form.customer_phone.data,
                address=form.customer_address.data
            )
            db.session.add(customer)
            db.session.flush()  # Get customer ID
            
            # Get location names from Pathao service
            location_names = PathaoService.get_location_names(
                city_id=form.city_id.data,
                zone_id=form.zone_id.data
            )
            
            # Create order with customer and location information
            order = Order(
                user_id=current_user.id,
                customer_id=customer.id,
                city_id=form.city_id.data,
                city_name=location_names.get('city_name'),
                zone_id=form.zone_id.data,
                zone_name=location_names.get('zone_name'),
                delivery_charge=form.delivery_charge.data or 0.00,
                discount=form.discount.data or 0.00,
                total_amount=0
            )
            db.session.add(order)
            db.session.flush()  # Get order ID
            
            # Process each product in the order
            for product_data in products_data:
                product_id = int(product_data['product_id'])
                quantity = int(product_data['quantity'])
                
                product = Product.query.get(product_id)
                if not product:
                    raise ValueError(f'Product with ID {product_id} not found')
                
                if not product.can_fulfill_order(quantity):
                    available = product.get_total_available_quantity()
                    raise ValueError(f'Only {available} items available for {product.get_display_name()}')
                
                # Create order item
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=product.price
                )
                db.session.add(order_item)
                db.session.flush()  # Get the OrderItem ID
                
                # Generate and set tracking code
                order_item.update_tracking_code()
                
                # Update product stock using the smart fulfillment system
                if not product.fulfill_order(quantity):
                    raise ValueError(f'Failed to fulfill order for {product.get_display_name()}')
            
            # Calculate total
            order.calculate_total()
            
            db.session.commit()
            
            total_items = sum(int(p['quantity']) for p in products_data)
            flash(f'Order #{order.id} created successfully for {customer.name} with {total_items} items!', 'success')
            return redirect(url_for('main.order_details', order_id=order.id))
            
        except ValueError as ve:
            db.session.rollback()
            flash(str(ve), 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error creating order. Please try again.', 'error')
    
    return render_template('create_order.html', form=form)

@main.route('/order_details/<int:order_id>')
@login_required
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Check access permissions
    if not current_user.is_admin() and order.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.orders'))
    
    # Create form for CSRF token generation
    update_status_form = UpdateOrderStatusForm()
    
    return render_template('order_details.html', order=order, update_status_form=update_status_form)

@main.route('/update_order_status', methods=['POST'])
@login_required
@admin_required
def update_order_status():
    form = UpdateOrderStatusForm()
    if form.validate_on_submit():
        order = Order.query.get_or_404(form.order_id.data)
        old_status = order.status
        order.status = form.status.data
        order.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash(f'Order #{order.id} status updated from {old_status} to {order.status}', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating order status', 'error')
    else:
        flash('Error updating order status. Please try again.', 'error')
    
    return redirect(url_for('main.orders'))

@main.route('/reports')
@login_required
def reports():
    form = ReportFilterForm()
    
    # Default to last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    form.start_date.data = start_date.strftime('%Y-%m-%d')
    form.end_date.data = end_date.strftime('%Y-%m-%d')
    
    return render_template('reports.html', form=form)

@main.route('/generate_report', methods=['POST'])
@login_required
def generate_report():
    form = ReportFilterForm()
    if form.validate_on_submit():
        start_date = datetime.strptime(form.start_date.data, '%Y-%m-%d')
        end_date = datetime.strptime(form.end_date.data, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)  # End of day
        
        # Base query
        if current_user.is_admin():
            orders_query = Order.query
        else:
            orders_query = Order.query.filter_by(user_id=current_user.id)
        
        # Filter by date range
        orders = orders_query.filter(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        ).all()
        
        # Calculate statistics
        total_orders = len(orders)
        total_revenue = sum(float(order.total_amount) for order in orders)
        completed_orders = len([o for o in orders if o.status == 'completed'])
        
        # Top products
        product_sales = {}
        for order in orders:
            for item in order.order_items:
                if item.product.name not in product_sales:
                    product_sales[item.product.name] = {'quantity': 0, 'revenue': 0}
                product_sales[item.product.name]['quantity'] += item.quantity
                product_sales[item.product.name]['revenue'] += float(item.subtotal)
        
        top_products = sorted(product_sales.items(), 
                            key=lambda x: x[1]['quantity'], reverse=True)[:5]
        
        report_data = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'completed_orders': completed_orders,
            'top_products': top_products,
            'orders': orders
        }
        
        return render_template('report_results.html', report=report_data)
    
    return render_template('reports.html', form=form)

@main.route('/manage_users')
@login_required
@admin_required
def manage_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.username).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('manage_users.html', users=users)

# Product Type Management Routes
@main.route('/admin/product-types')
@login_required
@admin_required
def product_types():
    page = request.args.get('page', 1, type=int)
    product_types = ProductType.query.order_by(ProductType.name).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/product_types.html', product_types=product_types)

@main.route('/admin/product-types/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product_type():
    form = ProductTypeForm()
    if form.validate_on_submit():
        product_type = ProductType(
            name=form.name.data,
            description=form.description.data
        )
        try:
            db.session.add(product_type)
            db.session.commit()
            flash(f'Product type "{product_type.name}" added successfully!', 'success')
            return redirect(url_for('main.product_types'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding product type. Please try again.', 'error')
    
    return render_template('admin/add_product_type.html', form=form)

@main.route('/admin/product-types/edit/<int:product_type_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product_type(product_type_id):
    product_type = ProductType.query.get_or_404(product_type_id)
    form = ProductTypeForm(obj=product_type, product_type_id=product_type_id)
    
    if form.validate_on_submit():
        product_type.name = form.name.data
        product_type.description = form.description.data
        
        try:
            db.session.commit()
            flash(f'Product type "{product_type.name}" updated successfully!', 'success')
            return redirect(url_for('main.product_types'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating product type. Please try again.', 'error')
    
    return render_template('admin/edit_product_type.html', form=form, product_type=product_type)

@main.route('/admin/product-types/delete/<int:product_type_id>')
@login_required
@admin_required
def delete_product_type(product_type_id):
    product_type = ProductType.query.get_or_404(product_type_id)
    
    # Check if product type has associated products
    if product_type.products:
        flash('Cannot delete product type with existing products', 'error')
        return redirect(url_for('main.product_types'))
    
    try:
        db.session.delete(product_type)
        db.session.commit()
        flash(f'Product type "{product_type.name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting product type. Please try again.', 'error')
    
    return redirect(url_for('main.product_types'))

# Size Group Management Routes
@main.route('/admin/size-groups')
@login_required
@admin_required
def size_groups():
    page = request.args.get('page', 1, type=int)
    product_type_filter = request.args.get('product_type', '', type=str)
    
    query = SizeGroup.query.join(ProductType)
    if product_type_filter:
        query = query.filter(ProductType.name == product_type_filter)
    
    size_groups = query.order_by(ProductType.name, SizeGroup.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get product types for filter dropdown
    product_types = ProductType.query.order_by(ProductType.name).all()
    
    return render_template('admin/size_groups.html', 
                         size_groups=size_groups, 
                         product_types=product_types,
                         product_type_filter=product_type_filter)

@main.route('/admin/size-groups/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_size_group():
    form = SizeGroupForm()
    if form.validate_on_submit():
        size_group = SizeGroup(
            name=form.name.data,
            product_type_id=form.product_type_id.data,
            description=form.description.data
        )
        
        try:
            db.session.add(size_group)
            db.session.flush()  # Get the ID
            
            # Add size mappings
            sizes = [s.strip() for s in form.sizes.data.split(',') if s.strip()]
            for size in sizes:
                mapping = SizeGroupMapping(size_group_id=size_group.id, size=size)
                db.session.add(mapping)
            
            db.session.commit()
            
            # Auto-assign existing products to this size group
            existing_products = Product.query.filter(
                Product.product_type_id == size_group.product_type_id,
                Product.size.in_(sizes),
                Product.size_group_id.is_(None)
            ).all()
            
            for product in existing_products:
                product.size_group_id = size_group.id
            
            if existing_products:
                db.session.commit()
                flash(f'Size group "{size_group.name}" added successfully! {len(existing_products)} existing products were automatically assigned.', 'success')
            else:
                flash(f'Size group "{size_group.name}" added successfully!', 'success')
            
            return redirect(url_for('main.size_groups'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding size group. Please try again.', 'error')
    
    return render_template('admin/add_size_group.html', form=form)

@main.route('/admin/size-groups/edit/<int:size_group_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_size_group(size_group_id):
    size_group = SizeGroup.query.get_or_404(size_group_id)
    
    # Pre-populate the sizes field
    current_sizes = ', '.join(size_group.get_sizes())
    form = SizeGroupForm(obj=size_group, size_group_id=size_group_id)
    form.sizes.data = current_sizes
    
    if form.validate_on_submit():
        size_group.name = form.name.data
        size_group.product_type_id = form.product_type_id.data
        size_group.description = form.description.data
        
        try:
            # Remove old size mappings
            SizeGroupMapping.query.filter_by(size_group_id=size_group.id).delete()
            
            # Add new size mappings
            sizes = [s.strip() for s in form.sizes.data.split(',') if s.strip()]
            for size in sizes:
                mapping = SizeGroupMapping(size_group_id=size_group.id, size=size)
                db.session.add(mapping)
            
            db.session.commit()
            flash(f'Size group "{size_group.name}" updated successfully!', 'success')
            return redirect(url_for('main.size_groups'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating size group. Please try again.', 'error')
    
    return render_template('admin/edit_size_group.html', form=form, size_group=size_group)

@main.route('/admin/size-groups/delete/<int:size_group_id>')
@login_required
@admin_required
def delete_size_group(size_group_id):
    size_group = SizeGroup.query.get_or_404(size_group_id)
    
    # Check if size group has associated products
    if size_group.products:
        flash('Cannot delete size group with existing products', 'error')
        return redirect(url_for('main.size_groups'))
    
    try:
        db.session.delete(size_group)
        db.session.commit()
        flash(f'Size group "{size_group.name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting size group. Please try again.', 'error')
    
    return redirect(url_for('main.size_groups'))

# API Routes for dynamic form updates
@main.route('/api/size-groups/<int:product_type_id>')
@login_required
def get_size_groups_for_product_type(product_type_id):
    """API endpoint to get size groups for a specific product type"""
    size_groups = SizeGroup.query.filter_by(product_type_id=product_type_id).all()
    return jsonify([
        {
            'id': sg.id,
            'name': sg.name,
            'sizes': sg.get_sizes()
        }
        for sg in size_groups
    ])

# Pathao API Routes for location data
@main.route('/api/cities')
@login_required
def api_cities():
    """API endpoint to get list of cities from Pathao"""
    try:
        cities = PathaoService.get_cities()
        return jsonify([
            {'id': city.city_id, 'name': city.city_name}
            for city in cities
        ])
    except Exception as e:
        return jsonify({'error': 'Failed to fetch cities'}), 500

@main.route('/api/zones/<int:city_id>')
@login_required
def api_zones(city_id):
    """API endpoint to get zones for a specific city"""
    try:
        zones = PathaoService.get_zones(city_id)
        return jsonify([
            {'id': zone.zone_id, 'name': zone.zone_name}
            for zone in zones
        ])
    except Exception as e:
        return jsonify({'error': 'Failed to fetch zones'}), 500


@main.route('/api/products')
@login_required
def api_products():
    """API endpoint to get list of available products for order creation"""
    try:
        products = Product.query.filter(Product.quantity > 0).all()
        return jsonify([
            {
                'id': product.id,
                'name': product.get_display_name(),
                'product_code': product.product_code,
                'size': product.size,
                'price': float(product.price),
                'stock': product.quantity,
                'total_available': product.get_total_available_quantity(),
                'display_text': f"{product.get_display_name()} - {product.product_code} - {product.size} - ${product.price} (Stock: {product.quantity})"
            }
            for product in products
        ])
    except Exception as e:
        return jsonify({'error': 'Failed to fetch products'}), 500

@main.route('/api/parse-address', methods=['POST'])
@login_required
def api_parse_address():
    """API endpoint to parse address using Pathao service"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        address = data.get('address', '').strip()
        if not address:
            return jsonify({'error': 'Address is required'}), 400
        
        parsed_data = PathaoService.parse_address(address)
        if not parsed_data:
            return jsonify({'error': 'Failed to parse address or no results found'}), 404
        
        return jsonify({'success': True, 'data': parsed_data})
    except Exception as e:
        current_app.logger.error(f"Error parsing address: {str(e)}")
        return jsonify({'error': 'Failed to parse address'}), 500


@main.route('/api/stores')
@login_required
def api_stores():
    """API endpoint to get list of stores from Pathao with 24-hour caching"""
    try:
        # Attempt to fetch from PathaoService (which handles caching)
        stores = PathaoService.get_stores()

        if stores:
            # Format for frontend
            store_data = [
                {
                    'id': store.id,
                    'name': store.store_name,
                    'address': store.store_address
                }
                for store in stores
                if store.id is not None  # Ensure valid ID
            ]
            return jsonify(store_data)
        
        # Fallback to active local stores (shouldn't happen unless DB is empty or failed)
        current_app.logger.warning("No Pathao stores available, falling back to local store data")
        fallback_stores = Store.query.filter_by(is_active=True).order_by(Store.store_name).all()
        fallback_data = [
            {
                'id': f"local_{store.id}",
                'name': f"{store.store_name} (Local)",
                'address': store.store_address
            }
            for store in fallback_stores
        ]
        return jsonify(fallback_data)

    except Exception as e:
        current_app.logger.error(f"Error in /api/stores: {str(e)}")
        # Final fallback
        try:
            stores = Store.query.filter_by(is_active=True).order_by(Store.store_name).all()
            store_data = [
                {
                    'id': f"local_{store.id}",
                    'name': f"{store.store_name} (Local)",
                    'address': store.store_address
                }
                for store in stores
            ]
            return jsonify(store_data)
        except Exception as fallback_error:
            current_app.logger.error(f"Fallback store fetch failed: {str(fallback_error)}")
            return jsonify({'error': 'Failed to fetch stores'}), 500


# User Management API Routes
@main.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def api_toggle_user_status(user_id):
    """API endpoint to toggle user active status"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent admin from deactivating themselves
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'Cannot deactivate your own account'}), 400
        
        user.is_active = not user.is_active
        db.session.commit()
        
        status = 'activated' if user.is_active else 'deactivated'
        return jsonify({'success': True, 'message': f'User {user.username} has been {status}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update user status'}), 500

@main.route('/api/users/<int:user_id>/toggle-role', methods=['POST'])
@login_required
@admin_required
def api_toggle_user_role(user_id):
    """API endpoint to toggle user role between user and admin"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent changing own role
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'Cannot change your own role'}), 400
        
        user.role = 'admin' if user.role == 'user' else 'user'
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'User {user.username} role changed to {user.role}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update user role'}), 500

@main.route('/api/users/<int:user_id>/delete', methods=['DELETE'])
@login_required
@admin_required
def api_delete_user(user_id):
    """API endpoint to delete a user"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent admin from deleting themselves
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 400
        
        # Check if user has associated orders
        if user.orders:
            return jsonify({'success': False, 'message': 'Cannot delete user with existing orders'}), 400
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'User {username} has been deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to delete user'}), 500

@main.route('/request_shipping/<int:order_id>', methods=['POST'])
@login_required
def request_shipping(order_id):
    order = Order.query.get_or_404(order_id)
    # Only allow if not already requested and user has access
    if not current_user.is_admin() and order.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.orders'))
    
    if order.shipping_requested:
        flash('Shipping already requested for this order.', 'info')
    else:
        # Get store_id from form data
        pathao_store_id = request.form.get('store_id')
        store_name = Store.query.get(pathao_store_id).store_name
        # Trigger create order request to Pathao
        from pathao_service import PathaoService
        try:
            response = PathaoService.create_order(order, store_id=pathao_store_id)
            if response.get('code') == 200:
                # Extract delivery data from response
                delivery_data = response.get('data', {})                
                # Create PathaoDelivery record
                try:
                    from models import PathaoDelivery
                    pathao_delivery = PathaoDelivery(
                        consignment_id=delivery_data.get('consignment_id'),
                        merchant_order_id=order.id,
                        order_status=delivery_data.get('order_status', 'Pending'),
                        delivery_fee=delivery_data.get('delivery_fee', 0)
                    )
                    
                    db.session.add(pathao_delivery)
                    order.shipping_requested = True
                    order.updated_at = datetime.utcnow()
                    db.session.commit()
                    
                    flash(f'Shipping request sent to Pathao successfully from {store_name}. Tracking ID: {pathao_delivery.consignment_id}', 'success')
                except Exception as db_error:
                    db.session.rollback()
                    # Still mark as requested since Pathao accepted the order
                    order.shipping_requested = True
                    order.updated_at = datetime.utcnow()
                    db.session.commit()
                    flash(f'Shipping request sent to Pathao successfully from {store_name}, but failed to save tracking info: {str(db_error)}', 'warning')
                    
            else:
                flash('Failed to send order to Pathao: ' + response.get('message', 'Unknown error'), 'error')
        except Exception as e:
            flash(f'Pathao API error: {str(e)}', 'error')
    return redirect(url_for('main.order_details', order_id=order.id))
