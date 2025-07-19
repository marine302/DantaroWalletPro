'use client';

import { useState, useEffect } from 'react';
import { getStoredErrors, clearStoredErrors } from '@/components/GlobalErrorHandler';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, RefreshCw, Trash2, ChevronDown, ChevronUp } from 'lucide-react';

interface StoredError {
  type: string;
  message: string;
  timestamp: string;
  filename?: string;
  lineno?: number;
  colno?: number;
  stack?: string;
  reason?: string;
  userAgent?: string;
  url?: string;
}

export default function ErrorLogger() {
  const [errors, setErrors] = useState<StoredError[]>([]);
  const [expandedErrors, setExpandedErrors] = useState<Set<number>>(new Set());
  
  const refreshErrors = () => {
    const storedErrors = getStoredErrors();
    setErrors(storedErrors);
  };
  
  const clearErrors = () => {
    clearStoredErrors();
    setErrors([]);
    setExpandedErrors(new Set());
  };
  
  const toggleErrorExpansion = (index: number) => {
    const newExpanded = new Set(expandedErrors);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedErrors(newExpanded);
  };
  
  useEffect(() => {
    refreshErrors();
    
    // Refresh errors every 5 seconds - 임시 비활성화 (개발 중 성능 문제로)
    // const interval = setInterval(refreshErrors, 5000);
    
    // return () => clearInterval(interval);
  }, []);
  
  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          Error Logger
          <Badge variant="secondary">{errors.length}</Badge>
        </CardTitle>
        <CardDescription>
          Captured runtime errors and unhandled promise rejections
        </CardDescription>
        <div className="flex gap-2">
          <Button onClick={refreshErrors} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={clearErrors} variant="outline" size="sm">
            <Trash2 className="h-4 w-4 mr-2" />
            Clear All
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {errors.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-8">
            No errors captured yet. This is good! 🎉
          </p>
        ) : (
          <div className="space-y-4">
            {errors.map((error, index) => (
              <div key={index} className="border rounded-lg p-4 bg-red-50 border-red-200">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="destructive">{error.type}</Badge>
                      <span className="text-xs text-gray-500">
                        {new Date(error.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-red-800 mb-2">
                      {error.message || error.reason || 'Unknown error'}
                    </p>
                    {error.filename && (
                      <p className="text-xs text-gray-600">
                        {error.filename}:{error.lineno}:{error.colno}
                      </p>
                    )}
                    {error.url && (
                      <p className="text-xs text-gray-600">
                        URL: {error.url}
                      </p>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleErrorExpansion(index)}
                  >
                    {expandedErrors.has(index) ? (
                      <ChevronUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                
                {expandedErrors.has(index) && error.stack && (
                  <div className="mt-3 p-3 bg-red-100 rounded text-xs">
                    <p className="font-medium mb-2">Stack trace:</p>
                    <pre className="whitespace-pre-wrap text-red-700 overflow-x-auto">
                      {error.stack}
                    </pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
