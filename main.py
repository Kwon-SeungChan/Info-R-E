import pygame
import sys
import random
import math
from brain import Brain

# ----------------------------
# 초기화 및 창 설정
# ----------------------------
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1800, 900
NEURON_PANEL_WIDTH = 900
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Worm Simulation with Neuron Visualization")
clock = pygame.time.Clock()

# ----------------------------
# 개발용 속도 조절 상수
# ----------------------------
GAME_SPEED = 1  # 1.0 = 정상 속도, 0.5 = 절반 속도, 2.0 = 두 배 속도

# ----------------------------
# 벌레 초기 상태 변수
# ----------------------------
target_position = [WINDOW_WIDTH // 2 - NEURON_PANEL_WIDTH, WINDOW_HEIGHT // 2]
facing_angle = 0
target_angle = 0
current_speed = 0
target_speed = 0
speed_change_rate = 0
food_positions = []

# ----------------------------
# 뇌 객체 생성 및 초기 자극
# ----------------------------
brain = Brain()
brain.setup()
brain.RandExcite()

# 뇌 업데이트 타이머 (JavaScript는 500ms마다 업데이트)
brain_update_interval = 500  # milliseconds
last_brain_update = 0

# 뉴런 자극 리셋 타이머 (JavaScript는 2000ms 후 리셋)
neuron_stimulation_reset_time = 2000  # milliseconds
last_touch_time = 0
last_food_sense_time = 0

# 음식 감지 거리 설정
FOOD_SENSE_DISTANCE = 200  # 픽셀 (원래 50에서 200으로 증가)
FOOD_EAT_DISTANCE = 20     # 픽셀 (먹는 거리)

# ----------------------------
# k 값 관련 변수 (배고픔 수치)
# ----------------------------
k_value = 0.5  # 초기값 0.5
start_time = pygame.time.get_ticks()  # 시작 시간 기록
K_INCREASE_INTERVAL = 1000  # 1초 = 1000 밀리초
K_INCREASE_AMOUNT = 0.01  # 1초마다 0.01씩 증가
K_DECREASE_ON_EAT = 0.1  # 먹이를 먹으면 0.1씩 감소

# ----------------------------
# 디버깅 모드
# ----------------------------
debug_mode = False  # False = 일반 모드, True = 디버깅 모드

# ----------------------------
# 온도 시스템
# ----------------------------
# 벌레가 선호하는 온도 (8~25도 범위에서 랜덤)
preferred_temperature = random.uniform(8.0, 25.0)

# 온도 맵 (각 픽셀의 온도 저장)
# 기본 온도는 20도
temperature_map = {}  # {(x, y): temperature}
DEFAULT_TEMPERATURE = 20.0
TEMPERATURE_MIN = -40.0
TEMPERATURE_MAX = 80.0

# 브러쉬 설정
brush_mode = 'heat'  # 'heat', 'cool', or 'erase'
brush_size = 50  # 브러쉬 반경
BRUSH_SIZE_MIN = 20
BRUSH_SIZE_MAX = 150
BRUSH_SIZE_STEP = 10
TEMPERATURE_BRUSH_STEP = 5.0  # 브러쉬로 변화시킬 온도

# 온도 스케일 (표시할 온도 값들)
temperature_scale = 5.0  # 한 칸당 5도씩 변화

# 온도 반응 상태 (디버깅용)
current_temp_at_worm = DEFAULT_TEMPERATURE
temp_reaction = "중립"  # "만족", "중립", "회피"

# 선호 온도 입력 모드
input_mode = False
input_text = ""

# 마우스 클릭 상태
mouse_pressed = False

# 키보드 상태 추적
keys_pressed = set()

# ----------------------------
# IK(벌레 본체) 관련 클래스
# ----------------------------
class InverseKinematicsSegment:
    def __init__(self, length, head_point, tail_point):
        self.length = length
        self.head_point = head_point
        self.tail_point = tail_point

    def update(self):
        dx = self.head_point[0] - self.tail_point[0]
        dy = self.head_point[1] - self.tail_point[1]
        distance = math.sqrt(dx * dx + dy * dy) if (dx != 0 or dy != 0) else 1
        force = 0.5 - (self.length / distance) * 0.5
        elasticity = 0.998
        force *= 0.99
        fx = force * dx
        fy = force * dy
        self.tail_point[0] += fx * elasticity * 2.0 * GAME_SPEED
        self.tail_point[1] += fy * elasticity * 2.0 * GAME_SPEED
        self.head_point[0] -= fx * (1.0 - elasticity) * 2.0 * GAME_SPEED
        self.head_point[1] -= fy * (1.0 - elasticity) * 2.0 * GAME_SPEED

class InverseKinematicsChain:
    def __init__(self, number_of_segments, segment_length):
        self.segments = []
        current_point = [random.randint(0, WINDOW_WIDTH // 2), random.randint(0, WINDOW_HEIGHT)]
        for _ in range(number_of_segments):
            head = current_point[:]
            tail = [head[0] + segment_length, head[1] + segment_length]
            self.segments.append(InverseKinematicsSegment(segment_length, head, tail))
            current_point = tail

    def update(self, target_point):
        self.segments[0].head_point = target_point[:]
        for segment in self.segments:
            segment.update()

worm_chain = InverseKinematicsChain(200, 1)

# ----------------------------
# 온도 관련 함수
# ----------------------------
def get_temperature_at_position(x, y):
    """특정 위치의 온도 반환"""
    # 주변 온도 소스들의 영향을 계산
    if len(temperature_map) == 0:
        return DEFAULT_TEMPERATURE
    
    # 가장 가까운 온도 포인트 찾기
    min_distance = float('inf')
    nearest_temp = DEFAULT_TEMPERATURE
    
    for (tx, ty), temp in temperature_map.items():
        distance = math.sqrt((x - tx)**2 + (y - ty)**2)
        # 브러쉬 크기 내에 있으면 해당 온도 적용
        if distance < brush_size:
            # 거리에 따라 온도 보간
            weight = 1 - (distance / brush_size)
            if distance < min_distance:
                min_distance = distance
                nearest_temp = DEFAULT_TEMPERATURE + (temp - DEFAULT_TEMPERATURE) * weight
    
    return nearest_temp if min_distance < brush_size else DEFAULT_TEMPERATURE

def apply_temperature_brush(x, y, mode):
    """브러쉬로 온도 적용"""
    if mode == 'erase':
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
        step = 10  # 온도 맵 해상도
        for dx in range(-brush_size, brush_size, step):
            for dy in range(-brush_size, brush_size, step):
                px, py = x + dx, y + dy
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance <= brush_size:
                    current_temp = temperature_map.get((px, py), DEFAULT_TEMPERATURE)
                    
                    if mode == 'heat':
                        new_temp = min(current_temp + temperature_scale, TEMPERATURE_MAX)
                    else:  # cool
                        new_temp = max(current_temp - temperature_scale, TEMPERATURE_MIN)
                    
                    temperature_map[(px, py)] = new_temp

def draw_temperature_map():
    """온도 맵 시각화"""
    if not debug_mode or len(temperature_map) == 0:
        return
    
    # 온도 맵을 반투명 오버레이로 표시
    temp_surface = pygame.Surface((WINDOW_WIDTH - NEURON_PANEL_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    font = pygame.font.SysFont("malgungothic,arial", 10)
    
    # 온도 포인트를 그리드로 그룹화
    temp_grid = {}
    grid_size = 30  # 그리드 크기
    
    for (x, y), temp in temperature_map.items():
        if 0 <= x < WINDOW_WIDTH - NEURON_PANEL_WIDTH and 0 <= y < WINDOW_HEIGHT:
            grid_x = int(x / grid_size) * grid_size
            grid_y = int(y / grid_size) * grid_size
            
            # 그리드 셀의 평균 온도 계산
            if (grid_x, grid_y) not in temp_grid:
                temp_grid[(grid_x, grid_y)] = []
            temp_grid[(grid_x, grid_y)].append(temp)
    
    # 그리드 셀별로 온도 표시
    for (grid_x, grid_y), temps in temp_grid.items():
        avg_temp = sum(temps) / len(temps)
        
        # 온도에 따라 색상 결정
        # 기본 온도(20도)를 중간으로 설정
        # -100 ~ 20: 파랑 -> 흰색
        # 20 ~ 100: 흰색 -> 빨강
        if avg_temp < DEFAULT_TEMPERATURE:
            # 차가움: 파랑 -> 흰색
            temp_ratio = (avg_temp - TEMPERATURE_MIN) / (DEFAULT_TEMPERATURE - TEMPERATURE_MIN)
            temp_ratio = max(0, min(1, temp_ratio))  # 0~1 사이로 제한
            r = int(255 * temp_ratio)
            g = int(255 * temp_ratio)
            b = 255
        else:
            # 뜨거움: 흰색 -> 빨강
            temp_ratio = (avg_temp - DEFAULT_TEMPERATURE) / (TEMPERATURE_MAX - DEFAULT_TEMPERATURE)
            temp_ratio = max(0, min(1, temp_ratio))  # 0~1 사이로 제한
            r = 255
            g = int(255 * (1 - temp_ratio))
            b = int(255 * (1 - temp_ratio))
        
        # 반투명 사각형 그리기
        pygame.draw.rect(temp_surface, (r, g, b, 80), 
                        (grid_x, grid_y, grid_size, grid_size))
        
        # 온도 텍스트 표시 (흰색)
        temp_text = font.render(f"{int(avg_temp)}°", True, (255, 255, 255))
        temp_surface.blit(temp_text, (grid_x + 3, grid_y + 8))
    
    screen.blit(temp_surface, (0, 0))

def draw_brush_cursor(pos):
    """브러쉬 커서 표시"""
    if not debug_mode:
        return
    
    x, y = pos
    if x >= WINDOW_WIDTH - NEURON_PANEL_WIDTH:
        return
    
    # 브러쉬 크기 표시
    if brush_mode == 'heat':
        color = (255, 100, 100, 100)  # 빨강 (뜨겁게)
    elif brush_mode == 'cool':
        color = (100, 100, 255, 100)  # 파랑 (차갑게)
    else:  # erase
        color = (150, 150, 150, 100)  # 회색 (지우기)
    
    brush_surface = pygame.Surface((brush_size * 2, brush_size * 2), pygame.SRCALPHA)
    pygame.draw.circle(brush_surface, color, (brush_size, brush_size), brush_size, 2)
    screen.blit(brush_surface, (x - brush_size, y - brush_size))


# ----------------------------
# 먹이 관련 함수
# ----------------------------
def add_food(position):
    food_positions.append(position)

def draw_food():
    for f in food_positions:
        pygame.draw.circle(screen, (251, 192, 45), f, 10)

# ----------------------------
# 디버깅 모드 표시
# ----------------------------
def draw_debug_info():
    if debug_mode:
        # 벌레 머리 기준 먹이 탐지 범위 (반투명 원)
        debug_surface = pygame.Surface((FOOD_SENSE_DISTANCE * 2, FOOD_SENSE_DISTANCE * 2), pygame.SRCALPHA)
        pygame.draw.circle(debug_surface, (100, 255, 100, 50), (FOOD_SENSE_DISTANCE, FOOD_SENSE_DISTANCE), FOOD_SENSE_DISTANCE)
        screen.blit(debug_surface, (target_position[0] - FOOD_SENSE_DISTANCE, target_position[1] - FOOD_SENSE_DISTANCE))
        
        # 먹이 먹는 범위 (작은 반투명 원)
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

# ----------------------------
# 벌레 그리기 함수
# ----------------------------
def draw_worm():
    body_segment_width = 20
    body_segment_count = 20
    frame_interval = 6 // GAME_SPEED

    if not hasattr(draw_worm, "head_path"):
        draw_worm.head_path = []

    draw_worm.head_path.insert(0, (target_position[0], target_position[1], facing_angle))
    max_path_length = body_segment_count * frame_interval
    if len(draw_worm.head_path) > max_path_length:
        draw_worm.head_path = draw_worm.head_path[:max_path_length]

    segment_points = []
    for i in range(body_segment_count):
        index = i * frame_interval
        if index < len(draw_worm.head_path):
            x, y, _ = draw_worm.head_path[index]
        else:
            x, y, _ = draw_worm.head_path[-1]
        segment_points.append((x, y))

    for i in range(len(segment_points) - 1):
        pygame.draw.line(screen, (255, 255, 255), segment_points[i], segment_points[i + 1], body_segment_width)

    for p in segment_points:
        pygame.draw.circle(screen, (255, 255, 255), p, body_segment_width // 2, 0)

# ----------------------------
# 뉴런 활성화 시각화 - 302개 뉴런만 표시 (근육 제외)
# ----------------------------
def draw_brain_activity(brain, surface, start_x, start_y, width, height):
    # 한글 폰트 설정 (Windows 기본 한글 폰트)
    font = pygame.font.SysFont("malgungothic,arial", 16)
    neuron_name_font = pygame.font.SysFont("malgungothic,arial", 9)  # 뉴런 이름용 작은 폰트
    # PostSynaptic에서 근육을 제외한 뉴런만 필터링
    muscle_prefixes = ['MDL', 'MDR', 'MVL', 'MVR']
    neurons = sorted([n for n in brain.PostSynaptic.keys() 
                     if not any(n.startswith(prefix) for prefix in muscle_prefixes)])
    total_neurons = len(neurons)

    max_rows = 20
    rows = min(max_rows, total_neurons)
    cols = math.ceil(total_neurons / rows)
    margin = 22.5
    circle_radius = 9  # 뉴런 원 크기 증가
    
    # 뉴런 표시를 오른쪽으로 이동 (왼쪽에 디버깅 정보 공간 확보)
    neuron_offset_x = 200  # 왼쪽에서 200픽셀 떨어진 곳부터 시작

    pygame.draw.rect(surface, (18, 18, 20), (start_x, start_y, width, height))
    
    current_y = start_y + 6
    
    # 디버깅 모드일 때만 표시
    if debug_mode:
        title_surf = font.render(f"C. elegans Connectome - {total_neurons} Neurons", True, (230, 230, 230))
        surface.blit(title_surf, (start_x + 8, current_y))
        current_y += 16
        
        thresh_surf = font.render(f"FireThreshold: {brain.FireThreshold}", True, (200, 200, 200))
        surface.blit(thresh_surf, (start_x + 8, current_y))
        current_y += 16
        
        # 배고픔 수치 표시
        k_surf = font.render(f"배고픔 (k): {k_value:.2f}", True, (100, 255, 100))
        surface.blit(k_surf, (start_x + 8, current_y))
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
        current_temp_surf = font.render(f"벌레 위치 온도: {current_temp_at_worm:.1f}°C", True, (255, 200, 100))
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
        temp_diff = abs(current_temp_at_worm - preferred_temperature)
        diff_surf = font.render(f"온도 차이: {temp_diff:.1f}°C", True, (200, 200, 200))
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
        
        brush_mode_text = {'heat': '가열', 'cool': '냉각', 'erase': '지우기'}[brush_mode]
        brush_color_map = {'heat': (255, 100, 100), 'cool': (100, 100, 255), 'erase': (150, 150, 150)}
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
    
    # 모드 표시 (항상 표시)
    if debug_mode:
        mode_text = "디버깅 모드 (1: 일반, 2: 디버깅, A/S/D: 브러쉬, 드래그: 페인트)"
    else:
        mode_text = "일반 모드 (1: 일반, 2: 디버깅, 클릭: 먹이)"
    mode_surf = font.render(mode_text, True, (255, 200, 100))
    surface.blit(mode_surf, (start_x + 8, current_y))

    # 뉴런을 오른쪽 하단에 배치
    neuron_start_y = height - (rows * (2 * circle_radius + margin)) - margin
    for i, neuron in enumerate(neurons):
        row = i % rows
        col = i // rows
        cx = start_x + neuron_offset_x + margin + col * (2 * circle_radius + margin)
        cy = start_y + neuron_start_y + row * (2 * circle_radius + margin)

        activity = brain.PostSynaptic[neuron][brain.CurrentSignalIntensityIndex]
        if activity > brain.FireThreshold:
            color = (255, 80, 80)
        elif activity > brain.FireThreshold * 0.5:
            color = (80, 220, 80)
        elif activity > 0:
            color = (80, 120, 220)
        else:
            color = (80, 80, 80)

        pygame.draw.circle(surface, color, (cx, cy), circle_radius)
        name_surf = neuron_name_font.render(neuron, True, (230, 230, 230))
        surface.blit(name_surf, (cx - name_surf.get_width() // 2, cy - circle_radius - 12))

# ----------------------------
# 뇌 상태 업데이트
# ----------------------------
def update_brain():
    global target_angle, target_speed, speed_change_rate
    global current_temp_at_worm, temp_reaction
    
    # 벌레 위치의 온도 확인
    worm_temp = get_temperature_at_position(target_position[0], target_position[1])
    current_temp_at_worm = worm_temp
    temp_diff = abs(worm_temp - preferred_temperature)
    
    # AFD 뉴런이 있는지 확인하고 자극
    if 'AFDL' in brain.PostSynaptic:
        if temp_diff > 5.0:
            # 온도 차이가 크면 강하게 자극 (회피)
            brain.PostSynaptic['AFDL'][brain.NextSignalIntensityIndex] += 10
            if 'AFDR' in brain.PostSynaptic:
                brain.PostSynaptic['AFDR'][brain.NextSignalIntensityIndex] += 10
            temp_reaction = "회피"
        elif temp_diff < 2.0:
            # 선호 온도에 가까우면 약하게 자극 (만족)
            brain.PostSynaptic['AFDL'][brain.NextSignalIntensityIndex] += 2
            if 'AFDR' in brain.PostSynaptic:
                brain.PostSynaptic['AFDR'][brain.NextSignalIntensityIndex] += 2
            temp_reaction = "만족"
        else:
            temp_reaction = "중립"
    
    brain.update()
    scaling_factor = 20
    new_angle_offset = (brain.AccumulatedLeftMusclesSignal - brain.AccumulatedRightMusclesSignal) / scaling_factor
    # A: 기본 이동 각도 (뇌의 신호에 따른)
    brain_target_angle = facing_angle + new_angle_offset * math.pi
    target_angle = brain_target_angle  # 일단 뇌의 신호로 설정 (먹이가 있으면 update()에서 수정됨)
    target_speed = ((abs(brain.AccumulatedLeftMusclesSignal) + abs(brain.AccumulatedRightMusclesSignal)) / (scaling_factor * 5)) * GAME_SPEED
    speed_change_rate = ((target_speed - current_speed) / (scaling_factor * 1.5)) * GAME_SPEED

# ----------------------------
# k 값 업데이트 (배고픔 증가)
# ----------------------------
def update_k_value():
    global k_value
    current_time = pygame.time.get_ticks()
    elapsed_time = current_time - start_time
    # 경과 시간에 따라 k 값 계산 (1초마다 0.01씩 증가)
    seconds_passed = elapsed_time // K_INCREASE_INTERVAL
    k_value = min(1.0, 0.5 + seconds_passed * K_INCREASE_AMOUNT)

# ----------------------------
# 배고픔 감소 (먹이를 먹었을 때)
# ----------------------------
def decrease_hunger():
    global k_value, start_time
    k_value = max(0.0, k_value - K_DECREASE_ON_EAT)
    # 시작 시간을 재조정하여 감소된 k 값을 반영
    current_time = pygame.time.get_ticks()
    # k_value = 0.5 + seconds_passed * 0.01 에서 역산
    # seconds_passed = (k_value - 0.5) / 0.01
    if k_value >= 0.5:
        seconds_passed = (k_value - 0.5) / K_INCREASE_AMOUNT
        start_time = current_time - int(seconds_passed * K_INCREASE_INTERVAL)
    else:
        # k_value가 0.5 미만이면 시작 시간을 미래로 설정
        seconds_to_reach_05 = (0.5 - k_value) / K_INCREASE_AMOUNT
        start_time = current_time + int(seconds_to_reach_05 * K_INCREASE_INTERVAL)

# ----------------------------
# 벌레 물리/이동 업데이트
# ----------------------------
def update():
    global current_speed, facing_angle, target_position, last_touch_time, last_food_sense_time, target_angle
    current_speed += speed_change_rate

    # A: 기본 이동 각도 (target_angle은 update_brain()에서 이미 설정됨)
    brain_target_angle = target_angle
    
    # B: 먹이를 향한 이동 각도
    food_target_angle = target_angle  # 기본값은 뇌의 각도
    
    # 먹이를 향해 이동: 가장 가까운 먹이 찾기
    if len(food_positions) > 0:
        closest_food = None
        min_distance = float('inf')
        
        for food in food_positions:
            distance = math.hypot(target_position[0] - food[0], target_position[1] - food[1])
            if distance < min_distance:
                min_distance = distance
                closest_food = food
        
        # 먹이가 감지 범위 내에 있으면 먹이 쪽 방향 계산
        if closest_food and min_distance <= FOOD_SENSE_DISTANCE:
            # 먹이 방향 계산
            food_dx = closest_food[0] - target_position[0]
            food_dy = closest_food[1] - target_position[1]
            food_target_angle = math.atan2(-food_dy, food_dx)  # y축이 반전되어 있어서 음수 적용
            
            # 전체 AI = (1-k)A + kB
            # A = 기본 이동 기능 (뇌의 신호)
            # B = 먹이쪽으로 이동하는 기능
            target_angle = (1 - k_value) * brain_target_angle + k_value * food_target_angle

    angle_difference = facing_angle - target_angle
    if abs(angle_difference) > math.pi:
        if facing_angle > target_angle:
            angle_difference = -1 * (2 * math.pi - facing_angle + target_angle)
        else:
            angle_difference = 2 * math.pi - target_angle + facing_angle

    if angle_difference > 0:
        facing_angle -= 0.1 * GAME_SPEED
    elif angle_difference < 0:
        facing_angle += 0.1 * GAME_SPEED

    target_position[0] += math.cos(facing_angle) * current_speed * GAME_SPEED
    target_position[1] -= math.sin(facing_angle) * current_speed * GAME_SPEED

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

    for f in food_positions[:]:
        distance = math.hypot(target_position[0] - f[0], target_position[1] - f[1])
        if distance <= FOOD_SENSE_DISTANCE:
            brain.IsStimulatedFoodSenseNeurons = True
            last_food_sense_time = pygame.time.get_ticks()
            if distance <= FOOD_EAT_DISTANCE:
                food_positions.remove(f)
                # 먹이를 먹으면 배고픔 감소
                decrease_hunger()

    worm_chain.update(target_position)

# ----------------------------
# 메인 루프
# ----------------------------
while True:
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if mx < WINDOW_WIDTH - NEURON_PANEL_WIDTH:
                if not debug_mode:
                    # 일반 모드에서만 먹이 추가
                    add_food([mx, my])
                elif debug_mode and event.button == 1:
                    # 디버깅 모드에서 왼쪽 마우스 버튼으로 온도 조절
                    mouse_pressed = True
                    apply_temperature_brush(mx, my, brush_mode)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                mouse_pressed = False
        elif event.type == pygame.KEYDOWN:
            if input_mode:
                # 선호 온도 입력 모드
                if event.key == pygame.K_RETURN:
                    # Enter 키: 입력 완료
                    try:
                        new_temp = float(input_text)
                        if 8.0 <= new_temp <= 25.0:
                            preferred_temperature = new_temp
                        input_text = ""
                        input_mode = False
                    except ValueError:
                        input_text = ""
                        input_mode = False
                elif event.key == pygame.K_ESCAPE:
                    # ESC 키: 입력 취소
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
                # 일반 키 입력
                if event.key == pygame.K_1:
                    debug_mode = False  # 일반 모드
                elif event.key == pygame.K_2:
                    debug_mode = True  # 디버깅 모드
                elif event.key == pygame.K_p and debug_mode:
                    # P 키: 선호 온도 설정 모드
                    input_mode = True
                    input_text = ""
                elif event.key == pygame.K_a and debug_mode:
                    brush_mode = 'heat'  # 온도 높이기 브러쉬
                elif event.key == pygame.K_s and debug_mode:
                    brush_mode = 'cool'  # 온도 낮추기 브러쉬
                elif event.key == pygame.K_d and debug_mode:
                    brush_mode = 'erase'  # 온도 지우기 브러쉬
                elif event.key == pygame.K_UP and debug_mode:
                    brush_size = min(brush_size + 10, BRUSH_SIZE_MAX)  # 브러쉬 크기 증가
                elif event.key == pygame.K_DOWN and debug_mode:
                    brush_size = max(brush_size - 10, BRUSH_SIZE_MIN)  # 브러쉬 크기 감소
                elif event.key == pygame.K_LEFT and debug_mode:
                    temperature_scale = max(temperature_scale - 1.0, 1.0)  # 온도 스케일 감소
                elif event.key == pygame.K_RIGHT and debug_mode:
                    temperature_scale = min(temperature_scale + 1.0, 60.0)  # 온도 스케일 증가
    
    # 마우스를 누르고 있을 때 드래그로 온도 조절
    if debug_mode and mouse_pressed:
        mx, my = pygame.mouse.get_pos()
        if mx < WINDOW_WIDTH - NEURON_PANEL_WIDTH:
            apply_temperature_brush(mx, my, brush_mode)

    screen.fill((0, 0, 0))
    
    # k 값 업데이트
    update_k_value()
    
    # JavaScript처럼 500ms마다 뇌 업데이트
    if current_time - last_brain_update >= brain_update_interval:
        update_brain()
        last_brain_update = current_time
    
    update()
    draw_temperature_map()  # 온도 맵 시각화
    draw_food()
    draw_worm()
    draw_debug_info()  # 디버깅 모드 정보 표시
    draw_brain_activity(brain, screen, WINDOW_WIDTH - NEURON_PANEL_WIDTH, 0, NEURON_PANEL_WIDTH, WINDOW_HEIGHT)
    
    # 디버깅 모드에서 브러쉬 커서 표시
    if debug_mode:
        draw_brush_cursor(pygame.mouse.get_pos())
    
    # 선호 온도 입력 모드 표시
    if input_mode:
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
    clock.tick(60 * GAME_SPEED)

    # JavaScript처럼 2초 후에 뉴런 자극 리셋
    brain.IsStimulatedHungerNeurons = True
    
    # 터치 자극은 2초 후 리셋
    if last_touch_time > 0 and current_time - last_touch_time >= neuron_stimulation_reset_time:
        brain.IsStimulatedNoseTouchNeurons = False
    
    # 음식 감지 자극은 2초 후 리셋
    if last_food_sense_time > 0 and current_time - last_food_sense_time >= neuron_stimulation_reset_time:
        brain.IsStimulatedFoodSenseNeurons = False
