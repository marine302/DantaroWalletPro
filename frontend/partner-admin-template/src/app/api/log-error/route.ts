import { NextRequest, NextResponse } from 'next/server';
import { writeFile, existsSync, mkdirSync } from 'fs';
import { join } from 'path';
import { promisify } from 'util';

const writeFileAsync = promisify(writeFile);

export async function POST(request: NextRequest) {
  try {
    const errorData = await request.json();
    
    // Create logs directory if it doesn't exist
    const logsDir = join(process.cwd(), 'logs');
    if (!existsSync(logsDir)) {
      mkdirSync(logsDir, { recursive: true });
    }
    
    // Create log filename with current date
    const today = new Date().toISOString().split('T')[0];
    const logFile = join(logsDir, `frontend-errors-${today}.log`);
    
    // Format error data
    const logEntry = {
      timestamp: new Date().toISOString(),
      ...errorData,
    };
    
    // Append to log file
    const logLine = JSON.stringify(logEntry) + '\n';
    await writeFileAsync(logFile, logLine, { flag: 'a' });
    
    // Also log to console for immediate visibility
    console.error('🚨 Frontend Error Logged:', logEntry);
    
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Failed to log error:', error);
    return NextResponse.json({ success: false, error: 'Failed to log error' }, { status: 500 });
  }
}
