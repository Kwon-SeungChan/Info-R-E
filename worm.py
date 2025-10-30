"""
벌레 관련 클래스 및 함수
"""
import pygame
import math
from config import *


class Worm:
    """벌레 상태 및 움직임을 관리하는 클래스"""
    
    def __init__(self, x, y):
        self.position = [x, y]
        self.facing_angle = 0
        self.target_angle = 0
        self.current_speed = 0
        self.target_speed = 0
        self.speed_change_rate = 0
        
        # 배고픔 시스템
        self.k_value = K_INITIAL_VALUE
        self.start_time = pygame.time.get_ticks()
        
    def update_hunger(self):
        """배고픔 수치 업데이트"""
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.start_time
        
        # 1초마다 k 값 증가
        k_increase = (elapsed_time // K_INCREASE_INTERVAL) * K_INCREASE_AMOUNT
        self.k_value = min(1.0, K_INITIAL_VALUE + k_increase)
    
    def eat_food(self):
        """먹이를 먹었을 때 배고픔 감소"""
        self.k_value = max(0.0, self.k_value - K_DECREASE_ON_EAT)
        self.start_time = pygame.time.get_ticks() - int((self.k_value - K_INITIAL_VALUE) / K_INCREASE_AMOUNT * K_INCREASE_INTERVAL)
    
    def update_position(self, delta_time):
        """위치 업데이트"""
        # 속도 변화 적용
        self.current_speed += self.speed_change_rate * delta_time
        self.current_speed = max(0, min(3, self.current_speed))
        
        # 위치 이동
        self.position[0] += math.cos(self.facing_angle) * self.current_speed * delta_time
        self.position[1] -= math.sin(self.facing_angle) * self.current_speed * delta_time
        
        # 화면 경계 체크
        sim_width = WINDOW_WIDTH - NEURON_PANEL_WIDTH
        if self.position[0] < 20:
            self.position[0] = 20
        elif self.position[0] > sim_width - 20:
            self.position[0] = sim_width - 20
        
        if self.position[1] < 20:
            self.position[1] = 20
        elif self.position[1] > WINDOW_HEIGHT - 20:
            self.position[1] = WINDOW_HEIGHT - 20
    
    def get_segment_points(self):
        """벌레 몸체의 세그먼트 포인트 계산"""
        segment_points = []
        body_length = 80
        num_segments = 15
        body_segment_width = 8
        
        for i in range(num_segments):
            offset = (i / (num_segments - 1) - 0.5) * body_length
            sx = self.position[0] - math.cos(self.facing_angle) * offset
            sy = self.position[1] + math.sin(self.facing_angle) * offset
            segment_points.append((int(sx), int(sy)))
        
        return segment_points, body_segment_width
    
    def draw(self, surface):
        """벌레 그리기"""
        segment_points, body_segment_width = self.get_segment_points()
        
        for p in segment_points:
            pygame.draw.circle(surface, COLOR_WORM_BODY, p, body_segment_width // 2, 0)


class FoodManager:
    """먹이 관리 클래스"""
    
    def __init__(self):
        self.food_positions = []
    
    def add_food(self, x, y):
        """먹이 추가"""
        self.food_positions.append([x, y])
    
    def remove_food(self, index):
        """먹이 제거"""
        if 0 <= index < len(self.food_positions):
            self.food_positions.pop(index)
    
    def find_nearest_food(self, worm_pos):
        """가장 가까운 먹이 찾기"""
        if not self.food_positions:
            return None, None, None
        
        nearest_food = None
        nearest_distance = float('inf')
        nearest_index = -1
        
        for i, food in enumerate(self.food_positions):
            dx = food[0] - worm_pos[0]
            dy = food[1] - worm_pos[1]
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_food = food
                nearest_index = i
        
        return nearest_food, nearest_distance, nearest_index
    
    def draw(self, surface):
        """먹이 그리기"""
        for food in self.food_positions:
            pygame.draw.circle(surface, COLOR_FOOD, (int(food[0]), int(food[1])), 5)
