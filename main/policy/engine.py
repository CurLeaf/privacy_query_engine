"""
PolicyEngine - 策略引擎
职责: 根据分析结果和预设规则，决定使用DP还是DeID
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..analyzer import AnalysisResult
from .config import ConfigManager


@dataclass
class PolicyDecision:
    """策略决策结果"""
    action: str  # "DP" | "DeID" | "PASS"
    params: Dict[str, Any] = field(default_factory=dict)
    matched_rule: Optional[str] = None
    reason: str = ""


class PolicyEngine:
    """策略引擎"""
    
    # 默认敏感列
    DEFAULT_SENSITIVE_COLUMNS = ["name", "email", "phone", "id_card", "ssn", "mobile"]
    
    def __init__(self, config: ConfigManager = None):
        """
        初始化策略引擎
        
        Args:
            config: 配置管理器实例
        """
        self.config = config or ConfigManager()
        self.sensitive_columns = self.config.get_sensitive_columns() or self.DEFAULT_SENSITIVE_COLUMNS
    
    def evaluate(self, analysis_result: AnalysisResult) -> PolicyDecision:
        """
        评估分析结果，返回策略决策
        
        Args:
            analysis_result: SQL分析结果
            
        Returns:
            PolicyDecision对象
        """
        # 检查SQL是否有效
        if not analysis_result.is_valid:
            return PolicyDecision(
                action="REJECT",
                reason=f"Invalid SQL: {analysis_result.error_message}"
            )
        
        # 规则1: 聚合查询 -> 使用差分隐私
        if analysis_result.is_aggregate_query or analysis_result.aggregations:
            return self._create_dp_decision(analysis_result)
        
        # 规则2: 包含敏感列 -> 使用去标识化
        if self._has_sensitive_columns(analysis_result):
            return self._create_deid_decision(analysis_result)
        
        # 默认: 透传 (MVP阶段可以考虑默认拒绝)
        return PolicyDecision(
            action="PASS",
            reason="No privacy protection required"
        )
    
    def _has_sensitive_columns(self, analysis_result: AnalysisResult) -> bool:
        """检查是否包含敏感列"""
        select_cols_lower = [col.lower() for col in analysis_result.select_columns]
        return any(
            col in self.sensitive_columns 
            for col in select_cols_lower
        )
    
    def _create_dp_decision(self, analysis_result: AnalysisResult) -> PolicyDecision:
        """创建差分隐私决策"""
        epsilon = self.config.get_default_epsilon()
        
        return PolicyDecision(
            action="DP",
            params={
                "epsilon": epsilon,
                "mechanism": "laplace",
                "sensitivity": 1.0,
            },
            matched_rule="aggregation_rule",
            reason=f"Aggregation detected: {analysis_result.aggregations}"
        )
    
    def _create_deid_decision(self, analysis_result: AnalysisResult) -> PolicyDecision:
        """创建去标识化决策"""
        # 找出需要脱敏的列
        cols_to_mask = [
            col for col in analysis_result.select_columns
            if col.lower() in self.sensitive_columns
        ]
        
        return PolicyDecision(
            action="DeID",
            params={
                "method": "hash",
                "columns": cols_to_mask,
            },
            matched_rule="sensitive_column_rule",
            reason=f"Sensitive columns detected: {cols_to_mask}"
        )

