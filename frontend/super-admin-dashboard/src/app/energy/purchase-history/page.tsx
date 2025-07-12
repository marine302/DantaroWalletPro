'use client';

import { useState, useEffect } from 'react';
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Download, Filter, Search, Eye, RefreshCw } from 'lucide-react';

interface PurchaseHistory {
  id: string;
  timestamp: string;
  provider: string;
  amount: number;
  pricePerEnergy: number;
  totalCost: number;
  margin: number;
  finalPrice: number;
  status: 'completed' | 'pending' | 'failed' | 'cancelled';
  type: 'auto' | 'manual';
  urgency: 'normal' | 'high' | 'emergency';
  approvedBy?: string;
  deliveryTime?: string;
  transactionHash?: string;
}

export default function PurchaseHistoryPage() {
  const [purchases, setPurchases] = useState<PurchaseHistory[]>([]);
  const [filteredPurchases, setFilteredPurchases] = useState<PurchaseHistory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [dateRange, setDateRange] = useState('7d');

  // 모의 데이터
  useEffect(() => {
    const mockPurchases: PurchaseHistory[] = [
      {
        id: '1',
        timestamp: '2024-01-15T10:30:00Z',
        provider: 'P2P Energy Trading',
        amount: 1000000,
        pricePerEnergy: 0.0041,
        totalCost: 4100,
        margin: 0.15,
        finalPrice: 0.0047,
        status: 'completed',
        type: 'auto',
        urgency: 'high',
        deliveryTime: '3분',
        transactionHash: '0x1234...5678'
      },
      {
        id: '2',
        timestamp: '2024-01-15T09:15:00Z',
        provider: 'JustLend Energy',
        amount: 2000000,
        pricePerEnergy: 0.0045,
        totalCost: 9000,
        margin: 0.10,
        finalPrice: 0.0050,
        status: 'completed',
        type: 'manual',
        urgency: 'normal',
        approvedBy: 'admin@example.com',
        deliveryTime: '8분',
        transactionHash: '0x9876...5432'
      },
      {
        id: '3',
        timestamp: '2024-01-15T08:45:00Z',
        provider: 'TronNRG',
        amount: 500000,
        pricePerEnergy: 0.0052,
        totalCost: 2600,
        margin: 0.25,
        finalPrice: 0.0065,
        status: 'failed',
        type: 'auto',
        urgency: 'emergency',
        deliveryTime: '실패'
      },
      {
        id: '4',
        timestamp: '2024-01-14T16:20:00Z',
        provider: 'JustLend Energy',
        amount: 1500000,
        pricePerEnergy: 0.0043,
        totalCost: 6450,
        margin: 0.10,
        finalPrice: 0.0047,
        status: 'completed',
        type: 'manual',
        urgency: 'normal',
        approvedBy: 'admin@example.com',
        deliveryTime: '12분',
        transactionHash: '0x1111...2222'
      },
      {
        id: '5',
        timestamp: '2024-01-14T14:10:00Z',
        provider: 'P2P Energy Trading',
        amount: 800000,
        pricePerEnergy: 0.0040,
        totalCost: 3200,
        margin: 0.15,
        finalPrice: 0.0046,
        status: 'pending',
        type: 'auto',
        urgency: 'high'
      }
    ];

    setTimeout(() => {
      setPurchases(mockPurchases);
      setFilteredPurchases(mockPurchases);
      setIsLoading(false);
    }, 1000);
  }, []);

  // 필터링 로직
  useEffect(() => {
    let filtered = purchases;

    // 검색 필터
    if (searchTerm) {
      filtered = filtered.filter(purchase => 
        purchase.provider.toLowerCase().includes(searchTerm.toLowerCase()) ||
        purchase.id.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // 상태 필터
    if (statusFilter !== 'all') {
      filtered = filtered.filter(purchase => purchase.status === statusFilter);
    }

    // 타입 필터
    if (typeFilter !== 'all') {
      filtered = filtered.filter(purchase => purchase.type === typeFilter);
    }

    // 날짜 필터
    const now = new Date();
    const filterDate = new Date();
    switch (dateRange) {
      case '1d':
        filterDate.setDate(now.getDate() - 1);
        break;
      case '7d':
        filterDate.setDate(now.getDate() - 7);
        break;
      case '30d':
        filterDate.setDate(now.getDate() - 30);
        break;
      default:
        filterDate.setFullYear(2000); // 모든 기간
    }
    
    filtered = filtered.filter(purchase => 
      new Date(purchase.timestamp) >= filterDate
    );

    setFilteredPurchases(filtered);
  }, [purchases, searchTerm, statusFilter, typeFilter, dateRange]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'auto': return 'bg-blue-100 text-blue-800';
      case 'manual': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'emergency': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'normal': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleExport = () => {
    // CSV 내보내기 로직
    const csvContent = "data:text/csv;charset=utf-8," + 
      "ID,날짜,공급자,수량,가격,총비용,마진,최종가격,상태,타입,긴급도\n" +
      filteredPurchases.map(p => 
        `${p.id},${p.timestamp},${p.provider},${p.amount},${p.pricePerEnergy},${p.totalCost},${p.margin},${p.finalPrice},${p.status},${p.type},${p.urgency}`
      ).join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "purchase-history.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const totalSpent = filteredPurchases.reduce((sum, p) => sum + p.totalCost, 0);
  const totalEnergy = filteredPurchases.reduce((sum, p) => sum + p.amount, 0);
  const avgPrice = filteredPurchases.length > 0 ? totalSpent / totalEnergy : 0;

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">구매 이력</h1>
              <p className="text-gray-600 mt-1">
                외부 에너지 구매 기록을 확인하고 관리합니다.
              </p>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" onClick={() => window.location.reload()}>
                <RefreshCw className="w-4 h-4 mr-2" />
                새로고침
              </Button>
              <Button onClick={handleExport}>
                <Download className="w-4 h-4 mr-2" />
                내보내기
              </Button>
            </div>
          </div>

          {/* 요약 통계 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardContent className="p-6">
                <div className="text-center">
                  <p className="text-sm text-gray-500">총 구매 건수</p>
                  <p className="text-2xl font-bold text-gray-900">{filteredPurchases.length}</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="text-center">
                  <p className="text-sm text-gray-500">총 구매 에너지</p>
                  <p className="text-2xl font-bold text-gray-900">{totalEnergy.toLocaleString()}</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="text-center">
                  <p className="text-sm text-gray-500">총 지출 금액</p>
                  <p className="text-2xl font-bold text-gray-900">{totalSpent.toFixed(2)} TRX</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="text-center">
                  <p className="text-sm text-gray-500">평균 가격</p>
                  <p className="text-2xl font-bold text-gray-900">{avgPrice.toFixed(4)} TRX</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 필터 섹션 */}
          <Card className="mb-6">
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="검색..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">모든 상태</option>
                  <option value="completed">완료</option>
                  <option value="pending">대기</option>
                  <option value="failed">실패</option>
                  <option value="cancelled">취소</option>
                </select>
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">모든 타입</option>
                  <option value="auto">자동</option>
                  <option value="manual">수동</option>
                </select>
                <select
                  value={dateRange}
                  onChange={(e) => setDateRange(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="1d">최근 1일</option>
                  <option value="7d">최근 7일</option>
                  <option value="30d">최근 30일</option>
                  <option value="all">전체 기간</option>
                </select>
                <Button variant="outline" className="w-full">
                  <Filter className="w-4 h-4 mr-2" />
                  필터 초기화
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 구매 이력 테이블 */}
        <Card>
          <CardHeader>
            <CardTitle>구매 기록</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-4">ID</th>
                    <th className="text-left p-4">날짜</th>
                    <th className="text-left p-4">공급자</th>
                    <th className="text-left p-4">수량</th>
                    <th className="text-left p-4">가격</th>
                    <th className="text-left p-4">총 비용</th>
                    <th className="text-left p-4">마진</th>
                    <th className="text-left p-4">상태</th>
                    <th className="text-left p-4">타입</th>
                    <th className="text-left p-4">긴급도</th>
                    <th className="text-left p-4">작업</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPurchases.map((purchase) => (
                    <tr key={purchase.id} className="border-b hover:bg-gray-50">
                      <td className="p-4 font-medium">{purchase.id}</td>
                      <td className="p-4">
                        {new Date(purchase.timestamp).toLocaleDateString('ko-KR', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </td>
                      <td className="p-4">{purchase.provider}</td>
                      <td className="p-4">{purchase.amount.toLocaleString()}</td>
                      <td className="p-4">{purchase.pricePerEnergy.toFixed(4)} TRX</td>
                      <td className="p-4">{purchase.totalCost.toFixed(2)} TRX</td>
                      <td className="p-4">{(purchase.margin * 100).toFixed(1)}%</td>
                      <td className="p-4">
                        <Badge className={getStatusColor(purchase.status)}>
                          {purchase.status}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <Badge className={getTypeColor(purchase.type)}>
                          {purchase.type}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <Badge className={getUrgencyColor(purchase.urgency)}>
                          {purchase.urgency}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <Button variant="ghost" size="sm">
                          <Eye className="w-4 h-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {filteredPurchases.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-500">검색 결과가 없습니다.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
