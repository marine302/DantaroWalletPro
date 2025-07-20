'use client'

import React from 'react'
import { Sidebar } from '@/components/layout/Sidebar'

export default function SimpleUserPage() {
  return (
    <Sidebar>
      <div className="container mx-auto p-6">
        <h1 className="text-2xl font-bold mb-4">사용자 관리 테스트</h1>
        <p>이 페이지가 정상적으로 표시되는지 확인합니다.</p>
        <div className="bg-blue-100 p-4 rounded mt-4">
          <p>Sidebar와 기본 레이아웃이 정상 작동 중입니다.</p>
        </div>
      </div>
    </Sidebar>
  )
}
