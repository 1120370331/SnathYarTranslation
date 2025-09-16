#!/bin/bash

# 沙斯亚尔语翻译器启动脚本 / Shathyar Translator Startup Script
# 启动后端和前端服务 / Start backend and frontend services

set -e

echo "🔮 启动沙斯亚尔语翻译器 / Starting Shathyar Translator"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Node.js is installed
check_node() {
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed. Please install Node.js 18+ to continue."
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js version 18+ is required. Current version: $(node --version)"
        exit 1
    fi
    
    print_success "Node.js $(node --version) detected ✓"
}

# Check if Python is installed  
check_python() {
    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        print_error "Python is not installed. Please install Python 3.11+ to continue."
        exit 1
    fi
    
    PYTHON_CMD=$(command -v python3 2>/dev/null || command -v python)
    PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    
    if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
        print_error "Python version 3.11+ is required. Current version: $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION detected ✓"
}

# Install backend dependencies
setup_backend() {
    print_status "🐍 设置后端环境 / Setting up backend environment..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install -e .
    
    print_success "Backend setup complete ✓"
    cd ..
}

# Install frontend dependencies
setup_frontend() {
    print_status "⚛️ 设置前端环境 / Setting up frontend environment..."
    
    cd frontend
    
    # Install dependencies
    if [ ! -d "node_modules" ]; then
        print_status "Installing Node.js dependencies..."
        npm install
    else
        print_status "Dependencies already installed, checking for updates..."
        npm ci
    fi
    
    print_success "Frontend setup complete ✓"
    cd ..
}

# Start backend server
start_backend() {
    print_status "🚀 启动后端服务器 / Starting backend server..."
    
    cd backend
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
    
    # Start FastAPI server
    python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    
    print_success "Backend server started (PID: $BACKEND_PID)"
    print_status "📍 Backend URL: http://localhost:8000"
    print_status "📚 API Docs: http://localhost:8000/docs"
    
    cd ..
    echo $BACKEND_PID > .backend_pid
}

# Start frontend server
start_frontend() {
    print_status "🎨 启动前端服务器 / Starting frontend server..."
    
    cd frontend
    
    # Start Vite dev server
    npm run dev &
    FRONTEND_PID=$!
    
    print_success "Frontend server started (PID: $FRONTEND_PID)"
    print_status "🌐 Frontend URL: http://localhost:5173"
    
    cd ..
    echo $FRONTEND_PID > .frontend_pid
}

# Wait for servers to be ready
wait_for_servers() {
    print_status "⏳ 等待服务器启动 / Waiting for servers to start..."
    
    # Wait for backend
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend server is ready ✓"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Backend server may not be ready yet"
        fi
        sleep 1
    done
    
    # Wait for frontend
    for i in {1..30}; do
        if curl -s http://localhost:5173 > /dev/null 2>&1; then
            print_success "Frontend server is ready ✓"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Frontend server may not be ready yet"
        fi
        sleep 1
    done
}

# Cleanup function
cleanup() {
    print_status "🛑 正在停止服务器 / Stopping servers..."
    
    if [ -f .backend_pid ]; then
        BACKEND_PID=$(cat .backend_pid)
        kill $BACKEND_PID 2>/dev/null || true
        rm .backend_pid
        print_status "Backend server stopped"
    fi
    
    if [ -f .frontend_pid ]; then
        FRONTEND_PID=$(cat .frontend_pid)
        kill $FRONTEND_PID 2>/dev/null || true
        rm .frontend_pid
        print_status "Frontend server stopped"
    fi
    
    print_success "✨ 沙斯亚尔语翻译器已停止 / Shathyar Translator stopped"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Main execution
main() {
    print_status "🔍 检查系统要求 / Checking system requirements..."
    check_node
    check_python
    
    print_status "📦 安装依赖 / Installing dependencies..."
    setup_backend
    setup_frontend
    
    print_status "🚀 启动服务 / Starting services..."
    start_backend
    sleep 2
    start_frontend
    
    wait_for_servers
    
    echo ""
    echo "🎉 沙斯亚尔语翻译器启动成功！/ Shathyar Translator started successfully!"
    echo "=================================================="
    echo -e "${PURPLE}🔮 翻译门户 / Translation Portal:${NC} http://localhost:5173"
    echo -e "${PURPLE}📚 API 文档 / API Documentation:${NC} http://localhost:8000/docs"
    echo -e "${PURPLE}💚 后端健康检查 / Backend Health:${NC} http://localhost:8000/health"
    echo ""
    echo -e "${YELLOW}提示 / Tips:${NC}"
    echo "• 使用 Ctrl+C 停止所有服务 / Use Ctrl+C to stop all services"
    echo "• 后端运行在端口 8000 / Backend runs on port 8000"
    echo "• 前端运行在端口 5173 / Frontend runs on port 5173"
    echo "• 查看实时日志请检查终端输出 / Check terminal output for live logs"
    echo ""
    echo -e "${GREEN}🌟 准备开始您的沙斯亚尔语翻译之旅！/ Ready to start your Shathyar translation journey!${NC}"
    
    # Keep script running
    wait
}

# Run main function
main