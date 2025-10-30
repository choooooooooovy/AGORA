"""TOPSIS Calculator Module"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

class TOPSISCalculator:
    """TOPSIS 계산을 수행하는 클래스"""
    
    def __init__(self):
        """TOPSIS 계산기 초기화"""
        pass
    
    def create_decision_matrix(
        self,
        alternatives: List[str],
        criteria: List[str],
        scores: Dict[str, Dict[str, float]]
    ) -> pd.DataFrame:
        """
        의사결정 행렬 생성
        
        Args:
            alternatives: 대안 리스트 (예: ['컴퓨터공학', '경영학', '심리학'])
            criteria: 기준 리스트 (예: ['취업', '적성', '안정성'])
            scores: 점수 딕셔너리
                예: {'컴퓨터공학': {'취업': 8.5, '적성': 7.0, '안정성': 9.0}}
            
        Returns:
            의사결정 행렬 (DataFrame)
        """
        data = []
        for alt in alternatives:
            row = [scores.get(alt, {}).get(crit, 0.0) for crit in criteria]
            data.append(row)
        
        df = pd.DataFrame(data, index=alternatives, columns=criteria)
        return df
    
    def normalize_matrix(
        self,
        matrix: pd.DataFrame,
        method: str = 'vector'
    ) -> pd.DataFrame:
        """
        의사결정 행렬 정규화
        
        Args:
            matrix: 원본 의사결정 행렬
            method: 정규화 방법
                - 'vector': 벡터 정규화 (기본값, TOPSIS 표준)
                - 'minmax': 최소-최대 정규화
            
        Returns:
            정규화된 행렬
        """
        if method == 'vector':
            # 벡터 정규화: r_ij = x_ij / sqrt(sum(x_ij^2))
            normalized = matrix / np.sqrt((matrix ** 2).sum(axis=0))
        elif method == 'minmax':
            # 최소-최대 정규화: r_ij = (x_ij - min) / (max - min)
            normalized = (matrix - matrix.min()) / (matrix.max() - matrix.min())
        else:
            raise ValueError(f"Unknown normalization method: {method}")
        
        return normalized
    
    def apply_weights(
        self,
        normalized_matrix: pd.DataFrame,
        weights: Dict[str, float]
    ) -> pd.DataFrame:
        """
        가중치 적용
        
        Args:
            normalized_matrix: 정규화된 행렬
            weights: 기준별 가중치 딕셔너리
                예: {'취업': 0.5, '적성': 0.3, '안정성': 0.2}
            
        Returns:
            가중 정규화 행렬
        """
        weighted_matrix = normalized_matrix.copy()
        
        for criterion in normalized_matrix.columns:
            weight = weights.get(criterion, 0.0)
            weighted_matrix[criterion] = normalized_matrix[criterion] * weight
        
        return weighted_matrix
    
    def identify_ideal_solutions(
        self,
        weighted_matrix: pd.DataFrame,
        criterion_types: Dict[str, str]
    ) -> Tuple[pd.Series, pd.Series]:
        """
        이상해/반이상해 식별
        
        Args:
            weighted_matrix: 가중 정규화 행렬
            criterion_types: 기준 타입 딕셔너리
                - 'benefit': 클수록 좋음 (예: 취업률, 만족도)
                - 'cost': 작을수록 좋음 (예: 학비, 난이도)
            
        Returns:
            (ideal_solution, anti_ideal_solution) 튜플
        """
        ideal = pd.Series(index=weighted_matrix.columns, dtype=float)
        anti_ideal = pd.Series(index=weighted_matrix.columns, dtype=float)
        
        for criterion in weighted_matrix.columns:
            crit_type = criterion_types.get(criterion, 'benefit')
            
            if crit_type == 'benefit':
                # benefit: 최댓값이 이상적, 최솟값이 부정적
                ideal[criterion] = weighted_matrix[criterion].max()
                anti_ideal[criterion] = weighted_matrix[criterion].min()
            else:  # cost
                # cost: 최솟값이 이상적, 최댓값이 부정적
                ideal[criterion] = weighted_matrix[criterion].min()
                anti_ideal[criterion] = weighted_matrix[criterion].max()
        
        return ideal, anti_ideal
    
    def calculate_distances(
        self,
        weighted_matrix: pd.DataFrame,
        ideal: pd.Series,
        anti_ideal: pd.Series
    ) -> Tuple[pd.Series, pd.Series]:
        """
        각 대안과 이상해/반이상해 간의 유클리드 거리 계산
        
        Args:
            weighted_matrix: 가중 정규화 행렬
            ideal: 이상해
            anti_ideal: 반이상해
            
        Returns:
            (distance_to_ideal, distance_to_anti_ideal) 튜플
        """
        # 이상해까지의 거리
        distance_to_ideal = np.sqrt(
            ((weighted_matrix - ideal) ** 2).sum(axis=1)
        )
        
        # 반이상해까지의 거리
        distance_to_anti_ideal = np.sqrt(
            ((weighted_matrix - anti_ideal) ** 2).sum(axis=1)
        )
        
        return distance_to_ideal, distance_to_anti_ideal
    
    def calculate_closeness_coefficient(
        self,
        distance_to_ideal: pd.Series,
        distance_to_anti_ideal: pd.Series
    ) -> pd.Series:
        """
        근접도 계수(closeness coefficient) 계산
        
        Args:
            distance_to_ideal: 이상적 해까지의 거리
            distance_to_anti_ideal: 부정적 해까지의 거리
            
        Returns:
            근접도 계수 (0~1, 클수록 좋음)
        """
        closeness = distance_to_anti_ideal / (
            distance_to_ideal + distance_to_anti_ideal
        )
        
        return closeness
    
    def rank_alternatives(
        self,
        closeness: pd.Series
    ) -> pd.DataFrame:
        """
        근접도 기준으로 대안 순위 매기기
        
        Args:
            closeness: 근접도 계수
            
        Returns:
            순위 정보 DataFrame (alternative, closeness, rank)
        """
        ranking = pd.DataFrame({
            'alternative': closeness.index,
            'closeness': closeness.values
        })
        
        # 내림차순 정렬 (closeness가 높을수록 좋음)
        ranking = ranking.sort_values('closeness', ascending=False)
        ranking['rank'] = range(1, len(ranking) + 1)
        
        return ranking.reset_index(drop=True)
    
    def process_topsis(
        self,
        alternatives: List[str],
        criteria: List[str],
        scores: Dict[str, Dict[str, float]],
        weights: Dict[str, float],
        criterion_types: Dict[str, str]
    ) -> Dict:
        """
        전체 TOPSIS 프로세스 실행
        
        Args:
            alternatives: 대안 리스트
            criteria: 기준 리스트
            scores: 점수 딕셔너리
            weights: 기준별 가중치
            criterion_types: 기준 타입 (benefit/cost)
            
        Returns:
            TOPSIS 결과 딕셔너리:
            {
                'ranking': [순위별 대안 정보],
                'decision_matrix': 원본 행렬,
                'normalized_matrix': 정규화 행렬,
                'weighted_matrix': 가중 행렬,
                'ideal_solution': 이상적 해,
                'anti_ideal_solution': 부정적 해,
                'distances': {alternative: (d+, d-)} 딕셔너리
            }
        """
        # 1. 의사결정 행렬 생성
        decision_matrix = self.create_decision_matrix(alternatives, criteria, scores)
        
        # 2. 정규화
        normalized_matrix = self.normalize_matrix(decision_matrix)
        
        # 3. 가중치 적용
        weighted_matrix = self.apply_weights(normalized_matrix, weights)
        
        # 4. 이상적 해 식별
        ideal, anti_ideal = self.identify_ideal_solutions(
            weighted_matrix, criterion_types
        )
        
        # 5. 거리 계산
        dist_ideal, dist_anti_ideal = self.calculate_distances(
            weighted_matrix, ideal, anti_ideal
        )
        
        # 6. 근접도 계산
        closeness = self.calculate_closeness_coefficient(dist_ideal, dist_anti_ideal)
        
        # 7. 순위 매기기
        ranking_df = self.rank_alternatives(closeness)
        
        # 결과 포맷팅
        ranking_list = []
        for _, row in ranking_df.iterrows():
            alt = row['alternative']
            ranking_list.append({
                'major': alt,
                'rank': int(row['rank']),
                'closeness_coefficient': float(row['closeness']),
                'distance_to_ideal': float(dist_ideal[alt]),
                'distance_to_anti_ideal': float(dist_anti_ideal[alt]),
                'criterion_scores': scores.get(alt, {}),
                'weighted_scores': {
                    crit: float(weighted_matrix.loc[alt, crit])
                    for crit in criteria
                }
            })
        
        return {
            'ranking': ranking_list,
            'decision_matrix': decision_matrix.to_dict(),
            'normalized_matrix': normalized_matrix.to_dict(),
            'weighted_matrix': weighted_matrix.to_dict(),
            'ideal_solution': ideal.to_dict(),
            'anti_ideal_solution': anti_ideal.to_dict()
        }
