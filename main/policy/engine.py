"""
PolicyEngine - 策略引擎 (v3.0 Enhanced)
职责: 根据分析结果和预设规则，决定使用DP还是DeID
支持角色基础隐私参数、模式匹配、数据分类规则
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..analyzer import AnalysisResult
from .config import ConfigManager, DataClassification, RoleConfig, ColumnPattern


@dataclass
class PolicyDecision:
    """策略决策结果"""
    action: str  # "DP" | "DeID" | "PASS" | "REJECT"
    params: Dict[str, Any] = field(default_factory=dict)
    matched_rule: Optional[str] = None
    reason: str = ""
    classification: Optional[DataClassification] = None
    role_applied: Optional[str] = None


class PolicyEngine:
    """策略引擎 (v3.0 Enhanced)"""
    
    # 默认敏感列
    DEFAULT_SENSITIVE_COLUMNS = ["name", "email", "phone", "id_card", "ssn", "mobile"]
    
    def __init__(self, config: ConfigManager = None, config_path: str = None):
        """
        初始化策略引擎
        
        Args:
            config: 配置管理器实例
            config_path: 配置文件路径
        """
        if config:
            self.config = config
        elif config_path:
            self.config = ConfigManager(config_path=config_path, enable_hot_reload=True)
        else:
            self.config = ConfigManager()
        
        self.sensitive_columns = self.config.get_sensitive_columns() or self.DEFAULT_SENSITIVE_COLUMNS
        
        # 注册配置重载回调
        self.config.on_reload(self._on_config_reload)
    
    def _on_config_reload(self, old_config: Dict, new_config: Dict):
        """配置重载回调"""
        self.sensitive_columns = self.config.get_sensitive_columns() or self.DEFAULT_SENSITIVE_COLUMNS
    
    def evaluate(
        self, 
        analysis_result: AnalysisResult,
        user_role: str = None,
        context: Dict[str, Any] = None,
    ) -> PolicyDecision:
        """
        评估分析结果，返回策略决策
        
        Args:
            analysis_result: SQL分析结果
            user_role: 用户角色 (v3.0)
            context: 额外上下文 (v3.0)
            
        Returns:
            PolicyDecision对象
        """
        context = context or {}
        
        # 检查SQL是否有效
        if not analysis_result.is_valid:
            return PolicyDecision(
                action="REJECT",
                reason=f"Invalid SQL: {analysis_result.error_message}"
            )
        
        # 获取角色配置 (v3.0)
        role_config = None
        if user_role:
            role_config = self.config.get_role_config(user_role)
        
        # 检查表访问权限 (v3.0)
        if role_config:
            access_check = self._check_table_access(analysis_result, role_config)
            if access_check:
                return access_check
        
        # 获取最高数据分类级别 (v3.0)
        classification = self._get_highest_classification(analysis_result)
        
        # 检查列模式匹配 (v3.0)
        pattern_decision = self._check_column_patterns(analysis_result)
        if pattern_decision:
            pattern_decision.classification = classification
            pattern_decision.role_applied = user_role
            return pattern_decision
        
        # 规则1: 聚合查询 -> 使用差分隐私
        if analysis_result.is_aggregate_query or analysis_result.aggregations:
            decision = self._create_dp_decision(analysis_result, role_config, classification)
            decision.role_applied = user_role
            return decision
        
        # 规则2: 包含敏感列 -> 使用去标识化
        if self._has_sensitive_columns(analysis_result):
            decision = self._create_deid_decision(analysis_result, role_config)
            decision.classification = classification
            decision.role_applied = user_role
            return decision
        
        # 默认: 透传
        return PolicyDecision(
            action="PASS",
            reason="No privacy protection required",
            classification=classification,
            role_applied=user_role,
        )
    
    def _check_table_access(
        self, 
        analysis_result: AnalysisResult, 
        role_config: RoleConfig,
    ) -> Optional[PolicyDecision]:
        """检查表访问权限 (v3.0)"""
        tables = analysis_result.tables
        
        # 检查拒绝列表
        for table in tables:
            if table in role_config.denied_tables:
                return PolicyDecision(
                    action="REJECT",
                    reason=f"Access denied to table: {table}",
                    matched_rule="role_table_deny",
                )
        
        # 检查允许列表 (如果配置了)
        if role_config.allowed_tables:
            for table in tables:
                if table not in role_config.allowed_tables:
                    return PolicyDecision(
                        action="REJECT",
                        reason=f"Table not in allowed list: {table}",
                        matched_rule="role_table_allow",
                    )
        
        return None
    
    def _get_highest_classification(self, analysis_result: AnalysisResult) -> DataClassification:
        """获取最高数据分类级别 (v3.0)"""
        highest = DataClassification.PUBLIC
        classification_order = [
            DataClassification.PUBLIC,
            DataClassification.INTERNAL,
            DataClassification.CONFIDENTIAL,
            DataClassification.RESTRICTED,
        ]
        
        for table in analysis_result.tables:
            table_policy = self.config.get_table_policy(table)
            if table_policy:
                table_class = table_policy.classification
                if classification_order.index(table_class) > classification_order.index(highest):
                    highest = table_class
        
        return highest
    
    def _check_column_patterns(self, analysis_result: AnalysisResult) -> Optional[PolicyDecision]:
        """检查列模式匹配 (v3.0)"""
        patterns = self.config.get_column_patterns()
        
        for column in analysis_result.select_columns:
            for pattern in patterns:
                if pattern.matches(column):
                    return PolicyDecision(
                        action=pattern.privacy_method,
                        params=pattern.params.copy(),
                        matched_rule=f"pattern:{pattern.pattern}",
                        reason=f"Column {column} matches pattern {pattern.pattern}",
                        classification=pattern.classification,
                    )
        
        return None
    
    def _has_sensitive_columns(self, analysis_result: AnalysisResult) -> bool:
        """检查是否包含敏感列"""
        select_cols_lower = [col.lower() for col in analysis_result.select_columns]
        return any(
            col in self.sensitive_columns 
            for col in select_cols_lower
        )
    
    def _create_dp_decision(
        self, 
        analysis_result: AnalysisResult,
        role_config: Optional[RoleConfig] = None,
        classification: DataClassification = None,
    ) -> PolicyDecision:
        """创建差分隐私决策"""
        # 基础epsilon
        epsilon = self.config.get_default_epsilon()
        delta = 1e-5
        
        # 应用角色配置 (v3.0)
        if role_config:
            epsilon = role_config.epsilon
            delta = role_config.delta
        
        # 应用分类规则 (v3.0)
        if classification:
            class_rules = self.config.get_classification_rules(classification)
            # 使用更严格的epsilon (较小值)
            class_epsilon = class_rules.get("epsilon", epsilon)
            epsilon = min(epsilon, class_epsilon)
        
        return PolicyDecision(
            action="DP",
            params={
                "epsilon": epsilon,
                "delta": delta,
                "mechanism": "laplace",
                "sensitivity": 1.0,
            },
            matched_rule="aggregation_rule",
            reason=f"Aggregation detected: {analysis_result.aggregations}",
            classification=classification,
        )
    
    def _create_deid_decision(
        self, 
        analysis_result: AnalysisResult,
        role_config: Optional[RoleConfig] = None,
    ) -> PolicyDecision:
        """创建去标识化决策"""
        # 找出需要脱敏的列
        cols_to_mask = [
            col for col in analysis_result.select_columns
            if col.lower() in self.sensitive_columns
        ]
        
        # 检查角色是否有列限制 (v3.0)
        if role_config and role_config.denied_columns:
            cols_to_mask.extend([
                col for col in analysis_result.select_columns
                if col.lower() in [c.lower() for c in role_config.denied_columns]
            ])
            cols_to_mask = list(set(cols_to_mask))
        
        return PolicyDecision(
            action="DeID",
            params={
                "method": "hash",
                "columns": cols_to_mask,
            },
            matched_rule="sensitive_column_rule",
            reason=f"Sensitive columns detected: {cols_to_mask}"
        )
    
    def get_policy_for_role(self, role_name: str) -> Optional[RoleConfig]:
        """获取角色策略 (v3.0)"""
        return self.config.get_role_config(role_name)
    
    def add_sensitive_column(self, column: str):
        """动态添加敏感列 (v3.0)"""
        if column.lower() not in self.sensitive_columns:
            self.sensitive_columns.append(column.lower())
    
    def remove_sensitive_column(self, column: str):
        """动态移除敏感列 (v3.0)"""
        col_lower = column.lower()
        if col_lower in self.sensitive_columns:
            self.sensitive_columns.remove(col_lower)
    
    def resolve_policy_conflicts(
        self, 
        decisions: List[PolicyDecision],
    ) -> PolicyDecision:
        """
        解决策略冲突 - 应用最严格的策略 (v3.0)
        
        Args:
            decisions: 多个策略决策
            
        Returns:
            最终决策
        """
        if not decisions:
            return PolicyDecision(action="PASS", reason="No policies to apply")
        
        # 优先级: REJECT > DP > DeID > PASS
        action_priority = {"REJECT": 4, "DP": 3, "DeID": 2, "PASS": 1}
        
        # 找到最高优先级的决策
        sorted_decisions = sorted(
            decisions, 
            key=lambda d: action_priority.get(d.action, 0),
            reverse=True,
        )
        
        winner = sorted_decisions[0]
        
        # 如果有多个DP决策，使用最小的epsilon
        if winner.action == "DP":
            dp_decisions = [d for d in decisions if d.action == "DP"]
            if len(dp_decisions) > 1:
                min_epsilon = min(d.params.get("epsilon", 1.0) for d in dp_decisions)
                winner.params["epsilon"] = min_epsilon
                winner.reason += f" (most restrictive epsilon: {min_epsilon})"
        
        return winner

