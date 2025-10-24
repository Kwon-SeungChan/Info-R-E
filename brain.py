# Axon : 축삭돌기

import constants
import random

class Brain:
    
    def __init__(self):
        self.weights = constants.weights
        self.CurrentSignalIntensityIndex = 0
        self.NextSignalIntensityIndex = 1
        self.FireThreshold = 30
        self.AccumulatedLeftMusclesSignal = 0
        self.AccumulatedRightMusclesSignal = 0

        self.IsStimulatedHungerNeurons = True
        self.IsStimulatedNoseTouchNeurons = True
        self.IsStimulatedFoodSenseNeurons = True
        
        self.PostSynaptic = {}

        self.Connectome = {}

        self.MusclesCategory = ['MVU', 'MVL', 'MDL', 'MVR', 'MDR']
      # MVU: 배쪽 상부 근육 (Muscle Ventral Upper)
      # MVL: 배쪽 좌측 근육 (Muscle Ventral Left)
      # MDL: 등쪽 좌측 근육 (Muscle Dorsal Left)
      # MVR: 배쪽 우측 근육 (Muscle Ventral Right)
      # MDR: 등쪽 우측 근육 (Muscle Dorsal Right)
      
        self.AllMuscleList = [  # 모든 근육의 세부적인 목록  # 숫자는 근육의 위치를 나타냄 (07-23)
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
# 왼쪽 근육들의 전체 목록
        self.AllLeftMuscles = [
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
        ]
        # 오른쪽 근육들의 전체 목록
        self.AllRightMuscles = [
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
            'MDL21', # WTF?? Why left muscle in right muscle list??
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
            'MVL21', # WTF?? Why left muscle in right muscle list??
            'MVR22',
            'MVR23',
        ]
        # 왼쪽 등쪽 근육 (Muscle Dorsal Left)
        self.AllLeftDorsalMuscles = [
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
            'MDL21', # WTF?? Why left muscle in right muscle list??
            'MDR22',
            'MDR23',
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
            'MVL21', # WTF?? Why left muscle in right muscle list??
            'MVR22',
            'MVR23',
        ]

# 시냅스 전 뉴런에 연결된 시냅스 후 뉴런의 신호 강도를 누적하는 함수
    def signal_indensity_accumulate(self, PreSynapticName : str):
        # KeyError 방지: PreSynapticName이 weights에 없으면 무시
        if PreSynapticName not in self.weights:
            return
        for SynapticsConnectedToPreSynaptic in self.weights[PreSynapticName]:
            self.PostSynaptic[SynapticsConnectedToPreSynaptic][self.NextSignalIntensityIndex] += self.weights[PreSynapticName][SynapticsConnectedToPreSynaptic]

    def RandExcite(self):   #뉴런에 무작위로 자극을 주는 역할의 함수
        for _ in range(40):
            neurons = list(self.Connectome.keys())
            random_neuron = random.choice(neurons)
            self.signal_indensity_accumulate(random_neuron)

    def setup(self):
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
        
        for neuron in neuron_names:
            self.PostSynaptic[neuron] = [0, 0]
        
        # Connectome을 weights의 키로 채움
        for PreSynaptic in self.weights:
            self.Connectome[PreSynaptic] = True

    def update (self):
        
        if (self.IsStimulatedHungerNeurons):
            self.signal_indensity_accumulate('RIML')
            self.signal_indensity_accumulate('RIMR')
            self.signal_indensity_accumulate('RICL')
            self.signal_indensity_accumulate('RICR')
            self.run_connectome()
            
        if (self.IsStimulatedNoseTouchNeurons):
            self.signal_indensity_accumulate('FLPR') # 앞쪽 감각
            self.signal_indensity_accumulate('FLPL')
            self.signal_indensity_accumulate('ASHL') # 머리 부분 감각
            self.signal_indensity_accumulate('ASHR')
            self.signal_indensity_accumulate('IL1VL') # 입 주변 감각
            self.signal_indensity_accumulate('IL1VR')
            self.signal_indensity_accumulate('OLQDL') # 외축 감각
            self.signal_indensity_accumulate('OLQDR')
            self.signal_indensity_accumulate('OLQVR')
            self.signal_indensity_accumulate('OLQVL')
            self.run_connectome()        
        
        if (self.IsStimulatedFoodSenseNeurons):
            self.signal_indensity_accumulate('ADFL') # 냄새 감지
            self.signal_indensity_accumulate('ADFR')
            self.signal_indensity_accumulate('ASGR') # 페로몬 감지
            self.signal_indensity_accumulate('ASGL')
            self.signal_indensity_accumulate('ASIL') # 화학물질 감지
            self.signal_indensity_accumulate('ASIR')
            self.signal_indensity_accumulate('ASJR')
            self.signal_indensity_accumulate('ASJL')
            self.run_connectome()            

  # RIML RIMR RICL RICR hunger neurons
  # PVDL PVDR nociceptors
  # ASEL ASER gustatory neurons

    def run_connectome(self): #시냅스 후에 뉴런들 검사해서 임계값 넘은 뉴런이면 발화시킴
        for PostSynaptic in self.PostSynaptic:
            # 근육은 발화할 수 없음 - JavaScript의 muscles 체크 로직 추가
            is_muscle = False
            for muscle_prefix in self.MusclesCategory:
                if PostSynaptic.startswith(muscle_prefix):
                    is_muscle = True
                    break
            
            if not is_muscle and self.PostSynaptic[PostSynaptic][self.CurrentSignalIntensityIndex] > self.FireThreshold:
                self.fire_neuron(PostSynaptic)
        
        self.accumulate_signal()
        
        # 시냅스 후 뉴런의 신호 강도를 다음 신호 강도로 이동
        for PostSynaptic in self.PostSynaptic:
            self.PostSynaptic[PostSynaptic][self.CurrentSignalIntensityIndex] = self.PostSynaptic[PostSynaptic][self.NextSignalIntensityIndex]
        
        self.CurrentSignalIntensityIndex, self.NextSignalIntensityIndex = swap(self.CurrentSignalIntensityIndex, self.NextSignalIntensityIndex)

    def fire_neuron(self, NeuronToFire):  # 뉴런이 발화하면 다른 신호 퍼뜨리고, 그 뉴런의 누적값 초기화화
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