# Secure Order Management Web Application

A comprehensive, secure web application for managing inventory and orders built with Flask, featuring robust authentication, CSRF protection, and modern UI design.

## 🔐 Security Features

- **User Authentication** with Flask-Login
- **Password Hashing** using werkzeug.security
- **Session Protection** (cookie-based with HttpOnly, Secure, SameSite)
- **CSRF Protection** via Flask-WTF
- **Input Validation & Escaping** (Jinja2 + WTForms)
- **Access Control**: Only authenticated users can access sensitive pages
- **Session Timeout** with idle detection
- **Secure Configuration** management

## 🚀 Features

### User Management
- Secure user registration and login
- Role-based access control (Admin/User)
- Password strength requirements
- Session management with timeout

### Inventory Management
- Add, edit, and delete products (Admin only)
- Real-time stock tracking
- Low stock alerts
- Search and pagination
- Product categorization

### Order Management
- Create orders with inventory validation
- Order status tracking (Pending, Processing, Completed, Cancelled)
- Order history and details
- Automatic inventory updates

### Dashboard & Reports
- Real-time statistics
- Order summaries
- Inventory status overview
- User activity tracking

## 🛠 Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Jinja2 templates + Bootstrap 5
- **Security**: Flask-Login, Flask-WTF, werkzeug.security
- **Icons**: Bootstrap Icons
- **Styling**: Custom CSS with responsive design

## 📋 Requirements

- Python 3.7+
- Flask and related packages (see requirements.txt)

## 🔧 Installation & Setup

### 1. Clone or Download the Project
```bash
# If using git
git clone <repository-url>
cd secure-order-management

# Or extract the downloaded files to a directory
```

### 2. Install Dependencies
```bash
# Install pip if not available
sudo apt update && sudo apt install -y python3-pip

# Install required packages
pip3 install -r requirements.txt
```

### 3. Initialize the Database
```bash
# Run the database initialization script
python3 init_db.py
```

This script will:
- Create all necessary database tables
- Prompt you to create an admin user
- Optionally add sample products for testing

### 4. Run the Application
```bash
# Production mode
python3 app.py

# Development mode (with debug enabled)
export FLASK_ENV=development
python3 app.py
```

The application will be available at `http://localhost:5000`

## 👤 Default Access

After running `init_db.py`, you'll have:
- **Admin User**: Username and password as configured during setup
- **Sample Products**: Optional test data for immediate use

## 🎯 Usage Guide

### For Administrators
1. **Login** with admin credentials
2. **Manage Inventory**:
   - Add new products via "Inventory" → "Add Product"
   - Edit existing products (price, stock, description)
   - Delete products (with confirmation)
   - Monitor low stock alerts

3. **Manage Orders**:
   - View all customer orders
   - Update order status (Pending → Processing → Completed)
   - Cancel orders if needed

4. **Dashboard Overview**:
   - Monitor key metrics
   - Track recent activity
   - View system statistics

### For Regular Users
1. **Login** with user credentials
2. **Browse Inventory**:
   - View available products
   - Check stock levels and prices
   - Search for specific items

3. **Place Orders**:
   - Select products and quantities
   - Review order details
   - Submit orders (inventory automatically updated)

4. **Track Orders**:
   - View order history
   - Check order status
   - Review order details

## 🔒 Security Best Practices

### Implemented Security Measures
- Passwords are hashed using werkzeug's secure methods
- CSRF tokens protect all forms
- Session cookies are configured with security flags
- Input validation prevents malicious data
- SQL injection protection via SQLAlchemy ORM
- XSS protection through Jinja2 auto-escaping

### Recommended Production Setup
1. **Use HTTPS**: Configure SSL/TLS certificates
2. **Environment Variables**: Store sensitive config in environment variables
3. **Database**: Use PostgreSQL or MySQL for production
4. **Reverse Proxy**: Use nginx or Apache as reverse proxy
5. **Monitoring**: Implement logging and monitoring
6. **Backups**: Regular database backups
7. **Updates**: Keep dependencies updated

## 📁 Project Structure

```
secure-order-management/
├── app.py                 # Main application entry point
├── config.py             # Configuration settings
├── models.py             # Database models
├── forms.py              # WTForms form definitions
├── auth.py               # Authentication blueprint
├── routes.py             # Main application routes
├── init_db.py            # Database initialization script
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── static/              # Static files (CSS, JS, images)
│   ├── css/
│   │   └── style.css    # Custom styles
│   └── js/
│       └── main.js      # Custom JavaScript
└── templates/           # Jinja2 templates
    ├── base.html        # Base template
    ├── dashboard.html   # Dashboard page
    ├── inventory.html   # Inventory management
    ├── orders.html      # Order management
    ├── create_order.html # Order creation
    ├── add_product.html # Product creation
    └── auth/
        └── login.html   # Login page
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Database Errors**: Re-run database initialization
   ```bash
   rm -f order_management.db
   python3 init_db.py
   ```

3. **Permission Errors**: Check file permissions
   ```bash
   chmod +x init_db.py
   ```

4. **Port Already in Use**: Change port in app.py or kill existing process
   ```bash
   # Find process using port 5000
   lsof -i :5000
   # Kill process
   kill -9 <PID>
   ```

### Development Tips

1. **Debug Mode**: Set `FLASK_ENV=development` for detailed error messages
2. **Database Reset**: Delete `order_management.db` and re-run `init_db.py`
3. **Log Files**: Check console output for error messages
4. **Browser Cache**: Clear browser cache if CSS/JS changes don't appear

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is provided as-is for educational and development purposes.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review error messages in the console
3. Ensure all dependencies are properly installed
4. Verify database initialization completed successfully

---

**Note**: This application is designed for educational purposes and small-scale deployments. For production use, additional security hardening and scalability considerations should be implemented.
