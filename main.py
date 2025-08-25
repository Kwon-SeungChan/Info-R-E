import pygame
import sys
import random
import math
import time  # 추가
from brain import Brain
import constants

pygame.init()
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Worm Simulation")

clock = pygame.time.Clock()

target = [WIDTH // 2, HEIGHT // 2]
facing_dir = 0
target_dir = 0
speed = 0
target_speed = 0
speed_change_interval = 0
food = []

brain = Brain()
brain.setup()
brain.RandExcite()

class IKSegment:
    def __init__(self, size, head, tail):
        self.size = size
        self.head = head
        self.tail = tail

    def update(self):
        dx = self.head[0] - self.tail[0]
        dy = self.head[1] - self.tail[1]
        dist = math.sqrt(dx * dx + dy * dy) if (dx != 0 or dy != 0) else 1
        force = 0.5 - (self.size / dist) * 0.5
        strength = 0.998
        force *= 0.99
        fx = force * dx
        fy = force * dy
        self.tail[0] += fx * strength * 2.0
        self.tail[1] += fy * strength * 2.0
        self.head[0] -= fx * (1.0 - strength) * 2.0
        self.head[1] -= fy * (1.0 - strength) * 2.0

class IKChain:
    def __init__(self, size, interval):
        self.links = []
        point = [random.randint(0, WIDTH), random.randint(0, HEIGHT)]
        for _ in range(size):
            head = point[:]
            tail = [head[0] + interval, head[1] + interval]
            self.links.append(IKSegment(interval, head, tail))
            point = tail

    def update(self, target):
        self.links[0].head = target[:]
        for link in self.links:
            link.update()

chain = IKChain(200, 1)

def add_food(pos):
    food.append(pos)

def draw_food():
    for f in food:
        pygame.draw.circle(screen, (251, 192, 45), f, 10)

def draw_worm():
    segment_width = 20
    segment_length = 8
    worm_length = 20  # 20마디
    # 머리의 이동 경로를 저장하는 버퍼
    if not hasattr(draw_worm, "head_path"):
        draw_worm.head_path = []
    # 머리 위치를 버퍼에 추가
    draw_worm.head_path.insert(0, (int(target[0]), int(target[1]), facing_dir))
    # 버퍼 길이 유지 (마디 수 * 간격)
    max_path_len = worm_length * 6  # 각 마디가 충분히 시간차를 두고 이동하도록
    if len(draw_worm.head_path) > max_path_len:
        draw_worm.head_path = draw_worm.head_path[:max_path_len]
    # 각 마디의 위치 계산 (시간차 적용)
    points = []
    for i in range(worm_length):
        idx = i * 6  # 각 마디가 머리의 과거 위치를 따라감 (6프레임 간격)
        if idx < len(draw_worm.head_path):
            x, y, _ = draw_worm.head_path[idx]
        else:
            x, y, _ = draw_worm.head_path[-1]
        points.append((x, y))
    # 마디 연결
    for i in range(len(points)-1):
        pygame.draw.line(screen, (255,255,255), points[i], points[i+1], segment_width)
    # 각 마디에 원으로 표시
    for p in points:
        pygame.draw.circle(screen, (255,255,255), p, segment_width//2, 0)

def update_brain():
    global target_dir, target_speed, speed_change_interval
    brain.update()
    scaling_factor = 20
    new_dir = (brain.AccumulatedLeftMusclesSignal - brain.AccumulatedRightMusclesSignal) / scaling_factor
    target_dir = facing_dir + new_dir * math.pi
    target_speed = (abs(brain.AccumulatedLeftMusclesSignal) + abs(brain.AccumulatedRightMusclesSignal)) / (scaling_factor * 5)
    speed_change_interval = (target_speed - speed) / (scaling_factor * 1.5)

def update():
    global speed, facing_dir, target
    speed += speed_change_interval
    angle_diff = facing_dir - target_dir
    if abs(angle_diff) > math.pi:
        if facing_dir > target_dir:
            angle_diff = -1 * (2 * math.pi - facing_dir + target_dir)
        else:
            angle_diff = 2 * math.pi - target_dir + facing_dir
    if angle_diff > 0:
        facing_dir -= 0.1
    elif angle_diff < 0:
        facing_dir += 0.1
    target[0] += math.cos(facing_dir) * speed
    target[1] -= math.sin(facing_dir) * speed
    if target[0] < 0:
        target[0] = 0
        brain.IsStimulatedNoseTouchNeurons = True
    elif target[0] > WIDTH:
        target[0] = WIDTH
        brain.IsStimulatedNoseTouchNeurons = True
    if target[1] < 0:
        target[1] = 0
        brain.IsStimulatedNoseTouchNeurons = True
    elif target[1] > HEIGHT:
        target[1] = HEIGHT
        brain.IsStimulatedNoseTouchNeurons = True
    for f in food[:]:
        dist = math.hypot(target[0] - f[0], target[1] - f[1])
        if dist <= 50:
            brain.IsStimulatedFoodSenseNeurons = True
            if dist <= 20:
                food.remove(f)
    chain.update(target)

reset_timer = 0

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            add_food(list(event.pos))

    screen.fill((0, 0, 0))
    update_brain()
    update()
    draw_food()
    draw_worm()
    pygame.display.flip()
    clock.tick(60)

    # 뉴런 자극 리셋 (2초 후)
    reset_timer += clock.get_time()
    if reset_timer > 2000:
        brain.IsStimulatedHungerNeurons = True
        brain.IsStimulatedNoseTouchNeurons = False
        brain.IsStimulatedFoodSenseNeurons = False
        reset_timer = 0