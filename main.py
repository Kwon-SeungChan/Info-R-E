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
    font = pygame.font.SysFont("Arial", 12)
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

    offset_y = start_y + 50
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
    target_angle = facing_angle + new_angle_offset * math.pi
    target_speed = ((abs(brain.AccumulatedLeftMusclesSignal) + abs(brain.AccumulatedRightMusclesSignal)) / (scaling_factor * 5)) * GAME_SPEED
    speed_change_rate = ((target_speed - current_speed) / (scaling_factor * 1.5)) * GAME_SPEED

# ----------------------------
# 벌레 물리/이동 업데이트
# ----------------------------
def update():
    global current_speed, facing_angle, target_position, last_touch_time, last_food_sense_time
    current_speed += speed_change_rate

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

    screen.fill((0, 0, 0))
    
    # JavaScript처럼 500ms마다 뇌 업데이트
    if current_time - last_brain_update >= brain_update_interval:
        update_brain()
        last_brain_update = current_time
    
    update()
    draw_food()
    draw_worm()
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
