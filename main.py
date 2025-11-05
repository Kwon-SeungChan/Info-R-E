import pygame
import sys
import random
import math
from enum import Enum
from brain import Brain

# ============================================================
# Enum 정의
# ============================================================

class BrushMode(Enum):
    """브러쉬 모드 열거형"""
    HEAT = 'heat'    # 가열 모드
    COOL = 'cool'    # 냉각 모드
    ERASE = 'erase'  # 지우기 모드

# ============================================================
# 상수 정의
# ============================================================

# 창 설정
WINDOW_WIDTH, WINDOW_HEIGHT = 1400, 700  # 시뮬레이션 창 크기
NEURON_PANEL_WIDTH = 700  # 오른쪽 뉴런 시각화 패널 너비

# 먹이 시스템
FOOD_SENSE_DISTANCE = 200  # 벌레가 먹이를 감지할 수 있는 최대 거리 (픽셀)
FOOD_EAT_DISTANCE = 20     # 먹이를 섭취하는 최소 거리 (픽셀)

# 배고픔 시스템 (하이브리드 AI의 k 값)
HUNGRY_LEVEL_INITIAL_VALUE = 0.5  # 초기 배고픔 수치 (0.0=배부름, 1.0=매우배고픔)
HUNGRY_LEVEL_INCREASE_INTERVAL = 1000  # 배고픔 증가 간격 (밀리초)
HUNGRY_LEVEL_INCREASE_AMOUNT = 0.01  # 1초당 배고픔 증가량
HUNGRY_LEVEL_DECREASE_ON_EAT = 0.1  # 먹이 섭취 시 배고픔 감소량

# 온도 시스템
DEFAULT_TEMPERATURE = 20.0  # 기본 환경 온도 (°C)
TEMPERATURE_MIN = -40.0  # 최저 온도
TEMPERATURE_MAX = 80.0  # 최고 온도
PREFERRED_TEMPERATURE_MIN = 8.0  # 벌레 선호 온도 최소값
PREFERRED_TEMPERATURE_MAX = 25.0  # 벌레 선호 온도 최대값
TEMPERATURE_GRID_SIZE = 30  # 온도 맵 그리드 셀 크기 (픽셀)
TEMPERATURE_DETECTION_RANGE = 100  # 벌레의 온도 감지 범위 (고정값)

# 브러쉬 설정 (디버깅 모드에서 온도 맵 페인팅)
BRUSH_SIZE_MIN = 20  # 브러쉬 최소 크기
BRUSH_SIZE_MAX = 150  # 브러쉬 최대 크기
BRUSH_SIZE_STEP = 10  # 브러쉬 크기 조절 단위
BRUSH_INITIAL_SIZE = 50  # 브러쉬 초기 크기
TEMPERATURE_SCALE_MIN = 1.0  # 온도 변화 최소값
TEMPERATURE_SCALE_MAX = 60.0  # 온도 변화 최대값
TEMPERATURE_SCALE_INITIAL = 5.0  # 온도 변화 초기값 (브러쉬 1회당 ±5도)

# 뉴런 시각화 설정
NEURON_MAX_ROWS = 20  # 뉴런 표시 최대 행 수 (창 크기에 맞게 조정)
NEURON_MARGIN = 18  # 뉴런 간 여백
NEURON_CIRCLE_RADIUS = 7  # 뉴런 원 반지름
NEURON_OFFSET_X = 150  # 뉴런 표시 시작 X 오프셋

# 타이머 설정
BRAIN_UPDATE_INTERVAL = 500  # 뇌 업데이트 주기 (밀리초) - 0.5초마다 신경망 계산
NEURON_RESET_TIME = 2000     # 뉴런 자극 리셋 시간 (밀리초) - 2초 후 자극 해제

# 벌레 렌더링 설정
WORM_BODY_WIDTH = 20  # 벌레 몸체 두께
WORM_SEGMENT_COUNT = 20  # 벌레 몸체 세그먼트 개수
WORM_FRAME_INTERVAL = 6  # 세그먼트 간 프레임 간격


# ============================================================
# 초기화
# ============================================================
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Worm Simulation with Neuron Visualization")
clock = pygame.time.Clock()

# ============================================================
# 전역 변수
# ============================================================

