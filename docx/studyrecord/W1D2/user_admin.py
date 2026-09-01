from typing import List, Optional


class User:
    """
    用户基类
    """
    def __init__(self, first_name: str, last_name: str, age: Optional[int] = None, email: Optional[str] = None):
        """
        初始化用户信息
        :param first_name: 名字
        :param last_name: 姓氏
        :param age: 年龄（可选）
        :param email: 邮箱（可选）
        """
        self.first_name = first_name
        self.last_name = last_name
        self.age = age
        self.email = email

    def describe_user(self) -> None:
        """
        打印用户详细信息
        """
        print(f"--- 用户信息 ---")
        print(f"姓名: {self.first_name} {self.last_name}")
        if self.age is not None:
            print(f"年龄: {self.age}")
        if self.email is not None:
            print(f"邮箱: {self.email}")

    def greet_user(self) -> None:
        """
        向用户打印个性化问候语
        """
        print(f"你好, {self.first_name} {self.last_name}！欢迎回来！")


class Admin(User):
    """
    管理员类，继承自 User
    """
    def __init__(
        self,
        first_name: str,
        last_name: str,
        privileges: Optional[List[str]] = None,
        age: Optional[int] = None,
        email: Optional[str] = None
    ):
        """
        初始化管理员信息及权限列表
        :param first_name: 名字
        :param last_name: 姓氏
        :param privileges: 权限列表，默认为基础管理员权限
        :param age: 年龄（可选）
        :param email: 邮箱（可选）
        """
        super().__init__(first_name, last_name, age=age, email=email)
        if privileges is None:
            self.privileges = [
                "can add post",
                "can delete post",
                "can ban user"
            ]
        else:
            self.privileges = privileges

    def show_privileges(self) -> None:
        """
        显示管理员的所有权限
        """
        print(f"管理员 {self.first_name} {self.last_name} 的权限列表:")
        for idx, privilege in enumerate(self.privileges, start=1):
            print(f"  {idx}. {privilege}")


def main():
    print("=================== 1. 普通用户实例演示 ===================")
    normal_user = User("San", "Zhang", age=25, email="zhangsan@example.com")
    normal_user.describe_user()
    normal_user.greet_user()

    print("\n=================== 2. 管理员实例演示 ===================")
    admin_user = Admin("Nijika", "Ijichi", age=17, email="admin@starry.com")
    
    # 调用 Admin 实例的所有方法
    admin_user.describe_user()
    admin_user.greet_user()
    admin_user.show_privileges()

    print("\n=================== 3. 自定义权限管理员演示 ===================")
    super_admin = Admin(
        "Ryo",
        "Yamada",
        privileges=["can add post", "can delete post", "can ban user", "can manage system", "can view logs"]
    )
    super_admin.describe_user()
    super_admin.greet_user()
    super_admin.show_privileges()


if __name__ == '__main__':
    main()
