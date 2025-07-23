/**
 * Security utilities for input sanitization and XSS prevention
 */

import DOMPurify from 'isomorphic-dompurify';

/**
 * Sanitize HTML content to prevent XSS attacks
 */
export function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
    ALLOWED_ATTR: ['href', 'target'],
  });
}

/**
 * Escape special HTML characters
 */
export function escapeHtml(unsafe: string): string {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Validate and sanitize user input
 */
export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  customValidator?: (value: string) => boolean;
}

export interface ValidationResult {
  isValid: boolean;
  sanitizedValue: string;
  errors: string[];
}

export function validateAndSanitizeInput(
  input: string,
  rules: ValidationRule = {}
): ValidationResult {
  const errors: string[] = [];
  let sanitizedValue = input.trim();

  // Required validation
  if (rules.required && !sanitizedValue) {
    errors.push('Field is required');
    return { isValid: false, sanitizedValue: '', errors };
  }

  // Length validations
  if (rules.minLength && sanitizedValue.length < rules.minLength) {
    errors.push(`Minimum length is ${rules.minLength} characters`);
  }

  if (rules.maxLength && sanitizedValue.length > rules.maxLength) {
    errors.push(`Maximum length is ${rules.maxLength} characters`);
    sanitizedValue = sanitizedValue.substring(0, rules.maxLength);
  }

  // Pattern validation
  if (rules.pattern && !rules.pattern.test(sanitizedValue)) {
    errors.push('Invalid format');
  }

  // Custom validation
  if (rules.customValidator && !rules.customValidator(sanitizedValue)) {
    errors.push('Custom validation failed');
  }

  // Sanitize the value
  sanitizedValue = escapeHtml(sanitizedValue);

  return {
    isValid: errors.length === 0,
    sanitizedValue,
    errors,
  };
}

/**
 * Common validation patterns
 */
export const ValidationPatterns = {
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  phone: /^\+?[\d\s\-\(\)]+$/,
  alphanumeric: /^[a-zA-Z0-9]+$/,
  alphanumericWithSpaces: /^[a-zA-Z0-9\s]+$/,
  numeric: /^\d+$/,
  decimal: /^\d+(\.\d+)?$/,
  url: /^https?:\/\/[^\s]+$/,
  ipAddress: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
  // Crypto address patterns
  tronAddress: /^T[A-Za-z1-9]{33}$/,
  ethereumAddress: /^0x[a-fA-F0-9]{40}$/,
};

/**
 * Sanitize object properties recursively
 */
export function sanitizeObject<T extends Record<string, any>>(obj: T): T {
  const sanitized = {} as T;

  for (const [key, value] of Object.entries(obj)) {
    if (typeof value === 'string') {
      sanitized[key as keyof T] = escapeHtml(value) as T[keyof T];
    } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      sanitized[key as keyof T] = sanitizeObject(value) as T[keyof T];
    } else if (Array.isArray(value)) {
      sanitized[key as keyof T] = value.map(item =>
        typeof item === 'string' ? escapeHtml(item) : 
        typeof item === 'object' && item !== null ? sanitizeObject(item) : item
      ) as T[keyof T];
    } else {
      sanitized[key as keyof T] = value;
    }
  }

  return sanitized;
}

/**
 * Generate secure random string for CSRF tokens
 */
export function generateSecureToken(length: number = 32): string {
  if (typeof window !== 'undefined' && window.crypto) {
    const array = new Uint8Array(length);
    window.crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }
  
  // Fallback for server-side
  const crypto = require('crypto');
  return crypto.randomBytes(length).toString('hex');
}

/**
 * Rate limiting helper
 */
class RateLimiter {
  private attempts: Map<string, { count: number; resetTime: number }> = new Map();

  isAllowed(identifier: string, maxAttempts: number, windowMs: number): boolean {
    const now = Date.now();
    const attempt = this.attempts.get(identifier);

    if (!attempt || now > attempt.resetTime) {
      this.attempts.set(identifier, { count: 1, resetTime: now + windowMs });
      return true;
    }

    if (attempt.count >= maxAttempts) {
      return false;
    }

    attempt.count++;
    return true;
  }

  getRemainingAttempts(identifier: string, maxAttempts: number): number {
    const attempt = this.attempts.get(identifier);
    if (!attempt) return maxAttempts;
    return Math.max(0, maxAttempts - attempt.count);
  }

  getResetTime(identifier: string): number {
    const attempt = this.attempts.get(identifier);
    return attempt ? attempt.resetTime : Date.now();
  }
}

export const rateLimiter = new RateLimiter();

/**
 * Secure localStorage wrapper with encryption
 */
export class SecureStorage {
  private static encode(value: string): string {
    return btoa(encodeURIComponent(value));
  }

  private static decode(encoded: string): string {
    try {
      return decodeURIComponent(atob(encoded));
    } catch {
      return '';
    }
  }

  static setItem(key: string, value: string): boolean {
    try {
      if (typeof window === 'undefined') return false;
      const encoded = this.encode(value);
      localStorage.setItem(key, encoded);
      return true;
    } catch {
      return false;
    }
  }

  static getItem(key: string): string | null {
    try {
      if (typeof window === 'undefined') return null;
      const encoded = localStorage.getItem(key);
      return encoded ? this.decode(encoded) : null;
    } catch {
      return null;
    }
  }

  static removeItem(key: string): boolean {
    try {
      if (typeof window === 'undefined') return false;
      localStorage.removeItem(key);
      return true;
    } catch {
      return false;
    }
  }

  static clear(): boolean {
    try {
      if (typeof window === 'undefined') return false;
      localStorage.clear();
      return true;
    } catch {
      return false;
    }
  }
}

/**
 * JWT token validation
 */
export function isValidJWT(token: string): boolean {
  if (!token) return false;
  
  const parts = token.split('.');
  if (parts.length !== 3) return false;
  
  try {
    // Decode header and payload
    const header = JSON.parse(atob(parts[0]));
    const payload = JSON.parse(atob(parts[1]));
    
    // Check if token is expired
    if (payload.exp && Date.now() >= payload.exp * 1000) {
      return false;
    }
    
    return true;
  } catch {
    return false;
  }
}

/**
 * Get JWT payload without verification (for client-side use only)
 */
export function getJWTPayload(token: string): any | null {
  if (!isValidJWT(token)) return null;
  
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload));
  } catch {
    return null;
  }
}
