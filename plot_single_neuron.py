"""
개별 뉴런 전압 그래프 프로그램

사용자가 뉴런 이름을 입력하면 해당 뉴런의 시간에 따른 전압 변화를
그래프로 표시합니다.

사용법:
    python plot_single_neuron.py
    뉴런 이름 입력: AVAL
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# ============================================================
# Matplotlib 한글 폰트 설정
# ============================================================
plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows 기본 한글 폰트
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# ============================================================
# 설정
# ============================================================

# CSV 파일 경로
CSV_FILE = "neuron_voltages.csv"

# 신호 강도 임계값 (시뮬레이터와 동일)
THRESHOLD_WEAK = 1.0      # 회색 -> 파란색
THRESHOLD_MEDIUM = 10.0   # 파란색 -> 초록색  
THRESHOLD_STRONG = 30.0   # 초록색 -> 빨간색 (발화)

# ============================================================
# 데이터 로드
# ============================================================

def load_neuron_data(csv_file):
    """
    CSV 파일에서 뉴런 전압 데이터 로드
    
    Returns:
        df: pandas DataFrame (행: 타임스텝, 열: 뉴런)
        time_steps: 시간 배열 (밀리초)
    """
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_file}")
    
    # 데이터 로드
    df = pd.read_csv(csv_file)
    
    # Time_ms 열 추출 (대문자 T)
    time_steps = df['Time_ms'].values
    df = df.drop(columns=['Frame', 'Time_ms'])
    
    return df, time_steps

# ============================================================
# 뉴런 선택 및 검증
# ============================================================

def get_neuron_name(available_neurons):
    """
    사용자로부터 뉴런 이름 입력받기
    
    Args:
        available_neurons: 사용 가능한 뉴런 이름 리스트
    
    Returns:
        str: 선택된 뉴런 이름
    """
    print("\n" + "="*60)
    print("개별 뉴런 전압 그래프")
    print("="*60)
    print(f"\n사용 가능한 뉴런: {len(available_neurons)}개")
    print(f"예시: {', '.join(available_neurons[:10])}, ...")
    print("\n뉴런 목록을 보려면 'list'를 입력하세요.")
    print("프로그램을 종료하려면 'quit' 또는 'exit'를 입력하세요.")
    
    while True:
        neuron_name = input("\n뉴런 이름 입력: ").strip().upper()
        
        # 종료 명령
        if neuron_name in ['QUIT', 'EXIT', 'Q']:
            print("프로그램을 종료합니다.")
            sys.exit(0)
        
        # 리스트 출력
        if neuron_name == 'LIST':
            print(f"\n사용 가능한 뉴런 ({len(available_neurons)}개):")
            # 10개씩 묶어서 출력
            for i in range(0, len(available_neurons), 10):
                chunk = available_neurons[i:i+10]
                print("  " + ", ".join(f"{n:6s}" for n in chunk))
            continue
        
        # 뉴런 이름 검증
        if neuron_name in available_neurons:
            return neuron_name
        else:
            print(f"❌ 오류: '{neuron_name}'는(은) 유효한 뉴런 이름이 아닙니다.")
            
            # 유사한 이름 찾기
            similar = [n for n in available_neurons if neuron_name in n or n in neuron_name]
            if similar:
                print(f"   비슷한 이름: {', '.join(similar[:5])}")

# ============================================================
# 그래프 그리기
# ============================================================

def plot_neuron_voltage(neuron_name, voltages, time_steps):
    """
    개별 뉴런의 전압 그래프를 그립니다.
    
    Args:
        neuron_name: 뉴런 이름
        voltages: 전압 배열
        time_steps: 시간 배열 (밀리초)
    """
    # 시간을 초 단위로 변환
    time_seconds = time_steps / 1000.0
    
    # Figure 생성
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={'height_ratios': [3, 1]})
    
    # ========================================
    # 상단: 전압 그래프
    # ========================================
    
    # 배경 색상 영역 표시 (신호 강도 구간)
    ax1.axhspan(0, THRESHOLD_WEAK, alpha=0.1, color='gray', label='신호 없음 (0)')
    ax1.axhspan(THRESHOLD_WEAK, THRESHOLD_MEDIUM, alpha=0.1, color='blue', label='약한 신호 (1-10)')
    ax1.axhspan(THRESHOLD_MEDIUM, THRESHOLD_STRONG, alpha=0.1, color='green', label='중간 신호 (10-30)')
    ax1.axhspan(THRESHOLD_STRONG, max(voltages.max(), THRESHOLD_STRONG), alpha=0.1, color='red', label='발화 (30+)')
    
    # 전압 라인 그래프
    ax1.plot(time_seconds, voltages, 'black', linewidth=2, label='전압', zorder=10)
    
    # 임계값 선 표시
    ax1.axhline(y=THRESHOLD_WEAK, color='blue', linestyle='--', linewidth=1, alpha=0.5)
    ax1.axhline(y=THRESHOLD_MEDIUM, color='green', linestyle='--', linewidth=1, alpha=0.5)
    ax1.axhline(y=THRESHOLD_STRONG, color='red', linestyle='--', linewidth=1, alpha=0.7, label='발화 임계값')
    
    # 축 레이블 및 제목
    ax1.set_xlabel('시간 (초)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('전압 (신호 강도)', fontsize=12, fontweight='bold')
    ax1.set_title(f'뉴런 {neuron_name} - 시간에 따른 전압 변화', fontsize=14, fontweight='bold', pad=15)
    ax1.grid(True, alpha=0.3, linestyle=':', linewidth=0.8)
    ax1.legend(loc='upper right', fontsize=9, framealpha=0.9)
    
    # Y축 범위 설정 (0부터 시작)
    y_max = max(voltages.max() * 1.1, THRESHOLD_STRONG * 1.2)
    ax1.set_ylim(0, y_max)
    
    # ========================================
    # 하단: 발화 이벤트 타임라인
    # ========================================
    
    # 발화 이벤트 표시 (임계값 이상)
    firing_events = voltages >= THRESHOLD_STRONG
    
    # 연속된 발화를 하나의 이벤트로 묶기
    firing_event_count = 0
    firing_start_times = []
    in_firing = False
    
    for i, is_firing in enumerate(firing_events):
        if is_firing and not in_firing:
            # 발화 시작
            firing_event_count += 1
            firing_start_times.append(time_seconds[i])
            in_firing = True
        elif not is_firing and in_firing:
            # 발화 종료
            in_firing = False
    
    # 타임라인에 발화 이벤트 표시
    if firing_event_count > 0:
        ax2.scatter(firing_start_times, np.ones(len(firing_start_times)), 
                   c='red', s=100, marker='|', linewidth=3, alpha=0.9)
        ax2.set_ylim(0.5, 1.5)
    else:
        ax2.text(0.5, 0.5, '발화 이벤트 없음', 
                ha='center', va='center', transform=ax2.transAxes,
                fontsize=12, color='gray')
        ax2.set_ylim(0, 1)
    
    ax2.set_xlabel('시간 (초)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('발화', fontsize=10)
    ax2.set_title('발화 이벤트 타임라인', fontsize=11, fontweight='bold', pad=10)
    ax2.grid(True, alpha=0.3, axis='x', linestyle=':', linewidth=0.8)
    ax2.set_yticks([])
    ax2.set_xlim(time_seconds.min(), time_seconds.max())
    
    # ========================================
    # 통계 정보 텍스트
    # ========================================
    
    # 발화 지속 시간 계산 (임계값 이상인 타임스텝 개수)
    total_firing_points = firing_events.sum()
    firing_duration_percent = (total_firing_points / len(voltages)) * 100
    
    stats_text = f"""통계:
