# 🧠 신경망 뉴런 모델 총정리

## 1. 뉴런 모델의 큰 계보

| 구분 | 특징 | 대표 모델 |
|------|------|------------|
| **생물학적(Spiking Neural Model) - SNN** | 실제 뇌 뉴런처럼 스파이크(전기 펄스)로 정보 전달 | LIF, Izhikevich, Hodgkin–Huxley 등 |
| **인공 신경망(ANN)** | 수학적으로 단순화된 뉴런, 연속 값으로 정보 전달 | Perceptron, McCulloch-Pitts, ReLU 뉴런 등 |

---

## 2. 비스파이킹 (Non-Spiking) 모델

### (1) McCulloch-Pitts Neuron (1943)
- 역사상 1호 뉴런 모델
- 입력 × 가중치 합 → 임계값 넘으면 1, 아니면 0

**수식:**  
\( y = \begin{cases}1, & \text{if } \sum w_i x_i > \theta \\ 0, & \text{otherwise}\end{cases} \)

---

### (2) Perceptron
- M-P 뉴런에서 학습(가중치 조정)을 추가한 버전
- XOR 안 풀리는 한계로 유명함 (선형 분리만 가능)

---

### (3) Sigmoid / Tanh / ReLU 뉴런
- 현대 딥러닝의 기본 유닛
- 연속적인 출력 (0~1 or -1~1 or 0~∞)
- 생물학보단 수학적 편의성에 초점

---

## 3. 스파이킹 뉴런 (Spiking Neural Models) - SNN

정보가 전압 변화(스파이크)로 전달되고, 시간 축이 중요함.  
즉, *“언제 발화하느냐”* 가 정보다.

---

### (1) LIF (Leaky Integrate-and-Fire)
- 전압 누적 + 누수 + 임계값 초과 시 스파이크 발생
- 스파이크 후 전압 reset
- 구현 쉽고 계산량 적음 → SNN 기본 단위

**미분방정식:**  
\( \tau_m \frac{dV}{dt} = - (V - V_{rest}) + R I \)  
임계값 초과 시 \(V \leftarrow V_{reset}\)

> 비유: 양동이에 물이 차다 넘치면 펑 터지는 모델

---

### (2) IF (Integrate-and-Fire)
- LIF의 단순 버전 (누수 없음)
- 전압 계속 누적하다가 임계값 넘으면 발화
- 수학적으로 단순하지만 생물학적 리얼리티 낮음

---

### (3) Izhikevich Model
- 계산은 빠르고, 생물학적 다양성도 표현 가능  
- 다양한 스파이킹 패턴(발작, 진동, 급발화 등)을 재현 가능

**식:**  
\[
\begin{cases}
\frac{dv}{dt} = 0.04v^2 + 5v + 140 - u + I \\
\frac{du}{dt} = a(bv - u)
\end{cases}
\]  
발화 시 \(v \geq 30mV\) → reset

---

### (4) Hodgkin–Huxley Model
- 가장 생물학적으로 정확한 뉴런 모델
- 나트륨/칼륨 채널의 열림 확률까지 모델링
- 계산량 매우 많음 → 주로 뇌과학 시뮬에 사용

---

### (5) Adaptive Exponential Integrate-and-Fire (AdEx)
- LIF에서 진화형
- 발화 후 적응(adaptation) 포함 → 연속 발화 시 반응 약화 (피로도 표현)

---

## 4. 요약 표

| 모델 | 생물학적 리얼함 | 계산비용 | 주요 용도 |
|------|------------------|-----------|------------|
| McCulloch-Pitts | ❌ | 🔹 매우 낮음 | 논리적 모델 |
| Perceptron / ANN | ❌ | 🔹 낮음 | 딥러닝 |
| IF | 🔸 | 🔹 낮음 | 기본 SNN 실험 |
| LIF | 🔸🔸 | 🔹 낮음 | SNN 기본 모델 |
| Izhikevich | 🔸🔸🔸 | 🔹 중간 | 생물학 + 효율 밸런스 |
| AdEx | 🔸🔸🔸 | 🔹 중간 | 실제 뇌 패턴 재현 |
| Hodgkin-Huxley | 🔸🔸🔸🔸 | 🔹 매우 높음 | 뇌 과학 시뮬레이션 |

---

## 5. 딥러닝 vs SNN 한 줄 요약

- **딥러닝 뉴런:** 숫자로 세게 때리기  
- **SNN 뉴런:** 언제 쏘냐로 말하기

시간축 정보엔 SNN이, 연속적 데이터(이미지·텍스트 등)는 ANN이 유리.

---

## 💡 보너스
원하면 LIF, Izhikevich, Hodgkin–Huxley 세 가지를 파이썬으로 구현해 비교 시뮬레이션할 수도 있다.
