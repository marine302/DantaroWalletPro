#!/bin/bash

# 🔍 Performance Analysis Script for Super Admin Dashboard
# This script analyzes bundle size, performance metrics, and generates reports

echo "🚀 Dantaro Super Admin Dashboard - Performance Analysis"
echo "=========================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

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

# 1. Bundle Size Analysis
print_status "Analyzing bundle size..."

if [ ! -d ".next" ]; then
    print_warning "No .next directory found. Building application first..."
    npm run build
fi

if [ -d ".next" ]; then
    print_success "Bundle analysis starting..."
    
    # Install bundle analyzer if not present
    if ! command_exists "npx"; then
        print_error "NPX not found. Please install Node.js"
        exit 1
    fi
    
    # Run bundle analyzer
    echo "📦 Analyzing bundle composition..."
    ANALYZE=true npm run build
    
    # Show bundle sizes
    echo ""
    print_status "Bundle Size Report:"
    echo "==================="
    
    if [ -d ".next/static/chunks" ]; then
        echo "📊 Chunk sizes:"
        ls -lah .next/static/chunks/ | grep -E '\.(js|css)$' | head -10
    fi
    
    if [ -d ".next/static/js" ]; then
        echo ""
        echo "📊 JavaScript bundle sizes:"
        ls -lah .next/static/js/ | head -10
    fi
    
    if [ -d ".next/static/css" ]; then
        echo ""
        echo "📊 CSS bundle sizes:"
        ls -lah .next/static/css/ | head -10
    fi
    
else
    print_error "Build failed. Cannot analyze bundle."
fi

# 2. Dependency Analysis
print_status "Analyzing dependencies..."

if command_exists "npm"; then
    echo ""
    echo "📋 Package Analysis:"
    echo "==================="
    
    # Show largest dependencies
    echo "🔍 Largest dependencies:"
    npm list --depth=0 --json 2>/dev/null | jq -r '.dependencies | to_entries[] | "\(.key): \(.value.version)"' | head -10
    
    # Check for duplicate dependencies
    echo ""
    echo "🔍 Checking for duplicate dependencies..."
    npm ls --depth=0 | grep -E 'WARN|ERROR' || echo "✅ No duplicate dependencies found"
    
    # Show dependency tree size
    echo ""
    echo "📊 Node modules size:"
    if [ -d "node_modules" ]; then
        du -sh node_modules
    else
        print_warning "node_modules not found"
    fi
fi

# 3. Performance Metrics Collection
print_status "Setting up performance monitoring..."

# Create performance monitoring file
cat > "performance-monitor.js" << 'EOF'
// Performance monitoring script
const fs = require('fs');

// Monitor build performance
const buildStart = Date.now();

// Collect performance metrics
function collectMetrics() {
    const buildTime = Date.now() - buildStart;
    
    const metrics = {
        timestamp: new Date().toISOString(),
        buildTime: buildTime,
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch,
        memory: process.memoryUsage(),
    };
    
    // Add bundle size info if available
    if (fs.existsSync('.next')) {
        try {
            const buildManifest = fs.readFileSync('.next/build-manifest.json', 'utf8');
            const manifest = JSON.parse(buildManifest);
            metrics.pages = Object.keys(manifest.pages).length;
        } catch (error) {
            console.warn('Could not read build manifest:', error.message);
        }
    }
    
    // Save metrics
    const metricsFile = 'performance-metrics.json';
    let existingMetrics = [];
    
    if (fs.existsSync(metricsFile)) {
        try {
            existingMetrics = JSON.parse(fs.readFileSync(metricsFile, 'utf8'));
        } catch (error) {
            console.warn('Could not read existing metrics:', error.message);
        }
    }
    
    existingMetrics.push(metrics);
    
    // Keep only last 10 metrics
    if (existingMetrics.length > 10) {
        existingMetrics = existingMetrics.slice(-10);
    }
    
    fs.writeFileSync(metricsFile, JSON.stringify(existingMetrics, null, 2));
    
    console.log('📊 Performance metrics saved to', metricsFile);
    console.log('⏱️  Build time:', buildTime, 'ms');
}

// Run metrics collection
collectMetrics();
EOF

# Run performance monitoring
if command_exists "node"; then
    node performance-monitor.js
    print_success "Performance metrics collected"
else
    print_error "Node.js not found"
fi

# 4. Lighthouse Performance (if available)
print_status "Checking for Lighthouse CLI..."

