/**
 * Content Security Policy configuration for enhanced security
 */

// Define CSP directives
const cspDirectives = {
  'default-src': ["'self'"],
  'script-src': [
    "'self'",
    "'unsafe-eval'", // Required for Next.js development
    "'unsafe-inline'", // Required for Next.js
    'https://vercel.live',
  ],
  'style-src': [
    "'self'",
    "'unsafe-inline'", // Required for styled-components and Tailwind
    'https://fonts.googleapis.com',
  ],
  'font-src': [
    "'self'",
    'https://fonts.gstatic.com',
    'data:',
  ],
  'img-src': [
    "'self'",
    'data:',
    'blob:',
    'https://images.unsplash.com',
    'https://via.placeholder.com',
  ],
  'connect-src': [
    "'self'",
    'http://localhost:3001', // Mock API server
    'http://localhost:8000', // Backend API server
    'ws://localhost:3002',   // WebSocket server
    'ws://localhost:3020',   // Next.js WebSocket
    'https://api.tron.network', // TronNRG API
    'https://energy.tron.network', // EnergyTron API
  ],
  'frame-src': [
    "'none'",
  ],
  'object-src': [
    "'none'",
  ],
  'base-uri': [
    "'self'",
  ],
  'form-action': [
    "'self'",
  ],
  'frame-ancestors': [
    "'none'",
  ],
  'upgrade-insecure-requests': [],
};

// Build CSP header value
const buildCSP = (directives: Record<string, string[]>) => {
  return Object.entries(directives)
    .map(([key, values]) => {
      if (values.length === 0) {
        return key;
      }
      return `${key} ${values.join(' ')}`;
    })
    .join('; ');
};

export const contentSecurityPolicy = buildCSP(cspDirectives);

// Security headers configuration
export const securityHeaders = [
  // Content Security Policy
  {
    key: 'Content-Security-Policy',
    value: contentSecurityPolicy,
  },
  // Prevent MIME type sniffing
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff',
  },
  // Prevent clickjacking
  {
    key: 'X-Frame-Options',
    value: 'DENY',
  },
  // Enable XSS filtering
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block',
  },
  // Referrer policy
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin',
  },
  // Permissions policy
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=(), payment=()',
  },
  // HSTS (HTTP Strict Transport Security)
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=31536000; includeSubDomains; preload',
  },
];

// Development-specific adjustments
if (process.env.NODE_ENV === 'development') {
  // Relax CSP for development
  const devCSP = buildCSP({
    ...cspDirectives,
    'script-src': [
      ...cspDirectives['script-src'],
      "'unsafe-eval'",
      "'unsafe-inline'",
    ],
    'connect-src': [
      ...cspDirectives['connect-src'],
      'ws://localhost:*',
      'http://localhost:*',
    ],
  });
  
  // Update CSP header for development
  const cspHeaderIndex = securityHeaders.findIndex(
    header => header.key === 'Content-Security-Policy'
  );
  if (cspHeaderIndex !== -1) {
    securityHeaders[cspHeaderIndex].value = devCSP;
  }
}
