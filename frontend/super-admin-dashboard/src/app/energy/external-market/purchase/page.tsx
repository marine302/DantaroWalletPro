'use client';

import { useState } from 'react';
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ArrowLeft, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

interface PurchaseRequest {
  providerId: string;
  providerName: string;
  amount: number;
  pricePerEnergy: number;
  totalCost: number;
  urgency: 'normal' | 'high' | 'emergency';
  marginRate: number;
  finalPrice: number;
  estimatedDelivery: string;
}

export default function ManualPurchasePage() {
  const [step, setStep] = useState(1);
  const [purchaseRequest, setPurchaseRequest] = useState<PurchaseRequest | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 모의 공급자 데이터
  const providers = [
    { id: '1', name: 'JustLend Energy', pricePerEnergy: 0.0045, available: 5000000 },
    { id: '2', name: 'TronNRG', pricePerEnergy: 0.0052, available: 3500000 },
    { id: '4', name: 'P2P Energy Trading', pricePerEnergy: 0.0041, available: 2800000 }
  ];

  const handleProviderSelect = (providerId: string, amount: number, urgency: 'normal' | 'high' | 'emergency') => {
    const provider = providers.find(p => p.id === providerId);
    if (!provider) return;

    const marginRate = urgency === 'emergency' ? 0.25 : urgency === 'high' ? 0.15 : 0.10;
    const totalCost = amount * provider.pricePerEnergy;
    const finalPrice = provider.pricePerEnergy * (1 + marginRate);

    setPurchaseRequest({
      providerId,
      providerName: provider.name,
      amount,
      pricePerEnergy: provider.pricePerEnergy,
      totalCost,
      urgency,
      marginRate,
      finalPrice,
      estimatedDelivery: urgency === 'emergency' ? '즉시' : urgency === 'high' ? '5분 내' : '10분 내'
    });

    setStep(2);
  };

  const handleSubmit = async () => {
    if (!purchaseRequest) return;

    setIsSubmitting(true);
    
    // 모의 API 호출
    setTimeout(() => {
      setIsSubmitting(false);
      setStep(3);
    }, 2000);
  };

  const handleGoBack = () => {
    window.history.back();
  };

  const handleGoToMarket = () => {
    window.location.href = '/energy/external-market';
  };

  const handleGoToHistory = () => {
    window.location.href = '/energy/purchase-history';
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'emergency': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'normal': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        {/* 헤더 */}
        <div className="mb-6">
          <div className="flex items-center mb-4">
            <Button
              variant="ghost"
              onClick={handleGoBack}
              className="mr-4"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              돌아가기
            </Button>
            <h1 className="text-2xl font-bold">수동 에너지 구매</h1>
          </div>
          
          {/* 진행 단계 */}
          <div className="flex items-center space-x-4">
            <div className={`flex items-center ${step >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
                1
              </div>
              <span className="ml-2 text-sm font-medium">구매 설정</span>
            </div>
            <div className="flex-1 h-0.5 bg-gray-200">
              <div className={`h-full ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`} />
            </div>
            <div className={`flex items-center ${step >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
                2
              </div>
              <span className="ml-2 text-sm font-medium">확인</span>
            </div>
            <div className="flex-1 h-0.5 bg-gray-200">
              <div className={`h-full ${step >= 3 ? 'bg-blue-600' : 'bg-gray-200'}`} />
            </div>
            <div className={`flex items-center ${step >= 3 ? 'text-blue-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 3 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
                3
              </div>
              <span className="ml-2 text-sm font-medium">완료</span>
            </div>
          </div>
        </div>

        {/* Step 1: 구매 설정 */}
        {step === 1 && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>구매 정보 설정</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      구매 수량
                    </label>
                    <select
                      id="amount"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      defaultValue="1000000"
                    >
                      <option value="500000">500,000 에너지</option>
                      <option value="1000000">1,000,000 에너지</option>
                      <option value="2000000">2,000,000 에너지</option>
                      <option value="5000000">5,000,000 에너지</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      긴급도
                    </label>
                    <select
                      id="urgency"
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      defaultValue="normal"
                    >
                      <option value="normal">일반 (마진 10%)</option>
                      <option value="high">높음 (마진 15%)</option>
                      <option value="emergency">긴급 (마진 25%)</option>
                    </select>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>공급자 선택</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {providers.map((provider) => (
                    <div
                      key={provider.id}
                      className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h3 className="font-medium text-gray-900">{provider.name}</h3>
                          <p className="text-sm text-gray-500">
                            가격: {provider.pricePerEnergy.toFixed(4)} TRX/에너지
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-gray-500">가용량</p>
                          <p className="font-medium">{provider.available.toLocaleString()}</p>
                        </div>
                      </div>
                      <Button
                        onClick={() => {
                          const amountSelect = document.getElementById('amount') as HTMLSelectElement;
                          const urgencySelect = document.getElementById('urgency') as HTMLSelectElement;
                          handleProviderSelect(
                            provider.id,
                            Number(amountSelect.value),
                            urgencySelect.value as 'normal' | 'high' | 'emergency'
                          );
                        }}
                        className="w-full"
                      >
                        선택
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Step 2: 확인 */}
        {step === 2 && purchaseRequest && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>구매 요청 확인</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">공급자</p>
                      <p className="font-medium">{purchaseRequest.providerName}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">구매 수량</p>
                      <p className="font-medium">{purchaseRequest.amount.toLocaleString()} 에너지</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">공급자 가격</p>
                      <p className="font-medium">{purchaseRequest.pricePerEnergy.toFixed(4)} TRX</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">총 비용</p>
                      <p className="font-medium">{purchaseRequest.totalCost.toFixed(2)} TRX</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">긴급도</p>
                      <Badge className={getUrgencyColor(purchaseRequest.urgency)}>
                        {purchaseRequest.urgency}
                      </Badge>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">마진율</p>
                      <p className="font-medium">{(purchaseRequest.marginRate * 100).toFixed(1)}%</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">파트너사 판매가</p>
                      <p className="font-medium text-blue-600">{purchaseRequest.finalPrice.toFixed(4)} TRX</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">예상 배송</p>
                      <p className="font-medium">{purchaseRequest.estimatedDelivery}</p>
                    </div>
                  </div>

                  <div className="border-t pt-4">
                    <div className="flex items-center text-amber-600 mb-2">
                      <AlertTriangle className="w-4 h-4 mr-2" />
                      <span className="text-sm font-medium">주의사항</span>
                    </div>
                    <ul className="text-sm text-gray-600 space-y-1">
                      <li>• 구매 승인 후 취소가 불가능합니다</li>
                      <li>• 에너지 배송은 공급자 상황에 따라 지연될 수 있습니다</li>
                      <li>• 마진율은 긴급도에 따라 자동 적용됩니다</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="flex gap-4">
              <Button variant="outline" onClick={() => setStep(1)}>
                이전
              </Button>
              <Button 
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="flex-1"
              >
                {isSubmitting ? (
                  <>
                    <Clock className="w-4 h-4 mr-2 animate-spin" />
                    처리 중...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    구매 승인
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: 완료 */}
        {step === 3 && purchaseRequest && (
          <div className="space-y-6">
            <Card>
              <CardContent className="p-8 text-center">
                <div className="mb-4">
                  <CheckCircle className="w-16 h-16 text-green-500 mx-auto" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  구매 요청이 완료되었습니다
                </h2>
                <p className="text-gray-600 mb-6">
                  {purchaseRequest.providerName}에서 {purchaseRequest.amount.toLocaleString()} 에너지를 구매했습니다.
                </p>
                
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">총 비용</p>
                      <p className="font-medium">{purchaseRequest.totalCost.toFixed(2)} TRX</p>
                    </div>
                    <div>
                      <p className="text-gray-500">예상 배송</p>
                      <p className="font-medium">{purchaseRequest.estimatedDelivery}</p>
                    </div>
                  </div>
                </div>

                <div className="flex gap-4">
                  <Button 
                    variant="outline" 
                    onClick={handleGoToMarket}
                    className="flex-1"
                  >
                    시장으로 돌아가기
                  </Button>
                  <Button 
                    onClick={handleGoToHistory}
                    className="flex-1"
                  >
                    구매 이력 보기
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
