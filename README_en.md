# lojinha-agro - E-commerce System

An e-commerce system specialized in agricultural products, animal feed, and supplements, developed with Flask. Designed for an intuitive and secure shopping experience.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

[English](README_en.md) | [Português](README.md)

## 🚀 Main Features

- **Complete Authentication System**
  - User Login/Registration
  - Password recovery with security question
  - Customizable user profile
  - Integrated anti-bruteforce system

- **Robust Admin Panel**
  - Product and category management
  - User and permission control
  - Multiple image upload per product
  - Demo video support
  - Important metrics dashboard

- **Smart Catalog**
  - Categorization by animal type
  - Advanced search filters
  - Responsive grid view
  - Optimized images for fast loading

- **Optimized Shopping Experience**
  - Intuitive shopping cart
  - Complete order system
  - Purchase history
  - Multiple payment methods

## 🛠️ Technologies

- Python 3.11+
- Flask Framework
- SQLite3
- HTML5/CSS3
- JavaScript
- Bootstrap 5

## 📋 Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git

## 🔧 Local Installation

1. Clone the repository:
```bash
git clone https://github.com/furiousofnightt/lojinha-agro-vitrine.git
cd lojinha-agro
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env file with your settings
```

5. Initialize database:
```bash
python init_db.py
```

6. Start server:
```bash
python app.py
```

## 🚀 Deployment

Detailed instructions for deploying on PythonAnywhere are available in [docs_importantes/deploy-pythonanywhere.md](docs_importantes/deploy-pythonanywhere.md)

## 📦 Project Structure

```
lojinha-agro/
├── app.py                 # Main Flask application
├── forms.py              # WTForms forms
├── init_db.py            # Database initialization
└── requirements.txt      # Dependencies
```

## 🤝 Contributing

Contributions are very welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## ⚠️ Security

To report security vulnerabilities, please read our [Security Policy](SECURITY.md)

## 📞 Support

For support and questions:
- Open an [issue](https://github.com/furiousofnightt/lojinha-agro-vitrine/issues)
- Check our [documentation](docs_importantes/)