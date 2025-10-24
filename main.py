import pygame
import sys
import random
import math
from brain import Brain

# ----------------------------
# 초기화 및 창 설정
# ----------------------------
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1600, 800
NEURON_PANEL_WIDTH = 800
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
    font = pygame.font.SysFont("malgungothic,arial", 12)
    # PostSynaptic에서 근육을 제외한 뉴런만 필터링
    muscle_prefixes = ['MDL', 'MDR', 'MVL', 'MVR']
    neurons = sorted([n for n in brain.PostSynaptic.keys() 
                     if not any(n.startswith(prefix) for prefix in muscle_prefixes)])
    total_neurons = len(neurons)

    max_rows = 20
    rows = min(max_rows, total_neurons)
    cols = math.ceil(total_neurons / rows)
    margin = 20
    circle_radius = min(8.5, (width - margin * 2) // (cols * 2))

    pygame.draw.rect(surface, (18, 18, 20), (start_x, start_y, width, height))
    title_surf = font.render(f"C. elegans Connectome - {total_neurons} Neurons", True, (230, 230, 230))
    surface.blit(title_surf, (start_x + 8, start_y + 6))
    thresh_surf = font.render(f"FireThreshold: {brain.FireThreshold}", True, (200, 200, 200))
    surface.blit(thresh_surf, (start_x + 8, start_y + 22))
    
    # 배고픔 수치 표시
    k_surf = font.render(f"배고픔 (k): {k_value:.2f}", True, (100, 255, 100))
    surface.blit(k_surf, (start_x + 8, start_y + 38))
    
    # 모드 표시
    mode_text = "디버깅 모드 (Press 1: 일반, 2: 디버깅)" if debug_mode else "일반 모드 (Press 1: 일반, 2: 디버깅)"
    mode_surf = font.render(mode_text, True, (255, 200, 100))
    surface.blit(mode_surf, (start_x + 8, start_y + 54))

    offset_y = start_y + 85  # 뉴런 표시 시작 위치를 더 아래로 (모드 표시 추가로 인해)
    for i, neuron in enumerate(neurons):
        row = i % rows
        col = i // rows
        cx = start_x + margin + col * (2 * circle_radius + margin)
        cy = offset_y + row * (2 * circle_radius + margin)

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
        name_surf = font.render(neuron, True, (230, 230, 230))
        surface.blit(name_surf, (cx - name_surf.get_width() // 2, cy - circle_radius - 12))

# ----------------------------
# 뇌 상태 업데이트
# ----------------------------
def update_brain():
    global target_angle, target_speed, speed_change_rate
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
                add_food([mx, my])
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                debug_mode = False  # 일반 모드
            elif event.key == pygame.K_2:
                debug_mode = True  # 디버깅 모드

    screen.fill((0, 0, 0))
    
    # k 값 업데이트
    update_k_value()
    
    # JavaScript처럼 500ms마다 뇌 업데이트
    if current_time - last_brain_update >= brain_update_interval:
        update_brain()
        last_brain_update = current_time
    
    update()
    draw_food()
    draw_worm()
    draw_debug_info()  # 디버깅 모드 정보 표시
    draw_brain_activity(brain, screen, WINDOW_WIDTH - NEURON_PANEL_WIDTH, 0, NEURON_PANEL_WIDTH, WINDOW_HEIGHT)

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
