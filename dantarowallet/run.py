#!/usr/bin/env python3
"""
DantaroWallet 개발 서버 실행 스크립트
Python으로 작성된 개발 전용 실행기

사용법:
    python run.py              # 개발 서버 시작
    python run.py --prod        # 프로덕션 모드
    python run.py --port 8080   # 포트 지정
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="DantaroWallet 개발 서버")
    parser.add_argument("--port", type=int, default=8000, help="서버 포트")
    parser.add_argument("--prod", action="store_true", help="프로덕션 모드")
    parser.add_argument("--host", default="0.0.0.0", help="서버 호스트")
    
    args = parser.parse_args()
    
    # 현재 디렉토리가 올바른지 확인
    if not Path("app/main.py").exists():
        print("❌ app/main.py를 찾을 수 없습니다. 프로젝트 루트에서 실행해주세요.")
        sys.exit(1)
    
    # uvicorn 명령어 구성
    cmd = [
        "uvicorn",
        "app.main:app",
        "--host", args.host,
        "--port", str(args.port)
    ]
    
    if not args.prod:
        cmd.extend(["--reload", "--log-level", "debug"])
    
    print(f"🚀 서버 시작 중... http://{args.host}:{args.port}")
    print(f"📖 API 문서: http://{args.host}:{args.port}/api/v1/docs")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 서버가 중지되었습니다.")


if __name__ == "__main__":
    main()
