'use client';

import { useState, useEffect } from 'react';
import { BasePage } from "@/components/ui/BasePage";
import { Section, Button, FormField } from '@/components/ui/DarkThemeComponents';
import { ArrowLeft, CheckCircle, AlertTriangle, Zap } from 'lucide-react';
import { tronNRGService, TronNRGProvider, TronNRGOrderRequest, TronNRGOrderResponse } from '@/services/tron-nrg-service';

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
  orderType: 'market' | 'limit';
  duration: number;
  fees: {
    tradingFee: number;
    withdrawalFee: number;
  };
}

export default function ManualPurchasePage() {
  const [step, setStep] = useState(1);
  const [purchaseRequest, setPurchaseRequest] = useState<PurchaseRequest | null>(null);
  const [orderResponse, setOrderResponse] = useState<TronNRGOrderResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProvider, setSelectedProvider] = useState('');
  const [purchaseAmount, setPurchaseAmount] = useState(1000000);
  const [urgencyLevel, setUrgencyLevel] = useState('normal');
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market');
  const [limitPrice, setLimitPrice] = useState(0);
  const [duration, setDuration] = useState(3); // 기본 3일

  // 실제 공급자 데이터
  const [providers, setProviders] = useState<TronNRGProvider[]>([]);
  const [mockProviders] = useState([
    { id: 'justlend-1', name: 'JustLend Energy', pricePerEnergy: 0.0045, availableEnergy: 5000000, reliability: 95.2, avgResponseTime: 3.8, minOrderSize: 1000, maxOrderSize: 5000000, fees: { tradingFee: 0.002, withdrawalFee: 0.0005 }, status: 'online' as const },
    { id: 'p2p-energy-1', name: 'P2P Energy Trading', pricePerEnergy: 0.0041, availableEnergy: 2000000, reliability: 93.8, avgResponseTime: 4.2, minOrderSize: 500, maxOrderSize: 3000000, fees: { tradingFee: 0.0025, withdrawalFee: 0.0008 }, status: 'online' as const },
  ]);

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    try {
      setIsLoading(true);
      const tronProviders = await tronNRGService.getProviders();
      
      // TronNRG 공급자와 Mock 공급자 병합
      const allProviders = [
        ...tronProviders,
        ...mockProviders.map(p => ({ ...p, lastUpdated: new Date().toISOString() }))
      ];
      
      setProviders(allProviders);
      
      // 첫 번째 공급자를 기본 선택
      if (allProviders.length > 0) {
        setSelectedProvider(allProviders[0].id);
      }
    } catch (error) {
      console.error('❌ Failed to load providers:', error);
      setError('공급자 정보를 불러오는데 실패했습니다.');
      setProviders(mockProviders.map(p => ({ ...p, lastUpdated: new Date().toISOString() })));
      if (mockProviders.length > 0) {
        setSelectedProvider(mockProviders[0].id);
      }
    } finally {
      setIsLoading(false);
    }
  };

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
    const basePrice = orderType === 'limit' ? limitPrice : provider.pricePerEnergy;
    const totalCost = purchaseAmount * basePrice;
    const finalPrice = basePrice * (1 + marginRate);
    const tradingFee = totalCost * provider.fees.tradingFee;
    const finalTotalCost = totalCost + tradingFee;

    setPurchaseRequest({
      providerId: provider.id,
      providerName: provider.name,
      amount: purchaseAmount,
      pricePerEnergy: basePrice,
      totalCost: finalTotalCost,
      urgency: urgencyLevel as 'normal' | 'high' | 'emergency',
      marginRate,
      finalPrice,
      estimatedDelivery: urgencyLevel === 'emergency' ? '즉시' : urgencyLevel === 'high' ? '5분' : '10분',
      orderType,
      duration,
      fees: provider.fees
    });

    setStep(2);
  };

  const submitPurchase = async () => {
    if (!purchaseRequest) return;
    
    setIsSubmitting(true);
    setError(null);
    
    try {
      // TronNRG API 주문 생성
      const orderRequest: TronNRGOrderRequest = {
        amount: purchaseRequest.amount,
        priceLimit: purchaseRequest.orderType === 'limit' ? purchaseRequest.pricePerEnergy : undefined,
        orderType: purchaseRequest.orderType,
        duration: purchaseRequest.duration
      };

      const response = await tronNRGService.createOrder(orderRequest);
      setOrderResponse(response);
      setStep(3);
      
    } catch (error) {
      console.error('❌ Purchase failed:', error);
      setError('구매 주문 생성에 실패했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const validatePurchase = () => {
    const provider = providers.find(p => p.id === selectedProvider);
    if (!provider) return false;
    
    if (purchaseAmount < provider.minOrderSize) {
      setError(`최소 주문량은 ${provider.minOrderSize.toLocaleString()}입니다.`);
      return false;
    }
    
    if (purchaseAmount > provider.maxOrderSize) {
      setError(`최대 주문량은 ${provider.maxOrderSize.toLocaleString()}입니다.`);
      return false;
    }
    
    if (purchaseAmount > provider.availableEnergy) {
      setError(`현재 가용량은 ${provider.availableEnergy.toLocaleString()}입니다.`);
      return false;
    }
    
    setError(null);
    return true;
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

  if (isLoading) {
    return (
      <BasePage title="에너지 구매" description="외부 공급자로부터 에너지를 구매합니다">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      </BasePage>
    );
  }

  if (step === 3) {
    return (
      <BasePage title="구매 완료" description="에너지 구매가 성공적으로 완료되었습니다">
        <div className="max-w-2xl mx-auto">
          <Section title="구매 결과">
            <div className="text-center py-8">
              <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-2">구매 주문 생성 완료!</h2>
              <p className="text-gray-400 mb-6">
                {purchaseRequest?.amount.toLocaleString()} 에너지 구매 주문이 생성되었습니다.
              </p>
              
              <div className="bg-gray-800 rounded-lg p-6 text-left mb-6">
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
                    <p className="text-sm text-gray-400">주문 ID</p>
                    <p className="font-mono text-sm text-blue-400">{orderResponse?.orderId}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">주문 상태</p>
                    <span className={`px-2 py-1 rounded text-xs ${
                      orderResponse?.status === 'filled' ? 'bg-green-900 text-green-200' :
                      orderResponse?.status === 'pending' ? 'bg-yellow-900 text-yellow-200' :
                      'bg-gray-900 text-gray-200'
                    }`}>
                      {orderResponse?.status === 'filled' ? '체결' :
                       orderResponse?.status === 'pending' ? '대기중' :
                       orderResponse?.status === 'cancelled' ? '취소됨' : '실패'}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">총 비용</p>
                    <p className="font-medium">${purchaseRequest?.totalCost.toFixed(4)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">예상 전달</p>
                    <p className="font-medium">{purchaseRequest?.estimatedDelivery}</p>
                  </div>
                </div>
              </div>

              {orderResponse?.status === 'pending' && (
                <div className="bg-yellow-900/50 border border-yellow-700 rounded-lg p-4 mb-6">
                  <div className="flex items-center gap-2 text-yellow-400">
                    <AlertTriangle className="w-5 h-5" />
                    <span className="font-medium">주문 처리 중</span>
                  </div>
                  <p className="text-sm text-yellow-200 mt-1">
                    주문이 처리되고 있습니다. 완료까지 {purchaseRequest?.estimatedDelivery}가 소요될 예정입니다.
                  </p>
                </div>
              )}
              
              <div className="flex gap-4 mt-6">
                <Button onClick={() => window.history.back()}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  마켓으로 돌아가기
                </Button>
                <Button onClick={() => {setStep(1); setPurchaseRequest(null); setOrderResponse(null);}}>
                  새 구매 주문
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
            {error && (
              <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 mb-6">
                <div className="flex items-center gap-2 text-red-400">
                  <AlertTriangle className="w-5 h-5" />
                  <span className="font-medium">오류</span>
                </div>
                <p className="text-sm text-red-200 mt-1">{error}</p>
              </div>
            )}
            
            <div className="space-y-6">
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Zap className="w-5 h-5 text-blue-400" />
                  구매 세부사항
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-400">제공업체</p>
                    <p className="font-medium">{purchaseRequest.providerName}</p>
                    {purchaseRequest.providerId.startsWith('tronnrg-') && (
                      <span className="text-xs text-blue-400">TronNRG API</span>
                    )}
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">구매량</p>
                    <p className="font-medium">{purchaseRequest.amount.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">주문 타입</p>
                    <p className="font-medium">{purchaseRequest.orderType === 'market' ? '시장가' : '지정가'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">기준 단가</p>
                    <p className="font-medium">${purchaseRequest.pricePerEnergy.toFixed(6)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">마진율</p>
                    <p className="font-medium">{(purchaseRequest.marginRate * 100).toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">최종 단가</p>
                    <p className="font-medium">${purchaseRequest.finalPrice.toFixed(6)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">거래 수수료</p>
                    <p className="font-medium">{(purchaseRequest.fees.tradingFee * 100).toFixed(3)}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">임대 기간</p>
                    <p className="font-medium">{purchaseRequest.duration}일</p>
                  </div>
                </div>
                
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className={`px-3 py-1 rounded-full text-sm ${getUrgencyBadge(purchaseRequest.urgency)}`}>
                        긴급도: {purchaseRequest.urgency === 'normal' ? '일반' : purchaseRequest.urgency === 'high' ? '높음' : '긴급'}
                      </span>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-green-400">
                        총 비용: ${purchaseRequest.totalCost.toFixed(4)}
                      </p>
                      <p className="text-sm text-gray-400">
                        예상 전달: {purchaseRequest.estimatedDelivery}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex gap-4">
                <Button variant="secondary" onClick={() => setStep(1)}>
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  이전
                </Button>
                <Button onClick={submitPurchase} className="flex-1" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <div className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      주문 생성 중...
                    </div>
                  ) : (
                    '구매 주문 생성'
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
          {error && (
            <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-2 text-red-400">
                <AlertTriangle className="w-5 h-5" />
                <span className="font-medium">오류</span>
              </div>
              <p className="text-sm text-red-200 mt-1">{error}</p>
            </div>
          )}
          
          <div className="space-y-6">
            <FormField
              label="구매량"
              type="number"
              value={purchaseAmount}
              onChange={(value) => {
                setPurchaseAmount(Number(value));
                setError(null);
              }}
              placeholder="1000000"
              helpText="최소 주문량과 최대 주문량을 확인하세요"
            />

            <div>
              <label className="block text-sm font-medium text-gray-200 mb-2">주문 타입</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setOrderType('market')}
                  className={`p-3 rounded-lg border ${
                    orderType === 'market' 
                      ? 'border-blue-500 bg-blue-900/20' 
                      : 'border-gray-600 bg-gray-700'
                  }`}
                >
                  <div className="text-center">
                    <div className="text-sm font-medium">시장가</div>
                    <div className="text-xs text-gray-400 mt-1">즉시 체결</div>
                  </div>
                </button>
                <button
                  onClick={() => setOrderType('limit')}
                  className={`p-3 rounded-lg border ${
                    orderType === 'limit' 
                      ? 'border-blue-500 bg-blue-900/20' 
                      : 'border-gray-600 bg-gray-700'
                  }`}
                >
                  <div className="text-center">
                    <div className="text-sm font-medium">지정가</div>
                    <div className="text-xs text-gray-400 mt-1">가격 지정</div>
                  </div>
                </button>
              </div>
            </div>

            {orderType === 'limit' && (
              <FormField
                label="지정 가격"
                type="number"
                value={limitPrice}
                onChange={(value) => setLimitPrice(Number(value))}
                placeholder="0.0041"
                step="0.000001"
                helpText="원하는 최대 구매 가격을 입력하세요"
              />
            )}

            <FormField
              label="임대 기간 (일)"
              type="number"
              value={duration}
              onChange={(value) => setDuration(Number(value))}
              placeholder="3"
              min="1"
              max="30"
              helpText="에너지 임대 기간을 설정하세요 (1-30일)"
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
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium">{provider.name}</h4>
                          {provider.id.startsWith('tronnrg-') && (
                            <span className="px-2 py-1 bg-blue-900 text-blue-200 rounded-full text-xs">
                              TronNRG
                            </span>
                          )}
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            provider.status === 'online' ? 'bg-green-900 text-green-200' :
                            provider.status === 'maintenance' ? 'bg-yellow-900 text-yellow-200' :
                            'bg-red-900 text-red-200'
                          }`}>
                            {provider.status === 'online' ? '온라인' : provider.status === 'maintenance' ? '점검중' : '오프라인'}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-4 text-sm text-gray-400 mt-2">
                          <p>가용량: {provider.availableEnergy.toLocaleString()}</p>
                          <p>신뢰도: {provider.reliability}%</p>
                          <p>최소: {provider.minOrderSize.toLocaleString()}</p>
                          <p>최대: {provider.maxOrderSize.toLocaleString()}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-green-400">${provider.pricePerEnergy.toFixed(6)}</p>
                        <p className="text-xs text-gray-400">per energy</p>
                        <p className="text-xs text-gray-400 mt-1">
                          수수료: {(provider.fees.tradingFee * 100).toFixed(3)}%
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <Button 
              onClick={() => {
                if (validatePurchase()) {
                  calculatePurchase();
                }
              }}
              className="w-full"
              disabled={!selectedProvider || purchaseAmount <= 0 || isLoading}
            >
              {isLoading ? '로딩 중...' : '구매 정보 계산'}
            </Button>
          </div>
        </Section>
      </div>
    </BasePage>
  );
}
