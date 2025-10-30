"""
UI 렌더링 관련 함수
"""
import pygame
import math
from config import *


def draw_brain_activity(brain, surface, start_x, start_y, width, height, 
                        worm, food_manager, temperature_system, debug_mode):
    """뉴런 활성화 및 디버깅 정보 시각화"""
    # 폰트 설정
    font = pygame.font.SysFont("malgungothic,arial", FONT_DEBUG)
    neuron_name_font = pygame.font.SysFont("malgungothic,arial", FONT_NEURON_NAME)
    
    # 근육을 제외한 뉴런만 필터링
    muscle_prefixes = ['MDL', 'MDR', 'MVL', 'MVR']
    neurons = sorted([n for n in brain.PostSynaptic.keys() 
                     if not any(n.startswith(prefix) for prefix in muscle_prefixes)])
    total_neurons = len(neurons)

    rows = min(NEURON_MAX_ROWS, total_neurons)
    cols = math.ceil(total_neurons / rows)
    
    pygame.draw.rect(surface, COLOR_BACKGROUND, (start_x, start_y, width, height))
    
    current_y = start_y + 6
    
    # 디버깅 모드일 때만 표시
    if debug_mode:
        # 제목
        title_surf = font.render(f"C. elegans Connectome - {total_neurons} Neurons", True, COLOR_TEXT_LIGHT_GRAY)
        surface.blit(title_surf, (start_x + 8, current_y))
        current_y += 16
        
        # FireThreshold
        thresh_surf = font.render(f"FireThreshold: {brain.FireThreshold}", True, COLOR_TEXT_GRAY)
        surface.blit(thresh_surf, (start_x + 8, current_y))
        current_y += 16
        
        # 배고픔 수치
        k_surf = font.render(f"배고픔 (k): {worm.k_value:.2f}", True, COLOR_TEMP_SATISFIED)
        surface.blit(k_surf, (start_x + 8, current_y))
        current_y += 16
        
        # 이동 방향 벡터
        direction_x = math.cos(worm.facing_angle)
        direction_y = -math.sin(worm.facing_angle)
        dir_surf = font.render(f"방향 벡터: ({direction_x:.2f}, {direction_y:.2f})", True, (150, 200, 255))
        surface.blit(dir_surf, (start_x + 8, current_y))
        current_y += 16
        
        # 먹이 정보
        range_surf = font.render(f"먹이 먹는 범위: {FOOD_EAT_DISTANCE}px", True, (255, 150, 150))
        surface.blit(range_surf, (start_x + 8, current_y))
        current_y += 16
        
        sense_surf = font.render(f"먹이 감지 범위: {FOOD_SENSE_DISTANCE}px", True, (150, 255, 150))
        surface.blit(sense_surf, (start_x + 8, current_y))
        current_y += 16
        
        # 온도 정보
        current_y += 8
        temp_title_surf = font.render("=== 온도 정보 ===", True, (255, 255, 150))
        surface.blit(temp_title_surf, (start_x + 8, current_y))
        current_y += 16
        
        current_temp_surf = font.render(f"벌레 위치 온도: {temperature_system.current_temp_at_worm:.1f}°C", 
                                       True, (255, 200, 100))
        surface.blit(current_temp_surf, (start_x + 8, current_y))
        current_y += 16
        
        pref_temp_surf = font.render(f"선호 온도: {temperature_system.preferred_temperature:.1f}°C", 
                                     True, COLOR_TEMP_SATISFIED)
        surface.blit(pref_temp_surf, (start_x + 8, current_y))
        current_y += 16
        
        pref_hint_surf = font.render("(P키: 선호 온도 변경)", True, (150, 200, 150))
        surface.blit(pref_hint_surf, (start_x + 8, current_y))
        current_y += 16
        
        temp_diff = abs(temperature_system.current_temp_at_worm - temperature_system.preferred_temperature)
        diff_surf = font.render(f"온도 차이: {temp_diff:.1f}°C", True, COLOR_TEXT_GRAY)
        surface.blit(diff_surf, (start_x + 8, current_y))
        current_y += 16
        
        # 온도 반응
        reaction_colors = {
            "만족": COLOR_TEMP_SATISFIED,
            "중립": COLOR_TEMP_NEUTRAL,
            "회피": COLOR_TEMP_AVOID
        }
        reaction_color = reaction_colors.get(temperature_system.temp_reaction, COLOR_TEXT_GRAY)
        reaction_surf = font.render(f"온도 반응: {temperature_system.temp_reaction}", True, reaction_color)
        surface.blit(reaction_surf, (start_x + 8, current_y))
        current_y += 16
        
        current_y += 8
        
        # 브러쉬 정보
        brush_title_surf = font.render("=== 브러쉬 ===", True, (200, 200, 255))
        surface.blit(brush_title_surf, (start_x + 8, current_y))
        current_y += 16
        
        brush_mode_text = {'heat': '가열', 'cool': '냉각', 'erase': '지우기'}[temperature_system.brush_mode]
        brush_color_map = {
            'heat': COLOR_BRUSH_HEAT,
            'cool': COLOR_BRUSH_COOL,
            'erase': COLOR_BRUSH_ERASE
        }
        brush_color = brush_color_map[temperature_system.brush_mode]
        brush_mode_surf = font.render(f"모드: {brush_mode_text} (A/S/D)", True, brush_color)
        surface.blit(brush_mode_surf, (start_x + 8, current_y))
        current_y += 16
        
        brush_size_surf = font.render(f"크기: {temperature_system.brush_size}px (UP/DOWN)", 
                                      True, (180, 180, 180))
        surface.blit(brush_size_surf, (start_x + 8, current_y))
        current_y += 16
        
        scale_surf = font.render(f"스케일: ±{temperature_system.temperature_scale:.1f}° (LEFT/RIGHT)", 
                                True, (180, 180, 180))
        surface.blit(scale_surf, (start_x + 8, current_y))
        current_y += 16
        
        temp_points_surf = font.render(f"온도 포인트: {len(temperature_system.temperature_map)}", 
                                       True, (150, 150, 150))
        surface.blit(temp_points_surf, (start_x + 8, current_y))
        current_y += 16
    
    # 모드 표시
    if debug_mode:
        mode_text = "디버깅 모드 (1: 일반, 2: 디버깅, A/S/D: 브러쉬, 드래그: 페인트)"
    else:
        mode_text = "일반 모드 (1: 일반, 2: 디버깅, 클릭: 먹이)"
    mode_surf = font.render(mode_text, True, COLOR_TEXT_YELLOW)
    surface.blit(mode_surf, (start_x + 8, current_y))

    # 뉴런을 오른쪽 하단에 배치
    neuron_start_y = height - (rows * (2 * NEURON_CIRCLE_RADIUS + NEURON_MARGIN)) - NEURON_MARGIN - NEURON_OFFSET_Y_FROM_BOTTOM
    for i, neuron in enumerate(neurons):
        row = i % rows
        col = i // rows
        cx = start_x + NEURON_OFFSET_X + NEURON_MARGIN + col * (2 * NEURON_CIRCLE_RADIUS + NEURON_MARGIN)
        cy = start_y + neuron_start_y + row * (2 * NEURON_CIRCLE_RADIUS + NEURON_MARGIN)

        activity = brain.PostSynaptic[neuron][brain.CurrentSignalIntensityIndex]
        if activity > brain.FireThreshold:
            color = COLOR_NEURON_HIGH
        elif activity > brain.FireThreshold * 0.5:
            color = COLOR_NEURON_MEDIUM
        elif activity > 0:
            color = COLOR_NEURON_LOW
        else:
            color = COLOR_NEURON_INACTIVE

        pygame.draw.circle(surface, color, (cx, cy), NEURON_CIRCLE_RADIUS)
        name_surf = neuron_name_font.render(neuron, True, COLOR_TEXT_LIGHT_GRAY)
        surface.blit(name_surf, (cx - name_surf.get_width() // 2, cy - NEURON_CIRCLE_RADIUS - 12))


def draw_input_mode(surface, input_text):
    """온도 입력 모드 UI 그리기"""
    # 반투명 배경
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(overlay, (0, 0, 0, 180), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
    surface.blit(overlay, (0, 0))
    
    # 입력 창
    input_font = pygame.font.SysFont("malgungothic,arial", FONT_INPUT)
    title_surf = input_font.render(f"선호 온도 설정 ({int(PREFERRED_TEMP_MIN)} ~ {int(PREFERRED_TEMP_MAX)}°C)", 
                                   True, COLOR_TEXT_WHITE)
    title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
    surface.blit(title_surf, title_rect)
    
    # 입력 텍스트
    input_display = input_text if input_text else "0"
    input_surf = input_font.render(f"{input_display}°C", True, COLOR_TEXT_INPUT)
    input_rect = input_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
    
    # 입력 박스
    box_width = 200
    box_height = 50
    box_rect = pygame.Rect(WINDOW_WIDTH // 2 - box_width // 2, 
                          WINDOW_HEIGHT // 2 - box_height // 2, 
                          box_width, box_height)
    pygame.draw.rect(surface, (50, 50, 50), box_rect)
    pygame.draw.rect(surface, (100, 100, 100), box_rect, 2)
    
    surface.blit(input_surf, input_rect)
    
    # 안내 문구
    hint_surf = input_font.render("Enter: 확인 | ESC: 취소", True, COLOR_TEXT_GRAY)
    hint_rect = hint_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
    surface.blit(hint_surf, hint_rect)
