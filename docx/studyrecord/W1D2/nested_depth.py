"""
计算列表最大嵌套深度模块
"""
def get_max_depth(lst: list) -> int:
    """
    计算传入列表的最大嵌套深度。
    
    规则：
    - 非列表对象嵌套深度为 0（若作为顶层输入传入则抛出 TypeError）。
    - 空列表 [] 深度为 1。
    - 嵌套列表的深度为其所有子列表最大深度 + 1。
    
    :param lst: 待计算的列表
    :return: 最大嵌套深度（int）
    :raises TypeError: 当顶层输入不是列表时抛出
    """
    if not isinstance(lst, list):
        raise TypeError(f"Expected a list, got {type(lst).__name__}")
    
    # 递归计算所有子列表的嵌套深度
    sub_depths = [get_max_depth(item) for item in lst if isinstance(item, list)]
    
    if not sub_depths:
        return 1
    
    return 1 + max(sub_depths)