# 벌레 상태
target_position = [WINDOW_WIDTH // 2 - NEURON_PANEL_WIDTH, WINDOW_HEIGHT // 2]
facing_angle = 0
target_angle = 0
current_speed = 0
target_speed = 0
speed_change_rate = 0

# 먹이
food_positions = []

# 배고픔
hungry_value = HUNGRY_LEVEL_INITIAL_VALUE
start_time = pygame.time.get_ticks()

# 온도
preferred_temperature = random.uniform(PREFERRED_TEMPERATURE_MIN, PREFERRED_TEMPERATURE_MAX)
temperature_map = {}
current_temperature_at_worm = DEFAULT_TEMPERATURE
temp_reaction = "중립"

# 브러쉬
brush_mode = BrushMode.HEAT  # 초기 브러쉬 모드
brush_size = BRUSH_INITIAL_SIZE
temperature_scale = TEMPERATURE_SCALE_INITIAL

# UI 상태
debug_mode = False
input_mode = False
input_text = ""
mouse_pressed = False
keys_pressed = set()

# 타이머
last_brain_update = 0
last_touch_time = 0
last_food_sense_time = 0

# ============================================================
# 뇌 객체 생성
# ============================================================
brain = Brain()
brain.setup()
brain.RandExcite()

# ============================================================
# IK(벌레 본체) 클래스
# ============================================================
class InverseKinematicsSegment:
    """
    역운동학(Inverse Kinematics) 세그먼트 클래스
    
    벌레의 각 몸체 세그먼트를 표현하며, 스프링-댐퍼 시스템을 사용하여
    자연스러운 움직임을 구현합니다.
    """
    def __init__(self, length, head_point, tail_point):
        """
        Args:
            length: 세그먼트의 길이
            head_point: 머리 좌표 [x, y]
            tail_point: 꼬리 좌표 [x, y]
        """
        self.length = length
        self.head_point = head_point
        self.tail_point = tail_point

    def update(self):
        """
        스프링-댐퍼 시스템을 사용하여 세그먼트의 위치를 업데이트
        
        물리 시뮬레이션:
        - 목표 길이와 현재 길이의 차이에 비례하는 힘 계산
        - 탄성(elasticity)과 감쇠(damping)를 적용하여 자연스러운 움직임 구현
        """
        # 머리와 꼬리 사이의 벡터 계산
        dx = self.head_point[0] - self.tail_point[0]
        dy = self.head_point[1] - self.tail_point[1]
        distance = math.sqrt(dx * dx + dy * dy) if (dx != 0 or dy != 0) else 1
        
        # 스프링 힘 계산 (목표 길이와 현재 길이의 차이)
        force = 0.5 - (self.length / distance) * 0.5
        elasticity = 0.998  # 탄성 계수
        force *= 0.99  # 감쇠 계수
        
        # 힘을 x, y 성분으로 분해
        fx = force * dx
        fy = force * dy
        
        # 꼬리와 머리에 힘 적용 (작용-반작용 법칙)
        self.tail_point[0] += fx * elasticity * 2.0
        self.tail_point[1] += fy * elasticity * 2.0
        self.head_point[0] -= fx * (1.0 - elasticity) * 2.0
        self.head_point[1] -= fy * (1.0 - elasticity) * 2.0

class InverseKinematicsChain:
    """
    역운동학 체인 클래스 - 벌레의 전체 몸체를 구성하는 세그먼트 체인
    
    여러 InverseKinematicsSegment를 연결하여 벌레의 부드러운 움직임을 구현합니다.
    첫 번째 세그먼트가 목표 지점을 따라가면, 나머지 세그먼트들이 순차적으로 따라갑니다.
    """
    def __init__(self, number_of_segments, segment_length):
        """
        Args:
            number_of_segments: 세그먼트 개수
            segment_length: 각 세그먼트의 길이
        """
        self.segments = []
        # 무작위 시작 위치 생성
        current_point = [random.randint(0, WINDOW_WIDTH // 2), random.randint(0, WINDOW_HEIGHT)]
        
        # 세그먼트 체인 생성
        for _ in range(number_of_segments):
            head = current_point[:]
            tail = [head[0] + segment_length, head[1] + segment_length]
            self.segments.append(InverseKinematicsSegment(segment_length, head, tail))
            current_point = tail

    def update(self, target_point):
        """
        목표 지점을 향해 체인 업데이트
        
        Args:
            target_point: 첫 번째 세그먼트(머리)가 향할 목표 위치 [x, y]
        """
        # 첫 번째 세그먼트의 머리를 목표 지점으로 설정
        self.segments[0].head_point = target_point[:]
        
        # 모든 세그먼트 업데이트 (물리 시뮬레이션)
        for segment in self.segments:
            segment.update()

# ----------------------------
# 온도 관련 함수
# ----------------------------
def get_temperature_at_position(x, y):
    """
    특정 위치의 온도를 반환합니다.
    
    주변 온도 소스들의 영향을 거리 기반으로 보간하여 계산합니다.
    브러쉬 크기 내에 있는 온도 포인트들의 영향을 받으며,
    거리에 따라 가중치가 감소합니다.
    
    Args:
        x, y: 온도를 조회할 위치 좌표
        
    Returns:
        float: 해당 위치의 온도 (°C)
    """
    # 온도 맵이 비어있으면 기본 온도 반환
    if len(temperature_map) == 0:
        return DEFAULT_TEMPERATURE
    
    # 가장 가까운 온도 포인트 찾기
    min_distance = float('inf')
    nearest_temperature = DEFAULT_TEMPERATURE
    
    for (tx, ty), temperature in temperature_map.items():
        distance = math.sqrt((x - tx)**2 + (y - ty)**2)
        
        # 브러쉬 크기 내에 있으면 해당 온도 적용
        if distance < TEMPERATURE_DETECTION_RANGE:
            # 거리에 따라 온도 보간 (가까울수록 강하게 영향)
            weight = 1 - (distance / TEMPERATURE_DETECTION_RANGE)
            if distance < min_distance:
                min_distance = distance
                nearest_temperature = DEFAULT_TEMPERATURE + (temperature - DEFAULT_TEMPERATURE) * weight
    
    return nearest_temperature if min_distance < TEMPERATURE_DETECTION_RANGE else DEFAULT_TEMPERATURE

def apply_temperature_brush(x, y, mode):
    """
    브러쉬를 사용하여 온도 맵을 수정합니다.
    
    디버그 모드에서 사용되는 온도 편집 도구입니다.
    HEAT/COOL 모드는 온도를 증가/감소시키고, ERASE 모드는 온도 데이터를 제거합니다.
    
    Args:
        x, y: 브러쉬 중심 좌표
        mode: 브러쉬 모드 (BrushMode.HEAT / BrushMode.COOL / BrushMode.ERASE)
    """
    if mode == BrushMode.ERASE:
        # 지우기 모드: 브러쉬 영역 내의 모든 온도 포인트 제거
        to_remove = []
        for (px, py) in temperature_map.keys():
            distance = math.sqrt((x - px)**2 + (y - py)**2)
            if distance <= brush_size:
                to_remove.append((px, py))
        
        for pos in to_remove:
            del temperature_map[pos]
    else:
        # 가열/냉각 모드: 브러쉬 영역 내의 포인트들에 온도 적용
        step = 10  # 온도 맵 해상도 (픽셀 단위)
        for dx in range(-brush_size, brush_size, step):
            for dy in range(-brush_size, brush_size, step):
                px, py = x + dx, y + dy
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance <= brush_size:
                    current_temp = temperature_map.get((px, py), DEFAULT_TEMPERATURE)
                    
                    # 온도 변경 (최소/최대 범위 제한)
                    if mode == BrushMode.HEAT:
                        new_temp = min(current_temp + temperature_scale, TEMPERATURE_MAX)
                    else:  # BrushMode.COOL
                        new_temp = max(current_temp - temperature_scale, TEMPERATURE_MIN)
                    
                    temperature_map[(px, py)] = new_temp

def draw_temperature_map():
    """
    온도 맵을 시각화하여 화면에 그립니다.
    
    온도를 색상으로 표현합니다:
    - 차가운 온도: 파란색 (TEMPERATURE_MIN)
    - 적정 온도: 녹색 (20°C 기준)
    - 뜨거운 온도: 빨간색 (TEMPERATURE_MAX)
    
    디버그 모드에서만 표시됩니다.
    """
    if not debug_mode or len(temperature_map) == 0:
        return
    
    # 반투명 온도 레이어 생성
    temperature_surface = pygame.Surface((WINDOW_WIDTH - NEURON_PANEL_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    # SRCALPHA 플래그를 사용하여 투명도 지원
    font = pygame.font.SysFont("malgungothic,arial", 10)
    
    # 온도 포인트를 그리드로 그룹화
    temperature_grid = {}
    
    # 온도 맵의 각 포인트 처리
    for (x, y), temperature in temperature_map.items():
        if 0 <= x < WINDOW_WIDTH - NEURON_PANEL_WIDTH and 0 <= y < WINDOW_HEIGHT: # 뉴런 패널을 제외한 영역만 처리
            # 그리드 셀 좌표 계산
            grid_x = int(x / TEMPERATURE_GRID_SIZE) * TEMPERATURE_GRID_SIZE
            grid_y = int(y / TEMPERATURE_GRID_SIZE) * TEMPERATURE_GRID_SIZE
            
            # 그리드 셀의 평균 온도 계산
            if (grid_x, grid_y) not in temperature_grid:
                temperature_grid[(grid_x, grid_y)] = []
            temperature_grid[(grid_x, grid_y)].append(temperature)
    # 그리드 셀별로 온도 표시
    for (grid_x, grid_y), temperatures in temperature_grid.items():
        average_temperature = sum(temperatures) / len(temperatures)
        
        # 온도에 따라 색상 결정
        # 기본 온도(20도)를 중간으로 설정
        # -100 ~ 20: 파랑 -> 흰색
        # 20 ~ 100: 흰색 -> 빨강
        if average_temperature < DEFAULT_TEMPERATURE:
            # 차가움: 파랑 -> 흰색
            temp_ratio = (average_temperature - TEMPERATURE_MIN) / (DEFAULT_TEMPERATURE - TEMPERATURE_MIN)
            temp_ratio = max(0, min(1, temp_ratio))  # 0~1 사이로 제한
            r = int(255 * temp_ratio)
            g = int(255 * temp_ratio)
            b = 255
        else:
            # 뜨거움: 흰색 -> 빨강
            temp_ratio = (average_temperature - DEFAULT_TEMPERATURE) / (TEMPERATURE_MAX - DEFAULT_TEMPERATURE)
            temp_ratio = max(0, min(1, temp_ratio))  # 0~1 사이로 제한
            r = 255
            g = int(255 * (1 - temp_ratio))
            b = int(255 * (1 - temp_ratio))
        
        # 반투명 사각형 그리기
        pygame.draw.rect(temperature_surface, (r, g, b, 80), 
                        (grid_x, grid_y, TEMPERATURE_GRID_SIZE, TEMPERATURE_GRID_SIZE))
        
        # 온도 텍스트 표시 (흰색)
        temp_text = font.render(f"{int(average_temperature)}°", True, (255, 255, 255))
        temperature_surface.blit(temp_text, (grid_x + 3, grid_y + 8))
    
    screen.blit(temperature_surface, (0, 0))

def draw_brush_cursor(pos):
    """
    브러쉬 커서를 화면에 표시합니다.
    
    브러쉬 모드에 따라 다른 색상으로 원형 커서를 그립니다.
    - HEAT: 빨간색 (가열)
    - COOL: 파란색 (냉각)
    - ERASE: 회색 (지우기)
    
    Args:
        pos: 마우스 위치 (x, y)
    """
    if not debug_mode:
        return
    
    x, y = pos
    # 뉴런 패널 영역은 제외
    if x >= WINDOW_WIDTH - NEURON_PANEL_WIDTH:
        return
    
    # 브러쉬 모드에 따른 색상 선택
    if brush_mode == BrushMode.HEAT:
        color = (255, 100, 100, 100)  # 빨강 (가열)
    elif brush_mode == BrushMode.COOL:
        color = (100, 100, 255, 100)  # 파랑 (냉각)
    else:  # BrushMode.ERASE
        color = (150, 150, 150, 100)  # 회색 (지우기)
    
    # 반투명 원형 브러쉬 커서 그리기
    brush_surface = pygame.Surface((brush_size * 2, brush_size * 2), pygame.SRCALPHA)
    pygame.draw.circle(brush_surface, color, (brush_size, brush_size), brush_size, 2)
    screen.blit(brush_surface, (x - brush_size, y - brush_size))


# ----------------------------
# 먹이 관련 함수
# ----------------------------
def add_food(position):
    """
    먹이를 추가합니다.
    
    Args:
        position: 먹이 위치 [x, y]
    """
    food_positions.append(position)

def draw_food():
    """모든 먹이를 화면에 그립니다."""
    for f in food_positions:
        pygame.draw.circle(screen, (251, 192, 45), f, 10)

# ----------------------------
# 디버깅 모드 표시
# ----------------------------
def draw_debug_info():
    """
    디버그 정보를 화면에 표시합니다.
    
    벌레의 감지 범위와 섭취 범위를 시각화하여 디버깅을 돕습니다.
    - 먹이 감지 범위: 큰 녹색 원 (FOOD_SENSE_DISTANCE)
    - 먹이 섭취 범위: 작은 노란색 원 (FOOD_EAT_DISTANCE)
    """
    if debug_mode:
        # 벌레 머리 기준 먹이 탐지 범위 (반투명 녹색 원)
        debug_surface = pygame.Surface((FOOD_SENSE_DISTANCE * 2, FOOD_SENSE_DISTANCE * 2), pygame.SRCALPHA)
        pygame.draw.circle(debug_surface, (100, 255, 100, 50), (FOOD_SENSE_DISTANCE, FOOD_SENSE_DISTANCE), FOOD_SENSE_DISTANCE)
        screen.blit(debug_surface, (target_position[0] - FOOD_SENSE_DISTANCE, target_position[1] - FOOD_SENSE_DISTANCE))
        
        # 먹이 먹는 범위 (작은 반투명 노란색 원)
        eat_surface = pygame.Surface((FOOD_EAT_DISTANCE * 2, FOOD_EAT_DISTANCE * 2), pygame.SRCALPHA)
        pygame.draw.circle(eat_surface, (255, 100, 100, 80), (FOOD_EAT_DISTANCE, FOOD_EAT_DISTANCE), FOOD_EAT_DISTANCE)
        screen.blit(eat_surface, (target_position[0] - FOOD_EAT_DISTANCE, target_position[1] - FOOD_EAT_DISTANCE))
        
        # 머리가 이동하는 방향 화살표
        arrow_length = 50
        arrow_end_x = target_position[0] + math.cos(facing_angle) * arrow_length
        arrow_end_y = target_position[1] - math.sin(facing_angle) * arrow_length
        
        # 화살표 선
        pygame.draw.line(screen, (255, 0, 0), target_position, (arrow_end_x, arrow_end_y), 3)
        
        # 화살촉
        arrow_angle1 = facing_angle + math.pi * 0.75
        arrow_angle2 = facing_angle - math.pi * 0.75
        arrow_tip_length = 15
        tip1_x = arrow_end_x + math.cos(arrow_angle1) * arrow_tip_length
        tip1_y = arrow_end_y - math.sin(arrow_angle1) * arrow_tip_length
        tip2_x = arrow_end_x + math.cos(arrow_angle2) * arrow_tip_length
        tip2_y = arrow_end_y - math.sin(arrow_angle2) * arrow_tip_length
        
        pygame.draw.line(screen, (255, 0, 0), (arrow_end_x, arrow_end_y), (tip1_x, tip1_y), 3)
        pygame.draw.line(screen, (255, 0, 0), (arrow_end_x, arrow_end_y), (tip2_x, tip2_y), 3)

def draw_adex_parameters():
    """
    메인 화면(왼쪽 상단)에 AdEx 모델 파라미터를 표시합니다.
    디버그 모드에서만 표시됩니다.
    """
    if not debug_mode:
        return
    
    font = pygame.font.SysFont("malgungothic,arial", 11)
    start_x = 10
    start_y = 10
    line_height = 14
    
    # 제목
    title_surf = font.render("=== AdEx Model ===", True, (255, 255, 150))
    screen.blit(title_surf, (start_x, start_y))
    start_y += line_height + 3
    
    # 막 특성
    cm_surf = font.render(f"C_m: {brain.C_m:.1f} pF", True, (150, 200, 255))
    screen.blit(cm_surf, (start_x, start_y))
    start_y += line_height
    
    gl_surf = font.render(f"g_L: {brain.g_L:.1f} nS", True, (150, 200, 255))
    screen.blit(gl_surf, (start_x, start_y))
    start_y += line_height
    
    taum_surf = font.render(f"tau_m: {brain.tau_m:.1f} ms", True, (150, 200, 255))
    screen.blit(taum_surf, (start_x, start_y))
    start_y += line_height + 2
    
    # 지수 스파이크
    vt_surf = font.render(f"V_T: {brain.V_T:.1f} mV", True, (255, 180, 120))
    screen.blit(vt_surf, (start_x, start_y))
    start_y += line_height
    
    deltat_surf = font.render(f"delta_T: {brain.delta_T:.1f} mV", True, (255, 180, 120))
    screen.blit(deltat_surf, (start_x, start_y))
    start_y += line_height + 2
    
    # 적응
    tauw_surf = font.render(f"tau_w: {brain.tau_w:.1f} ms", True, (255, 150, 150))
    screen.blit(tauw_surf, (start_x, start_y))
    start_y += line_height
    
    a_surf = font.render(f"a: {brain.a:.1f} nS", True, (255, 150, 150))
    screen.blit(a_surf, (start_x, start_y))
    start_y += line_height
    
    b_surf = font.render(f"b: {brain.b:.1f} pA", True, (255, 150, 150))
    screen.blit(b_surf, (start_x, start_y))

# ============================================================
# 벌레 그리기 함수
# ============================================================
def draw_worm():
    """
    벌레를 화면에 그립니다.
    
    벌레의 움직임 기록(head_path)을 사용하여 몸체를 렌더링합니다.
    이전 위치들을 추적하여 자연스러운 꼬불꼬불한 몸체를 표현합니다.
    
    작동 방식:
    1. 현재 머리 위치를 경로에 추가
    2. 일정 간격(frame_interval)마다 샘플링하여 세그먼트 위치 계산
    3. 세그먼트 간을 선으로 연결하여 몸체 렌더링
    
    전역 변수:
        draw_worm.head_path: 벌레 머리의 이동 경로 [(x, y, angle), ...]
    """
    # 게임 속도에 따른 프레임 간격 조정
    frame_interval = WORM_FRAME_INTERVAL

    # 정적 변수 초기화 (함수 속성 사용)
    if not hasattr(draw_worm, "head_path"):
        draw_worm.head_path = []

    # 현재 머리 위치를 경로에 추가
    draw_worm.head_path.insert(0, (target_position[0], target_position[1], facing_angle))
    
    # 최대 경로 길이 제한 (메모리 절약)
    max_path_length = WORM_SEGMENT_COUNT * frame_interval
    if len(draw_worm.head_path) > max_path_length:
        draw_worm.head_path = draw_worm.head_path[:max_path_length]

    # 세그먼트 위치 계산 (일정 간격마다 샘플링)
    segment_points = []
    for i in range(WORM_SEGMENT_COUNT):
        index = i * frame_interval
        if index < len(draw_worm.head_path):
            x, y, _ = draw_worm.head_path[index]
        else:
            # 경로가 짧으면 마지막 위치 사용
            x, y, _ = draw_worm.head_path[-1]
        segment_points.append((x, y))

    # 세그먼트 간을 선으로 연결하여 몸체 그리기
    for i in range(len(segment_points) - 1):
        pygame.draw.line(screen, (255, 255, 255), segment_points[i], segment_points[i + 1], WORM_BODY_WIDTH)

    # 각 세그먼트를 원으로 그려서 부드러운 연결 효과
    for p in segment_points:
        pygame.draw.circle(screen, (255, 255, 255), p, WORM_BODY_WIDTH // 2, 0)

# ============================================================
# 뉴런 활성화 시각화
# ============================================================
def draw_brain_activity(brain, surface, start_x, start_y, width, height):
    """
    C. elegans 뇌의 뉴런 활성화 상태를 시각화합니다.
    
    302개 뉴런 중 근육을 제외한 뉴런들을 색상으로 표시합니다:
    - 빨간색: 활성화 (신호 강도 > FireThreshold)
    - 녹색: 중간 활성 (신호 강도 > FireThreshold * 0.5)
    - 파란색: 약한 신호 (신호 강도 > 0)
    - 회색: 비활성 (신호 강도 = 0)
    
    추가 정보 (디버그 모드):
    - 뉴런 수, FireThreshold
    - 배고픔 수치 (hungry_value)
    - 현재 온도, 선호 온도, 온도 반응
    - 브러쉬 설정 (모드, 크기, 스케일)
    
    Args:
        brain: Brain 객체 (신경망)
        surface: 렌더링할 pygame 표면
        start_x, start_y: 패널 시작 위치
        width, height: 패널 크기
    """
    # 한글 폰트 설정
    font = pygame.font.SysFont("malgungothic,arial", 16)
    neuron_name_font = pygame.font.SysFont("malgungothic,arial", 9)
    
    # PostSynaptic에서 근육을 제외한 뉴런만 필터링
    # (근육은 뇌 뉴런이 아니라 출력 단위)
    muscle_prefixes = ['MDL', 'MDR', 'MVL', 'MVR']
    neurons = sorted([n for n in brain.PostSynaptic.keys() 
                     if not any(n.startswith(prefix) for prefix in muscle_prefixes)])
    total_neurons = len(neurons)

    # 뉴런 배치 계산 (행/열)
    rows = min(NEURON_MAX_ROWS, total_neurons)
    cols = math.ceil(total_neurons / rows)
    
    # 배경 그리기 (어두운 회색)
    pygame.draw.rect(surface, (18, 18, 20), (start_x, start_y, width, height))
    
    current_y = start_y + 6
    
    # ========================================
    # 디버그 정보 표시
    # ========================================
    if debug_mode:
        # 제목 및 뉴런 수
        title_surf = font.render(f"C. elegans Connectome - {total_neurons} Neurons", True, (230, 230, 230))
        surface.blit(title_surf, (start_x + 8, current_y))
        current_y += 16
        
        # ========================================
        # AdEx 모델 파라미터
        # ========================================
        # 발화 임계값
        thresh_surf = font.render(f"FireThreshold: {brain.FireThreshold}", True, (200, 200, 200))
        surface.blit(thresh_surf, (start_x + 8, current_y))
        current_y += 16
        
        # ========================================
        # 벌레 상태 정보
        # ========================================
        # ========================================
        # 벌레 상태 정보
        # ========================================
        current_y += 8  # 빈 줄
        
        # 배고픔 수치 표시
        hungry_surf = font.render(f"배고픔 (k): {hungry_value:.2f}", True, (100, 255, 100))
        surface.blit(hungry_surf, (start_x + 8, current_y))
        current_y += 16
        
        # 이동 방향 벡터 표시
        direction_x = math.cos(facing_angle)
        direction_y = -math.sin(facing_angle)
        dir_surf = font.render(f"방향 벡터: ({direction_x:.2f}, {direction_y:.2f})", True, (150, 200, 255))
        surface.blit(dir_surf, (start_x + 8, current_y))
        current_y += 16
        
        # 먹이 먹는 범위 표시
        range_surf = font.render(f"먹이 먹는 범위: {FOOD_EAT_DISTANCE}px", True, (255, 150, 150))
        surface.blit(range_surf, (start_x + 8, current_y))
        current_y += 16
        
        # 먹이 감지 범위 표시
        sense_surf = font.render(f"먹이 감지 범위: {FOOD_SENSE_DISTANCE}px", True, (150, 255, 150))
        surface.blit(sense_surf, (start_x + 8, current_y))
        current_y += 16
        
        # 온도 정보 표시
        current_y += 8  # 빈 줄
        temp_title_surf = font.render("=== 온도 정보 ===", True, (255, 255, 150))
        surface.blit(temp_title_surf, (start_x + 8, current_y))
        current_y += 16
        
        # 벌레 위치의 현재 온도
        current_temp_surf = font.render(f"벌레 위치 온도: {current_temperature_at_worm:.1f}°C", True, (255, 200, 100))
        surface.blit(current_temp_surf, (start_x + 8, current_y))
        current_y += 16
        
        pref_temp_surf = font.render(f"선호 온도: {preferred_temperature:.1f}°C", True, (100, 255, 150))
        surface.blit(pref_temp_surf, (start_x + 8, current_y))
        current_y += 16
    
        # P 키 안내
        pref_hint_surf = font.render("(P키: 선호 온도 변경)", True, (150, 200, 150))
        surface.blit(pref_hint_surf, (start_x + 8, current_y))
        current_y += 16
        
        # 온도 차이
        temperature_difference = abs(current_temperature_at_worm - preferred_temperature)
        diff_surf = font.render(f"온도 차이: {temperature_difference:.1f}°C", True, (200, 200, 200))
        surface.blit(diff_surf, (start_x + 8, current_y))
        current_y += 16
        
        # 온도 반응 (색상으로 구분)
        reaction_colors = {
            "만족": (100, 255, 100),  # 초록
            "중립": (200, 200, 200),  # 회색
            "회피": (255, 100, 100)   # 빨강
        }
        reaction_color = reaction_colors.get(temp_reaction, (200, 200, 200))
        reaction_surf = font.render(f"온도 반응: {temp_reaction}", True, reaction_color)
        surface.blit(reaction_surf, (start_x + 8, current_y))
        current_y += 16
        
        current_y += 8  # 빈 줄
        
        # 브러쉬 정보
        brush_title_surf = font.render("=== 브러쉬 ===", True, (200, 200, 255))
        surface.blit(brush_title_surf, (start_x + 8, current_y))
        current_y += 16
        
        # BrushMode enum의 값에 따라 텍스트 및 색상 결정
        brush_mode_text = {
            BrushMode.HEAT: '가열', 
            BrushMode.COOL: '냉각', 
            BrushMode.ERASE: '지우기'
        }[brush_mode]
        brush_color_map = {
            BrushMode.HEAT: (255, 100, 100), 
            BrushMode.COOL: (100, 100, 255), 
            BrushMode.ERASE: (150, 150, 150)
        }
        brush_color = brush_color_map[brush_mode]
        brush_mode_surf = font.render(f"모드: {brush_mode_text} (A/S/D)", True, brush_color)
        surface.blit(brush_mode_surf, (start_x + 8, current_y))
        current_y += 16
        
        brush_size_surf = font.render(f"크기: {brush_size}px (UP/DOWN)", True, (180, 180, 180))
        surface.blit(brush_size_surf, (start_x + 8, current_y))
        current_y += 16
        
        # 온도 스케일 표시
        scale_surf = font.render(f"스케일: ±{temperature_scale:.1f}° (LEFT/RIGHT)", True, (180, 180, 180))
        surface.blit(scale_surf, (start_x + 8, current_y))
        current_y += 16
        
        # 온도 맵 포인트 수
        temp_points_surf = font.render(f"온도 포인트: {len(temperature_map)}", True, (150, 150, 150))
        surface.blit(temp_points_surf, (start_x + 8, current_y))
        current_y += 16
    
    # ========================================
    # 모드 표시 (항상 표시)
    # ========================================
    if debug_mode:
        mode_text = "디버깅 모드 (1: 일반, 2: 디버깅, A/S/D: 브러쉬, 드래그: 페인트)"
    else:
        mode_text = "일반 모드 (1: 일반, 2: 디버깅, 클릭: 먹이)"
    mode_surf = font.render(mode_text, True, (255, 200, 100))
    surface.blit(mode_surf, (start_x + 8, current_y))

    # ========================================
    # 뉴런 렌더링 (오른쪽 하단에 배치)
    # ========================================
    neuron_start_y = height - (rows * (2 * NEURON_CIRCLE_RADIUS + NEURON_MARGIN)) - NEURON_MARGIN
    
    for i, neuron in enumerate(neurons):
        # 행/열 계산 (세로로 먼저 채움)
        row = i % rows
        col = i // rows
        
        # 뉴런 위치 계산
        cx = start_x + NEURON_OFFSET_X + NEURON_MARGIN + col * (2 * NEURON_CIRCLE_RADIUS + NEURON_MARGIN)
        cy = start_y + neuron_start_y + row * (2 * NEURON_CIRCLE_RADIUS + NEURON_MARGIN)

        # 뉴런 활성화 수준에 따른 색상 결정
        activity = brain.PostSynaptic[neuron][brain.CurrentSignalIntensityIndex]
        
        if activity > brain.FireThreshold:
            # 발화 임계값 초과: 빨간색 (강한 활성화)
            color = (255, 80, 80)
        elif activity > brain.FireThreshold * 0.5:
            # 중간 활성: 녹색
            color = (80, 220, 80)
        elif activity > 0:
            # 약한 신호: 파란색
            color = (80, 120, 220)
        else:
            # 비활성: 회색
            color = (80, 80, 80)

        # 뉴런 원 그리기
        pygame.draw.circle(surface, color, (cx, cy), NEURON_CIRCLE_RADIUS)
        
        # 뉴런 이름 표시 (원 위에)
        name_surf = neuron_name_font.render(neuron, True, (230, 230, 230))
        surface.blit(name_surf, (cx - name_surf.get_width() // 2, cy - NEURON_CIRCLE_RADIUS - 12))

# ----------------------------
# 뇌 상태 업데이트
# ----------------------------
def update_brain():
    """
    뇌의 신경망을 업데이트하고 온도 자극을 처리합니다.
    
    이 함수는 다음을 수행합니다:
    1. 벌레 위치의 온도를 감지
    2. 온도 차이에 따라 AFD 온도 감각 뉴런을 자극
       - 온도 차이 > 5°C: 강한 회피 반응 (신호 강도 +10)
       - 온도 차이 < 2°C: 만족 반응 (신호 강도 +2)
       - 그 외: 중립
    3. 뇌 신경망 업데이트 (brain.update())
    4. 근육 신호에 따라 이동 방향과 속도 계산
    
    전역 변수 수정:
        target_angle: 뇌 신호에 따른 목표 이동 각도
        target_speed: 근육 활성화에 따른 목표 속도
        speed_change_rate: 속도 변화율
        current_temperature_at_worm: 현재 벌레 위치의 온도
        temp_reaction: 온도 반응 ("만족", "중립", "회피")
    """
    global target_angle, target_speed, speed_change_rate
    global current_temperature_at_worm, temp_reaction
    
    # 1. 벌레 위치의 온도 확인
    worm_temperature = get_temperature_at_position(target_position[0], target_position[1])
    current_temperature_at_worm = worm_temperature
    temperature_difference = abs(worm_temperature - preferred_temperature) # 선호 온도와 현재 온도 차이
    

    TEMPERATURE_SATISFIED_THRESHOLD = 2.0  # 만족 상태 임계값 (±2°C 이내)
    TEMPERATURE_AVOIDANCE_THRESHOLD = 5.0  # 회피 상태 임계값 (5°C 초과)
    TEMPERATURE_SATISFIED_STIMULUS = 2     # 만족 시 AFD 뉴런 자극 강도
    TEMPERATURE_AVOIDANCE_STIMULUS = 10    # 회피 시 AFD 뉴런 자극 강도

    # 2. AFD 온도 감각 뉴런 자극
    stimulus = 0
    if temperature_difference > TEMPERATURE_AVOIDANCE_THRESHOLD:
        # 온도 차이가 크면 강하게 자극 (회피 반응)
        stimulus = TEMPERATURE_AVOIDANCE_STIMULUS
        temp_reaction = "회피"
    elif temperature_difference < TEMPERATURE_SATISFIED_THRESHOLD:
        # 선호 온도에 가까우면 약하게 자극 (만족 반응)
        stimulus = TEMPERATURE_SATISFIED_STIMULUS
        temp_reaction = "만족"
    else:
        temp_reaction = "중립"
    brain.PostSynaptic['AFDL'][brain.NextSignalIntensityIndex] += stimulus
    brain.PostSynaptic['AFDR'][brain.NextSignalIntensityIndex] += stimulus
    
    
    
    # 3. 뇌 신경망 업데이트 (302개 뉴런 시뮬레이션)
    brain.update()
    
    # 4. 근육 신호에 따른 이동 방향과 속도 계산
    SCALING_FACTOR = 20
    # 좌우 근육 신호 차이 → 회전 각도
    new_angle_offset = (brain.AccumulatedLeftMusclesSignal - brain.AccumulatedRightMusclesSignal) / SCALING_FACTOR
    
    # A: 기본 이동 각도 (뇌의 신호에 따른 방향)
    brain_target_angle = facing_angle + new_angle_offset * math.pi
    target_angle = brain_target_angle  # 일단 뇌의 신호로 설정 (먹이가 있으면 update()에서 하이브리드 AI로 수정됨)
    
    # 좌우 근육 신호 합계 → 이동 속도
    target_speed = ((abs(brain.AccumulatedLeftMusclesSignal) + abs(brain.AccumulatedRightMusclesSignal)) / (SCALING_FACTOR * 5))
    speed_change_rate = ((target_speed - current_speed) / (SCALING_FACTOR * 1.5))

# ----------------------------
# k 값 업데이트 (배고픔 증가)
# ----------------------------
def update_hungry_value():
    """
    시간 경과에 따라 배고픔 수치를 증가시킵니다.
    
    배고픔(hungry_value)은 하이브리드 AI의 k 값으로 사용됩니다:
    - 0.0: 배부름 → 뇌 신호 100% 우선
    - 1.0: 매우 배고픔 → 먹이 탐색 100% 우선
    
    증가율: 1초당 0.01 (HUNGRY_LEVEL_INCREASE_AMOUNT)
    """
    global hungry_value
    current_time = pygame.time.get_ticks()
    elapsed_time = current_time - start_time
    # 경과 시간에 따라 배고픔 값 계산 (1초마다 0.01씩 증가)
    seconds_passed = elapsed_time // HUNGRY_LEVEL_INCREASE_INTERVAL
    hungry_value = min(1.0, HUNGRY_LEVEL_INITIAL_VALUE + seconds_passed * HUNGRY_LEVEL_INCREASE_AMOUNT)

# ----------------------------
# 배고픔 감소 (먹이를 먹었을 때)
# ----------------------------
def decrease_hunger():
    """
    먹이를 섭취했을 때 배고픔 수치를 감소시킵니다.
    
    감소량: 0.1 (HUNGRY_LEVEL_DECREASE_ON_EAT)
    시작 시간을 재조정하여 지속적인 배고픔 증가 시스템과 동기화합니다.
    """
    global hungry_value, start_time
    hungry_value = max(0.0, hungry_value - HUNGRY_LEVEL_DECREASE_ON_EAT)
    
    # 시작 시간을 재조정하여 감소된 배고픔 값을 반영
    current_time = pygame.time.get_ticks()
    
    # hungry_value = 0.5 + seconds_passed * 0.01 공식에서 역산
    if hungry_value >= HUNGRY_LEVEL_INITIAL_VALUE:
        seconds_passed = (hungry_value - HUNGRY_LEVEL_INITIAL_VALUE) / HUNGRY_LEVEL_INCREASE_AMOUNT
        start_time = current_time - int(seconds_passed * HUNGRY_LEVEL_INCREASE_INTERVAL)
    else:
        # hungry_value가 초기값 미만이면 시작 시간을 미래로 설정
        seconds_to_reach_initial = (HUNGRY_LEVEL_INITIAL_VALUE - hungry_value) / HUNGRY_LEVEL_INCREASE_AMOUNT
        start_time = current_time + int(seconds_to_reach_initial * HUNGRY_LEVEL_INCREASE_INTERVAL)

# ----------------------------
# 벌레 물리/이동 업데이트
# ----------------------------
def update():
    """
    벌레의 물리 시뮬레이션과 하이브리드 AI를 업데이트합니다.
    
    === 하이브리드 AI 공식 ===
    최종 이동 방향 = (1 - hungry_value) × brain_signal + hungry_value × food_direction
    
    - brain_signal (A): C. elegans 뇌 신경망의 근육 신호에 따른 방향
    - food_direction (B): 가장 가까운 먹이를 향한 방향
    - hungry_value (k): 0.0~1.0 사이의 배고픔 수치
    
    배고픔이 낮으면 뇌 신호를 우선하고, 높으면 먹이 탐색을 우선합니다.
    
    추가 기능:
    - 화면 경계 충돌 시 코 터치 뉴런 자극
    - 먹이 섭취 범위 내에서 먹이 제거 및 배고픔 감소
    """
    global current_speed, facing_angle, target_position, last_touch_time, last_food_sense_time, target_angle
    
    # 속도 업데이트
    current_speed += speed_change_rate

    # A: 기본 이동 각도 (target_angle은 update_brain()에서 이미 설정됨)
    brain_target_angle = target_angle
    
    # B: 먹이를 향한 이동 각도 (초기값은 뇌의 각도)
    food_target_angle = target_angle
    
    # === 하이브리드 AI: 먹이 감지 및 방향 계산 ===
    if len(food_positions) > 0:
        # 가장 가까운 먹이 찾기
        closest_food = None
        min_distance = float('inf')
        
        for food in food_positions:
            distance = math.hypot(target_position[0] - food[0], target_position[1] - food[1])
            if distance < min_distance:
                min_distance = distance
                closest_food = food
        
        # 먹이가 감지 범위 내에 있으면 먹이 방향 계산
        if closest_food and min_distance <= FOOD_SENSE_DISTANCE:
            # 먹이 방향 벡터 계산
            food_dx = closest_food[0] - target_position[0]
            food_dy = closest_food[1] - target_position[1]
            food_target_angle = math.atan2(-food_dy, food_dx)  # y축 반전 보정
            
            # === 하이브리드 AI 공식 적용 ===
            # 최종 방향 = (1-k)A + kB
            # A = 뇌 신호에 따른 방향
            # B = 먹이를 향한 방향
            # k = 배고픔 수치 (0.0~1.0)
            target_angle = (1 - hungry_value) * brain_target_angle + hungry_value * food_target_angle

    # 각도 차이 계산 및 부드러운 회전
    angle_difference = facing_angle - target_angle
    # 각도를 -π ~ π 범위로 정규화
    if abs(angle_difference) > math.pi:
        if facing_angle > target_angle:
            angle_difference = -1 * (2 * math.pi - facing_angle + target_angle)
        else:
            angle_difference = 2 * math.pi - target_angle + facing_angle

    # 부드러운 회전 적용
    if angle_difference > 0:
        facing_angle -= 0.1
    elif angle_difference < 0:
        facing_angle += 0.1

    # 위치 업데이트
    target_position[0] += math.cos(facing_angle) * current_speed
    target_position[1] -= math.sin(facing_angle) * current_speed

    # 화면 경계 충돌 검사 및 코 터치 뉴런 자극
    if target_position[0] < 0:
        target_position[0] = 0
        brain.IsStimulatedNoseTouchNeurons = True
        last_touch_time = pygame.time.get_ticks()
    elif target_position[0] > WINDOW_WIDTH - NEURON_PANEL_WIDTH:
        target_position[0] = WINDOW_WIDTH - NEURON_PANEL_WIDTH
        brain.IsStimulatedNoseTouchNeurons = True
        last_touch_time = pygame.time.get_ticks()

    if target_position[1] < 0:
        target_position[1] = 0
        brain.IsStimulatedNoseTouchNeurons = True
        last_touch_time = pygame.time.get_ticks()
    elif target_position[1] > WINDOW_HEIGHT:
        target_position[1] = WINDOW_HEIGHT
        brain.IsStimulatedNoseTouchNeurons = True
        last_touch_time = pygame.time.get_ticks()

    # 먹이 감지 및 섭취
    for f in food_positions[:]:
        distance = math.hypot(target_position[0] - f[0], target_position[1] - f[1])
        
        # 먹이 감지 범위 내: 먹이 감각 뉴런 자극
        if distance <= FOOD_SENSE_DISTANCE:
            brain.IsStimulatedFoodSenseNeurons = True
            last_food_sense_time = pygame.time.get_ticks()
            
            # 먹이 섭취 범위 내: 먹이 제거 및 배고픔 감소
            if distance <= FOOD_EAT_DISTANCE:
                food_positions.remove(f)
                decrease_hunger()

    # 벌레 몸체 체인 업데이트 (역운동학)
    worm_chain.update(target_position)

worm_chain = InverseKinematicsChain(200, 1)

# ============================================================
# 메인 게임 루프
# ============================================================
while True:
    current_time = pygame.time.get_ticks()
    # ========================================
    # 이벤트 처리
    # ========================================
    for event in pygame.event.get():
        # 창 닫기
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        # 마우스 클릭
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # 뉴런 패널 영역 제외
            if mx < WINDOW_WIDTH - NEURON_PANEL_WIDTH:
                if not debug_mode:
                    # 일반 모드: 클릭으로 먹이 추가
                    add_food([mx, my])
                elif debug_mode and event.button == 1:
                    # 디버그 모드: 왼쪽 버튼으로 온도 브러쉬 적용
                    mouse_pressed = True
        
        # 마우스 버튼 떼기
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                mouse_pressed = False
        
        # 키보드 입력
        elif event.type == pygame.KEYDOWN:
            if input_mode:
                # === 선호 온도 입력 모드 ===
                if event.key == pygame.K_RETURN:
                    # Enter: 입력 완료
                    try:
                        new_temp = float(input_text)
                        # 유효 범위 검사 (8~25°C)
                        if PREFERRED_TEMPERATURE_MIN <= new_temp <= PREFERRED_TEMPERATURE_MAX:
                            preferred_temperature = new_temp
                        input_text = ""
                        input_mode = False
                    except ValueError:
                        # 잘못된 입력은 무시
                        input_text = ""
                        input_mode = False
                elif event.key == pygame.K_ESCAPE:
                    # ESC: 입력 취소
                    input_text = ""
                    input_mode = False
                elif event.key == pygame.K_BACKSPACE:
                    # Backspace: 한 글자 삭제
                    input_text = input_text[:-1]
                elif event.unicode in '0123456789.-':
                    # 숫자, 소수점, 마이너스만 입력 가능
                    if len(input_text) < 10:  # 최대 10자
                        input_text += event.unicode
            else:
                # === 일반 키 입력 ===
                if event.key == pygame.K_1:
                    debug_mode = False  # 일반 모드 전환
                elif event.key == pygame.K_2:
                    debug_mode = True  # 디버그 모드 전환
                elif event.key == pygame.K_p and debug_mode:
                    # P: 선호 온도 설정 모드 진입
                    input_mode = True
                    input_text = ""
                elif event.key == pygame.K_a and debug_mode:
                    brush_mode = BrushMode.HEAT  # A: 가열 브러쉬
                elif event.key == pygame.K_s and debug_mode:
                    brush_mode = BrushMode.COOL  # S: 냉각 브러쉬
                elif event.key == pygame.K_d and debug_mode:
                    brush_mode = BrushMode.ERASE  # D: 지우기 브러쉬
                elif event.key == pygame.K_UP and debug_mode:
                    # ↑: 브러쉬 크기 증가
                    brush_size = min(brush_size + BRUSH_SIZE_STEP, BRUSH_SIZE_MAX)
                elif event.key == pygame.K_DOWN and debug_mode:
                    # ↓: 브러쉬 크기 감소
                    brush_size = max(brush_size - BRUSH_SIZE_STEP, BRUSH_SIZE_MIN)
                elif event.key == pygame.K_LEFT and debug_mode:
                    # ←: 온도 변화량 감소
                    temperature_scale = max(temperature_scale - 1.0, TEMPERATURE_SCALE_MIN)
                elif event.key == pygame.K_RIGHT and debug_mode:
                    # →: 온도 변화량 증가
                    temperature_scale = min(temperature_scale + 1.0, TEMPERATURE_SCALE_MAX)
    
    # ========================================
    # 마우스 드래그로 온도 브러쉬 적용
    # ========================================
    if debug_mode and mouse_pressed:
        mx, my = pygame.mouse.get_pos()
        if mx < WINDOW_WIDTH - NEURON_PANEL_WIDTH:
            apply_temperature_brush(mx, my, brush_mode)

    # ========================================
    # 화면 지우기
    # ========================================
    screen.fill((0, 0, 0))
    
    # ========================================
    # 게임 로직 업데이트
    # ========================================
    
    # 배고픔 수치 업데이트 (시간 경과에 따라 증가)
    update_hungry_value()
    
    # 뇌 신경망 업데이트 (500ms마다)
    if current_time - last_brain_update >= BRAIN_UPDATE_INTERVAL:
        update_brain()
        last_brain_update = current_time
    
    # 벌레 이동 및 물리 시뮬레이션 업데이트
    update()
    
    # ========================================
    # 렌더링
    # ========================================
    draw_temperature_map()  # 온도 맵 시각화 (디버그 모드)
    draw_food()  # 먹이 그리기
    draw_worm()  # 벌레 그리기
    draw_debug_info()  # 디버그 정보 (감지 범위 등)
    draw_adex_parameters()  # AdEx 모델 파라미터 표시 (메인 화면 왼쪽 상단)
    draw_brain_activity(brain, screen, WINDOW_WIDTH - NEURON_PANEL_WIDTH, 0, NEURON_PANEL_WIDTH, WINDOW_HEIGHT)  # 뉴런 시각화
    
    # 디버그 모드: 브러쉬 커서 표시
    if debug_mode:
        draw_brush_cursor(pygame.mouse.get_pos())
    
    # ========================================
    # 선호 온도 입력 UI 표시
    # ========================================
    if input_mode: # 선호 온도 입력 모드
        # 반투명 배경
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 180), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(overlay, (0, 0))
        
        # 입력 창
        input_font = pygame.font.SysFont("malgungothic,arial", 24)
        title_surf = input_font.render("선호 온도 설정 (8 ~ 25°C)", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        screen.blit(title_surf, title_rect)
        
        # 입력 텍스트
        input_display = input_text if input_text else "0"
        input_surf = input_font.render(f"{input_display}°C", True, (255, 255, 100))
        input_rect = input_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        
        # 입력 박스
        box_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - 25, 300, 50)
        pygame.draw.rect(screen, (50, 50, 50), box_rect)
        pygame.draw.rect(screen, (255, 255, 100), box_rect, 2)
        screen.blit(input_surf, input_rect)
        
        # 안내 텍스트
        hint_font = pygame.font.SysFont("malgungothic,arial", 16)
        hint_surf = hint_font.render("Enter: 확인 | ESC: 취소", True, (200, 200, 200))
        hint_rect = hint_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        screen.blit(hint_surf, hint_rect)

    pygame.display.flip()
    clock.tick(60)

    # JavaScript처럼 2초 후에 뉴런 자극 리셋
    brain.IsStimulatedHungerNeurons = True
    
    # 터치 자극은 2초 후 리셋
    if last_touch_time > 0 and current_time - last_touch_time >= NEURON_RESET_TIME:
        brain.IsStimulatedNoseTouchNeurons = False
    
    # 음식 감지 자극은 2초 후 리셋
    if last_food_sense_time > 0 and current_time - last_food_sense_time >= NEURON_RESET_TIME:
        brain.IsStimulatedFoodSenseNeurons = False