평균: {voltages.mean():.2f}
최대: {voltages.max():.2f}
최소: {voltages.min():.2f}
표준편차: {voltages.std():.2f}
발화 횟수: {firing_event_count}회
발화 지속: {firing_duration_percent:.1f}% ({total_firing_points}개 타임스텝)"""
    
    ax1.text(0.02, 0.98, stats_text, 
            transform=ax1.transAxes,
            fontsize=9, 
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='black'))
    
    # 레이아웃 조정
    plt.tight_layout()
    
    return fig

# ============================================================
# 메인 함수
# ============================================================

def main():
    """
    메인 실행 함수
    """
    try:
        # 데이터 로드
        print("데이터를 로드하는 중...")
        df, time_steps = load_neuron_data(CSV_FILE)
        available_neurons = sorted(df.columns.tolist())
        print(f"✓ {len(available_neurons)}개의 뉴런 데이터 로드 완료")
        print(f"✓ {len(time_steps)}개의 타임스텝 ({time_steps[0]:.1f}ms ~ {time_steps[-1]:.1f}ms)")
        
    except FileNotFoundError as e:
        print(f"\n❌ 오류: {e}")
        print("먼저 시뮬레이션을 실행하여 neuron_voltages.csv 파일을 생성하세요.")
        return
    
    # 반복해서 뉴런 선택 및 그래프 표시
    while True:
        # 뉴런 선택
        neuron_name = get_neuron_name(available_neurons)
        
        # 전압 데이터 추출
        voltages = df[neuron_name].values
        
        # 그래프 생성
        print(f"\n'{neuron_name}' 뉴런의 그래프를 생성 중...")
        fig = plot_neuron_voltage(neuron_name, voltages, time_steps)
        
        # 이미지 저장
        output_file = f"neuron_{neuron_name}_voltage.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ 그래프가 '{output_file}'에 저장되었습니다.")
        
        # 화면에 표시
        print("✓ 그래프를 표시합니다. 창을 닫으면 다시 뉴런을 선택할 수 있습니다.")
        plt.show()
        
        # 계속 여부 확인
        continue_choice = input("\n다른 뉴런을 보시겠습니까? (y/n): ").strip().lower()
        if continue_choice not in ['y', 'yes', '']:
            print("프로그램을 종료합니다.")
            break

if __name__ == "__main__":
    main()
