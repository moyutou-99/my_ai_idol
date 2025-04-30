from typing import Dict, Set

class PermissionManager:
    """权限管理器，用于管理不同等级Agent的权限"""
    
    def __init__(self):
        # 定义各等级Agent的权限集合
        self._permissions: Dict[int, Set[str]] = {
            0: set(),  # 无Agent，无权限
            1: {
                'file.read',
                'file.create',
                'file.delete',
                'system.info',
                'process.list'
            },  # 初级Agent权限
            2: {
                'file.*',
                'system.*',
                'network.*',
                'process.*',
                'task.plan',
                'memory.long_term'
            },  # 中级Agent权限
            3: {'*'}  # 高级Agent权限，拥有所有权限
        }
    
    def check_permission(self, level: int, permission: str) -> bool:
        """检查指定等级的Agent是否具有特定权限"""
        if level not in self._permissions:
            return False
        
        # 如果是最高级Agent，直接返回True
        if level == 3:
            return True
        
        # 检查具体权限
        permissions = self._permissions[level]
        if '*' in permissions:
            return True
        
        # 检查通配符权限
        for perm in permissions:
            if perm.endswith('.*'):
                prefix = perm[:-2]
                if permission.startswith(prefix):
                    return True
        
        return permission in permissions
    
    def get_permissions(self, level: int) -> Set[str]:
        """获取指定等级Agent的所有权限"""
        return self._permissions.get(level, set()) 