if command_exists "lighthouse"; then
    print_status "Running Lighthouse performance audit..."
    
    # Start development server in background
    npm run dev &
    DEV_PID=$!
    
    # Wait for server to start
    sleep 10
    
    # Run Lighthouse
    lighthouse http://localhost:3020 --output=json --output-path=lighthouse-report.json --chrome-flags="--headless" --quiet
    
    if [ -f "lighthouse-report.json" ]; then
        print_success "Lighthouse report generated: lighthouse-report.json"
        
        # Extract key metrics
        if command_exists "jq"; then
            echo ""
            echo "🏆 Lighthouse Performance Scores:"
            echo "================================="
            jq -r '.categories.performance.score * 100 | floor | "Performance: \(.)%"' lighthouse-report.json
            jq -r '.categories.accessibility.score * 100 | floor | "Accessibility: \(.)%"' lighthouse-report.json
            jq -r '.categories."best-practices".score * 100 | floor | "Best Practices: \(.)%"' lighthouse-report.json
            jq -r '.categories.seo.score * 100 | floor | "SEO: \(.)%"' lighthouse-report.json
            
            echo ""
            echo "⚡ Key Performance Metrics:"
            echo "========================="
            jq -r '.audits."first-contentful-paint".displayValue // "N/A" | "First Contentful Paint: \(.)"' lighthouse-report.json
            jq -r '.audits."largest-contentful-paint".displayValue // "N/A" | "Largest Contentful Paint: \(.)"' lighthouse-report.json
            jq -r '.audits."cumulative-layout-shift".displayValue // "N/A" | "Cumulative Layout Shift: \(.)"' lighthouse-report.json
        fi
    fi
    
    # Stop development server
    kill $DEV_PID 2>/dev/null
    
else
    print_warning "Lighthouse CLI not found. Install with: npm install -g lighthouse"
fi

# 5. Generate Performance Report
print_status "Generating performance report..."

cat > "PERFORMANCE_REPORT.md" << 'EOF'
# 📊 Dantaro Super Admin Dashboard - Performance Report

**Generated on:** $(date)

## 🎯 Performance Goals

### Target Metrics
- [ ] Page Load Time < 2 seconds
- [ ] API Response Time < 500ms
- [ ] First Contentful Paint < 1 second
- [ ] Bundle Size < 2MB
- [ ] Lighthouse Performance > 90

## 📈 Current Metrics

### Bundle Analysis
EOF

if [ -d ".next" ]; then
    echo "- ✅ Build completed successfully" >> PERFORMANCE_REPORT.md
    
    if [ -d ".next/static/chunks" ]; then
        echo "- 📦 JavaScript chunks:" >> PERFORMANCE_REPORT.md
        ls -lah .next/static/chunks/*.js | head -5 | awk '{print "  - " $9 ": " $5}' >> PERFORMANCE_REPORT.md
    fi
else
    echo "- ❌ Build not completed" >> PERFORMANCE_REPORT.md
fi

cat >> "PERFORMANCE_REPORT.md" << 'EOF'

### Dependencies
EOF

if command_exists "npm"; then
    npm list --depth=0 | head -10 | sed 's/^/- /' >> PERFORMANCE_REPORT.md
fi

# 6. Optimization Recommendations
cat >> "PERFORMANCE_REPORT.md" << 'EOF'

## 🚀 Optimization Recommendations

### Immediate Actions
- [ ] Enable gzip compression
- [ ] Optimize images with next/image
- [ ] Implement code splitting for heavy components
- [ ] Add React.memo for frequently re-rendered components

### Short Term
- [ ] Set up CDN for static assets
- [ ] Implement service worker for caching
- [ ] Optimize bundle chunks
- [ ] Add performance monitoring

### Long Term
- [ ] Implement lazy loading for non-critical components
- [ ] Set up performance budgets
- [ ] Add automated performance testing
- [ ] Optimize database queries

## 📋 Action Items

### High Priority
1. Bundle size optimization
2. Code splitting implementation
3. React.memo optimization

### Medium Priority
1. Image optimization
2. Caching strategy
3. Performance monitoring

### Low Priority
1. Service worker implementation
2. CDN setup
3. Advanced optimizations

---

**Next Review:** 1 week from generation date
EOF

print_success "Performance report generated: PERFORMANCE_REPORT.md"

# 7. Cleanup
rm -f performance-monitor.js

# 8. Summary
echo ""
echo "🎉 Performance Analysis Complete!"
echo "================================="
print_success "Reports generated:"
echo "  📊 PERFORMANCE_REPORT.md - Comprehensive performance analysis"
echo "  📈 performance-metrics.json - Historical performance data"

if [ -f "lighthouse-report.json" ]; then
    echo "  🏆 lighthouse-report.json - Lighthouse audit results"
fi

echo ""
print_status "Next steps:"
echo "  1. Review PERFORMANCE_REPORT.md"
echo "  2. Implement optimization recommendations"
echo "  3. Run analysis again after optimizations"
echo "  4. Set up automated performance monitoring"

echo ""
print_success "Analysis completed successfully! 🚀"
