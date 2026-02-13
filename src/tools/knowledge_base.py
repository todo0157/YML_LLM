"""
3D 프린팅 지식베이스
- 재료별 가이드
- 결함 해결 가이드
- 사용자 실험 데이터
"""
import json
from pathlib import Path
from typing import Optional


class KnowledgeBase:
    """3D 프린팅 도메인 지식베이스"""

    def __init__(self, data_path: Optional[Path] = None):
        if data_path is None:
            data_path = Path(__file__).parent.parent.parent / "data"
        self.data_path = data_path
        self._load_data()

    def _load_data(self):
        """데이터 로드"""
        # 사용자 실험 데이터
        experiments_file = self.data_path / "sample_experiments.json"
        if experiments_file.exists():
            with open(experiments_file, "r", encoding="utf-8") as f:
                self.experiments = json.load(f)
        else:
            self.experiments = []

        # 재료별 가이드 (내장)
        self.material_guides = {
            "PLA": {
                "name": "PLA (Polylactic Acid)",
                "nozzle_temp": {"min": 190, "max": 220, "optimal": 205},
                "bed_temp": {"min": 50, "max": 65, "optimal": 60},
                "print_speed": {"min": 40, "max": 100, "optimal": 60},
                "retraction": {"distance": 5, "speed": 45},
                "fan_speed": 100,
                "tips": [
                    "가장 출력이 쉬운 재료",
                    "냉각이 중요 - 팬 100% 권장",
                    "고온 시 stringing 발생 가능",
                    "베드 접착: PEI 시트 또는 유리 + 풀스틱"
                ]
            },
            "ABS": {
                "name": "ABS (Acrylonitrile Butadiene Styrene)",
                "nozzle_temp": {"min": 220, "max": 260, "optimal": 240},
                "bed_temp": {"min": 90, "max": 110, "optimal": 100},
                "print_speed": {"min": 40, "max": 60, "optimal": 50},
                "retraction": {"distance": 4, "speed": 40},
                "fan_speed": 0,
                "tips": [
                    "인클로저 필수 권장",
                    "워핑 방지를 위해 팬 끄기",
                    "베드 온도 높게 유지",
                    "Brim 또는 Raft 사용 권장",
                    "환기 필요 - 유해 가스 발생"
                ]
            },
            "PETG": {
                "name": "PETG (Polyethylene Terephthalate Glycol)",
                "nozzle_temp": {"min": 220, "max": 250, "optimal": 230},
                "bed_temp": {"min": 70, "max": 85, "optimal": 75},
                "print_speed": {"min": 30, "max": 60, "optimal": 45},
                "retraction": {"distance": 5, "speed": 35},
                "fan_speed": 50,
                "tips": [
                    "Stringing 발생하기 쉬움 - retraction 중요",
                    "온도에 민감 - 너무 높으면 stringing 심함",
                    "베드 접착력이 강함 - 분리 시 주의",
                    "습기에 민감 - 건조 보관 필수",
                    "첫 레이어 속도 낮추기 권장"
                ]
            },
            "TPU": {
                "name": "TPU (Thermoplastic Polyurethane)",
                "nozzle_temp": {"min": 220, "max": 250, "optimal": 230},
                "bed_temp": {"min": 50, "max": 70, "optimal": 60},
                "print_speed": {"min": 15, "max": 30, "optimal": 25},
                "retraction": {"distance": 2, "speed": 20},
                "fan_speed": 50,
                "tips": [
                    "매우 느린 속도로 출력",
                    "Direct Drive 익스트루더 권장",
                    "Retraction 최소화 또는 비활성화",
                    "Bowden 튜브에서는 출력 어려움"
                ]
            }
        }

        # 결함 해결 가이드 (내장)
        self.defect_guides = {
            "stringing": {
                "name": "Stringing (실뜨기)",
                "description": "이동 경로에 가는 실 같은 필라멘트 잔여물이 남음",
                "causes": [
                    "노즐 온도가 너무 높음",
                    "Retraction 설정 부족",
                    "필라멘트 습기",
                    "Travel 속도가 너무 느림"
                ],
                "solutions": [
                    {"action": "노즐 온도 5-10°C 낮추기", "priority": 1},
                    {"action": "Retraction distance 1-2mm 증가", "priority": 2},
                    {"action": "Retraction speed 10-20mm/s 증가", "priority": 3},
                    {"action": "Travel speed 150mm/s 이상으로 증가", "priority": 4},
                    {"action": "필라멘트 건조 (50°C, 4-6시간)", "priority": 5}
                ]
            },
            "warping": {
                "name": "Warping (뒤틀림)",
                "description": "출력물 모서리가 베드에서 들뜸",
                "causes": [
                    "베드 온도 부족",
                    "냉각이 너무 빠름",
                    "베드 접착력 부족",
                    "주변 온도 차이"
                ],
                "solutions": [
                    {"action": "베드 온도 5-10°C 높이기", "priority": 1},
                    {"action": "Brim (8-10mm) 추가", "priority": 2},
                    {"action": "인클로저 사용 (ABS)", "priority": 3},
                    {"action": "첫 레이어 팬 속도 0%", "priority": 4},
                    {"action": "베드 접착제 사용 (풀스틱, 헤어스프레이)", "priority": 5}
                ]
            },
            "layer_adhesion": {
                "name": "Layer Adhesion (레이어 접착 불량)",
                "description": "레이어 간 접착이 약해 쉽게 분리됨",
                "causes": [
                    "노즐 온도가 너무 낮음",
                    "레이어 높이가 너무 높음",
                    "출력 속도가 너무 빠름",
                    "과도한 냉각"
                ],
                "solutions": [
                    {"action": "노즐 온도 5-10°C 높이기", "priority": 1},
                    {"action": "레이어 높이 줄이기 (노즐 직경의 75%)", "priority": 2},
                    {"action": "출력 속도 10-20% 낮추기", "priority": 3},
                    {"action": "팬 속도 줄이기", "priority": 4}
                ]
            },
            "under_extrusion": {
                "name": "Under Extrusion (과소 압출)",
                "description": "필라멘트가 충분히 압출되지 않아 틈이 생김",
                "causes": [
                    "노즐 막힘",
                    "필라멘트 경로 마찰",
                    "온도 부족",
                    "익스트루더 그립 부족"
                ],
                "solutions": [
                    {"action": "노즐 청소 또는 교체", "priority": 1},
                    {"action": "Flow rate 5-10% 증가", "priority": 2},
                    {"action": "노즐 온도 5-10°C 높이기", "priority": 3},
                    {"action": "출력 속도 낮추기", "priority": 4},
                    {"action": "익스트루더 텐션 조정", "priority": 5}
                ]
            },
            "over_extrusion": {
                "name": "Over Extrusion (과다 압출)",
                "description": "필라멘트가 과다하게 압출되어 표면이 울퉁불퉁",
                "causes": [
                    "Flow rate가 너무 높음",
                    "필라멘트 직경 설정 오류",
                    "E-steps 캘리브레이션 오류"
                ],
                "solutions": [
                    {"action": "Flow rate 5-10% 낮추기", "priority": 1},
                    {"action": "필라멘트 직경 캘리브레이션", "priority": 2},
                    {"action": "E-steps 재캘리브레이션", "priority": 3}
                ]
            },
            "first_layer": {
                "name": "First Layer Issues (첫 레이어 문제)",
                "description": "첫 레이어가 베드에 잘 붙지 않음",
                "causes": [
                    "베드 레벨링 불량",
                    "노즐-베드 거리가 너무 멂",
                    "베드 온도 부족",
                    "베드 표면 오염"
                ],
                "solutions": [
                    {"action": "베드 레벨링 재수행", "priority": 1},
                    {"action": "Z-offset 조정 (노즐 더 가깝게)", "priority": 2},
                    {"action": "베드 온도 5-10°C 높이기", "priority": 3},
                    {"action": "첫 레이어 속도 50% 낮추기", "priority": 4},
                    {"action": "첫 레이어 Flow 105-110%", "priority": 5},
                    {"action": "베드 IPA로 청소", "priority": 6}
                ]
            }
        }

    def get_material_guide(self, material: str) -> Optional[str]:
        """재료별 가이드 반환"""
        material = material.upper()
        guide = self.material_guides.get(material)

        if not guide:
            return None

        # 텍스트 형식으로 변환
        text = f"""
재료: {guide['name']}

권장 설정:
- 노즐 온도: {guide['nozzle_temp']['optimal']}°C (범위: {guide['nozzle_temp']['min']}-{guide['nozzle_temp']['max']}°C)
- 베드 온도: {guide['bed_temp']['optimal']}°C (범위: {guide['bed_temp']['min']}-{guide['bed_temp']['max']}°C)
- 출력 속도: {guide['print_speed']['optimal']}mm/s (범위: {guide['print_speed']['min']}-{guide['print_speed']['max']}mm/s)
- Retraction: {guide['retraction']['distance']}mm @ {guide['retraction']['speed']}mm/s
- 팬 속도: {guide['fan_speed']}%

팁:
{chr(10).join(['- ' + tip for tip in guide['tips']])}
"""
        return text

    def get_defect_solution(self, defect: str) -> Optional[str]:
        """결함 해결 가이드 반환"""
        defect = defect.lower().replace(" ", "_")

        # 별칭 매핑
        aliases = {
            "adhesion": "first_layer",
            "bed_adhesion": "first_layer",
            "sticking": "first_layer",
            "oozing": "stringing",
            "warp": "warping",
            "delamination": "layer_adhesion",
        }
        defect = aliases.get(defect, defect)

        guide = self.defect_guides.get(defect)

        if not guide:
            return None

        text = f"""
결함: {guide['name']}
설명: {guide['description']}

원인:
{chr(10).join(['- ' + cause for cause in guide['causes']])}

해결책 (우선순위순):
{chr(10).join([f"{s['priority']}. {s['action']}" for s in guide['solutions']])}
"""
        return text

    def search_similar_experiments(
        self,
        material: Optional[str] = None,
        defect: Optional[str] = None,
        limit: int = 3
    ) -> list[dict]:
        """유사 실험 데이터 검색"""
        results = []

        for exp in self.experiments:
            score = 0

            # 재료 매칭
            if material:
                if exp.get("material", {}).get("type", "").upper() == material.upper():
                    score += 2

            # 결함 매칭
            if defect:
                exp_defects = exp.get("result", {}).get("defects", [])
                if defect.lower() in [d.lower() for d in exp_defects]:
                    score += 3

            if score > 0:
                results.append((score, exp))

        # 점수순 정렬
        results.sort(key=lambda x: x[0], reverse=True)

        return [exp for _, exp in results[:limit]]

    def add_experiment(self, experiment: dict):
        """새 실험 데이터 추가"""
        self.experiments.append(experiment)

        # 파일에 저장
        experiments_file = self.data_path / "sample_experiments.json"
        with open(experiments_file, "w", encoding="utf-8") as f:
            json.dump(self.experiments, f, ensure_ascii=False, indent=2)
