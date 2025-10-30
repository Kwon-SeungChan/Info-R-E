"""
설정 및 상수 정의
"""
import random

# ----------------------------
# 창 설정
# ----------------------------
WINDOW_WIDTH = 1800
WINDOW_HEIGHT = 900
NEURON_PANEL_WIDTH = 900

# ----------------------------
# 게임 속도
# ----------------------------
GAME_SPEED = 1  # 1.0 = 정상 속도, 0.5 = 절반 속도, 2.0 = 두 배 속도

# ----------------------------
# 뇌 업데이트 설정
# ----------------------------
BRAIN_UPDATE_INTERVAL = 500  # milliseconds
NEURON_STIMULATION_RESET_TIME = 2000  # milliseconds

# ----------------------------
# 먹이 시스템 설정
# ----------------------------
FOOD_SENSE_DISTANCE = 200  # 픽셀
FOOD_EAT_DISTANCE = 20     # 픽셀

# ----------------------------
# 배고픔 시스템 설정
# ----------------------------
K_INITIAL_VALUE = 0.5
K_INCREASE_INTERVAL = 1000  # 1초 = 1000 밀리초
K_INCREASE_AMOUNT = 0.01  # 1초마다 0.01씩 증가
K_DECREASE_ON_EAT = 0.1  # 먹이를 먹으면 0.1씩 감소

# ----------------------------
# 온도 시스템 설정
# ----------------------------
DEFAULT_TEMPERATURE = 20.0
TEMPERATURE_MIN = -40.0
TEMPERATURE_MAX = 80.0
PREFERRED_TEMP_MIN = 8.0
PREFERRED_TEMP_MAX = 25.0

# 브러쉬 설정
BRUSH_SIZE_MIN = 20
BRUSH_SIZE_MAX = 150
BRUSH_SIZE_STEP = 10
BRUSH_INITIAL_SIZE = 50
TEMPERATURE_BRUSH_STEP = 5.0

# 온도 스케일 설정
TEMPERATURE_SCALE_MIN = 1.0
TEMPERATURE_SCALE_MAX = 60.0
TEMPERATURE_SCALE_INITIAL = 5.0

# 온도 그리드 설정
TEMPERATURE_GRID_SIZE = 30

# ----------------------------
# 뉴런 시각화 설정
# ----------------------------
NEURON_MAX_ROWS = 20
NEURON_MARGIN = 22.5
NEURON_CIRCLE_RADIUS = 9
NEURON_OFFSET_X = 200
NEURON_OFFSET_Y_FROM_BOTTOM = 120

# 폰트 설정
FONT_DEBUG = 16
FONT_NEURON_NAME = 9
FONT_INPUT = 24

# ----------------------------
# 색상 설정
# ----------------------------
COLOR_BACKGROUND = (18, 18, 20)
COLOR_WORM_BODY = (255, 255, 255)
COLOR_FOOD = (0, 255, 0)

# 뉴런 활성화 색상
COLOR_NEURON_HIGH = (255, 80, 80)      # 빨간색
COLOR_NEURON_MEDIUM = (80, 220, 80)    # 초록색
COLOR_NEURON_LOW = (80, 120, 220)      # 파란색
COLOR_NEURON_INACTIVE = (80, 80, 80)   # 회색

# UI 색상
COLOR_TEXT_WHITE = (255, 255, 255)
COLOR_TEXT_GRAY = (200, 200, 200)
COLOR_TEXT_LIGHT_GRAY = (230, 230, 230)
COLOR_TEXT_YELLOW = (255, 200, 100)
COLOR_TEXT_INPUT = (255, 255, 100)

# 온도 관련 색상
COLOR_TEMP_SATISFIED = (100, 255, 100)  # 초록색
COLOR_TEMP_NEUTRAL = (200, 200, 200)    # 회색
COLOR_TEMP_AVOID = (255, 100, 100)      # 빨강색

# 브러쉬 색상
COLOR_BRUSH_HEAT = (255, 100, 100)
COLOR_BRUSH_COOL = (100, 100, 255)
COLOR_BRUSH_ERASE = (150, 150, 150)
