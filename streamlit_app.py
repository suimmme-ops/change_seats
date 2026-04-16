import streamlit as st
import pandas as pd
import numpy as np
import random
import math
import re
import io
from itertools import combinations, permutations

# Custom CSS for iOS-style UI
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .card {
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        padding: 20px;
        margin: 10px 0;
        border: 1px solid #e9ecef;
    }
    .step-header {
        background: linear-gradient(135deg, #22714b, #2d8a5f);
        color: white;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
        text-align: center;
        font-weight: 600;
    }
    .btn-primary {
        background-color: #22714b !important;
        border-color: #22714b !important;
        border-radius: 8px;
        font-weight: 500;
    }
    .btn-secondary {
        background-color: #6c757d !important;
        border-color: #6c757d !important;
        border-radius: 8px;
    }
    .stTextInput, .stNumberInput, .stTextArea {
        border-radius: 8px;
        border: 1px solid #ced4da;
    }
    .seat-card {
        background: #fff;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        text-align: center;
        min-height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 500;
        font-size: 14px;
    }
    .group-header {
        font-size: 20px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 15px;
        color: #22714b;
    }
    .front-seat { background-color: #e3f2fd; }
    .back-seat { background-color: #f3e5f5; }
    .warning { color: #dc3545; font-weight: 500; }
    .success { color: #22714b; font-weight: 500; }
    .progress-bar {
        background: #e9ecef;
        border-radius: 10px;
        height: 8px;
        margin: 10px 0;
    }
    .progress-fill {
        background: #22714b;
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# 앱 제목
st.title("🎓 똑똑한 자리 배치 도우미")
st.markdown("초등학교 학급 자리 바꾸기를 쉽고 스마트하게!")

# 세션 상태 초기화
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'students' not in st.session_state:
    st.session_state.students = []
if 'seats' not in st.session_state:
    st.session_state.seats = []
if 'balance_students' not in st.session_state:
    st.session_state.balance_students = []
if 'separation_groups' not in st.session_state:
    st.session_state.separation_groups = []
if 'front_priority' not in st.session_state:
    st.session_state.front_priority = []
if 'back_priority' not in st.session_state:
    st.session_state.back_priority = []
if 'arrangement' not in st.session_state:
    st.session_state.arrangement = {}
if 'seat_layout' not in st.session_state:
    st.session_state.seat_layout = {}

# 유틸리티 함수들
def parse_student_input(text):
    """학생 명단 텍스트 파싱"""
    lines = text.strip().split('\n')
    students = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # 번호, 이름 형식 파싱
        match = re.match(r'^(\d+)\s*[,\-\s]\s*(.+)$', line)
        if match:
            num, name = match.groups()
            students.append({'번호': int(num), '이름': name.strip()})
        else:
            # 이름만 있는 경우
            students.append({'번호': len(students)+1, '이름': line.strip()})
    return pd.DataFrame(students)

def load_csv_file(uploaded_file):
    """CSV 파일 로드 및 파싱"""
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        # 컬럼명 유추
        col_map = {}
        for col in df.columns:
            if '번호' in col or 'num' in col.lower():
                col_map['번호'] = col
            elif '이름' in col or 'name' in col.lower() or '학생' in col:
                col_map['이름'] = col
        
        if '번호' not in col_map:
            df['번호'] = range(1, len(df)+1)
        else:
            df = df.rename(columns={col_map['번호']: '번호'})
        
        if '이름' not in col_map:
            st.error("이름 컬럼을 찾을 수 없습니다.")
            return pd.DataFrame()
        
        df = df.rename(columns={col_map['이름']: '이름'})
        df = df[['번호', '이름']].dropna()
        return df
    except Exception as e:
        st.error(f"CSV 파일 로드 중 오류: {str(e)}")
        return pd.DataFrame()

def build_seat_layout(num_groups, seats_per_group):
    """좌석 구조 생성"""
    seats = []
    group_x = {i: i*10 for i in range(num_groups)}  # 분단 간 거리
    
    for group in range(num_groups):
        rows = math.ceil(seats_per_group[group] / 2)  # 좌우 2열 가정
        seat_count = 0
        for row in range(rows):
            for col in range(2):
                if seat_count >= seats_per_group[group]:
                    break
                seat = {
                    '분단': group + 1,
                    '행': row,
                    '열': col,
                    'x': group_x[group] + col * 2,
                    'y': row,
                    '앞줄': row < 2,  # 앞 2줄
                    '뒷줄': row >= rows - 2,  # 뒤 2줄
                    '좌석번호': len(seats) + 1
                }
                seats.append(seat)
                seat_count += 1
    return seats

def calculate_distance(seat1, seat2):
    """좌석 간 거리 계산"""
    return math.sqrt((seat1['x'] - seat2['x'])**2 + (seat1['y'] - seat2['y'])**2)

def score_arrangement(arrangement, seats, balance_students, separation_groups, front_priority, back_priority):
    """배치 점수 계산"""
    score = 0
    
    # 모둠 균형 배치 점수
    balance_groups = set()
    for student in balance_students:
        if student in arrangement:
            seat = next(s for s in seats if s['좌석번호'] == arrangement[student])
            balance_groups.add(seat['분단'])
    score += len(balance_groups) * 10  # 서로 다른 분단에 배치될수록 점수 +
    
    # 분리 배치 점수
    for group in separation_groups:
        group_seats = [next(s for s in seats if s['좌석번호'] == arrangement[student]) for student in group if student in arrangement]
        if len(group_seats) > 1:
            distances = [calculate_distance(s1, s2) for s1, s2 in combinations(group_seats, 2)]
            score += sum(distances) * 5  # 거리 합 최대화
    
    # 앞줄 우선 점수
    for student in front_priority:
        if student in arrangement:
            seat = next(s for s in seats if s['좌석번호'] == arrangement[student])
            if seat['앞줄']:
                score += 8
    
    # 뒷줄 우선 점수
    for student in back_priority:
        if student in arrangement:
            seat = next(s for s in seats if s['좌석번호'] == arrangement[student])
            if seat['뒷줄']:
                score += 8
    
    return score

def generate_best_arrangement(students, seats, balance_students, separation_groups, front_priority, back_priority, iterations=1000):
    """최적 배치 생성"""
    best_score = -1
    best_arrangement = {}
    
    student_names = [s['이름'] for s in students]
    
    for _ in range(iterations):
        # 랜덤 배치 생성
        shuffled_seats = random.sample(range(1, len(seats)+1), len(student_names))
        arrangement = dict(zip(student_names, shuffled_seats))
        
        # 점수 계산
        score = score_arrangement(arrangement, seats, balance_students, separation_groups, front_priority, back_priority)
        
        if score > best_score:
            best_score = score
            best_arrangement = arrangement.copy()
    
    return best_arrangement

def render_seat_map(arrangement, seats):
    """좌석 배치 시각화"""
    st.markdown("### 📍 자리 배치 결과")
    
    # 분단별 그룹화
    groups = {}
    for seat in seats:
        group = seat['분단']
        if group not in groups:
            groups[group] = []
        groups[group].append(seat)
    
    cols = st.columns(len(groups))
    
    for i, (group, group_seats) in enumerate(groups.items()):
        with cols[i]:
            # 분단 제목을 먼저 표시
            st.markdown(f'<div class="group-header">{group}분단</div>', unsafe_allow_html=True)
            
            # 행별 정렬 (앞줄부터)
            sorted_seats = sorted(group_seats, key=lambda s: (s['행'], s['열']))
            
            # 세로 1렬로 표시
            rows = []
            for seat in sorted_seats:
                student = next((name for name, seat_num in arrangement.items() if seat_num == seat['좌석번호']), "")
                seat_class = "front-seat" if seat['앞줄'] else "back-seat" if seat['뒷줄'] else ""
                rows.append(f'<div class="seat-card {seat_class}">{student}<br/><small>({seat["좌석번호"]}번)</small></div>')
            
            st.markdown(''.join(rows), unsafe_allow_html=True)

# 단계별 UI 함수들
def step_0_welcome():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 👋 환영합니다!")
    st.markdown("우리 반 자리 바꾸기를 시작해 볼까요? 단계별로 안내해 드릴게요.")
    if st.button("시작하기", key="start", help="자리 배치 과정을 시작합니다"):
        st.session_state.step = 1
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def step_1_students():
    st.markdown('<div class="step-header">1단계: 학생 명단 입력</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("학생 명단을 불러와 볼까요?")
    
    input_method = st.radio("입력 방식 선택", ["직접 입력", "CSV 파일 업로드"], key="input_method")
    
    if input_method == "직접 입력":
        # 이전 입력값이 있으면 불러오기
        default_text = ""
        if st.session_state.students:
            default_text = "\n".join([f"{s['번호']} {s['이름']}" for s in st.session_state.students])
        
        text_input = st.text_area(
            "학생 명단을 입력하세요 (예: 1 김민준\\n2 박서연)",
            value=default_text,
            placeholder="1 김민준\n2 박서연\n3 이도윤",
            height=150,
            key="student_text"
        )
        if text_input:
            df = parse_student_input(text_input)
            if not df.empty:
                st.success(f"{len(df)}명의 학생을 불러왔어요!")
                st.dataframe(df, use_container_width=True)
                if st.button("이 명단으로 진행", key="confirm_students"):
                    st.session_state.students = df.to_dict('records')
                    st.session_state.step = 2
                    st.rerun()
    
    else:  # CSV 업로드
        uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=['csv'], key="student_csv")
        if uploaded_file:
            df = load_csv_file(uploaded_file)
            if not df.empty:
                st.success(f"{len(df)}명의 학생을 불러왔어요!")
                st.dataframe(df, use_container_width=True)
                if st.button("이 명단으로 진행", key="confirm_csv"):
                    st.session_state.students = df.to_dict('records')
                    st.session_state.step = 2
                    st.rerun()
    
    st.markdown("💡 **팁**: 한글(.hwp) 파일은 표를 복사해 텍스트로 붙여넣거나 CSV로 저장해 업로드해 주세요.")
    st.markdown('</div>', unsafe_allow_html=True)

def step_2_seats():
    st.markdown('<div class="step-header">2단계: 자리 구조 입력</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("교실 자리 구조를 설정해 주세요.")
    
    num_groups = st.number_input("총 분단 수", min_value=1, max_value=10, value=4, key="num_groups")
    
    seats_per_group = []
    cols = st.columns(num_groups)
    for i in range(num_groups):
        with cols[i]:
            seats = st.number_input(f"{i+1}분단 좌석 수", min_value=1, max_value=20, value=5, key=f"group_{i}")
            seats_per_group.append(seats)
    
    total_seats = sum(seats_per_group)
    student_count = len(st.session_state.students)
    
    st.info(f"총 좌석 수: {total_seats}, 학생 수: {student_count}")
    
    if total_seats != student_count:
        st.warning("⚠️ 좌석 수와 학생 수가 맞지 않아요. 조정해 주세요.")
    else:
        st.success("✅ 좌석 구조가 설정되었습니다!")
        if st.button("다음 단계로", key="confirm_seats"):
            st.session_state.seats = build_seat_layout(num_groups, seats_per_group)
            st.session_state.seat_layout = {'num_groups': num_groups, 'seats_per_group': seats_per_group}
            st.session_state.step = 3
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def step_3_balance():
    st.markdown('<div class="step-header">3단계: 모둠 균형 배치 학생</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("각 모둠별로 1명씩 들어가면 좋을 학생들을 입력하세요.")
    st.markdown("이 학생들은 가능한 서로 다른 분단에 분산 배치됩니다.")
    
    balance_input = st.text_area(
        "학생 이름 입력 (쉼표로 구분)",
        placeholder="김갑수, 박은영, 조미진",
        key="balance_text"
    )
    
    if balance_input:
        names = [name.strip() for name in balance_input.split(',') if name.strip()]
        valid_names = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
        invalid_names = [name for name in names if name not in valid_names]
        
        if invalid_names:
            st.warning(f"명단에 없는 이름: {', '.join(invalid_names)}")
        
        if valid_names:
            st.success(f"균형 배치 학생 {len(valid_names)}명 확인됨")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("없음", key="no_balance"):
            st.session_state.balance_students = []
            st.session_state.step = 4
            st.rerun()
    with col2:
        if st.button("입력 완료", key="confirm_balance"):
            if balance_input:
                names = [name.strip() for name in balance_input.split(',') if name.strip()]
                st.session_state.balance_students = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
            st.session_state.step = 4
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def step_4_separation():
    st.markdown('<div class="step-header">4단계: 분리 배치 학생 세트</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("서로 멀리 떨어뜨려 배치할 학생 세트를 입력하세요.")
    st.markdown("**입력 예시:**")
    st.markdown("- 한 줄에 한 세트씩 입력")
    st.markdown("- 학생 이름은 띄어쓰기, 쉼표, 하이픈(-) 중 아무거나 사용 가능")
    st.markdown("- 예: 박은영 조미진")
    st.markdown("- 예: 김민수,이지후")
    st.markdown("- 예: 최도윤-김민준")
    
    separation_input = st.text_area(
        "세트별로 한 줄씩 입력",
        placeholder="박은영 조미진\n김민수 이지후 최도윤",
        height=100,
        key="separation_text"
    )
    
    groups = []
    if separation_input:
        lines = separation_input.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 다양한 구분자 처리
            names = re.split(r'[,\-\s/]+', line)
            names = [name.strip() for name in names if name.strip()]
            if names:
                valid_names = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
                if valid_names:
                    groups.append(valid_names)
        
        st.success(f"분리 배치 세트 {len(groups)}개 확인됨")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("없음", key="no_separation"):
            st.session_state.separation_groups = []
            st.session_state.step = 5
            st.rerun()
    with col2:
        if st.button("입력 완료", key="confirm_separation"):
            if separation_input:
                lines = separation_input.strip().split('\n')
                groups = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    names = re.split(r'[,\-\s/]+', line)
                    names = [name.strip() for name in names if name.strip()]
                    valid_names = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
                    if valid_names:
                        groups.append(valid_names)
                st.session_state.separation_groups = groups
            st.session_state.step = 5
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def step_5_front_priority():
    st.markdown('<div class="step-header">5단계: 앞줄 우선 학생</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("앞자리에 앉히면 좋은 학생들을 입력하세요.")
    
    front_input = st.text_area(
        "학생 이름 입력 (쉼표로 구분)",
        placeholder="김민준, 박서연",
        key="front_text"
    )
    
    if front_input:
        names = [name.strip() for name in front_input.split(',') if name.strip()]
        valid_names = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
        if valid_names:
            st.success(f"앞줄 우선 학생 {len(valid_names)}명 확인됨")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("없음", key="no_front"):
            st.session_state.front_priority = []
            st.session_state.step = 6
            st.rerun()
    with col2:
        if st.button("입력 완료", key="confirm_front"):
            if front_input:
                names = [name.strip() for name in front_input.split(',') if name.strip()]
                st.session_state.front_priority = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
            st.session_state.step = 6
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def step_6_back_priority():
    st.markdown('<div class="step-header">6단계: 뒷줄 우선 학생</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("뒷자리에 앉히면 좋은 학생들을 입력하세요.")
    
    back_input = st.text_area(
        "학생 이름 입력 (쉼표로 구분)",
        placeholder="이도윤, 최민수",
        key="back_text"
    )
    
    if back_input:
        names = [name.strip() for name in back_input.split(',') if name.strip()]
        valid_names = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
        if valid_names:
            st.success(f"뒷줄 우선 학생 {len(valid_names)}명 확인됨")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("없음", key="no_back"):
            st.session_state.back_priority = []
            st.session_state.step = 7
            st.rerun()
    with col2:
        if st.button("입력 완료", key="confirm_back"):
            if back_input:
                names = [name.strip() for name in back_input.split(',') if name.strip()]
                st.session_state.back_priority = [name for name in names if any(s['이름'] == name for s in st.session_state.students)]
            st.session_state.step = 7
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def step_7_generate():
    st.markdown('<div class="step-header">7단계: 자리 배정 실행</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("입력하신 조건을 반영하여 최적의 자리 배치를 생성합니다.")
    
    # 조건 요약
    st.markdown("**입력된 조건 요약:**")
    st.write(f"- 모둠 균형 배치 학생: {len(st.session_state.balance_students)}명")
    st.write(f"- 분리 배치 세트: {len(st.session_state.separation_groups)}개")
    st.write(f"- 앞줄 우선 학생: {len(st.session_state.front_priority)}명")
    st.write(f"- 뒷줄 우선 학생: {len(st.session_state.back_priority)}명")
    
    if st.button("자리 배정 시작", key="generate"):
        with st.spinner("최적 배치를 찾는 중..."):
            arrangement = generate_best_arrangement(
                st.session_state.students,
                st.session_state.seats,
                st.session_state.balance_students,
                st.session_state.separation_groups,
                st.session_state.front_priority,
                st.session_state.back_priority
            )
            st.session_state.arrangement = arrangement
            st.session_state.step = 8
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def step_8_result():
    st.markdown('<div class="step-header">8단계: 결과 확인 및 수정</div>', unsafe_allow_html=True)
    
    # 결과 표시
    render_seat_map(st.session_state.arrangement, st.session_state.seats)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ✏️ 직접 수정")
    st.markdown("마음에 들지 않는 부분이 있다면 직접 수정하세요.")
    
    # 수정 방식 선택
    edit_mode = st.radio("수정 방식", ["좌석별 학생 변경", "학생 자리 교환"], key="edit_mode")
    
    if edit_mode == "좌석별 학생 변경":
        st.markdown("각 좌석의 학생을 선택하세요:")
        cols = st.columns(3)
        for i, seat in enumerate(st.session_state.seats):
            with cols[i % 3]:
                current_student = next((name for name, seat_num in st.session_state.arrangement.items() if seat_num == seat['좌석번호']), "")
                options = [""] + [s['이름'] for s in st.session_state.students]
                try:
                    default_index = options.index(current_student) if current_student else 0
                except ValueError:
                    default_index = 0
                new_student = st.selectbox(
                    f"좌석 {seat['좌석번호']} ({seat['분단']}분단)",
                    options,
                    index=default_index,
                    key=f"seat_{seat['좌석번호']}"
                )
                if new_student and new_student != current_student:
                    # 기존 자리 비우기
                    if current_student and current_student in st.session_state.arrangement:
                        del st.session_state.arrangement[current_student]
                    # 새 자리 할당
                    st.session_state.arrangement[new_student] = seat['좌석번호']
    
    else:  # 학생 자리 교환
        st.markdown("교환할 두 학생을 선택하세요:")
        col1, col2 = st.columns(2)
        with col1:
            student1 = st.selectbox("첫 번째 학생", [s['이름'] for s in st.session_state.students], key="swap1")
        with col2:
            student2 = st.selectbox("두 번째 학생", [s['이름'] for s in st.session_state.students], key="swap2")
        
        if student1 and student2 and student1 != student2:
            if st.button("자리 교환", key="swap"):
                seat1 = st.session_state.arrangement[student1]
                seat2 = st.session_state.arrangement[student2]
                st.session_state.arrangement[student1] = seat2
                st.session_state.arrangement[student2] = seat1
                st.success("자리 교환이 완료되었습니다!")
                st.rerun()
    
    # 최종 확정
    if st.button("최종 자리 확정", key="finalize"):
        st.success("자리 배치가 확정되었습니다!")
        # CSV 다운로드
        df_result = pd.DataFrame([
            {'이름': name, '좌석번호': seat_num, **next(s for s in st.session_state.seats if s['좌석번호'] == seat_num)}
            for name, seat_num in st.session_state.arrangement.items()
        ])
        csv = df_result.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="결과 CSV 다운로드",
            data=csv,
            file_name="자리배치결과.csv",
            mime="text/csv",
            key="download"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)

# 진행 상태 표시
steps = [
    "1단계: 환영", "2단계: 학생 명단", "3단계: 자리 구조", "4단계: 모둠 균형", "5단계: 분리 배치", "6단계: 앞줄 우선", "7단계: 뒷줄 우선", "8단계: 배정 실행", "9단계: 결과 확인"
]
progress = (st.session_state.step / (len(steps) - 1)) * 100
st.markdown(f'<div class="progress-bar"><div class="progress-fill" style="width: {progress}%"></div></div>', unsafe_allow_html=True)
st.markdown(f"**진행 단계: {steps[st.session_state.step]}**")

# 이전 단계 버튼
if st.session_state.step > 0:
    if st.button("◀ 이전 단계", key="prev"):
        st.session_state.step -= 1
        st.rerun()

# 단계별 UI 호출
if st.session_state.step == 0:
    step_0_welcome()
elif st.session_state.step == 1:
    step_1_students()
elif st.session_state.step == 2:
    step_2_seats()
elif st.session_state.step == 3:
    step_3_balance()
elif st.session_state.step == 4:
    step_4_separation()
elif st.session_state.step == 5:
    step_5_front_priority()
elif st.session_state.step == 6:
    step_6_back_priority()
elif st.session_state.step == 7:
    step_7_generate()
elif st.session_state.step == 8:
    step_8_result()

# 사용 안내
st.markdown("---")
st.markdown("**사용 안내:** 이 앱은 초등학교 학급 자리 바꾸기를 돕기 위해 만들어졌습니다. 단계별로 입력하시면 최적의 배치를 자동 생성해 드려요. 결과가 마음에 들지 않으면 직접 수정할 수도 있어요!")
