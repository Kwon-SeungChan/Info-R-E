# ============================================================
# Brain.py - C. elegans 신경망 시뮬레이션 (AdEx 모델)
# ============================================================
# 
# 이 파일은 예쁜꼬마선충(C. elegans)의 302개 뉴런으로 구성된
# 커넥톰(connectome)을 시뮬레이션합니다.
#
# 모델: AdEx (Adaptive Exponential Integrate-and-Fire)
# - 신호 누적 (Integrate)
# - 시간 감쇠 (Leaky)
# - 지수적 급등 (Exponential spike)
# - 적응 전류 (Adaptation) - 연속 발화 시 피로도
# - 임계값 발화 (Fire)
#
# Axon: 축삭돌기 (neuron에서 신호를 전달하는 구조)
# ============================================================

import constants
import random
import math

class Brain:
    """
    C. elegans의 302개 뉴런 신경망을 시뮬레이션하는 클래스 (AdEx 모델)
    
    주요 기능:
    - 뉴런 간 연결(connectome) 관리
    - 신호 전달 및 누적
    - 시간에 따른 신호 감쇠 (Leaky)
    - 지수적 스파이크 상승 (Exponential)
    - 적응 전류를 통한 피로도 표현 (Adaptation)
    - 근육 신호 계산 (좌/우 근육 활성화)
    - 감각 뉴런 자극 처리
    
    속성:
        weights: 뉴런 간 연결 가중치 (constants.py에서 로드)
        PostSynaptic: 각 뉴런의 신호 강도 (double buffering)
        AdaptationCurrent: 각 뉴런의 적응 전류 (w)
        FireThreshold: 뉴런 발화 임계값 (30)
        DecayRate: 신호 감쇠율 (0.95 = 5% 감쇠)
        DeltaT: 지수적 스파이크 급등 파라미터 (2.0)
        AdaptationTimeConstant: 적응 전류 감쇠 시간 상수 (0.98)
        AdaptationIncrement: 발화 시 적응 전류 증가량 (5.0)
        AccumulatedLeftMusclesSignal: 좌측 근육 신호 누적
        AccumulatedRightMusclesSignal: 우측 근육 신호 누적
    """
    
    def __init__(self):
        """Brain 객체 초기화"""
        # 뉴런 간 연결 가중치 (constants.py에서 로드)
        self.weights = constants.weights
        
        # Double buffering: 동시 업데이트를 위해 두 개의 신호 강도 배열 사용
        self.CurrentSignalIntensityIndex = 0  # 현재 신호 강도 인덱스
        self.NextSignalIntensityIndex = 1      # 다음 신호 강도 인덱스
        
        # 뉴런 발화 임계값
        self.FireThreshold = 30
        
        # ========================================
        # AdEx 모델 파라미터 (생물학적으로 정확한 구현)
        # ========================================
        
        # === 막 특성 (Membrane Properties) ===
        self.C_m = 200.0      # 막 커패시턴스 (pF)
        self.g_L = 10.0       # 누수전도도 (nS)
        self.E_L = 0.0        # 누수 평형 전위 (정규화: 0 = 휴지전위)
        self.V_reset = 0.0    # 발화 후 리셋 전위
        self.V_T = 20.0       # 동역학적 임계값 (spike threshold)
        
        # === 지수 스파이크 항 (Exponential Spike) ===
        self.delta_T = 2.0    # 스파이크 급등 폭 파라미터 (mV)
        
        # === 적응 변수 (Adaptation) ===
        self.tau_w = 30.0     # 적응 시간 상수 (ms)
        self.a = 2.0          # 부적응 결합 파라미터 (nS)
        self.b = 5.0          # 스파이크 발동 적응 증가량 (pA)
        
        # === 시간 상수 (Time Constants) ===
        self.tau_m = self.C_m / self.g_L  # 막 시간 상수 (ms)
        self.dt = 1.0         # 시뮬레이션 타임스텝 (ms)
        
        # 발화 임계값 (실제 스파이크 감지)
        self.FireThreshold = 30.0  # 스파이크 감지 임계값
        
        # 각 뉴런의 적응 전류 (w)
        # 형식: {neuron_name: adaptation_current}
        self.AdaptationCurrent = {}
        
        # 좌우 근육 신호 누적 (이동 방향 결정에 사용)
        self.AccumulatedLeftMusclesSignal = 0
        self.AccumulatedRightMusclesSignal = 0

        # 감각 뉴런 자극 플래그
        self.IsStimulatedHungerNeurons = True      # 배고픔 뉴런 자극 여부
        self.IsStimulatedNoseTouchNeurons = True   # 코 터치 뉴런 자극 여부
        self.IsStimulatedFoodSenseNeurons = True   # 먹이 감각 뉴런 자극 여부
        
        # 각 뉴런의 신호 강도 딕셔너리 (double buffering)
        # 형식: {neuron_name: [current_signal, next_signal]}
        self.PostSynaptic = {}

        # 뉴런 연결 맵 (connectome)
        # 형식: {source_neuron: [(target_neuron, weight), ...]}
        self.Connectome = {}

        # 근육 카테고리
        self.MusclesCategory = ['MVU', 'MVL', 'MDL', 'MVR', 'MDR']
        # MVU: 배쪽 상부 근육 (Muscle Ventral Upper)
        # MVL: 배쪽 좌측 근육 (Muscle Ventral Left)
        # MDL: 등쪽 좌측 근육 (Muscle Dorsal Left)
        # MVR: 배쪽 우측 근육 (Muscle Ventral Right)
        # MDR: 등쪽 우측 근육 (Muscle Dorsal Right)
      
        # 모든 근육의 세부 목록 (07-23 번호는 벌레 몸체의 위치를 나타냄)
        self.AllMuscleList = [
            'MDL07',
            'MDL08',
            'MDL09',
            'MDL10',
            'MDL11',
            'MDL12',
            'MDL13',
            'MDL14',
            'MDL15',
            'MDL16',
            'MDL17',
            'MDL18',
            'MDL19',
            'MDL20',
            'MDL21',
            'MDL22',
            'MDL23',
            'MVL07',
            'MVL08',
            'MVL09',
            'MVL10',
            'MVL11',
            'MVL12',
            'MVL13',
            'MVL14',
            'MVL15',
            'MVL16',
            'MVL17',
            'MVL18',
            'MVL19',
            'MVL20',
            'MVL21',
            'MVL22',
            'MVL23',
            'MDR07',
            'MDR08',
            'MDR09',
            'MDR10',
            'MDR11',
            'MDR12',
            'MDR13',
            'MDR14',
            'MDR15',
            'MDR16',
            'MDR17',
            'MDR18',
            'MDR19',
            'MDR20',
            'MDL21',
            'MDR22',
            'MDR23',
            'MVR07',
            'MVR08',
            'MVR09',
            'MVR10',
            'MVR11',
            'MVR12',
            'MVR13',
            'MVR14',
            'MVR15',
            'MVR16',
            'MVR17',
            'MVR18',
            'MVR19',
            'MVR20',
            'MVL21',
            'MVR22',
            'MVR23',
        ]
        
        # ========================================
        # 왼쪽 근육 목록 (좌측 회전 담당)
        # ========================================
        self.AllLeftMuscles = [
            'MDR07',
            'MDR08',
            'MDR09',
            'MDR10',
            'MDR11',
            'MDR12',
            'MDR13',
            'MDR14',
            'MDR15',
            'MDR16',
            'MDR17',
            'MDR18',
            'MDR19',
            'MDR20',
            'MDR21',
            'MDR22',
            'MDR23',
            'MVL07',
            'MVL08',
            'MVL09',
            'MVL10',
            'MVL11',
            'MVL12',
            'MVL13',
            'MVL14',
            'MVL15',
            'MVL16',
            'MVL17',
            'MVL18',
            'MVL19',
            'MVL20',
            'MVL21',
            'MVL22',
            'MVL23',
        ]
        # 오른쪽 근육들의 전체 목록
        self.AllRightMuscles = [
            'MDL07',
            'MDL08',
            'MDL09',
            'MDL10',
            'MDL11',
            'MDL12',
            'MDL13',
            'MDL14',
            'MDL15',
            'MDL16',
            'MDL17',
            'MDL18',
            'MDL19',
            'MDL20',
            'MDL21', # WTF?? Why left muscle in right muscle list??
            'MDL22',
            'MDL23',
            'MVR07',
            'MVR08',
            'MVR09',
            'MVR10',
            'MVR11',
            'MVR12',
            'MVR13',
            'MVR14',
            'MVR15',
            'MVR16',
            'MVR17',
            'MVR18',
            'MVR19',
            'MVR20',
            'MVR21', # WTF?? Why left muscle in right muscle list??
            'MVR22',
            'MVR23',
        ]
        # 왼쪽 등쪽 근육 (Muscle Dorsal Left)
        self.AllLeftDorsalMuscles = [
            'MDR07',
            'MDR08',
            'MDR09',
            'MDR10',
            'MDR11',
            'MDR12',
            'MDR13',
            'MDR14',
            'MDR15',
            'MDR16',
            'MDR17',
            'MDR18',
            'MDR19',
            'MDR20',
            'MDR21',
            'MDR22',
            'MDR23',
        ]
        # 왼쪽 배쪽 근육 (Muscle Ventral Left)
        self.AllLeftVentralMuscles = [
            'MVL07',
            'MVL08',
            'MVL09',
            'MVL10',
            'MVL11',
            'MVL12',
            'MVL13',
            'MVL14',
            'MVL15',
            'MVL16',
            'MVL17',
            'MVL18',
            'MVL19',
            'MVL20',
            'MVL21',
            'MVL22',
            'MVL23',
        ]
        # 오른쪽 등쪽 근육 (Muscle Dorsal Right)
        self.AllRightDorsalMuscles = [
            'MDL07',
            'MDL08',
            'MDL09',
            'MDL10',
            'MDL11',
            'MDL12',
            'MDL13',
            'MDL14',
            'MDL15',
            'MDL16',
            'MDL17',
            'MDL18',
            'MDL19',
            'MDL20',
            'MDL21', # WTF?? Why left muscle in right muscle list??
            'MDL22',
            'MDL23',
        ]
        # 오른쪽 배쪽 근육 (Muscle Ventral Right)
        self.AllRightVentralMuscles = [
            'MVR07',
            'MVR08',
            'MVR09',
            'MVR10',
            'MVR11',
            'MVR12',
            'MVR13',
            'MVR14',
            'MVR15',
            'MVR16',
            'MVR17',
            'MVR18',
            'MVR19',
            'MVR20',
            'MVR21', # 주의: MVL21이어야 하는데 MVR21로 잘못 표기됨 (버그)
            'MVR22',
            'MVR23',
        ]

    # ========================================
    # 신경망 시뮬레이션 메서드
    # ========================================
    
    def signal_indensity_accumulate(self, PreSynapticName : str):
        """
        시냅스 전 뉴런(PreSynaptic)에서 연결된 모든 시냅스 후 뉴런(PostSynaptic)으로
        신호를 전달하고 누적합니다.
        
        작동 방식:
        1. PreSynapticName이 weights에 있는지 확인
        2. 연결된 모든 PostSynaptic 뉴런에 가중치만큼 신호 누적
        3. NextSignalIntensityIndex를 사용하여 다음 프레임에 적용
        
        Args:
            PreSynapticName: 신호를 발생시키는 뉴런 이름
        """
        # KeyError 방지: PreSynapticName이 weights에 없으면 무시
        if PreSynapticName not in self.weights:
            return
        
        # 연결된 모든 PostSynaptic 뉴런에 신호 전달
        for SynapticsConnectedToPreSynaptic in self.weights[PreSynapticName]:
            self.PostSynaptic[SynapticsConnectedToPreSynaptic][self.NextSignalIntensityIndex] += \
                self.weights[PreSynapticName][SynapticsConnectedToPreSynaptic]

    def RandExcite(self):
        """
        무작위로 뉴런을 자극하여 신경망 초기 활성화를 유도합니다.
        
        40개의 무작위 뉴런을 선택하여 신호를 전달함으로써
        신경망이 정적 상태에서 벗어나 활동하도록 만듭니다.
        """
        for _ in range(40):
            neurons = list(self.Connectome.keys())
            random_neuron = random.choice(neurons)
            self.signal_indensity_accumulate(random_neuron)

    def setup(self):
        """
        뇌 신경망을 초기화합니다.
        
        302개의 모든 뉴런과 근육을 PostSynaptic 딕셔너리에 등록하고,
        각각 [current_signal, next_signal] 형태의 double buffering 배열을 생성합니다.
        또한 weights에서 Connectome 연결 맵을 구축합니다.
        """
        # JavaScript의 방식대로 명시적으로 모든 뉴런을 초기화
        # 이는 정확한 뉴런 목록을 보장합니다
        neuron_names = ['ADAL', 'ADAR', 'ADEL', 'ADER', 'ADFL', 'ADFR', 'ADLL', 'ADLR', 
                       'AFDL', 'AFDR', 'AIAL', 'AIAR', 'AIBL', 'AIBR', 'AIML', 'AIMR', 
                       'AINL', 'AINR', 'AIYL', 'AIYR', 'AIZL', 'AIZR', 'ALA', 'ALML', 
                       'ALMR', 'ALNL', 'ALNR', 'AQR', 'AS1', 'AS10', 'AS11', 'AS2', 
                       'AS3', 'AS4', 'AS5', 'AS6', 'AS7', 'AS8', 'AS9', 'ASEL', 'ASER', 
                       'ASGL', 'ASGR', 'ASHL', 'ASHR', 'ASIL', 'ASIR', 'ASJL', 'ASJR', 
                       'ASKL', 'ASKR', 'AUAL', 'AUAR', 'AVAL', 'AVAR', 'AVBL', 'AVBR', 
                       'AVDL', 'AVDR', 'AVEL', 'AVER', 'AVFL', 'AVFR', 'AVG', 'AVHL', 
                       'AVHR', 'AVJL', 'AVJR', 'AVKL', 'AVKR', 'AVL', 'AVM', 'AWAL', 
                       'AWAR', 'AWBL', 'AWBR', 'AWCL', 'AWCR', 'BAGL', 'BAGR', 'BDUL', 
                       'BDUR', 'CEPDL', 'CEPDR', 'CEPVL', 'CEPVR', 'DA1', 'DA2', 'DA3', 
                       'DA4', 'DA5', 'DA6', 'DA7', 'DA8', 'DA9', 'DB1', 'DB2', 'DB3', 
                       'DB4', 'DB5', 'DB6', 'DB7', 'DD1', 'DD2', 'DD3', 'DD4', 'DD5', 
                       'DD6', 'DVA', 'DVB', 'DVC', 'FLPL', 'FLPR', 'HSNL', 'HSNR', 'I1L', 
                       'I1R', 'I2L', 'I2R', 'I3', 'I4', 'I5', 'I6', 'IL1DL', 'IL1DR', 
                       'IL1L', 'IL1R', 'IL1VL', 'IL1VR', 'IL2L', 'IL2R', 'IL2DL', 'IL2DR', 
                       'IL2VL', 'IL2VR', 'LUAL', 'LUAR', 'M1', 'M2L', 'M2R', 'M3L', 'M3R', 
                       'M4', 'M5', 'MANAL', 'MCL', 'MCR', 'MDL01', 'MDL02', 'MDL03', 
                       'MDL04', 'MDL05', 'MDL06', 'MDL07', 'MDL08', 'MDL09', 'MDL10', 
                       'MDL11', 'MDL12', 'MDL13', 'MDL14', 'MDL15', 'MDL16', 'MDL17', 
                       'MDL18', 'MDL19', 'MDL20', 'MDL21', 'MDL22', 'MDL23', 'MDL24', 
                       'MDR01', 'MDR02', 'MDR03', 'MDR04', 'MDR05', 'MDR06', 'MDR07', 
                       'MDR08', 'MDR09', 'MDR10', 'MDR11', 'MDR12', 'MDR13', 'MDR14', 
                       'MDR15', 'MDR16', 'MDR17', 'MDR18', 'MDR19', 'MDR20', 'MDR21', 
                       'MDR22', 'MDR23', 'MDR24', 'MI', 'MVL01', 'MVL02', 'MVL03', 'MVL04', 
                       'MVL05', 'MVL06', 'MVL07', 'MVL08', 'MVL09', 'MVL10', 'MVL11', 
                       'MVL12', 'MVL13', 'MVL14', 'MVL15', 'MVL16', 'MVL17', 'MVL18', 
                       'MVL19', 'MVL20', 'MVL21', 'MVL22', 'MVL23', 'MVR01', 'MVR02', 
                       'MVR03', 'MVR04', 'MVR05', 'MVR06', 'MVR07', 'MVR08', 'MVR09', 
                       'MVR10', 'MVR11', 'MVR12', 'MVR13', 'MVR14', 'MVR15', 'MVR16', 
                       'MVR17', 'MVR18', 'MVR19', 'MVR20', 'MVR21', 'MVR22', 'MVR23', 
                       'MVR24', 'MVULVA', 'NSML', 'NSMR', 'OLLL', 'OLLR', 'OLQDL', 'OLQDR', 
                       'OLQVL', 'OLQVR', 'PDA', 'PDB', 'PDEL', 'PDER', 'PHAL', 'PHAR', 
                       'PHBL', 'PHBR', 'PHCL', 'PHCR', 'PLML', 'PLMR', 'PLNL', 'PLNR', 
                       'PQR', 'PVCL', 'PVCR', 'PVDL', 'PVDR', 'PVM', 'PVNL', 'PVNR', 
                       'PVPL', 'PVPR', 'PVQL', 'PVQR', 'PVR', 'PVT', 'PVWL', 'PVWR', 
                       'RIAL', 'RIAR', 'RIBL', 'RIBR', 'RICL', 'RICR', 'RID', 'RIFL', 
                       'RIFR', 'RIGL', 'RIGR', 'RIH', 'RIML', 'RIMR', 'RIPL', 'RIPR', 
                       'RIR', 'RIS', 'RIVL', 'RIVR', 'RMDDL', 'RMDDR', 'RMDL', 'RMDR', 
                       'RMDVL', 'RMDVR', 'RMED', 'RMEL', 'RMER', 'RMEV', 'RMFL', 'RMFR', 
                       'RMGL', 'RMGR', 'RMHL', 'RMHR', 'SAADL', 'SAADR', 'SAAVL', 'SAAVR', 
                       'SABD', 'SABVL', 'SABVR', 'SDQL', 'SDQR', 'SIADL', 'SIADR', 'SIAVL', 
                       'SIAVR', 'SIBDL', 'SIBDR', 'SIBVL', 'SIBVR', 'SMBDL', 'SMBDR', 
                       'SMBVL', 'SMBVR', 'SMDDL', 'SMDDR', 'SMDVL', 'SMDVR', 'URADL', 
                       'URADR', 'URAVL', 'URAVR', 'URBL', 'URBR', 'URXL', 'URXR', 'URYDL', 
                       'URYDR', 'URYVL', 'URYVR', 'VA1', 'VA10', 'VA11', 'VA12', 'VA2', 
                       'VA3', 'VA4', 'VA5', 'VA6', 'VA7', 'VA8', 'VA9', 'VB1', 'VB10', 
                       'VB11', 'VB2', 'VB3', 'VB4', 'VB5', 'VB6', 'VB7', 'VB8', 'VB9', 
                       'VC1', 'VC2', 'VC3', 'VC4', 'VC5', 'VC6', 'VD1', 'VD10', 'VD11', 
                       'VD12', 'VD13', 'VD2', 'VD3', 'VD4', 'VD5', 'VD6', 'VD7', 'VD8', 'VD9']
        
        # 모든 뉴런을 PostSynaptic에 등록 (double buffering: [current, next])
        for neuron in neuron_names:
            self.PostSynaptic[neuron] = [0, 0]
            # AdEx 모델을 위한 적응 전류 초기화
            self.AdaptationCurrent[neuron] = 0
        
        # Connectome을 weights의 키로 채움 (연결된 뉴런 목록)
        for PreSynaptic in self.weights:
            self.Connectome[PreSynaptic] = True

    def update(self):
        """
        뇌의 신경망을 한 프레임 업데이트합니다.
        
        감각 뉴런 자극 처리:
        1. IsStimulatedHungerNeurons: 배고픔 감각 (RIM, RIC 뉴런)
        2. IsStimulatedNoseTouchNeurons: 코 터치 감각 (FLP, ASH, IL1V, OLQ 뉴런)
        3. IsStimulatedFoodSenseNeurons: 먹이 감각 (ADF, ASG, ASI 뉴런)
        
        각 자극에 따라 해당 감각 뉴런을 활성화하고 run_connectome()을 호출하여
        전체 신경망에 신호를 전파합니다.
        """
        
        # 배고픔 뉴런 자극
        if (self.IsStimulatedHungerNeurons):
            self.signal_indensity_accumulate('RIML')  # 링 인터뉴런 (좌)
            self.signal_indensity_accumulate('RIMR')  # 링 인터뉴런 (우)
            self.signal_indensity_accumulate('RICL')  # 링 인터뉴런 (좌)
            self.signal_indensity_accumulate('RICR')  # 링 인터뉴런 (우)
            self.run_connectome()
            
        # 코 터치(벽 충돌) 뉴런 자극
        if (self.IsStimulatedNoseTouchNeurons):
            self.signal_indensity_accumulate('FLPR')  # 앞쪽 감각 (우)
            self.signal_indensity_accumulate('FLPL')  # 앞쪽 감각 (좌)
            self.signal_indensity_accumulate('ASHL')  # 머리 부분 감각 (좌)
            self.signal_indensity_accumulate('ASHR')  # 머리 부분 감각 (우)
            self.signal_indensity_accumulate('IL1VL') # 입 주변 감각 (좌)
            self.signal_indensity_accumulate('IL1VR') # 입 주변 감각 (우)
            self.signal_indensity_accumulate('OLQDL') # 외축 감각 (좌등)
            self.signal_indensity_accumulate('OLQDR') # 외축 감각 (우등)
            self.signal_indensity_accumulate('OLQVR') # 외축 감각 (우복)
            self.signal_indensity_accumulate('OLQVL') # 외축 감각 (좌복)
            self.run_connectome()        
        
        # 먹이 감각 뉴런 자극
        if (self.IsStimulatedFoodSenseNeurons):
            self.signal_indensity_accumulate('ADFL')  # 냄새 감지 (좌)
            self.signal_indensity_accumulate('ADFR')  # 냄새 감지 (우)
            self.signal_indensity_accumulate('ASGR')  # 페로몬 감지 (우)
            self.signal_indensity_accumulate('ASGL')  # 페로몬 감지 (좌)
            self.signal_indensity_accumulate('ASIL') # 화학물질 감지
            self.signal_indensity_accumulate('ASIR')
            self.signal_indensity_accumulate('ASJR')
            self.signal_indensity_accumulate('ASJL')
            self.run_connectome()            

  # RIML RIMR RICL RICR hunger neurons
  # PVDL PVDR nociceptors
  # ASEL ASER gustatory neurons

    def run_connectome(self):
        """
        Connectome을 실행하여 신경망 신호를 전파합니다 (AdEx 모델 - 수학적 구현)
        
        AdEx (Adaptive Exponential Integrate-and-Fire) 모델 방정식:
        
        막전위 방정식:
        C_m * dV/dt = -g_L(V - E_L) + g_L*delta_T*exp((V - V_T)/delta_T) - w + I
        
        적응 전류 방정식:
        tau_w * dw/dt = a(V - E_L) - w
        
        스파이크 조건:
        if V > FireThreshold:
            V ← V_reset
            w ← w + b
        
        프로세스:
        1. 막전위 업데이트 (Leak current + Exponential term + Input current - Adaptation)
        2. 적응 전류 업데이트 (Subthreshold adaptation + Decay)
        3. 임계값 검사 및 발화 (Fire)
        4. 근육 신호 누적
        5. 버퍼 스왑 (double buffering)
        """
        
        # =============================================
        # 1단계: 막전위 업데이트 (Euler method)
        # =============================================
        # dV/dt = (-g_L(V - E_L) + g_L*delta_T*exp((V-V_T)/delta_T) - w + I) / C_m
        for PostSynaptic in self.PostSynaptic:
            V = self.PostSynaptic[PostSynaptic][self.CurrentSignalIntensityIndex]
            w = self.AdaptationCurrent[PostSynaptic]
            
            # Leak current: -g_L * (V - E_L)
            leak_current = -self.g_L * (V - self.E_L)
            
            # Exponential term: g_L * delta_T * exp((V - V_T) / delta_T)
            # 오버플로 방지: V가 V_T보다 훨씬 크면 지수 항을 제한
            exponential_term = 0.0
            if V > self.V_T and V < self.FireThreshold:
                exponent = (V - self.V_T) / self.delta_T
                # 오버플로 방지: exponent가 10 이상이면 제한
                if exponent < 10.0:
                    exponential_term = self.g_L * self.delta_T * math.exp(exponent)
                else:
                    exponential_term = self.g_L * self.delta_T * math.exp(10.0)
            
            # 시냅스 입력 전류 (I): 다음 프레임에서 받을 신호
            I = self.PostSynaptic[PostSynaptic][self.NextSignalIntensityIndex]
            
            # Euler integration: V_new = V + (dV/dt) * dt
            dV_dt = (leak_current + exponential_term - w + I) / self.C_m
            self.PostSynaptic[PostSynaptic][self.CurrentSignalIntensityIndex] += dV_dt * self.dt
        
        # =============================================
        # 2단계: 적응 전류 업데이트 (Euler method)
        # =============================================
        # dw/dt = (a(V - E_L) - w) / tau_w
        for PostSynaptic in self.PostSynaptic:
            V = self.PostSynaptic[PostSynaptic][self.CurrentSignalIntensityIndex]
            w = self.AdaptationCurrent[PostSynaptic]
            
            # Euler integration: w_new = w + (dw/dt) * dt
            dw_dt = (self.a * (V - self.E_L) - w) / self.tau_w
            self.AdaptationCurrent[PostSynaptic] += dw_dt * self.dt
        
        # =============================================
        # 3단계: 임계값 검사 및 발화 (Fire)
        # =============================================
        for PostSynaptic in self.PostSynaptic:
            # 근육은 발화할 수 없음 (근육은 신호를 받기만 함)
            is_muscle = False
            for muscle_prefix in self.MusclesCategory:
                if PostSynaptic.startswith(muscle_prefix):
                    is_muscle = True
                    break
            
            # 임계값을 넘은 뉴런만 발화
            if not is_muscle and self.PostSynaptic[PostSynaptic][self.CurrentSignalIntensityIndex] > self.FireThreshold:
                self.fire_neuron(PostSynaptic)
                # AdEx: 발화 시 전압 리셋 및 적응 전류 증가
                self.PostSynaptic[PostSynaptic][self.CurrentSignalIntensityIndex] = self.V_reset
                self.AdaptationCurrent[PostSynaptic] += self.b
        
        # =============================================
        # 4단계: 근육 신호 누적 및 초기화
        # =============================================
        self.accumulate_signal()
        
        # =============================================
        # 5단계: Double buffering (버퍼 스왑)
        # =============================================
        # 다음 프레임을 위해 버퍼를 교체
        for PostSynaptic in self.PostSynaptic:
            self.PostSynaptic[PostSynaptic][self.CurrentSignalIntensityIndex] = self.PostSynaptic[PostSynaptic][self.NextSignalIntensityIndex]
        
        self.CurrentSignalIntensityIndex, self.NextSignalIntensityIndex = swap(self.CurrentSignalIntensityIndex, self.NextSignalIntensityIndex)

    def fire_neuron(self, NeuronToFire):
        """
        뉴런 발화 처리 (AdEx 모델)
        
        발화 시:
        1. 연결된 다른 뉴런들에게 신호 전달
        2. 자신의 신호 강도를 다음 프레임에서 0으로 초기화
        
        Note: 전압 리셋(V ← V_reset)과 적응 전류 증가(w ← w + b)는 run_connectome()에서 처리됨
        """
        # KeyError 방지: NeuronToFire가 weights에 없으면 무시
        if NeuronToFire != 'MVULVA' and NeuronToFire in self.weights:
            self.signal_indensity_accumulate(NeuronToFire)
            self.PostSynaptic[NeuronToFire][self.NextSignalIntensityIndex] = 0

    def accumulate_signal(self):     #왼쪽/오른쪽 근육에 전달된 누적값 함산후 AccumulatedLeftMusclesSignal/AccumulatedRightMusclesSignal에 저장 
        self.AccumulatedLeftMusclesSignal = 0      #저장 후에 각 근육 누적값을 0으로 초기화
        self.AccumulatedRightMusclesSignal = 0

        m = 0
        while m < len(self.AllMuscleList):
            MuscleName = self.AllMuscleList[m]

            if (MuscleName in self.AllLeftMuscles):
                self.AccumulatedLeftMusclesSignal += self.PostSynaptic[MuscleName][self.NextSignalIntensityIndex]
                self.PostSynaptic[MuscleName][self.NextSignalIntensityIndex] = 0
            elif (MuscleName in self.AllRightMuscles):
                self.AccumulatedRightMusclesSignal += self.PostSynaptic[MuscleName][self.NextSignalIntensityIndex]
                self.PostSynaptic[MuscleName][self.NextSignalIntensityIndex] = 0
              
            m += 1

def swap(a, b):
    return b, a