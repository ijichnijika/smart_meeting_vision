"""
列表最大嵌套深度单元测试模块
"""
import unittest
from nested_depth import get_max_depth


class TestGetMaxDepth(unittest.TestCase):
    """
    测试 get_max_depth 函数的各种场景与边界条件
    """

    def test_flat_list(self):
        """测试用例 1：扁平列表（无嵌套），深度为 1"""
        self.assertEqual(get_max_depth([1, 2, 3]), 1)
        self.assertEqual(get_max_depth(["a", "b", "c"]), 1)

    def test_example_nested_list(self):
        """测试用例 2：题目样例列表 [[1], [2, [3]]]，深度为 3"""
        self.assertEqual(get_max_depth([[1], [2, [3]]]), 3)

    def test_empty_list(self):
        """测试用例 3：空列表边界，深度为 1"""
        self.assertEqual(get_max_depth([]), 1)

    def test_nested_empty_lists(self):
        """测试用例 4：包含空列表的嵌套结构 [[], [[]]]，深度为 3"""
        self.assertEqual(get_max_depth([[], [[]]]), 3)

    def test_deep_single_branch(self):
        """测试用例 5：深层单链嵌套 [[[[[100]]]]]，深度为 5"""
        self.assertEqual(get_max_depth([[[[[100]]]]]), 5)

    def test_mixed_types_and_multiple_branches(self):
        """测试用例 6：混合类型与多分支结构"""
        sample = [1, "hello", [2, [3, [4]]], 5, True]
        self.assertEqual(get_max_depth(sample), 4)

    def test_invalid_input_raises_type_error(self):
        """测试用例 7：非列表类型入参抛出 TypeError"""
        with self.assertRaises(TypeError):
            get_max_depth("not a list")
        with self.assertRaises(TypeError):
            get_max_depth(12345)
        with self.assertRaises(TypeError):
            get_max_depth((1, 2, 3))


if __name__ == '__main__':
    unittest.main(verbosity=2)
