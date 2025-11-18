"""AHP (Analytic Hierarchy Process) Calculator Module"""

import numpy as np
from typing import Dict, List, Tuple, Optional


class AHPCalculator:
    """AHP 계산을 수행하는 클래스"""
    
    # AHP 일관성 지수 (Random Index) - Saaty의 표준값
    RANDOM_INDEX = {
        1: 0.00,
        2: 0.00,
        3: 0.58,
        4: 0.90,
        5: 1.12,
        6: 1.24,
        7: 1.32,
        8: 1.41,
        9: 1.45,
        10: 1.49
    }
    
    def __init__(self, max_cr: float = 0.10, max_retries: int = 3):
        """
        AHP 계산기 초기화
        
        Args:
            max_cr: 최대 허용 일관성 비율 (기본값: 0.10)
            max_retries: CR 실패 시 최대 재시도 횟수 (기본값: 3)
        """
        self.max_cr = max_cr
        self.max_retries = max_retries
    
    def create_pairwise_matrix(
        self,
        criteria: List[str],
        comparisons: Dict[Tuple[str, str], float]
    ) -> np.ndarray:
        """
        쌍대비교 행렬 생성
        
        Args:
            criteria: 기준 리스트 (예: ['취업', '적성', '안정성'])
            comparisons: 쌍대비교 결과 딕셔너리
                예: {('취업', '적성'): 3.0} → 취업이 적성보다 3배 중요
            
        Returns:
            n×n 쌍대비교 행렬 (numpy array)
        """
        n = len(criteria)
        matrix = np.ones((n, n))  # 대각선은 모두 1
        
        # 상삼각 행렬 채우기
        for i in range(n):
            for j in range(i + 1, n):
                criterion_a = criteria[i]
                criterion_b = criteria[j]
                
                # (A, B) 비교값 찾기
                if (criterion_a, criterion_b) in comparisons:
                    value = comparisons[(criterion_a, criterion_b)]
                    matrix[i, j] = value
                    matrix[j, i] = 1.0 / value  # 역수
                # (B, A) 비교값 찾기
                elif (criterion_b, criterion_a) in comparisons:
                    value = comparisons[(criterion_b, criterion_a)]
                    matrix[j, i] = value
                    matrix[i, j] = 1.0 / value  # 역수
                else:
                    # 비교값이 없으면 동등하다고 가정
                    matrix[i, j] = 1.0
                    matrix[j, i] = 1.0
        
        return matrix
    
    def calculate_weights(self, matrix: np.ndarray) -> np.ndarray:
        """
        고유값 방법으로 가중치 계산
        
        Args:
            matrix: 쌍대비교 행렬
            
        Returns:
            정규화된 가중치 벡터 (합 = 1.0)
        """
        # 고유값과 고유벡터 계산
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        
        # 최대 고유값의 인덱스 찾기
        max_eigenvalue_idx = np.argmax(eigenvalues.real)
        
        # 최대 고유값에 해당하는 고유벡터 추출
        principal_eigenvector = eigenvectors[:, max_eigenvalue_idx].real
        
        # 정규화 (합이 1이 되도록)
        weights = principal_eigenvector / principal_eigenvector.sum()
        
        return weights
    
    def calculate_consistency_ratio(
        self,
        matrix: np.ndarray,
        weights: np.ndarray
    ) -> Tuple[float, float]:
        """
        일관성 비율(CR) 계산
        
        Args:
            matrix: 쌍대비교 행렬
            weights: 가중치 벡터
            
        Returns:
            (lambda_max, CR) 튜플
            - lambda_max: 최대 고유값
            - CR: 일관성 비율 (≤0.10이면 통과)
        """
        n = len(matrix)
        
        # λ_max 계산
        weighted_sum = matrix @ weights  # 행렬-벡터 곱
        lambda_max = (weighted_sum / weights).mean()
        
        # CI (일관성 지수) 계산
        ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
        
        # RI (무작위 지수) 가져오기
        ri = self.RANDOM_INDEX.get(n, 1.49)
        
        # CR (일관성 비율) 계산
        cr = ci / ri if ri > 0 else 0.0
        
        return lambda_max, cr
    
    def validate_consistency(
        self,
        matrix: np.ndarray
    ) -> Tuple[bool, float, float, np.ndarray]:
        """
        행렬의 일관성 검증
        
        Args:
            matrix: 쌍대비교 행렬
            
        Returns:
            (is_valid, lambda_max, cr, weights) 튜플
            - is_valid: CR ≤ max_cr인지 여부
            - lambda_max: 최대 고유값
            - cr: 일관성 비율
            - weights: 가중치 벡터
        """
        # 가중치 계산
        weights = self.calculate_weights(matrix)
        
        # CR 계산
        lambda_max, cr = self.calculate_consistency_ratio(matrix, weights)
        
        # 일관성 검증
        is_valid = cr <= self.max_cr
        
        return is_valid, lambda_max, cr, weights
    
    def process_ahp(
        self,
        criteria: List[str],
        comparisons: Dict[Tuple[str, str], float]
    ) -> Dict:
        """
        전체 AHP 프로세스 실행
        
        Args:
            criteria: 기준 리스트
            comparisons: 쌍대비교 결과
            
        Returns:
            AHP 결과 딕셔너리:
            {
                'status': 'passed' 또는 'failed',
                'weights': {기준명: 가중치} 딕셔너리,
                'lambda_max': 최대 고유값,
                'cr': 일관성 비율,
                'matrix': 쌍대비교 행렬,
                'retry_count': 재시도 횟수
            }
        """
        # 쌍대비교 행렬 생성
        matrix = self.create_pairwise_matrix(criteria, comparisons)
        
        # 일관성 검증
        is_valid, lambda_max, cr, weight_vector = self.validate_consistency(matrix)
        
        # 가중치 딕셔너리 생성
        weights_dict = {
            criterion: float(weight)
            for criterion, weight in zip(criteria, weight_vector)
        }
        
        return {
            'status': 'passed' if is_valid else 'failed',
            'weights': weights_dict,
            'lambda_max': float(lambda_max),
            'cr': float(cr),
            'matrix': matrix.tolist(),
            'retry_count': 0  # 실제 재시도는 상위 레이어에서 처리
        }
    
    def geometric_mean_method(self, matrix: np.ndarray) -> np.ndarray:
        """
        기하평균 방법으로 가중치 계산 (대안적 방법)
        
        Args:
            matrix: 쌍대비교 행렬
            
        Returns:
            정규화된 가중치 벡터
        """
        n = len(matrix)
        
        # 각 행의 기하평균 계산
        geometric_means = np.zeros(n)
        for i in range(n):
            row_product = np.prod(matrix[i, :])
            geometric_means[i] = row_product ** (1.0 / n)
        
        # 정규화
        weights = geometric_means / geometric_means.sum()
        
        return weights
