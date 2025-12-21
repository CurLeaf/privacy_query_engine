"""
CSV 隐私处理和评估示例

演示如何使用 CSVPrivacyProcessor 和 PrivacyUtilityEvaluator
"""
from main.data import CSVPrivacyProcessor, SchemaDetector
from main.data.csv_processor import ProcessingConfig
from main.evaluation import PrivacyUtilityEvaluator, EvaluationConfig


def main():
    # 示例数据
    sample_data = [
        {"id": 1, "name": "张三", "email": "zhangsan@example.com", "phone": "13812345678", "age": 25, "zipcode": "100001", "disease": "感冒"},
        {"id": 2, "name": "李四", "email": "lisi@example.com", "phone": "13987654321", "age": 32, "zipcode": "100001", "disease": "发烧"},
        {"id": 3, "name": "王五", "email": "wangwu@example.com", "phone": "13611112222", "age": 28, "zipcode": "100002", "disease": "感冒"},
        {"id": 4, "name": "赵六", "email": "zhaoliu@example.com", "phone": "13733334444", "age": 45, "zipcode": "100002", "disease": "高血压"},
        {"id": 5, "name": "钱七", "email": "qianqi@example.com", "phone": "13855556666", "age": 38, "zipcode": "100001", "disease": "感冒"},
        {"id": 6, "name": "孙八", "email": "sunba@example.com", "phone": "13977778888", "age": 52, "zipcode": "100003", "disease": "糖尿病"},
        {"id": 7, "name": "周九", "email": "zhoujiu@example.com", "phone": "13199990000", "age": 29, "zipcode": "100001", "disease": "发烧"},
        {"id": 8, "name": "吴十", "email": "wushi@example.com", "phone": "13288881111", "age": 35, "zipcode": "100002", "disease": "感冒"},
    ]
    
    print("=" * 60)
    print("1. 自动检测数据模式")
    print("=" * 60)
    
    # 自动检测数据模式
    detector = SchemaDetector()
    schema = detector.detect(sample_data)
    
    print(f"检测到 {len(schema.columns)} 列:")
    for col_name, col_schema in schema.columns.items():
        print(f"  - {col_name}: {col_schema.data_type.value}, "
              f"敏感度: {col_schema.sensitivity.value}, "
              f"推荐方法: {col_schema.recommended_method}")
    
    print(f"\n直接标识符: {schema.direct_identifiers}")
    print(f"敏感属性: {schema.sensitive_attributes}")
    print(f"准标识符: {schema.quasi_identifiers}")
    
    print("\n" + "=" * 60)
    print("2. 处理数据（自动脱敏）")
    print("=" * 60)
    
    # 创建处理器
    processor = CSVPrivacyProcessor()
    
    # 配置处理参数
    config = ProcessingConfig(
        auto_detect=True,
        k_anonymity=2,  # K-匿名化
        quasi_identifiers=["age", "zipcode"],
        sensitive_attribute="disease",
        l_diversity=2,  # L-多样性
    )
    
    # 处理数据
    result = processor.process_data(sample_data, config)
    
    print(f"处理成功: {result.success}")
    print(f"原始行数: {result.original_row_count}")
    print(f"处理后行数: {result.processed_row_count}")
    print(f"处理的列: {result.columns_processed}")
    print(f"应用的方法: {result.methods_applied}")
    
    print("\n处理后的数据示例:")
    for row in result.data[:3]:
        print(f"  {row}")
    
    print("\n" + "=" * 60)
    print("3. 评估脱敏效果")
    print("=" * 60)
    
    # 创建评估器
    evaluator = PrivacyUtilityEvaluator()
    
    # 配置评估参数
    eval_config = EvaluationConfig(
        quasi_identifiers=["age", "zipcode"],
        sensitive_attribute="disease",
        numeric_columns=["age"],
        categorical_columns=["zipcode", "disease"],
        target_k=2,
        target_l=2,
    )
    
    # 执行评估
    report = evaluator.evaluate(sample_data, result.data, eval_config)
    
    # 打印评估报告
    print(report.summary())
    
    print("\n" + "=" * 60)
    print("4. 快速评估")
    print("=" * 60)
    
    quick_result = evaluator.quick_evaluate(
        sample_data, 
        result.data, 
        quasi_identifiers=["age", "zipcode"]
    )
    
    print("快速评估结果:")
    for key, value in quick_result.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
