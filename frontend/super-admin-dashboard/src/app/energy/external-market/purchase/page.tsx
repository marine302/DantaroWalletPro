'use client';

import { useState } from 'react';
import { BasePage } from "@/components/ui/BasePage";
import { Section, Button, FormField } from '@/components/ui/DarkThemeComponents';
import { ArrowLeft, CheckCircle } from 'lucide-react';

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
  const [selectedProvider, setSelectedProvider] = useState('');
  const [purchaseAmount, setPurchaseAmount] = useState(1000000);
  const [urgencyLevel, setUrgencyLevel] = useState('normal');

  // 모의 공급자 데이터
  const providers = [
    { id: '1', name: 'JustLend Energy', pricePerEnergy: 0.0045, available: 5000000 },
    { id: '2', name: 'TronNRG', pricePerEnergy: 0.0052, available: 3500000 },
    { id: '3', name: 'P2P Energy Trading', pricePerEnergy: 0.0041, available: 2000000 },
  ];

  const getMarginRate = (urgency: string) => {
    switch (urgency) {
      case 'emergency': return 0.20;
      case 'high': return 0.15;
      default: return 0.10;
    }
  };

  const calculatePurchase = () => {
    const provider = providers.find(p => p.id === selectedProvider);
    if (!provider) return;

    const marginRate = getMarginRate(urgencyLevel);
    const totalCost = purchaseAmount * provider.pricePerEnergy;
    const finalPrice = provider.pricePerEnergy * (1 + marginRate);

    setPurchaseRequest({
      providerId: provider.id,
      providerName: provider.name,
      amount: purchaseAmount,
      pricePerEnergy: provider.pricePerEnergy,
      totalCost,
      urgency: urgencyLevel as 'normal' | 'high' | 'emergency',
      marginRate,
      finalPrice,
      estimatedDelivery: urgencyLevel === 'emergency' ? '즉시' : urgencyLevel === 'high' ? '5분' : '10분'
    });

    setStep(2);
  };

  const submitPurchase = async () => {
    setIsSubmitting(true);
    // 모의 제출 프로세스
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsSubmitting(false);
    setStep(3);
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'emergency': return 'text-red-400';
      case 'high': return 'text-orange-400';
      default: return 'text-green-400';
    }
  };

  const getUrgencyBadge = (urgency: string) => {
    const colors = {
      normal: 'bg-green-900 text-green-200',
      high: 'bg-orange-900 text-orange-200',
      emergency: 'bg-red-900 text-red-200'
    };
    return colors[urgency as keyof typeof colors] || 'bg-gray-900 text-gray-200';
  };

  if (step === 3) {
    return (
      <BasePage title="구매 완료" description="에너지 구매가 성공적으로 완료되었습니다">
        <div className="max-w-2xl mx-auto">
          <Section title="구매 결과">
            <div className="text-center py-8">
              <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-2">구매 성공!</h2>
              <p className="text-gray-400 mb-6">
                {purchaseRequest?.amount.toLocaleString()} 에너지가 성공적으로 구매되었습니다.
              </p>
              
              <div className="bg-gray-800 rounded-lg p-6 text-left">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-400">제공업체</p>
                    <p className="font-medium">{purchaseRequest?.providerName}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">구매량</p>
                    <p className="font-medium">{purchaseRequest?.amount.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">총 비용</p>
                    <p className="font-medium">${purchaseRequest?.totalCost.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">트랜잭션 ID</p>
                    <p className="font-mono text-sm">0x1234...abcd</p>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-4 mt-6">
                <Button onClick={() => window.history.back()}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  돌아가기
                </Button>
                <Button onClick={() => {setStep(1); setPurchaseRequest(null);}}>
                  새 구매
                </Button>
              </div>
            </div>
          </Section>
        </div>
      </BasePage>
    );
  }

  if (step === 2 && purchaseRequest) {
    return (
      <BasePage title="구매 확인" description="구매 정보를 확인하고 최종 승인합니다">
        <div className="max-w-2xl mx-auto">
          <Section title="구매 정보 확인">
            <div className="space-y-6">
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">구매 세부사항</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-400">제공업체</p>
                    <p className="font-medium">{purchaseRequest.providerName}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">구매량</p>
                    <p className="font-medium">{purchaseRequest.amount.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">원가</p>
                    <p className="font-medium">${purchaseRequest.pricePerEnergy}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">마진</p>
                    <p className="font-medium">{(purchaseRequest.marginRate * 100).toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">최종 단가</p>
                    <p className="font-medium">${purchaseRequest.finalPrice.toFixed(4)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">총 비용</p>
                    <p className="text-lg font-bold text-green-400">${purchaseRequest.totalCost.toFixed(2)}</p>
                  </div>
                </div>
                
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <div className="flex items-center justify-between">
                    <span className={`px-3 py-1 rounded-full text-sm ${getUrgencyBadge(purchaseRequest.urgency)}`}>
                      {purchaseRequest.urgency}
                    </span>
                    <span className="text-sm text-gray-400">
                      예상 배송: {purchaseRequest.estimatedDelivery}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex gap-4">
                <Button variant="secondary" onClick={() => setStep(1)}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  이전
                </Button>
                <Button onClick={submitPurchase} className="flex-1">
                  {isSubmitting ? (
                    <div className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      구매 중...
                    </div>
                  ) : (
                    '구매 확인'
                  )}
                </Button>
              </div>
            </div>
          </Section>
        </div>
      </BasePage>
    );
  }

  return (
    <BasePage title="수동 에너지 구매" description="원하는 제공업체에서 직접 에너지를 구매합니다">
      <div className="max-w-2xl mx-auto">
        <Section title="구매 설정">
          <div className="space-y-6">
            <FormField
              label="구매량"
              type="number"
              value={purchaseAmount}
              onChange={(value) => setPurchaseAmount(Number(value))}
              placeholder="1000000"
            />

            <div>
              <label className="block text-sm font-medium text-gray-200 mb-2">긴급도</label>
              <div className="grid grid-cols-3 gap-2">
                {['normal', 'high', 'emergency'].map((level) => (
                  <button
                    key={level}
                    onClick={() => setUrgencyLevel(level)}
                    className={`p-3 rounded-lg border ${
                      urgencyLevel === level 
                        ? 'border-blue-500 bg-blue-900/20' 
                        : 'border-gray-600 bg-gray-700'
                    }`}
                  >
                    <div className="text-center">
                      <div className={`text-sm font-medium ${getUrgencyColor(level)}`}>
                        {level === 'normal' ? '일반' : level === 'high' ? '높음' : '긴급'}
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        마진 {(getMarginRate(level) * 100).toFixed(0)}%
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-200 mb-2">제공업체 선택</label>
              <div className="space-y-2">
                {providers.map((provider) => (
                  <button
                    key={provider.id}
                    onClick={() => setSelectedProvider(provider.id)}
                    className={`w-full p-4 rounded-lg border text-left ${
                      selectedProvider === provider.id
                        ? 'border-blue-500 bg-blue-900/20'
                        : 'border-gray-600 bg-gray-700'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{provider.name}</h4>
                        <p className="text-sm text-gray-400">
                          가용량: {provider.available.toLocaleString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-green-400">${provider.pricePerEnergy}</p>
                        <p className="text-xs text-gray-400">per energy</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <Button 
              onClick={calculatePurchase} 
              className={`w-full ${(!selectedProvider || purchaseAmount <= 0) ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              구매 계산
            </Button>
          </div>
        </Section>
      </div>
    </BasePage>
  );
}
