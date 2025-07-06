# 🚀 DantaroWallet

**Hybrid USDT wallet system with multi-tenant support**

A modern, secure, and scalable cryptocurrency wallet application built with FastAPI, following clean architecture principles.

## ✨ Features

- 🔐 **Secure** - Multi-layered security with JWT authentication
- 🏗️ **Scalable** - Clean architecture with modular design
- 🔄 **Multi-tenant** - Support for multiple wallet instances
- 🌐 **TRON Integration** - Native USDT support on TRON network
- 📊 **Real-time** - Live transaction monitoring and updates
- 🧪 **Well-tested** - Comprehensive test coverage

## 🛠️ Tech Stack

- **Backend**: FastAPI + Python 3.11+
- **Database**: PostgreSQL with AsyncPG
- **Cache**: Redis
- **Blockchain**: TRON Network (TronPy)
- **Testing**: Pytest with async support
- **Code Quality**: Black, Flake8, MyPy
- **Container**: Docker + Docker Compose

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Poetry
- Docker & Docker Compose

### Installation

1. **Clone and navigate to project**:
   ```bash
   cd dantarowallet
   ```

2. **Install dependencies**:
   ```bash
   make install
   ```

3. **Copy environment variables**:
   ```bash
   cp .env.example .env
   ```

   ⚠️ **Important**: Update the `.env` file with your actual configuration values.

4. **Start development environment**:
   ```bash
   make dev
   ```

5. **Verify installation**:
   ```bash
   curl http://localhost:8000/health
   ```

## 📋 Available Commands

```bash
make help       # Show all available commands
make install    # Install dependencies
make dev        # Run development server
make test       # Run tests with coverage
make lint       # Run code linters
make format     # Format code with Black
make clean      # Clean up temporary files
```

## 🏗️ Project Structure

```
dantarowallet/
├── app/                    # Main application package
│   ├── api/               # API routes and endpoints
│   ├── core/              # Core configuration and utilities
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic services
│   └── main.py           # FastAPI application entry point
├── tests/                 # Test suite
├── scripts/               # Utility scripts
├── docs/                  # Documentation
└── alembic/              # Database migrations
```

## 🔧 Development

### Running Tests

```bash
# Run all tests with coverage
make test

# Run specific test file
poetry run pytest tests/test_health.py -v

# Run tests with detailed output
poetry run pytest -v --tb=short
```

### Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Type checking
poetry run mypy app
```

### Database Management

```bash
# Initialize database
poetry run alembic upgrade head

# Create new migration
poetry run alembic revision --autogenerate -m "Description"
```

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- Environment-based configuration
- CORS protection
- Rate limiting (coming soon)

## 🌍 Environment Variables

Key environment variables (see `.env.example` for complete list):

```env
# Application
APP_NAME=DantaroWallet
DEBUG=False
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dantarowallet

# TRON Network
TRON_NETWORK=mainnet
TRON_API_KEY=your-api-key-here
```

## 🤝 Contributing

1. Follow the existing code style
2. Write tests for new features
3. Update documentation as needed
4. Run `make lint` and `make test` before committing

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions, please refer to the project documentation or create an issue.

---

**Built with ❤️ by the DantaroWallet Team**
